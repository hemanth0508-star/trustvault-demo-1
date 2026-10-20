# TrustVault — Secure Document Sharing

TrustVault is a Django demo application for authenticated document storage, owner-controlled sharing, permission revocation, and audit events. It includes a cybersecurity-themed landing page, branded login/registration screens, document search and management, and an administrator audit dashboard.

## Deploy to Render with Neon PostgreSQL

This repository includes `render.yaml` for a Render web service. In the Render dashboard:

1. Push the **contents of this project folder** to your GitHub repository (the files `manage.py`, `requirements.txt`, and `render.yaml` should be at the repository root).
2. Create a PostgreSQL database in [Neon](https://neon.tech/) and copy its connection string. Use the pooled connection string if available, with SSL enabled (`sslmode=require`).
3. In Render, create a new Blueprint from the repository, or create a Web Service with the build/start commands in `render.yaml`.
4. Add `DATABASE_URL` to the Render service's environment variables and paste the Neon connection string. `DJANGO_SECRET_KEY` should be a long random secret, `DJANGO_DEBUG=0`, `DJANGO_ALLOWED_HOSTS` should contain the Render hostname, and `DJANGO_CSRF_TRUSTED_ORIGINS` should contain its HTTPS origin.
5. Deploy. The build command collects static files and runs database migrations automatically. Create an admin user from the Render Shell with `python manage.py createsuperuser`.

**Important:** production refuses to start without `DATABASE_URL`; SQLite is only a local-development fallback. Existing SQLite users/documents are not automatically copied into Neon. If you need that data, export/import it separately before switching.

### Uploaded document storage

The database stores document metadata, but uploaded file bytes currently use Django's local `private_uploads/` directory. Render and Vercel filesystems are not durable for user uploads across redeploys/restarts. For a real deployment, configure S3-compatible object storage (for example, Cloudflare R2 or Amazon S3) before relying on persistent uploaded documents. Do not store sensitive documents in the public static directory.

### Environment variables

See `.env.example` for the required settings. Never commit your real `DATABASE_URL`, production secret key, or demo credentials.

## Requirements
- Python 3.11 or newer
- pip

## Run locally (Windows PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
Open `http://127.0.0.1:8000/`. Use **Sign Up** to create a regular account. The admin dashboard is at `/admin/`; audit events are at `/audit/` for staff users.

## Create demo users and sample documents
For local development only, run:
```powershell
python manage.py seed_demo
```
This creates/ensures 29 standard users (`tvuser01` through `tvuser29`), synthetic `.txt` documents, and sample read-only shares. Newly created users get random passwords written to `demo_credentials.csv` in the project root. Existing accounts are not reset; their CSV row says the password was preserved. Keep this file private; `.gitignore` excludes it. The command refuses to run when `DJANGO_DEBUG=0`.

## Security notes
- Passwords are stored using Django's password hashers, not plaintext.
- Document storage uses `private_uploads/`, not the public static directory. Keep the web server from serving this directory directly.
- Authorization must be checked server-side on every document action; hiding a button is not authorization.
- Upload validation restricts extensions, file sizes, signatures, and image decoding.
- CSRF middleware and Django template escaping are enabled.
- Audit records are append-only through normal Django model operations, but this is **not** protection against an administrator with direct database/filesystem access. Production deployments should export audit events to a separately controlled append-only system.
- The local development secret is not suitable for production. Configure `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=0`, and `DJANGO_ALLOWED_HOSTS` before deployment. HTTPS must be configured at the hosting layer.
- The 29 demo accounts and documents are synthetic and intended for local testing only.

## Tests
```powershell
python manage.py test
python manage.py check
```

## Challenge documentation
See `THREATS.md` and `PROMPTS.md`. Update `PROMPTS.md` honestly with the AI prompts actually used and verify all claims before public submission.
