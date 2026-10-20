import logging
from datetime import date
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from audit.models import AuditEvent
from .forms import DocumentUploadForm, DocumentShareForm
from .models import Document, DocumentPermission
from .permissions import (
    can_read_document,
    can_edit_document,
)



logger = logging.getLogger(__name__)


# --------------------------------------------------
# HELPER: RECORD AN AUDIT EVENT
# --------------------------------------------------

def record_audit(
    request,
    event_type,
    document=None,
    success=True,
    details=None,
):
    """
    Record an audit event in the database.

    Audit events are created by the application.
    Existing events must not be updated or deleted
    through normal application operations.
    """
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    # Only trust forwarded IP information when the deployment
    # is configured to accept it from a trusted proxy.
    # For local development, use REMOTE_ADDR.
    ip_address = request.META.get("REMOTE_ADDR")

    if not ip_address and forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()

    event = AuditEvent(
        actor=request.user if request.user.is_authenticated else None,
        document=document,
        event_type=event_type,
        success=success,
        details=details or {},
        ip_address=ip_address or None,
    )

    # Use force_insert so this helper only inserts a new event.
    event.save(force_insert=True)


# --------------------------------------------------
# 1. LIST, SEARCH, AND DISPLAY DOCUMENTS
# --------------------------------------------------


@login_required
def document_list(request):
    # Read search and filter values
    search_query = request.GET.get("q", "").strip()
    owner_query = request.GET.get("owner", "").strip()
    category_query = request.GET.get("category", "").strip()
    date_from = request.GET.get("date_from", "").strip()
    date_to = request.GET.get("date_to", "").strip()

    # Validate category
    valid_categories = {
        choice[0] for choice in Document.CATEGORY_CHOICES
    }

    if category_query and category_query not in valid_categories:
        category_query = ""

    # Validate dates before applying database filters
    invalid_date = False

    if date_from:
        try:
            date_from = date.fromisoformat(date_from).isoformat()
        except ValueError:
            invalid_date = True
            date_from = ""

    if date_to:
        try:
            date_to = date.fromisoformat(date_to).isoformat()
        except ValueError:
            invalid_date = True
            date_to = ""

    # Reject an inverted date range
    if date_from and date_to and date_from > date_to:
        invalid_date = True

    # Documents owned by the logged-in user
    owned_documents = Document.objects.filter(
        owner=request.user
    )

    # Documents shared with the logged-in user
    shared_document_ids = DocumentPermission.objects.filter(
        user=request.user,
        can_read=True,
        user__is_active=True,
    ).values_list("document_id", flat=True)

    shared_documents = Document.objects.filter(
        pk__in=shared_document_ids
    ).exclude(owner=request.user)

    # Search by title or description
    if search_query:
        search_filter = (
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
        )

        owned_documents = owned_documents.filter(search_filter)
        shared_documents = shared_documents.filter(search_filter)

    # Filter by owner username
    if owner_query:
        owned_documents = owned_documents.filter(
            owner__username__icontains=owner_query
        )

        shared_documents = shared_documents.filter(
            owner__username__icontains=owner_query
        )

    # Filter by category
    if category_query:
        owned_documents = owned_documents.filter(
            category=category_query
        )

        shared_documents = shared_documents.filter(
            category=category_query
        )

    # Apply upload date filters only when the dates are valid
    if date_from:
        owned_documents = owned_documents.filter(
            created_at__date__gte=date_from
        )
        shared_documents = shared_documents.filter(
            created_at__date__gte=date_from
        )

    if date_to:
        owned_documents = owned_documents.filter(
            created_at__date__lte=date_to
        )
        shared_documents = shared_documents.filter(
            created_at__date__lte=date_to
        )

    # Invalid dates or date ranges return no results
    if invalid_date:
        owned_documents = owned_documents.none()
        shared_documents = shared_documents.none()

    # Load related objects efficiently and sort newest first
    owned_documents = (
        owned_documents
        .select_related("owner")
        .prefetch_related("permissions__user")
        .order_by("-created_at")
    )

    shared_documents = (
        shared_documents
        .select_related("owner")
        .order_by("-created_at")
    )

    return render(
        request,
        "documents/document_list.html",
        {
            "documents": owned_documents,
            "shared_documents": shared_documents,
            "search_query": search_query,
            "owner_query": owner_query,
            "category_query": category_query,
            "date_from": date_from,
            "date_to": date_to,
            "category_choices": Document.CATEGORY_CHOICES,
        },
    )
