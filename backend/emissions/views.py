from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Q
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DataSource, EmissionRecord, AuditLog
from .serializers import (
    UserSerializer,
    DataSourceSerializer,
    EmissionRecordListSerializer,
    EmissionRecordDetailSerializer,
    ReviewActionSerializer,
    AuditLogSerializer,
    DashboardStatsSerializer,
)
from .parsers import parse_csv


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    """Returns the logged-in user with their company context."""
    # Ensure UserProfile exists
    if not hasattr(request.user, 'profile'):
        company, _ = Company.objects.get_or_create(
            slug='acme-corp',
            defaults={'name': 'Acme Corporation'}
        )
        UserProfile.objects.get_or_create(
            user=request.user,
            defaults={'company': company}
        )
    return Response(UserSerializer(request.user).data)


class DashboardStats(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Ensure UserProfile exists
        if not hasattr(request.user, 'profile'):
            company, _ = Company.objects.get_or_create(
                slug='acme-corp',
                defaults={'name': 'Acme Corporation'}
            )
            UserProfile.objects.get_or_create(
                user=request.user,
                defaults={'company': company}
            )
        company = request.user.profile.company
        qs = EmissionRecord.objects.filter(company=company)

        total = qs.count()
        pending = qs.filter(status='pending_review').count()
        approved = qs.filter(status='approved').count()
        rejected = qs.filter(status='rejected').count()
        failed = qs.filter(status='failed').count()
        suspicious = qs.filter(flag='suspicious').exclude(status__in=['approved', 'rejected']).count()

        by_scope = {}
        for item in qs.filter(status='approved').values('scope').annotate(count=Count('id')):
            by_scope[item['scope']] = item['count']

        return Response({
            'total': total,
            'pending': pending,
            'approved': approved,
            'rejected': rejected,
            'failed': failed,
            'suspicious': suspicious,
            'by_scope': by_scope,
        })


class UploadCSV(APIView):
    """
    POST /api/upload/
    Accepts: multipart/form-data with 'file' and 'source_type'
    Synchronously parses the CSV, creates records, returns a summary.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        file = request.FILES.get('file')
        source_type = request.data.get('source_type')

        if not file:
            return Response({'error': 'No file uploaded.'}, status=400)

        if source_type not in ('sap_fuel', 'utility', 'travel'):
            return Response({'error': 'Invalid source_type.'}, status=400)

        # Ensure UserProfile exists
        if not hasattr(request.user, 'profile'):
            company, _ = Company.objects.get_or_create(
                slug='acme-corp',
                defaults={'name': 'Acme Corporation'}
            )
            UserProfile.objects.get_or_create(
                user=request.user,
                defaults={'company': company}
            )
        company = request.user.profile.company

        try:
            parsed_rows = parse_csv(file, source_type)
        except Exception as e:
            return Response({'error': f'Could not parse CSV: {str(e)}'}, status=400)

        with transaction.atomic():
            data_source = DataSource.objects.create(
                company=company,
                uploaded_by=request.user,
                source_type=source_type,
                filename=file.name,
                row_count=len(parsed_rows),
            )

            records_to_create = []
            failed_count = 0
            suspicious_count = 0

            for row in parsed_rows:
                flag = row.get('flag', 'ok')
                normalized = row.get('normalized')

                # Skip rows that failed parsing — no valid data to insert.
                # failed_count still tracks them for the summary response.
                if flag == 'failed' or normalized is None:
                    failed_count += 1
                    continue

                if flag == 'suspicious':
                    suspicious_count += 1

                records_to_create.append(EmissionRecord(
                    company=company,
                    data_source=data_source,
                    source_row_index=row.get('row_index', 0),
                    scope=normalized.get('scope', 'scope3'),
                    activity_type=normalized.get('activity_type', 'unknown'),
                    quantity=normalized.get('quantity', 0),
                    unit=normalized.get('unit', ''),
                    activity_date=normalized.get('activity_date'),
                    location=normalized.get('location', ''),
                    description=normalized.get('description', ''),
                    raw_data=row.get('raw', {}),
                    status='pending_review',
                    flag=flag,
                    flag_reason=row.get('flag_reason', ''),
                ))

            EmissionRecord.objects.bulk_create(records_to_create)

            data_source.failed_count = failed_count
            data_source.suspicious_count = suspicious_count
            data_source.save()

            AuditLog.objects.create(
                data_source=data_source,
                actor=request.user,
                action='uploaded',
                detail=f"Uploaded {len(parsed_rows)} rows: {failed_count} failed, {suspicious_count} suspicious",
            )

        return Response({
            'data_source_id': data_source.id,
            'total_rows': len(parsed_rows),
            'pending_review': len(records_to_create),
            'failed': failed_count,
            'suspicious': suspicious_count,
        }, status=201)


class DataSourceList(generics.ListAPIView):
    serializer_class = DataSourceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Ensure UserProfile exists
        if not hasattr(self.request.user, 'profile'):
            company, _ = Company.objects.get_or_create(
                slug='acme-corp',
                defaults={'name': 'Acme Corporation'}
            )
            UserProfile.objects.get_or_create(
                user=self.request.user,
                defaults={'company': company}
            )
        return DataSource.objects.filter(
            company=self.request.user.profile.company
        ).order_by('-uploaded_at')


class EmissionRecordList(generics.ListAPIView):
    serializer_class = EmissionRecordListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Ensure UserProfile exists
        if not hasattr(self.request.user, 'profile'):
            company, _ = Company.objects.get_or_create(
                slug='acme-corp',
                defaults={'name': 'Acme Corporation'}
            )
            UserProfile.objects.get_or_create(
                user=self.request.user,
                defaults={'company': company}
            )
        company = self.request.user.profile.company
        qs = EmissionRecord.objects.filter(company=company)

        status_filter = self.request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)

        scope_filter = self.request.query_params.get('scope')
        if scope_filter:
            qs = qs.filter(scope=scope_filter)

        flag_filter = self.request.query_params.get('flag')
        if flag_filter:
            qs = qs.filter(flag=flag_filter)

        source_filter = self.request.query_params.get('data_source')
        if source_filter:
            qs = qs.filter(data_source_id=source_filter)

        return qs.select_related('data_source', 'reviewed_by')


class EmissionRecordDetail(generics.RetrieveUpdateAPIView):
    serializer_class = EmissionRecordDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return EmissionRecord.objects.filter(company=self.request.user.profile.company)

    def perform_update(self, serializer):
        instance = serializer.save()
        AuditLog.objects.create(
            record=instance,
            actor=self.request.user,
            action='edited',
            detail="Record fields updated before review",
        )


class ReviewRecord(APIView):
    """
    POST /api/records/<id>/review/
    Body: { "action": "approve"|"reject", "analyst_note": "...", ...optional field edits }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            record = EmissionRecord.objects.get(
                pk=pk,
                company=request.user.profile.company
            )
        except EmissionRecord.DoesNotExist:
            return Response({'error': 'Record not found.'}, status=404)

        if record.status == 'approved':
            return Response({'error': 'Record is already approved and locked.'}, status=400)

        if record.status == 'failed':
            return Response({'error': 'Failed records cannot be approved. Fix the data and re-upload.'}, status=400)

        serializer = ReviewActionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        action = serializer.validated_data['action']
        note = serializer.validated_data.get('analyst_note', '')

        # Apply optional field edits before locking
        edited_fields = []
        for field in ('quantity', 'unit', 'activity_date'):
            if field in serializer.validated_data:
                old_val = getattr(record, field)
                new_val = serializer.validated_data[field]
                if old_val != new_val:
                    setattr(record, field, new_val)
                    edited_fields.append(f"{field}: {old_val} → {new_val}")

        if action == 'approve':
            record.status = 'approved'
            audit_action = 'approved'
        else:
            record.status = 'rejected'
            audit_action = 'rejected'

        record.reviewed_by = request.user
        record.reviewed_at = timezone.now()
        record.analyst_note = note
        record.save()

        detail = note
        if edited_fields:
            detail = f"Edits: {'; '.join(edited_fields)}. Note: {note}"

        AuditLog.objects.create(
            record=record,
            actor=request.user,
            action=audit_action,
            detail=detail,
        )

        return Response(EmissionRecordDetailSerializer(record).data)


class RecordAuditLog(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        record_id = self.kwargs['pk']
        EmissionRecord.objects.get(
            pk=record_id,
            company=self.request.user.profile.company
        )
        return AuditLog.objects.filter(record_id=record_id)