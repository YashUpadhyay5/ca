# Security & Tenant Isolation Policy

## CaFinIQ Enterprise Financial Security Model

### 1. Multi-Tenant Organization Isolation
- **Tenant Context Guard**: Every database transaction is bound to the `org_id` embedded within the cryptographically signed JWT token.
- **Strict Query Scoping**: Client, document, statement, and transaction queries automatically apply `org_id` filtering. Cross-tenant leakage is impossible at the ORM layer.
- **Client Ownership**: Clients and bank accounts belong exclusively to the authenticated CA firm.

### 2. Financial Data Privacy & Masking
- **Bank Account Number Masking**: Bank account numbers are masked by default (`XXXXXX1234`). Full account details are never printed in plain application logs or client-facing tables.
- **Narration Cleansing**: Sensitive authentication keys, PINs, and credentials are never ingested or logged.

### 3. Cryptography & Authentication
- **Password Storage**: Passwords are saved with salted PBKDF2-HMAC-SHA256 with 100,000 iterations.
- **JWT Signing**: Bearer tokens are signed using SHA-256 HMAC keys with configurable expiration horizons.

### 4. File Storage & Path Traversal Guards
- **Secure File Storage**: Uploaded PDF statements are named by cryptographically random UUIDs and isolated per tenant: `storage/documents/<org_id>/<doc_uuid>.pdf`.
- **Path Traversal Protection**: Every file retrieval resolves the absolute canonical path and ensures it strictly begins with `STORAGE_DIR`. Arbitrary path resolution is forbidden.
- **SHA-256 Checksums**: File integrity is validated via streaming SHA-256 checksums calculated upon ingest.

### 5. Forensic Audit Trail
- **Immutable Log Store**: Financial edits, category overrides, and review resolutions create non-destructive audit log records storing:
  - Timestamp (UTC)
  - Auditor email / ID
  - Action code
  - Pre-modification value (`old_value`)
  - Post-modification value (`new_value`)
  - Justification note for ICAI working paper compliance.