# --------------------------------------------------
# 2. UPLOAD A DOCUMENT
# --------------------------------------------------

@login_required
def document_upload(request):
    if request.method == "POST":
        form = DocumentUploadForm(
            request.POST,
            request.FILES,
        )

        if form.is_valid():
            with transaction.atomic():
                document = form.save(commit=False)

                # Ownership is assigned by the server.
                document.owner = request.user
                document.save()

                record_audit(
                    request=request,
                    event_type="UPLOAD",
                    document=document,
                    details={
                        "document_title": document.title,
                        "category": document.category,
                    },
                )

            logger.info(
                "Document uploaded: document_id=%s user_id=%s",
                document.pk,
                request.user.pk,
            )

            return redirect("document_list")

    else:
        form = DocumentUploadForm()

    return render(
        request,
        "documents/document_upload.html",
        {"form": form},
    )


# --------------------------------------------------
# 3. SECURE DOCUMENT DOWNLOAD
# --------------------------------------------------

@login_required
def document_download(request, document_id):
    document = get_object_or_404(
        Document,
        pk=document_id,
    )

    # Authorization must happen before opening the file.
    if not can_read_document(request.user, document):
        record_audit(
            request=request,
            event_type="ACCESS_DENIED",
            document=document,
            success=False,
            details={
                "action": "download",
                "reason": "User lacks document read permission",
            },
        )

        logger.warning(
            "Document download denied: document_id=%s user_id=%s",
            document.pk,
            request.user.pk,
        )

        raise Http404("Document not found.")

    try:
        document.file.open("rb")

    except (OSError, ValueError):
        logger.exception(
            "Document file unavailable: document_id=%s",
            document.pk,
        )

        raise Http404("Document file not found.")

    # Record the successful authorization and download initiation.
    # This does not prove the recipient received every byte.
    try:
        record_audit(
            request=request,
            event_type="DOWNLOAD",
            document=document,
            details={
                "action": "download",
            },
        )
    except Exception:
        # Do not silently allow an unlogged download if audit
        # storage is unavailable.
        document.file.close()
        logger.exception("Could not record download audit event.")
        raise

    logger.info(
        "Document download initiated: document_id=%s user_id=%s",
        document.pk,
        request.user.pk,
    )

    return FileResponse(
        document.file,
        as_attachment=True,
        filename=document.file.name.rsplit("/", 1)[-1],
    )


# --------------------------------------------------
# 4. SHARE A DOCUMENT
# --------------------------------------------------

@login_required
def document_share(request, document_id):
    # Only the owner can grant or change permissions.
    document = get_object_or_404(
        Document,
        pk=document_id,
        owner=request.user,
    )

    if request.method == "POST":
        form = DocumentShareForm(request.POST)

        if form.is_valid():
            target_user = form.cleaned_data["user"]
            can_read = form.cleaned_data["can_read"]
            can_edit = form.cleaned_data["can_edit"]

            if target_user == request.user:
                form.add_error(
                    "user",
                    "You already own this document.",
                )

            elif not can_read and not can_edit:
                form.add_error(
                    None,
                    "Select at least one permission.",
                )

            else:
                with transaction.atomic():
                    permission, created = (
                        DocumentPermission.objects.update_or_create(
                            document=document,
                            user=target_user,
                            defaults={
                                "can_read": can_read,
                                "can_edit": can_edit,
                                "granted_by": request.user,
                            },
                        )
                    )

                    record_audit(
                        request=request,
                        event_type="PERMISSION_GRANTED",
                        document=document,
                        details={
                            "target_user_id": target_user.pk,
                            "target_username": target_user.username,
                            "can_read": can_read,
                            "can_edit": can_edit,
                            "created": created,
                        },
                    )

                logger.info(
                    "Document permission updated: "
                    "document_id=%s owner_id=%s target_user_id=%s",
                    document.pk,
                    request.user.pk,
                    target_user.pk,
                )

                return redirect("document_list")

    else:
        form = DocumentShareForm()

    return render(
        request,
        "documents/document_share.html",
        {
            "document": document,
            "form": form,
        },
    )


