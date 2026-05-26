from django.contrib import admin
from .models import Company, UserProfile, DataSource, EmissionRecord, AuditLog


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'company']
    list_select_related = ['user', 'company']


@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ['filename', 'source_type', 'company', 'uploaded_by', 'uploaded_at', 'row_count']
    list_filter = ['source_type', 'company']


@admin.register(EmissionRecord)
class EmissionRecordAdmin(admin.ModelAdmin):
    list_display = ['activity_type', 'quantity', 'unit', 'activity_date', 'scope', 'status', 'flag', 'company']
    list_filter = ['status', 'flag', 'scope', 'company']
    readonly_fields = ['raw_data', 'created_at', 'updated_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'actor', 'timestamp', 'record']
    list_filter = ['action']
    readonly_fields = ['record', 'actor', 'action', 'detail', 'timestamp']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
