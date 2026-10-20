from .models import DocumentPermission


def can_read_document(user, document):
    """
    Return True if the user can read and download the document.

    Access is granted only to:
    1. The authenticated document owner.
    2. An authenticated user with explicit read permission.
    """

    if not user.is_authenticated or not user.is_active:
        return False

    if not document.pk:
        return False

    # The document owner has full access to their document.
    if document.owner_id == user.pk:
        return True

    # Other users must have explicit read permission.
    return DocumentPermission.objects.filter(
        document_id=document.pk,
        user_id=user.pk,
        can_read=True,
        user__is_active=True,
    ).exists()


def can_edit_document(user, document):
    """
    Return True if the user can edit the document.

    Access is granted only to:
    1. The authenticated document owner.
    2. An authenticated user with explicit edit permission.
    """

    if not user.is_authenticated or not user.is_active:
        return False

    if not document.pk:
        return False

    # The document owner can edit their own document.
    if document.owner_id == user.pk:
        return True

    # Other users must have explicit edit permission.
    return DocumentPermission.objects.filter(
        document_id=document.pk,
        user_id=user.pk,
        can_edit=True,
        user__is_active=True,
    ).exists()