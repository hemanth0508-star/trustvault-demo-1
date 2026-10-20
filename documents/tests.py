from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from audit.models import AuditEvent
from documents.forms import DocumentUploadForm, MAX_FILE_SIZE
from .models import Document, DocumentPermission


User = get_user_model()


class TrustVaultSecurityTests(TestCase):
    def test_viewer_cannot_revoke_another_users_permission(self):
            DocumentPermission.objects.create(
                document=self.document,
                user=self.viewer,
                can_read=True,
                can_edit=False,
                granted_by=self.owner,
            )
    
            self.client.force_login(self.viewer)
    
            revoke_url = reverse(
                "document_revoke",
                args=[self.document.pk, self.viewer.pk],
            )
    
            response = self.client.post(revoke_url)
    
            self.assertEqual(response.status_code, 404)
    
            self.assertTrue(
                DocumentPermission.objects.filter(
                    document=self.document,
                    user=self.viewer,
                ).exists()
            )

    def setUp(self):
        self.owner = User.objects.create_user(
            username="document_owner",
            password="Owner-Test-Password-123!",
        )

        self.viewer = User.objects.create_user(
            username="document_viewer",
            password="Viewer-Test-Password-123!",
        )

        self.editor = User.objects.create_user(
            username="document_editor",
            password="Editor-Test-Password-123!",
        )

        self.document = Document.objects.create(
            title="Confidential Test Document",
            description="Security test document",
            category="OTHER",
            owner=self.owner,
            file=SimpleUploadedFile(
                "confidential.txt",
                b"This is confidential test content.",
                content_type="text/plain",
            ),
        )

        self.download_url = reverse(
            "document_download",
            args=[self.document.pk],
        )

        self.edit_url = reverse(
            "document_edit",
            args=[self.document.pk],
        )

        self.delete_url = reverse(
            "document_delete",
            args=[self.document.pk],
        )

    def tearDown(self):
        # Clean up test files from storage.
        # Model deletion does not automatically remove FileField files.
        for document in Document.objects.filter(
            owner__username__in=[
                "document_owner",
                "document_viewer",
                "document_editor",
            ]
        ):
            if document.file:
                storage = document.file.storage
                file_name = document.file.name

                if file_name and storage.exists(file_name):
                    storage.delete(file_name)

    # --------------------------------------------------
    # DOWNLOAD AND AUTHORIZATION TESTS
    # --------------------------------------------------

    def test_anonymous_user_cannot_download_document(self):
        response = self.client.get(self.download_url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_unapproved_user_cannot_download_document(self):
        self.client.force_login(self.viewer)

        response = self.client.get(self.download_url)

        self.assertEqual(response.status_code, 404)

        self.assertTrue(
            AuditEvent.objects.filter(
                actor=self.viewer,
                document=self.document,
                event_type="ACCESS_DENIED",
                success=False,
            ).exists()
        )
    def test_inactive_user_cannot_download_document(self):
        DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            can_read=True,
            can_edit=False,
            granted_by=self.owner,
        )

        # Deactivate the user after permission has been granted.
        self.viewer.is_active = False
        self.viewer.save(update_fields=["is_active"])

        # Simulate an already authenticated session.
        self.client.force_login(self.viewer)

        response = self.client.get(self.download_url)

        # Django's standard authentication backend should reject
        # inactive users.
        self.assertNotEqual(response.status_code, 200)

    def test_owner_can_download_document(self):
        self.client.force_login(self.owner)

        response = self.client.get(self.download_url)

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            AuditEvent.objects.filter(
                actor=self.owner,
                document=self.document,
                event_type="DOWNLOAD",
                success=True,
            ).exists()
        )

        response.close()

    def test_viewer_can_download_document_with_read_permission(self):
        DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            can_read=True,
            can_edit=False,
            granted_by=self.owner,
        )

        self.client.force_login(self.viewer)

        response = self.client.get(self.download_url)

        self.assertEqual(response.status_code, 200)

        self.assertTrue(
            AuditEvent.objects.filter(
                actor=self.viewer,
                document=self.document,
                event_type="DOWNLOAD",
                success=True,
            ).exists()
        )

        response.close()

    def test_revoked_user_cannot_download_document(self):
        permission = DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            can_read=True,
            can_edit=False,
            granted_by=self.owner,
        )

        self.client.force_login(self.viewer)

        first_response = self.client.get(self.download_url)
        self.assertEqual(first_response.status_code, 200)
        first_response.close()

        permission.delete()

        second_response = self.client.get(self.download_url)
        self.assertEqual(second_response.status_code, 404)

        self.assertTrue(
            AuditEvent.objects.filter(
                actor=self.viewer,
                document=self.document,
                event_type="ACCESS_DENIED",
                success=False,
            ).exists()
        )
    def test_owner_can_revoke_access_and_audit_event_is_recorded(self):
        DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            can_read=True,
            can_edit=False,
            granted_by=self.owner,
        )

        # The owner revokes the viewer's permission.
        self.client.force_login(self.owner)

        revoke_url = reverse(
            "document_revoke",
            args=[self.document.pk, self.viewer.pk],
        )

        response = self.client.post(revoke_url)

        self.assertEqual(response.status_code, 302)

        # Confirm that the permission was removed.
        self.assertFalse(
            DocumentPermission.objects.filter(
                document=self.document,
                user=self.viewer,
            ).exists()
        )

        # Confirm that the revocation was audited.
        self.assertTrue(
            AuditEvent.objects.filter(
                actor=self.owner,
                document=self.document,
                event_type="PERMISSION_REVOKED",
                success=True,
                details__target_user_id=self.viewer.pk,
            ).exists()
        )

        # The viewer must no longer be able to download the document.
        self.client.force_login(self.viewer)

        download_response = self.client.get(self.download_url)

        self.assertEqual(download_response.status_code, 404)

        # Confirm that the denied download was audited.
        self.assertTrue(
            AuditEvent.objects.filter(
                actor=self.viewer,
                document=self.document,
                event_type="ACCESS_DENIED",
                success=False,
            ).exists()
        )

    

    # --------------------------------------------------
    # DOCUMENT EDITING TESTS
    # --------------------------------------------------

    def test_owner_can_open_edit_page(self):
        self.client.force_login(self.owner)

        response = self.client.get(self.edit_url)

        self.assertEqual(response.status_code, 200)

    def test_owner_can_edit_document_details(self):
        self.client.force_login(self.owner)

        response = self.client.post(
            self.edit_url,
            {
                "title": "Updated Confidential Document",
                "description": "Updated description",
                "category": "TECHNICAL",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.document.refresh_from_db()

        self.assertEqual(
            self.document.title,
            "Updated Confidential Document",
        )

        self.assertEqual(
            self.document.description,
            "Updated description",
        )

        self.assertEqual(
            self.document.category,
            "TECHNICAL",
        )

        self.assertTrue(
            AuditEvent.objects.filter(
                actor=self.owner,
                document=self.document,
                event_type="DOCUMENT_EDITED",
                success=True,
            ).exists()
        )

    def test_user_with_edit_permission_can_edit_document(self):
        DocumentPermission.objects.create(
            document=self.document,
            user=self.editor,
            can_read=True,
            can_edit=True,
            granted_by=self.owner,
        )

        self.client.force_login(self.editor)

        response = self.client.post(
            self.edit_url,
            {
                "title": "Edited By Authorized Editor",
                "description": "Editor updated this document",
                "category": "TECHNICAL",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.document.refresh_from_db()

        self.assertEqual(
            self.document.title,
            "Edited By Authorized Editor",
        )

        self.assertTrue(
            AuditEvent.objects.filter(
                actor=self.editor,
                document=self.document,
                event_type="DOCUMENT_EDITED",
                success=True,
            ).exists()
        )

    def test_read_only_viewer_cannot_edit_document(self):
        DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            can_read=True,
            can_edit=False,
            granted_by=self.owner,
        )

        self.client.force_login(self.viewer)

        response = self.client.post(
            self.edit_url,
            {
                "title": "Unauthorized Modification",
                "description": "This should not be saved",
                "category": "OTHER",
            },
        )

        self.assertEqual(response.status_code, 404)

        self.document.refresh_from_db()

        self.assertEqual(
            self.document.title,
            "Confidential Test Document",
        )

        self.assertTrue(
            AuditEvent.objects.filter(
                actor=self.viewer,
                document=self.document,
                event_type="ACCESS_DENIED",
                success=False,
                details__action="edit",
            ).exists()
        )

    # --------------------------------------------------
    # DOCUMENT DELETION TESTS
    # --------------------------------------------------

    def test_owner_can_delete_document(self):
        self.client.force_login(self.owner)

        document_id = self.document.pk
        file_name = self.document.file.name
        storage = self.document.file.storage

        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, 302)

        self.assertFalse(
            Document.objects.filter(pk=document_id).exists()
        )

        self.assertTrue(
            AuditEvent.objects.filter(
                actor=self.owner,
                event_type="DOCUMENT_DELETED",
                details__document_id=document_id,
                details__document_title="Confidential Test Document",
                success=True,
            ).exists()
        )

        # The current delete view does not remove physical files.
        # Clean up the test file explicitly.
        if file_name and storage.exists(file_name):
            storage.delete(file_name)

    def test_viewer_cannot_delete_document(self):
        DocumentPermission.objects.create(
            document=self.document,
            user=self.viewer,
            can_read=True,
            can_edit=True,
            granted_by=self.owner,
        )

        self.client.force_login(self.viewer)

        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, 404)

        self.assertTrue(
            Document.objects.filter(pk=self.document.pk).exists()
        )

    def test_get_request_cannot_delete_document(self):
        self.client.force_login(self.owner)

        response = self.client.get(self.delete_url)

        self.assertEqual(response.status_code, 405)

        self.assertTrue(
            Document.objects.filter(pk=self.document.pk).exists()
        )


class DocumentUploadValidationTests(TestCase):

    def make_form(self, filename, content):
        """
        Create an upload form with a supplied filename and file content.
        """

        uploaded_file = SimpleUploadedFile(
            filename,
            content,
        )

        return DocumentUploadForm(
            data={
                "title": "Test Document",
                "category": "OTHER",
                "description": "Upload validation test",
            },
            files={"file": uploaded_file},
        )

    def test_valid_text_file_is_accepted(self):
        form = self.make_form(
            "notes.txt",
            b"TrustVault test document.",
        )

        self.assertTrue(form.is_valid(), form.errors)

    def test_unsupported_extension_is_rejected(self):
        form = self.make_form(
            "malicious.exe",
            b"example executable content",
        )

        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_oversized_file_is_rejected(self):
        form = self.make_form(
            "large.txt",
            b"A" * (MAX_FILE_SIZE + 1),
        )

        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_empty_file_is_rejected(self):
        form = self.make_form(
            "empty.txt",
            b"",
        )

        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_invalid_pdf_signature_is_rejected(self):
        form = self.make_form(
            "fake.pdf",
            b"This is not a PDF file.",
        )

        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)

    def test_invalid_png_signature_is_rejected(self):
        form = self.make_form(
            "fake.png",
            b"This is not a PNG file.",
        )

        self.assertFalse(form.is_valid())
        self.assertIn("file", form.errors)