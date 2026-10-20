# TrustVault — AI Usage and Development Log

## 1. Purpose

This document records how AI assistance was used during the development
of TrustVault, a secure document-sharing application built with Django.

AI assistance supported code development, debugging, documentation,
and security-test planning. Suggestions were reviewed and tested
during development.

## 2. Development Tasks

### Task 1: Django Form and File Validation

**Goal:** Validate uploaded documents and restrict unsupported files.

**AI assistance requested:**
Help create a Django ModelForm that validates file extensions,
file sizes, basic file signatures, image content, and document titles.

**Implementation:**
The upload form was updated to validate file size, reject empty files,
restrict extensions, inspect selected file signatures, and validate
image content using Pillow.

**Verification:**
The project test suite includes tests for unsupported extensions,
oversized files, empty files, invalid PDF signatures, and invalid
PNG signatures.

### Task 2: Debugging a Missing Dependency

**Problem:**
The application raised `ModuleNotFoundError: No module named 'PIL'`.

**AI assistance requested:**
Explain the error and provide commands to install and verify Pillow
inside the active Python virtual environment.

**Resolution:**
Pillow was installed, and the project test suite subsequently ran.

### Task 3: Document Search and Filtering

**Goal:**
Support searching and filtering documents by title, description,
owner, category, and upload date.

**AI assistance requested:**
Help update the document-list view and HTML template while preserving
existing sharing and download functionality.

**Implementation:**
The document-list view and search form were extended with filtering
parameters and category choices.

**Verification:**
The developer tested the filters through the application.

### Task 4: Document Editing and Deletion

**Goal:**
Add document editing and deletion with server-side authorization.

**AI assistance requested:**
Help create Django views, URL routes, templates, and test cases
for editing and deleting documents.

**Security requirements:**
- Only owners can delete documents.
- Only owners or users with edit permission can edit documents.
- Read-only viewers must not be allowed to modify documents.
- State-changing requests must use appropriate HTTP methods.
- Important operations must be recorded in the audit trail.

**Verification:**
Automated tests were added for editing, deletion, and access control.

### Task 5: Automated Security Testing

**Goal:**
Test access controls and prevent unauthorized document operations.

**AI assistance requested:**
Help expand Django tests for document downloads, permission checks,
editing, deletion, upload validation, and audit events.

**Verification:**
The full Django test suite completed successfully with 22 passing
tests during development.

This result describes that test run; it does not guarantee that every
possible security issue has been identified.

### Task 6: Threat Modeling

**Goal:**
Document TrustVault's security risks and mitigations.

**AI assistance requested:**
Help structure a threat model covering unauthorized access,
privilege escalation, permission revocation, malicious uploads,
audit-log tampering, private storage exposure, and operational risks.

**Deliverable:**
THREATS.md

## 3. Developer Responsibilities

The developer is responsible for reviewing AI-generated suggestions,
integrating the code, running tests, checking errors, and verifying
the final application behavior.

AI-generated code is not assumed to be secure merely because it
compiles or passes the current test suite.

## 4. Known Limitations

- Automated tests cover specific scenarios, not every possible attack.
- Application-level audit protections do not prevent direct database
  modification by sufficiently privileged operators.
- File-signature checks do not prove that all uploaded files are safe.
- Production storage, HTTPS, secrets, and deployment settings require
  separate verification.
- File cleanup after document deletion requires dedicated testing.

## 5. Future Improvements

- Add further authorization and permission-revocation tests.
- Improve file-content validation and consider malware scanning.
- Verify private storage configuration in deployment.
- Strengthen audit-log protection.
- Test file cleanup and error handling.
- Review dependencies and production security settings.