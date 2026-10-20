from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    ROLE_ADMIN = "ADMIN"
    ROLE_OWNER = "OWNER"
    ROLE_VIEWER = "VIEWER"

    ROLE_CHOICES = [
        (ROLE_ADMIN, "Administrator"),
        (ROLE_OWNER, "Document Owner"),
        (ROLE_VIEWER, "Viewer"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trustvault_profile",
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default=ROLE_VIEWER,
    )

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"