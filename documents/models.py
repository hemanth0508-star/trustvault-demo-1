from django.conf import settings
from django.db import models


class Document(models.Model):
    CATEGORY_CHOICES = [
        ("CONTRACT", "Contract"),
        ("SALARY", "Salary Document"),
        ("FINANCIAL", "Financial Document"),
        ("TECHNICAL", "Technical Document"),
        ("OTHER", "Other"),
    ]

    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="documents/")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_documents",
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="OTHER",
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
class DocumentPermission(models.Model):
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name="permissions",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="document_permissions",
    )
    can_read = models.BooleanField(default=True)
    can_edit = models.BooleanField(default=False)
    granted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="granted_document_permissions",
    )
    granted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["document", "user"],
                name="unique_document_permission",
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.document.title}"