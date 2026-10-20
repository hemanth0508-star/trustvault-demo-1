from django.contrib import admin
from .models import Document, DocumentPermission


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "category", "created_at")
    list_filter = ("category", "created_at")
    search_fields = ("title", "owner__username")
    readonly_fields = ("created_at", "updated_at")


@admin.register(DocumentPermission)
class DocumentPermissionAdmin(admin.ModelAdmin):
    list_display = (
        "document",
        "user",
        "can_read",
        "can_edit",
        "granted_by",
        "granted_at",
    )
    list_filter = ("can_read", "can_edit", "granted_at")
    search_fields = ("document__title", "user__username")
    readonly_fields = ("granted_at",)