# --------------------------------------------------
# 5. REVOKE DOCUMENT ACCESS
# --------------------------------------------------

@login_required
@require_POST
def document_revoke(request, document_id, user_id):
    # Only the owner can revoke a permission.
    document = get_object_or_404(
        Document,
        pk=document_id,
        owner=request.user,
    )

    permission = get_object_or_404(
        DocumentPermission,
        document=document,
        user_id=user_id,
    )

    with transaction.atomic():
        revoked_user_id = permission.user_id
        revoked_username = permission.user.username

        # Record the revocation before removing the permission.
        # Both database operations commit together.
        record_audit(
            request=request,
            event_type="PERMISSION_REVOKED",
            document=document,
            details={
                "target_user_id": revoked_user_id,
                "target_username": revoked_username,
                "previous_can_read": permission.can_read,
                "previous_can_edit": permission.can_edit,
            },
        )

        permission.delete()

    logger.info(
        "Document permission revoked: "
        "document_id=%s owner_id=%s revoked_user_id=%s",
        document.pk,
        request.user.pk,
        user_id,
    )

    return redirect("document_list")
# --------------------------------------------------
# 6. EDIT DOCUMENT DETAILS
# --------------------------------------------------

@login_required
def document_edit(request, document_id):
    document = get_object_or_404(
        Document,
        pk=document_id,
    )

    # Only the owner or a user with edit permission can edit.
    if not can_edit_document(request.user, document):
        record_audit(
            request=request,
            event_type="ACCESS_DENIED",
            document=document,
            success=False,
            details={
                "action": "edit",
                "reason": "User lacks document edit permission",
            },
        )

        logger.warning(
            "Document edit denied: document_id=%s user_id=%s",
            document.pk,
            request.user.pk,
        )

        raise Http404("Document not found.")

    if request.method == "POST":
        form = DocumentUploadForm(
            request.POST,
            request.FILES,
            instance=document,
        )

        if form.is_valid():
            with transaction.atomic():
                updated_document = form.save()

                record_audit(
                    request=request,
                    event_type="DOCUMENT_EDITED",
                    document=updated_document,
                    details={
                        "document_title": updated_document.title,
                        "category": updated_document.category,
                    },
                )

            logger.info(
                "Document edited: document_id=%s user_id=%s",
                document.pk,
                request.user.pk,
            )

            return redirect("document_list")

    else:
        form = DocumentUploadForm(instance=document)

    return render(
        request,
        "documents/document_edit.html",
        {
            "form": form,
            "document": document,
        },
    )
# --------------------------------------------------
# 7. DELETE DOCUMENT
# --------------------------------------------------

# --------------------------------------------------
# 7. DELETE DOCUMENT
# --------------------------------------------------

@login_required
@require_POST
def document_delete(request, document_id):
    # Only the owner can delete the document.
    document = get_object_or_404(
        Document,
        pk=document_id,
        owner=request.user,
    )

    document_id_for_audit = document.pk
    document_title_for_audit = document.title
    file_name = document.file.name if document.file else None
    storage = document.file.storage if document.file else None

    # Record the deletion before deleting the database record.
    with transaction.atomic():
        record_audit(
            request=request,
            event_type="DOCUMENT_DELETED",
            document=document,
            details={
                "document_id": document_id_for_audit,
                "document_title": document_title_for_audit,
            },
        )

        document.delete()

    # Remove the physical file after the database transaction succeeds.
    # If storage cleanup fails, log the failure for investigation.
    if file_name and storage:
        try:
            if storage.exists(file_name):
                storage.delete(file_name)
        except Exception:
            logger.exception(
                "Failed to remove deleted document file: "
                "document_id=%s",
                document_id_for_audit,
            )

    logger.info(
        "Document deleted: document_id=%s user_id=%s",
        document_id_for_audit,
        request.user.pk,
    )

    return redirect("document_list")