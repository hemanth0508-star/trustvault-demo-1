from django.urls import path

from . import views


urlpatterns = [
    # List and search documents
    path("", views.document_list, name="document_list"),

    # Upload a new document
    path("upload/", views.document_upload, name="document_upload"),

    # Download a document
    path(
        "<int:document_id>/download/",
        views.document_download,
        name="document_download",
    ),

    # Share a document
    path(
        "<int:document_id>/share/",
        views.document_share,
        name="document_share",
    ),

    # Revoke document permissions
    path(
        "<int:document_id>/revoke/<int:user_id>/",
        views.document_revoke,
        name="document_revoke",
    ),

    # Edit document details
    path(
        "<int:document_id>/edit/",
        views.document_edit,
        name="document_edit",
    ),

    # Delete a document
    path(
        "<int:document_id>/delete/",
        views.document_delete,
        name="document_delete",
    ),
]