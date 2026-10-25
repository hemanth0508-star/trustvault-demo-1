from pathlib import Path

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from PIL import Image, UnidentifiedImageError

from .models import Document


# Maximum file size: 10 MB
MAX_FILE_SIZE = 10 * 1024 * 1024


# Allowed file extensions
ALLOWED_EXTENSIONS = {
    ".pdf",
    ".txt",
    ".docx",
    ".png",
    ".jpg",
    ".jpeg",
}


# File signatures used to check the actual file content
FILE_SIGNATURES = {
    ".pdf": [b"%PDF-"],
    ".png": [b"\x89PNG\r\n\x1a\n"],
    ".jpg": [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
    ".docx": [b"PK\x03\x04"],
}


class DocumentUploadForm(forms.ModelForm):
    """
    Form for uploading documents to TrustVault.

    Validates the document title, file extension, file size,
    file signature, and image content.
    """

    class Meta:
        model = Document
        fields = [
            "title",
            "file",
            "category",
            "description",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["file"].widget.attrs.update(
            {
                "accept": ".pdf,.txt,.docx,.png,.jpg,.jpeg",
                "aria-label": "Choose a document to upload",
            }
        )

    def clean_title(self):
        title = self.cleaned_data.get("title", "").strip()

        if not title:
            raise ValidationError("Document title is required.")

        if len(title) > 200:
            raise ValidationError(
                "Document title cannot exceed 200 characters."
            )

        return title

    def clean_file(self):
        uploaded_file = self.cleaned_data.get("file")

        if not uploaded_file:
            raise ValidationError("Please select a file to upload.")

        # Validate file size
        if uploaded_file.size > MAX_FILE_SIZE:
            raise ValidationError(
                "File size cannot exceed 10 MB."
            )

        # Reject empty files
        if uploaded_file.size == 0:
            raise ValidationError(
                "Empty files cannot be uploaded."
            )

        # Validate the file extension
        extension = Path(uploaded_file.name).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise ValidationError(
                "Unsupported file type. "
                "Allowed types are PDF, TXT, DOCX, PNG, JPG, and JPEG."
            )

        # Check the file signature for supported formats
        expected_signatures = FILE_SIGNATURES.get(extension)

        if expected_signatures:
            uploaded_file.seek(0)
            file_start = uploaded_file.read(8)
            uploaded_file.seek(0)

            if not any(
                file_start.startswith(signature)
                for signature in expected_signatures
            ):
                raise ValidationError(
                    "The file content does not match its extension."
                )

        # Verify that uploaded images contain valid image data
        if extension in {".png", ".jpg", ".jpeg"}:
            try:
                uploaded_file.seek(0)

                with Image.open(uploaded_file) as image:
                    image.verify()

            except (
                UnidentifiedImageError,
                OSError,
                ValueError,
            ):
                raise ValidationError(
                    "The uploaded image is invalid or corrupted."
                )

            finally:
                uploaded_file.seek(0)

        return uploaded_file


# Get the project's configured user model
User = get_user_model()


class DocumentShareForm(forms.Form):
    """
    Form for sharing a document with another TrustVault user.
    """

    user = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Share with",
        empty_label="Select a user",
    )

    can_read = forms.BooleanField(
        required=False,
        initial=True,
        label="Allow viewing and downloading",
    )

    can_edit = forms.BooleanField(
        required=False,
        initial=False,
        label="Allow editing",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Only active users can receive document permissions
        self.fields["user"].queryset = (
            User.objects.filter(is_active=True)
            .order_by("username")
        )

    def clean(self):
        cleaned_data = super().clean()

        can_read = cleaned_data.get("can_read", False)
        can_edit = cleaned_data.get("can_edit", False)

        # Require at least one permission
        if not can_read and not can_edit:
            raise ValidationError(
                "Select at least one permission: "
                "view/download or edit."
            )

        return cleaned_data