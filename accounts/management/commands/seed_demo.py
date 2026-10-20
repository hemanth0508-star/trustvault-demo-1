"""Create 29 local-only demo users and safe sample text documents.

Run: python manage.py seed_demo
A CSV containing generated demo credentials is written to demo_credentials.csv.
This command is for local demonstrations only; never run it on production.
"""
import csv
import secrets
import string
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from documents.models import Document, DocumentPermission

User = get_user_model()

class Command(BaseCommand):
    help = "Create 29 demo users and sample documents for local testing."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            self.stderr.write(self.style.ERROR("Refusing to seed demo accounts when DEBUG=False."))
            return
        alphabet = string.ascii_letters + string.digits + "!@#$%"
        credentials = []
        users = []
        for number in range(1, 30):
            username = f"tvuser{number:02d}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@example.test", "is_active": True,
                  "is_staff": False, "is_superuser": False},
            )
            if created:
                password = "Tv!" + "".join(secrets.choice(alphabet) for _ in range(17))
                user.set_password(password)
                user.is_staff = False
                user.is_superuser = False
                user.save()
            else:
                # Existing accounts are not reset silently; preserve their credentials.
                password = "EXISTING_ACCOUNT_PASSWORD_NOT_RESET"
            users.append(user)
            credentials.append((username, password, "standard user"))

        sample_docs = [
            ("Project Brief - Demo", "OTHER", "Sample demo brief. No real personal information."),
            ("Budget Summary - Demo", "FINANCIAL", "Illustrative demo budget: hosting 120, testing 80, contingency 50."),
            ("Technical Notes - Demo", "TECHNICAL", "Example technical notes for the TrustVault demonstration."),
            ("Agreement Checklist - Demo", "CONTRACT", "Demo checklist: review, approval, and signature."),
            ("Salary Letter - Demo", "SALARY", "Fictional salary letter used only for application testing."),
        ]
        created_docs = []
        for idx, (title, category, body) in enumerate(sample_docs):
            owner = users[idx]
            doc = Document.objects.filter(owner=owner, title=title).first()
            if doc is None:
                doc = Document(title=title, owner=owner, category=category,
                               description="Synthetic sample document for local testing.")
                doc.file.save(f"{title.lower().replace(' ', '_')}.txt", ContentFile(body.encode("utf-8")), save=False)
                doc.save()
            created_docs.append(doc)
        # Create a few explicit read-only shares to demonstrate cross-user permissions.
        for idx, doc in enumerate(created_docs):
            recipient = users[(idx + 10) % len(users)]
            DocumentPermission.objects.get_or_create(
                document=doc, user=recipient,
                defaults={"can_read": True, "can_edit": False, "granted_by": doc.owner},
            )

        out = Path(settings.BASE_DIR) / "demo_credentials.csv"
        with out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["username", "password", "role", "note"])
            for username, password, role in credentials:
                note = "Generated now" if password != "EXISTING_ACCOUNT_PASSWORD_NOT_RESET" else "Already existed; password preserved"
                writer.writerow([username, password, role, note])
        self.stdout.write(self.style.SUCCESS(f"Demo users processed: {len(users)}; sample documents: {len(created_docs)}."))
        self.stdout.write(self.style.WARNING(f"Credentials file: {out}"))
        self.stdout.write("Existing users are not reset. Credentials CSV is ignored by Git; do not share it publicly.")
