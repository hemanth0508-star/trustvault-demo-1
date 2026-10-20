from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class AuditEvent(models.Model):

    EVENT_CHOICES = [
        ("UPLOAD", "Document Uploaded"),
        ("DOWNLOAD", "Document Downloaded"),
        ("ACCESS_DENIED", "Access Denied"),
        ("PERMISSION_GRANTED", "Permission Granted"),
        ("PERMISSION_REVOKED", "Permission Revoked"),
        ("DOCUMENT_EDITED", "Document Edited"),
        ("DOCUMENT_DELETED", "Document Deleted"),
    ]

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )

    document = models.ForeignKey(
        "documents.Document",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )

    event_type = models.CharField(
        max_length=30,
        choices=EVENT_CHOICES,
    )

    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    success = models.BooleanField(default=True)

    details = models.JSONField(default=dict, blank=True)

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Audit Event"
        verbose_name_plural = "Audit Events"

    def save(self, *args, **kwargs):
        # Prevent updating an existing audit record
        # through the normal Django model save operation.
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError(
                "Existing audit records cannot be modified."
            )

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Prevent deleting an audit record through
        # the normal Django model delete operation.
        raise ValidationError(
            "Audit records cannot be deleted."
        )

    def __str__(self):
        return (
            f"{self.event_type} | "
            f"{self.actor_id} | "
            f"{self.timestamp}"
        )