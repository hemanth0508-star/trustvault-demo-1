from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from audit.models import AuditEvent
from documents.models import Document

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

    def test_non_staff_user_only_sees_their_own_events(self):
        own_event = AuditEvent.objects.create(
            actor=self.viewer,
            event_type="UPLOAD",
            details={"document_title": "My private report"},
        )
        other_event = AuditEvent.objects.create(
            actor=self.staff,
            event_type="UPLOAD",
            details={"document_title": "Staff-only report"},
        )
        self.client.force_login(self.viewer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context["events"]),
            [own_event],
        )
        self.assertNotContains(response, "Staff-only report")
        self.assertNotContains(response, "Search username")

    def test_non_staff_cannot_expand_activity_with_username_filter(self):
        AuditEvent.objects.create(
            actor=self.viewer,
            event_type="UPLOAD",
        )
        AuditEvent.objects.create(
            actor=self.staff,
            event_type="UPLOAD",
            details={"document_title": "Other profile event"},
        )
        self.client.force_login(self.viewer)

        response = self.client.get(self.url, {"username": "audit_staff"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["events"]), 1)
        self.assertNotContains(response, "Other profile event")

    def test_non_staff_cannot_see_titles_of_documents_they_cannot_read(self):
        document = Document.objects.create(
            title="Another users confidential file",
            owner=self.staff,
        )
        event = AuditEvent.objects.create(
            actor=self.viewer,
            document=document,
            event_type="ACCESS_DENIED",
            success=False,
            details={"action": "download"},
        )
        self.client.force_login(self.viewer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["events"]), [event])
        self.assertNotContains(response, document.title)
        self.assertContains(response, "Unavailable")

    def test_staff_user_can_access_dashboard(self):
        document = Document.objects.create(
            title="Staff-visible document",
            owner=self.staff,
        )
        staff_event = AuditEvent.objects.create(
            actor=self.staff,
            document=document,
            event_type="UPLOAD",
        )
        viewer_event = AuditEvent.objects.create(
            actor=self.viewer,
            event_type="DOWNLOAD",
        )
        self.client.force_login(self.staff)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.context["events"]),
            {staff_event, viewer_event},
        )
        self.assertContains(response, document.title)

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