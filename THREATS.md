# TrustVault — Threat Model

## 1. Project Overview

TrustVault is a secure document-sharing application built with Python and Django.

Users can upload documents, search and filter documents, download authorized files, and share documents with other users through explicit permissions.

The application uses Django authentication, server-side authorization checks, private file storage, and database-backed audit events.

## 2. Assets to Protect

The primary assets are:

- Confidential uploaded documents.
- User credentials and authenticated sessions.
- Document ownership information.
- Read and edit permissions.
- Audit records.
- Document metadata, including titles, descriptions, categories, and upload dates.
- The database and private file storage directory.

## 3. Threat Actors

Potential threat actors include:

- An unauthenticated visitor attempting to access private documents.
- An authenticated user attempting to access another user's documents.
- A viewer attempting to edit or delete a document.
- A user attempting to retain access after permission revocation.
- A malicious user uploading an invalid or potentially harmful file.
- An application administrator or database operator with excessive privileges.

## 4. Threats and Mitigations

### Threat 1: Unauthorized Document Access

**Risk:** A user may attempt to download a document they do not own and have not been authorized to read.

**Potential impact:** Confidential information could be disclosed.

**Mitigation implemented:**

- Authentication is required for document downloads.
- The download view checks document permissions on the server.
- The application checks authorization before opening the file.
- Denied download attempts are recorded as audit events.

**Verification:**

Automated tests check that unauthorized users receive a not-found response and that denied access is recorded.

**Remaining limitation:**

These checks protect requests handled by the application. They do not protect files if an attacker gains direct access to the server's private storage or operating system.

### Threat 2: Privilege Escalation

**Risk:** A viewer may attempt to edit a document, change permissions, or delete another user's document.

**Potential impact:** Unauthorized modification, deletion, or sharing of confidential information.

**Mitigation implemented:**

- The application checks document permissions on the server.
- Only document owners can grant or revoke document permissions.
- Document deletion is restricted to the owner.
- Document editing requires ownership or an explicit edit permission.
- Deletion uses POST requests and CSRF protection.

**Verification:**

Automated tests check that read-only viewers cannot edit documents and that non-owners cannot delete documents.

**Remaining limitation:**

The application must continue enforcing these checks in every new view and API endpoint. Hiding a button in the interface is not an authorization mechanism.

### Threat 3: Access After Permission Revocation

**Risk:** A user may try to download a document after the owner revokes access.

**Potential impact:** Continued unauthorized disclosure of confidential information.

**Mitigation implemented:**

- Document access is checked on each download request.
- Read permissions are stored in the database.
- Removing a permission prevents subsequent authorized downloads.

**Verification:**

Automated tests check that a user who loses permission cannot download the document on a subsequent request.

**Remaining limitation:**

Revocation cannot retrieve files that a user already downloaded or copied while they had permission.

### Threat 4: Malicious or Invalid File Uploads

**Risk:** A user may upload an unsupported, empty, oversized, corrupted, or misleadingly named file.

**Potential impact:** Storage exhaustion, processing errors, or exposure to harmful file content.

**Mitigation implemented:**

- The upload form restricts permitted file extensions.
- File sizes are limited.
- Empty files are rejected.
- Basic file-signature checks are applied to supported formats.
- Pillow validates uploaded image content.

**Verification:**

Automated tests cover unsupported extensions, oversized files, empty files, invalid PDF signatures, and invalid PNG signatures.

**Remaining limitation:**

File extensions and signatures are not proof that a file is safe. DOCX validation is limited, and malware scanning is not currently implemented. Production deployments should add deeper content validation, malware scanning, and appropriate storage limits.

### Threat 5: Audit Record Modification

**Risk:** An attacker may attempt to modify or delete audit events to conceal activity.

**Potential impact:** Investigations may become unreliable, and malicious actions may be harder to detect.

**Mitigation implemented:**

- The application creates database-backed audit events.
- The AuditEvent model prevents ordinary instance updates and deletes.
- Django admin does not permit adding, changing, or deleting audit events through its normal interface.
- Important actions include document uploads, downloads, edits, deletions, permission changes, and denied access.

**Remaining limitation:**

