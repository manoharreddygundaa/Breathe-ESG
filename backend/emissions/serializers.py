from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Company, DataSource, EmissionRecord, AuditLog


class UserSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='profile.company.name', read_only=True)
    company_id = serializers.IntegerField(source='profile.company.id', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'company_name', 'company_id']


class DataSourceSerializer(serializers.ModelSerializer):
    uploaded_by_name = serializers.CharField(source='uploaded_by.username', read_only=True)

    class Meta:
        model = DataSource
        fields = [
            'id', 'source_type', 'filename', 'uploaded_at',
            'row_count', 'failed_count', 'suspicious_count',
            'uploaded_by_name',
        ]


class EmissionRecordListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list views — excludes raw_data."""
    data_source_name = serializers.CharField(source='data_source.filename', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True)

    class Meta:
        model = EmissionRecord
        fields = [
            'id', 'scope', 'activity_type', 'quantity', 'unit',
            'activity_date', 'location', 'description',
            'status', 'flag', 'flag_reason',
            'data_source', 'data_source_name', 'source_row_index',
            'reviewed_by_name', 'reviewed_at', 'analyst_note',
            'created_at',
        ]


class EmissionRecordDetailSerializer(serializers.ModelSerializer):
    """Full serializer including raw_data, used on detail endpoints."""
    data_source_name = serializers.CharField(source='data_source.filename', read_only=True)
    reviewed_by_name = serializers.CharField(source='reviewed_by.username', read_only=True)

    class Meta:
        model = EmissionRecord
        fields = '__all__'
        read_only_fields = [
            'company', 'data_source', 'source_row_index',
            'scope', 'activity_type', 'raw_data',
            'reviewed_by', 'reviewed_at',
            'created_at', 'updated_at',
        ]

    def validate(self, data):
        # Approved records are locked — no edits allowed
        if self.instance and self.instance.status == 'approved':
            raise serializers.ValidationError("Approved records are locked and cannot be edited.")
        return data


class ReviewActionSerializer(serializers.Serializer):
    """Used for approve/reject actions. Separate from the record serializer."""
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    analyst_note = serializers.CharField(required=False, allow_blank=True)

    # Optional field edits allowed before approval
    quantity = serializers.DecimalField(max_digits=14, decimal_places=4, required=False)
    unit = serializers.CharField(max_length=20, required=False)
    activity_date = serializers.DateField(required=False)
    analyst_note = serializers.CharField(required=False, allow_blank=True)


class AuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor.username', read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'action', 'detail', 'actor_name', 'timestamp']


class DashboardStatsSerializer(serializers.Serializer):
    """Summary stats for the dashboard header."""
    total = serializers.IntegerField()
    pending = serializers.IntegerField()
    approved = serializers.IntegerField()
    rejected = serializers.IntegerField()
    failed = serializers.IntegerField()
    suspicious = serializers.IntegerField()
    by_scope = serializers.DictField()
