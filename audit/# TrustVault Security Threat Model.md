# TrustVault Security Threat Model

## 1. Project Overview

TrustVault is a secure document-sharing application built with
Python and Django.

It allows authenticated users to upload documents, grant
permissions to specific users, download authorized documents,
and revoke access.

The application uses server-side authorization checks and
records document activity in an audit database.

## 2. Assets to Protect

- Confidential uploaded documents.
- User accounts and authentication credentials.
- Document ownership information.
- Document permissions.
- Audit records.
- Document metadata.

## 3. Threats and Mitigations

### Threat 1: Unauthorized Document Download

**Attack:** A user changes a document ID in a download URL
to access another user's document.

**Mitigation:** The download view checks whether the current
user owns the document or has explicit read permission.

**Verification:** Automated tests verify that users without
permission receive an HTTP 404 response.

### Threat 2: Access After Permission Revocation

**Attack:** A previously authorized user attempts to download
a document after their permission has been revoked.

**Mitigation:** The download endpoint checks the current
database permission on every request.

**Verification:** An automated test confirms that a download
is denied after the permission record is removed.

**Limitation:** A file already downloaded or copied cannot
be remotely deleted from the recipient's device.

### Threat 3: Unauthorized Permission Changes

**Attack:** A viewer attempts to grant or revoke permissions
for a document they do not own.

**Mitigation:** Sharing and revocation views restrict access
to the document owner.

**Verification:** An automated test confirms that a viewer
cannot revoke permissions on another user's document.

### Threat 4: Unauthorized Access to Shared Documents

**Attack:** A user attempts to download a document that has
not been shared with them.

**Mitigation:** The application checks explicit read permission
before opening the document file.

**Verification:** Automated tests cover denied downloads.

### Threat 5: Audit Record Modification

**Attack:** Someone attempts to alter or delete an audit record.

**Mitigation:** Audit model operations reject normal updates
and deletions. Django Admin does not allow audit records to
be added, changed, or deleted through its standard interface.

**Limitation:** A database administrator or someone with
direct database access may still modify the records.
External append-only or tamper-evident storage is not yet
implemented.

### Threat 6: Unauthorized Access Attempts Go Unrecorded

**Attack:** An unauthorized user attempts to download a
document, but the application does not record the attempt.

**Mitigation:** The download view creates an ACCESS_DENIED
audit event before returning an error response.

**Limitation:** Requests rejected by authentication before
reaching the download view are not currently recorded by
that view.

### Threat 7: Malicious File Upload

**Attack:** A user uploads a dangerous or oversized file.

**Mitigation:** File validation and upload-size restrictions
must be enforced on the server before deployment.

**Current Status:** Comprehensive content validation and
size limits require verification before production use.

### Threat 8: Direct Access to Stored Files

**Attack:** A user bypasses Django authorization by accessing
an uploaded file through a public media URL.

**Mitigation:** Uploaded documents must be stored privately
and served only through an authorization-protected endpoint.

**Current Status:** Private storage and deployment settings
must be verified before public deployment.

### Threat 9: Cross-Site Request Forgery

**Attack:** A malicious website attempts to trigger a
permission change using another user's authenticated session.

**Mitigation:** State-changing HTML forms use Django CSRF
tokens, and permission revocation requires a POST request.

**Verification:** CSRF protection must remain enabled.

### Threat 10: Unauthorized Document Editing

**Attack:** A viewer attempts to edit a document without
edit permission.

**Mitigation:** Any editing endpoint must check ownership
or explicit edit permission on the server.

**Current Status:** Every document-editing route must be
implemented and tested before this feature is considered secure.

## 4. Security Testing

The current automated test suite checks:

- Anonymous download restrictions.
- Unauthorized download restrictions.
- Owner download access.
- Authorized viewer download access.
- Access denial after permission removal.
- Prevention of unauthorized permission revocation.

Additional tests are needed for permission grants, the actual
revocation endpoint, upload validation, and audit protection.

## 5. Accepted and Outstanding Risks

- Downloaded files cannot be remotely recalled.
- Database administrators may alter audit records.
- External tamper-evident audit storage is not implemented.
- File content validation requires completion and testing.
- Production storage and deployment security require verification.
- Editing and deletion routes require authorization tests.
- Unauthenticated access attempts are not yet recorded by
  the document download view.

## 6. Deployment Requirement

TrustVault must not be considered production-ready until
authorization tests pass, uploaded files are stored privately,
file validation is implemented, and production settings are
configured securely.