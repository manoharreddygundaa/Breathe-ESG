from django.db import models
from django.contrib.auth.models import User


class Company(models.Model):
    """
    Represents an enterprise client. Every record belongs to a company.
    Simple multi-tenancy: analysts are tied to a company via UserProfile.
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'companies'


class UserProfile(models.Model):
    """
    Extends Django's User. Ties an analyst to a company.
    Not trying to build RBAC here — one role, one company.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='analysts')

    def __str__(self):
        return f"{self.user.username} @ {self.company.name}"


class DataSource(models.Model):
    """
    Represents an upload batch from one of the three source types.
    Each CSV upload creates one DataSource. Records link back here.
    """
    SOURCE_TYPES = [
        ('sap_fuel', 'SAP Fuel & Procurement'),
        ('utility', 'Utility Electricity'),
        ('travel', 'Corporate Travel'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='data_sources')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    row_count = models.IntegerField(default=0)
    failed_count = models.IntegerField(default=0)
    suspicious_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.source_type} – {self.filename} ({self.uploaded_at.date()})"


class EmissionRecord(models.Model):
    """
    The normalized representation of one activity row, regardless of source.

    Scope classification:
    - Scope 1: Direct combustion (SAP fuel)
    - Scope 2: Purchased electricity (utility)
    - Scope 3: Business travel, supply chain (travel)

    Status workflow:
    pending_review → approved (locked) or rejected
    suspicious rows still enter pending_review but are flagged

    Approved records are immutable for audit purposes.
    We enforce this in the serializer/view, not at DB level — good enough for a prototype.
    """
    SCOPE_CHOICES = [
        ('scope1', 'Scope 1 – Direct Emissions'),
        ('scope2', 'Scope 2 – Indirect (Electricity)'),
        ('scope3', 'Scope 3 – Value Chain'),
    ]

    STATUS_CHOICES = [
        ('pending_review', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('failed', 'Failed – Parse Error'),
    ]

    FLAG_CHOICES = [
        ('ok', 'No Issues'),
        ('suspicious', 'Suspicious – Needs Attention'),
        ('failed', 'Failed – Could Not Parse'),
    ]

    # Provenance
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='records')
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='records')
    source_row_index = models.IntegerField(help_text="Row number in original CSV, 1-indexed")

    # Normalized fields — these are what every source gets mapped into
    scope = models.CharField(max_length=10, choices=SCOPE_CHOICES)
    activity_type = models.CharField(max_length=100, help_text="e.g. diesel, electricity, flight")
    quantity = models.DecimalField(max_digits=14, decimal_places=4)
    unit = models.CharField(max_length=20, help_text="Normalized unit: L, kWh, km")
    activity_date = models.DateField(help_text="Normalized to YYYY-MM-DD")
    location = models.CharField(max_length=255, blank=True, help_text="Plant code, meter ID, or route")
    description = models.TextField(blank=True, help_text="Free text context from source")

    # Raw snapshot — what the original row actually said, as JSON
    raw_data = models.JSONField(help_text="Original CSV row, unmodified")

    # Review workflow
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending_review')
    flag = models.CharField(max_length=12, choices=FLAG_CHOICES, default='ok')
    flag_reason = models.TextField(blank=True, help_text="Why this row was flagged")

    # Analyst actions
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_records'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    analyst_note = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.activity_type} | {self.quantity} {self.unit} | {self.activity_date} [{self.status}]"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'scope']),
            models.Index(fields=['data_source']),
        ]


class AuditLog(models.Model):
    """
    Append-only log of analyst actions on records.
    We write here on approve/reject/edit. Never delete rows.
    """
    ACTION_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('edited', 'Edited Before Approval'),
        ('uploaded', 'Batch Uploaded'),
    ]

    record = models.ForeignKey(
        EmissionRecord, on_delete=models.CASCADE,
        related_name='audit_logs', null=True, blank=True,
        help_text="Null for batch-level events like uploads"
    )
    data_source = models.ForeignKey(
        DataSource, on_delete=models.CASCADE,
        related_name='audit_logs', null=True, blank=True
    )
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    detail = models.TextField(blank=True, help_text="What changed, or why rejected")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.actor} → {self.action} at {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']