These controls do not make audit records tamper-proof. Database administrators, direct SQL operations, or other privileged code may bypass application-level protections.

For stronger protection, production deployments should consider restricted database privileges, append-only external logging, and independently protected audit storage.

### Threat 6: Direct Exposure of Private Files

**Risk:** Uploaded documents could become publicly accessible if served directly from a public media directory.

**Potential impact:** An attacker could bypass application authorization and download confidential files.

**Mitigation implemented:**

- Uploaded documents are stored under the project's private storage directory.
- The application serves downloads through an authorization-checked view.
- Uploaded files should not be exposed through public media URLs.

**Verification:**

Review the deployment configuration to confirm that the private storage directory is not publicly served.

**Remaining limitation:**

Local storage permissions, web-server configuration, backups, and deployment settings must also be secured.

### Threat 7: Cross-Site Request Forgery

**Risk:** An attacker may attempt to make an authenticated user's browser perform an unwanted action.

**Potential impact:** Unauthorized sharing, permission revocation, or document deletion.

**Mitigation implemented:**

- State-changing HTML forms include Django CSRF tokens.
- The document-revocation and document-deletion endpoints require POST requests.
- Django's CSRF middleware should remain enabled.

**Remaining limitation:**

All future state-changing endpoints must follow the same pattern. CSRF protection does not replace authentication or authorization checks.

### Threat 8: Unauthorized Access Through Search and Filters

**Risk:** A user may manipulate search parameters to discover documents belonging to other users.

**Potential impact:** Disclosure of confidential document metadata.

**Mitigation implemented:**

- The document list starts with documents owned by the current user.
- Shared documents are selected using the current user's read permissions.
- Search and filter parameters narrow these authorized querysets.

**Remaining limitation:**

Every new search endpoint and API must independently enforce authorization. Search filters must never be treated as access controls.

### Threat 9: Accidental File Retention After Deletion

**Risk:** Deleting a document record may leave the underlying file in storage.

**Potential impact:** Unnecessary retention of confidential information and increased storage usage.

**Current status:**

The application deletes document records, but Django's FileField does not automatically remove the underlying file when a model instance is deleted.

**Required improvement:**

Implement and test safe file cleanup. Ensure that cleanup does not delete a file still referenced by another record and that failures are logged and recoverable.

### Threat 10: Compromised Administrator or Database

**Risk:** An attacker with operating-system, database, or administrator privileges may access or alter sensitive application data.

**Potential impact:** Confidentiality, integrity, and availability may all be compromised.

**Mitigation and operational controls:**

- Restrict administrator accounts.
- Use strong passwords and secure deployment secrets.
- Limit database and server access.
- Keep private storage outside publicly served directories.
- Back up the database and uploaded files securely.
- Use HTTPS in production.
- Avoid committing secrets, local databases, or confidential documents to public repositories.

**Remaining limitation:**

Application-level authorization cannot fully protect data from an attacker who has unrestricted control over the host or database.

## 5. Security Testing

The current automated test suite covers:

- Authentication requirements for document downloads.
- Owner and viewer download permissions.
- Access denial and audit event recording.
- Permission revocation behavior.
- Upload file validation.
- Owner and authorized-editor document updates.
- Read-only viewer edit denial.
- Owner-only document deletion.
- Rejection of GET requests for document deletion.

Tests provide evidence for the specific cases they exercise. They do not establish that every possible attack has been prevented.

## 6. Security Priorities Before Deployment

The following work should be completed or verified before production use:

1. Test the actual permission-revocation endpoint.
2. Test authorization on every document-changing endpoint.
3. Implement safe cleanup of deleted files.
4. Add stronger PDF and DOCX content validation.
5. Consider malware scanning for uploaded documents.
6. Verify private storage is not publicly accessible.
7. Use HTTPS and secure cookie settings in production.
8. Store secrets outside source control.
9. Protect audit logs against privileged tampering.
10. Review dependencies and deployment configuration.

## 7. Conclusion

TrustVault implements server-side document access checks, permission-based sharing, upload validation, and database-backed audit events.

Automated tests help verify these controls against specific scenarios. Additional testing, deployment hardening, and operational controls are required before the application should be considered suitable for sensitive production documents.