from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    # Display important audit information.
    list_display = (
        "timestamp",
        "event_type",
        "actor",
        "document",
        "success",
        "ip_address",
    )

    # Allow administrators to filter audit events.
    list_filter = (
        "event_type",
        "success",
        "timestamp",
    )

    # Allow searching audit records.
    search_fields = (
        "actor__username",
        "document__title",
        "event_type",
        "ip_address",
    )

    # Newest events appear first.
    ordering = ("-timestamp",)

    # Make audit records read-only in Django Admin.
    readonly_fields = (
        "actor",
        "document",
        "event_type",
        "timestamp",
        "success",
        "details",
        "ip_address",
    )

    # Disable creating audit records manually.
    def has_add_permission(self, request):
        return False

    # Disable editing audit records.
    def has_change_permission(self, request, obj=None):
        return False

    # Disable deleting audit records.
    def has_delete_permission(self, request, obj=None):
        return False