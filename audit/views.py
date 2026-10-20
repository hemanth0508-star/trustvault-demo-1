import logging

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render

from .models import AuditEvent


logger = logging.getLogger(__name__)


def get_client_ip(request):
    """
    Return the direct client IP address.

    Only trust forwarded IP headers when a trusted proxy
    has been configured correctly.
    """
    return request.META.get("REMOTE_ADDR")


def record_audit_event(
    *,
    actor,
    document,
    event_type,
    success=True,
    details=None,
    ip_address=None,
):
    """
    Create a new audit event.

    Audit events are append-only through normal application
    operations. Database-level protection is also required
    for stronger tamper resistance.
    """
    return AuditEvent.objects.create(
        actor=actor,
        document=document,
        event_type=event_type,
        success=success,
        details=details or {},
        ip_address=ip_address,
    )


@staff_member_required
def audit_dashboard(request):
    """
    Display recent audit events to staff members.
    """
    events = AuditEvent.objects.select_related(
        "actor",
        "document",
    ).order_by("-timestamp")

    event_type = request.GET.get("event_type", "").strip()
    username = request.GET.get("username", "").strip()

    allowed_types = {
        choice[0]
        for choice in AuditEvent.EVENT_CHOICES
    }

    if event_type in allowed_types:
        events = events.filter(event_type=event_type)

    if username:
        events = events.filter(
            actor__username__icontains=username
        )

    return render(
        request,
        "audit/audit_dashboard.html",
        {
            "events": events[:200],
            "event_choices": AuditEvent.EVENT_CHOICES,
            "selected_event_type": event_type,
            "username_query": username,
        },
    )