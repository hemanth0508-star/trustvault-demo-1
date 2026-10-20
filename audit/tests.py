from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from audit.models import AuditEvent

User = get_user_model()


class AuditDashboardSecurityTests(TestCase):

    def setUp(self):
        self.viewer = User.objects.create_user(
            username="audit_viewer",
            password="Test-Password-123!",
        )

        self.staff = User.objects.create_user(
            username="audit_staff",
            password="Test-Password-456!",
            is_staff=True,
        )

        self.url = reverse("audit_dashboard")

    def test_anonymous_user_cannot_access_dashboard(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_non_staff_user_cannot_access_dashboard(self):
        self.client.force_login(self.viewer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)

    def test_staff_user_can_access_dashboard(self):
        self.client.force_login(self.staff)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)

    def test_existing_audit_event_cannot_be_modified(self):
        event = AuditEvent.objects.create(
            actor=self.staff,
            event_type="UPLOAD",
            success=True,
            details={"message": "Original audit event"},
        )

        event.success = False

        with self.assertRaises(ValidationError):
            event.save()

        event.refresh_from_db()

        self.assertTrue(event.success)
        self.assertEqual(
            event.details["message"],
            "Original audit event",
        )

    def test_existing_audit_event_cannot_be_deleted(self):
        event = AuditEvent.objects.create(
            actor=self.staff,
            event_type="UPLOAD",
            success=True,
            details={"message": "Keep this audit event"},
        )

        event_id = event.pk

        with self.assertRaises(ValidationError):
            event.delete()

        self.assertTrue(
            AuditEvent.objects.filter(pk=event_id).exists()
        )