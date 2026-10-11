# VaultGuard — Product Requirements Document (PRD)

**Project:** VaultGuard — Threshold-Based Secure Backup & Recovery Platform  
**Document type:** Product Requirements Document  
**Status:** MVP implementation draft  
**Target:** Academic / portfolio prototype

---

## 1. Executive Summary

VaultGuard is a secure file backup and recovery application. Files are encrypted before being stored. The encryption key is split into three shares using Shamir Secret Sharing, with a **2-of-3 recovery threshold**: any two valid shares can reconstruct the key, while one share alone is insufficient.

Restoration also requires approval from **two distinct custodians**. Security-relevant actions are recorded in a hash-chained audit log so changes to logged events can be detected.

This PRD defines the MVP, technology stack, separate frontend and backend repositories/folders, core workflows, API endpoints, data model, security requirements, and implementation phases. It describes an academic prototype, not a production-certified backup service.

## 2. Problem Statement

A backup may become unusable or unsafe if its encryption key is lost, stolen, or controlled by one person. VaultGuard demonstrates a recovery design in which no single custodian holds enough key material to restore a file and restoration requires a multi-person approval process with an auditable record.

## 3. Goals and Non-Goals

### 3.1 Goals

- Allow users to register, sign in, and upload files for encrypted backup.
- Encrypt file bytes using AES-256-GCM with a fresh, cryptographically secure data-encryption key (DEK).
- Split the DEK into three shares with a threshold of two.
- Keep encrypted files and key shares in separate logical storage locations with server-side access controls.
- Require two distinct authorized custodians to approve a recovery request.
- Detect file tampering through authenticated encryption verification.
- Record uploads, verification attempts, recovery requests, approvals, restores, and relevant security actions in a hash-chained audit log.
- Provide a simple dashboard for backups, recovery requests, approvals, and audit events.
- Document setup, architecture, security assumptions, and a demonstration flow.

### 3.2 Non-Goals for the MVP

- Production-grade cloud storage, multi-region replication, or guaranteed disaster recovery.
- Real email/SMS notifications or paid external APIs.
- Independent physical custodian devices. The MVP uses separate accounts and roles to demonstrate the workflow.
- Client-side-only encryption where the server never sees plaintext or key material. The MVP encrypts on the backend; do not describe it as zero-knowledge or end-to-end encryption.
- Hardware security modules, compliance certification, or formal cryptographic verification.
- Mobile applications, collaborative editing, or large-file streaming encryption.

## 4. Users and Roles

| Role | Permissions |
|---|---|
| **Owner** | Uploads files, views their own backups, requests recovery, checks integrity, and downloads restored files. |
| **Custodian** | Views relevant recovery requests and approves or rejects them. One custodian cannot approve the same request twice. |
| **Administrator (optional)** | Manages demo users and views system health. Must not have an undocumented recovery bypass. |

Every permission must be enforced by the backend. Hiding a button in the frontend is not access control.

## 5. Main Workflows

### 5.1 Secure Backup

1. The user signs in and selects a file in the frontend.
2. The backend validates authentication, file size, and filename.
3. The backend generates a random 256-bit DEK and a unique nonce.
4. The backend encrypts the file bytes with AES-256-GCM.
5. The backend splits the DEK into three shares using a Shamir implementation configured for a 2-of-3 threshold.
6. The ciphertext is saved using a generated backup ID. Each share is stored separately and is never returned through ordinary API responses.
7. Backup metadata is saved, and an audit event is appended.
8. The frontend displays the backup ID, timestamp, and status.

### 5.2 Recovery and Restore

1. The owner selects a backup and creates a recovery request with a reason.
2. The request is stored with status `PENDING`.
3. Two different authorized custodians approve the request.
4. After the approval threshold is met, the recovery service obtains two valid shares through a controlled server-side path and reconstructs the DEK in memory.
5. AES-GCM authenticates and decrypts the ciphertext. If authentication fails, the restore stops and no output file is provided.
6. The result is recorded in the audit log and the restored file is returned to the authorized owner.

### 5.3 Integrity Verification

1. The owner requests verification for one of their backups.
2. The backend checks the stored encrypted payload and relevant metadata using authenticated decryption or an equivalent controlled verification routine.
3. The API returns a clear result such as `VERIFIED` or `TAMPERED_OR_UNVERIFIABLE`.
4. The verification result is added to the audit log.

## 6. Functional Requirements

| ID | Feature | Requirement |
|---|---|---|
| FR-01 | Authentication | Users can register and log in. Passwords are stored as secure hashes, never plaintext. Protected endpoints require valid authentication. |
| FR-02 | Authorization | The backend checks resource ownership and role permissions on every protected request. |
| FR-03 | Upload validation | Enforce a configurable file-size limit, sanitize filenames, and use generated storage names. Never trust a client-supplied path. |
| FR-04 | Encryption | Use the `cryptography` library for AES-256-GCM. Generate a fresh DEK per backup and never reuse a nonce with the same key. |
| FR-05 | Key splitting | Split each DEK into three shares with a threshold of two using a maintained, reviewed Shamir implementation. |
| FR-06 | Backup listing | Users can list only their own backups, including safe metadata and integrity status. Never return keys or shares. |
| FR-07 | Recovery requests | Owners can create and view recovery requests, including reason, status, and timestamps. |
| FR-08 | Approval policy | Only authorized custodians can approve or reject requests. Require two distinct approvals and prevent duplicate approvals. |
| FR-09 | Restore | Only an eligible, approved request can restore a file. Reconstruct the key in memory and authenticate before returning plaintext. |
| FR-10 | Tamper detection | Changes to ciphertext or authenticated metadata must cause verification/decryption to fail safely. |
| FR-11 | Audit trail | Append events containing event ID, timestamp, actor, action, target, outcome, previous hash, and current hash. |
| FR-12 | Audit viewer | Authorized users can view relevant audit events. Never log passwords, tokens, plaintext file contents, DEKs, or shares. |
| FR-13 | Error handling | Return consistent JSON errors and appropriate HTTP status codes. Do not expose stack traces or cryptographic secrets. |
| FR-14 | Documentation | Include setup instructions, environment configuration, architecture, threat-model notes, API documentation, and a demo walkthrough. |

## 7. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | Python 3.12+ or another currently supported Python 3.x version | Backend implementation |
| API framework | FastAPI + Uvicorn | REST API |
| Validation | Pydantic | Request/response validation |
| Database | SQLite | Simple local MVP database |
| ORM | SQLAlchemy 2.x | Database models and queries |
| Password hashing | `pwdlib` with Argon2, or another maintained password-hashing library | Secure password storage |
| Authentication | JWT bearer tokens for the prototype, or secure server-side sessions | Authenticated API access |
| Encryption | `cryptography` | AES-GCM and secure random generation |
| Secret sharing | A maintained Shamir Secret Sharing package, reviewed before adoption | Split and reconstruct the DEK |
| Frontend | HTML5, CSS3, vanilla JavaScript | Web interface |
| Frontend API calls | Fetch API | Call the backend REST endpoints |
| Configuration | `pydantic-settings` and environment variables | Centralized configuration |
| API exploration | FastAPI Swagger UI at `/docs` | Inspect and try API endpoints |
| Version control | Git and GitHub | Source control |

**Not required for the initial MVP:** Alembic, Redis, Celery, Docker, a cloud bucket, paid APIs, or a frontend framework. Use SQLAlchemy's simple `create_all` initialization for the early local prototype. If the schema changes later, reset only disposable development data or add a migration tool as a separate future task.

## 8. Project Folder Structure

Keep the frontend and backend in **separate top-level folders**. The frontend must not contain server-side cryptography, database access, or secret shares.

```text
vaultguard/
├── README.md
├── PRD.md
├── .gitignore
│
├── backend/
│   ├── requirements.txt
│   ├── .env.example
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # Create FastAPI app and register routers
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # Read environment-based settings
│   │   │   ├── security.py         # Password hashing and token helpers
│   │   │   ├── permissions.py      # Shared authorization rules
│   │   │   └── errors.py           # Consistent API error responses
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── session.py          # SQLAlchemy engine and DB sessions
│   │   │   └── base.py             # Base model metadata/imports
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── backup.py
│   │   │   ├── key_share.py
│   │   │   ├── recovery.py
│   │   │   ├── approval.py
│   │   │   └── audit_event.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── user.py
│   │   │   ├── backup.py
│   │   │   ├── recovery.py
│   │   │   └── audit.py
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py              # Current user and DB dependencies
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py
│   │   │       ├── users.py
│   │   │       ├── backups.py
│   │   │       ├── recovery.py
│   │   │       ├── approvals.py
│   │   │       ├── integrity.py
│   │   │       └── audit.py
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── backup_service.py
│   │   │   ├── recovery_service.py
│   │   │   ├── approval_service.py
│   │   │   ├── integrity_service.py
│   │   │   └── audit_service.py
│   │   │
│   │   ├── crypto/
│   │   │   ├── __init__.py
│   │   │   ├── encryption.py       # AES-GCM encrypt/decrypt helpers
│   │   │   ├── secret_sharing.py   # Shamir split/combine wrapper
│   │   │   └── formats.py          # Versioned encrypted-payload format
│   │   │
│   │   └── storage/
│   │       ├── __init__.py
│   │       └── local_storage.py    # Safe generated paths for ciphertext/shares
│   │
│   └── data/
│       ├── .gitkeep
│       └── README.md               # Explain local runtime storage; no real data in Git
│
└── frontend/
    ├── README.md
    ├── index.html                  # Landing / redirect to login or dashboard
    ├── login.html
    ├── register.html
    ├── dashboard.html
    ├── backup-details.html
    ├── recovery.html
    ├── custodian.html
    ├── audit.html
    ├── assets/
    │   ├── css/
    │   │   └── styles.css
    │   ├── js/
    │   │   ├── config.js           # Backend base URL
    │   │   ├── api.js              # Shared fetch wrapper and error handling
    │   │   ├── auth.js
    │   │   ├── dashboard.js
    │   │   ├── backups.js
    │   │   ├── recovery.js
    │   │   ├── custodian.js
    │   │   └── audit.js
    │   └── images/
    │       └── .gitkeep
    └── .gitignore
```

### Folder responsibilities

- **`backend/app/api/routes/`**: HTTP endpoints only; parse input, call services, and return responses.
- **`backend/app/services/`**: Business workflows such as creating backups, requesting recovery, checking approvals, and recording audit events.
- **`backend/app/crypto/`**: Small, isolated cryptographic helpers. Do not put encryption logic directly in route handlers.
- **`backend/app/models/`**: SQLAlchemy database models.
- **`backend/app/schemas/`**: Pydantic request and response schemas.
- **`backend/app/storage/`**: Reads/writes encrypted payloads and key-share files using generated IDs and safe paths.
- **`backend/data/`**: Local runtime data only. Never serve this directory as static frontend content or commit real backup files/shares.
- **`frontend/`**: Browser UI only. It calls the backend API and must never store or calculate DEKs or Shamir shares.

The structure is a target layout. Create modules gradually as each feature is implemented; avoid empty files that do not yet serve a purpose.

## 9. Database Model

| Entity | Suggested fields |
|---|---|
| `User` | `id`, `email` (unique), `password_hash`, `display_name`, `role`, `is_active`, `created_at` |
| `Backup` | `id`, `owner_id`, `original_filename`, `stored_path`, `size_bytes`, `algorithm`, `nonce`, `payload_version`, `created_at`, `status` |
| `KeyShare` | `id`, `backup_id`, `share_index`, `protected_share_path` or `encrypted_share_value`, `created_at` |
| `RecoveryRequest` | `id`, `backup_id`, `requester_id`, `reason`, `status`, `created_at`, `expires_at`, `completed_at` |
| `Approval` | `id`, `recovery_request_id`, `custodian_id`, `decision`, `comment`, `created_at`; unique constraint on `(recovery_request_id, custodian_id)` |
| `AuditEvent` | `id`, `actor_id` (nullable), `action`, `target_type`, `target_id`, `outcome`, `timestamp`, `previous_hash`, `event_hash`, `safe_metadata_json` |

Use UUIDs or similarly unguessable external IDs. Add foreign keys and useful indexes. Do not store plaintext file contents in the database. Avoid persisting DEKs; reconstruct them only for an authorized operation. For a real deployment, simple share files on one machine are not equivalent to independent custody.

## 10. API Endpoint Plan

| Method | Endpoint | Purpose |
|---|---|---|
| `POST` | `/api/auth/register` | Register a user |
| `POST` | `/api/auth/login` | Authenticate and issue token/session |
| `POST` | `/api/auth/logout` | Invalidate session where supported |
| `GET` | `/api/users/me` | Return the current user's safe profile |
| `POST` | `/api/backups` | Upload, encrypt, split key, and create backup |
| `GET` | `/api/backups` | List the current user's backups |
| `GET` | `/api/backups/{backup_id}` | Get safe metadata for one owned backup |
| `DELETE` | `/api/backups/{backup_id}` | Delete backup and associated shares according to policy |
| `POST` | `/api/backups/{backup_id}/verify` | Verify integrity/authentication |
| `POST` | `/api/backups/{backup_id}/recovery-requests` | Create a recovery request |
| `GET` | `/api/recovery-requests` | List requests relevant to the current user |
| `GET` | `/api/recovery-requests/{request_id}` | View request status and approvals |
| `POST` | `/api/recovery-requests/{request_id}/approve` | Custodian approves a request |
| `POST` | `/api/recovery-requests/{request_id}/reject` | Custodian rejects a request |
| `POST` | `/api/recovery-requests/{request_id}/restore` | Restore only after approval threshold is met |
| `GET` | `/api/audit-events` | View authorized audit events with pagination |
| `POST` | `/api/audit-events/verify-chain` | Verify the audit hash chain |

Use consistent response schemas and status codes. All resource-specific endpoints must enforce ownership and role checks.

## 11. Recovery State Machine

Allowed recovery request states:

- **`PENDING`** — Request created; approvals are being collected.
- **`APPROVED`** — Two distinct authorized custodians approved; eligible for restoration.
- **`REJECTED`** — Request rejected under the configured policy.
- **`EXPIRED`** — Request exceeded its validity window.
- **`COMPLETED`** — Restore succeeded and the result was delivered.
- **`FAILED`** — Restore failed, including a cryptographic authentication failure.

State transitions must be enforced by backend services and rechecked during the database transaction. Never trust a status value sent by the frontend.

## 12. Security and Privacy Requirements

- Use cryptographically secure randomness for DEKs, nonces, tokens, and share generation.
- Use AES-GCM correctly. Never reuse a nonce with the same key; store the nonce and required format metadata; fail closed on authentication failure.
- Use a fresh DEK for each backup. Do not hard-code encryption keys or authentication secrets in source code.
- Use maintained libraries; do not implement AES, password hashing, or token algorithms from scratch.
- Treat the backend, database, and local storage as part of the trust boundary. Do not claim zero-knowledge or end-to-end encryption.
- Protect key shares separately as far as the local MVP allows. Separate paths and role-gated service methods demonstrate the concept but do not provide the security of independent physical custody.
- Require two distinct authorized custodians. Database constraints must prevent duplicate approvals by the same account.
- Enforce upload limits, safe generated storage paths, and path traversal protections.
- Use HTTPS in any deployed environment. If cookie-based sessions are selected, set secure cookie attributes.
- Never log passwords, tokens, plaintext contents, DEKs, or shares.
- Use safe client-facing error messages for cryptographic failures.
- Restrict and paginate audit event access.
- Hash chaining detects changes to events when a trusted checkpoint is available. An attacker able to rewrite the entire log and recompute all hashes may evade detection; document this limitation.
- Deletion should remove ciphertext, shares, and metadata consistently. Do not claim guaranteed physical erasure from a normal local filesystem.

## 13. Frontend Screens

| Screen | Required UI |
|---|---|
| Login / Register | Account forms, validation, and clear error messages |
| Dashboard | Backup list, recent activity, integrity status, and quick actions |
| Upload Backup | File picker, size validation, upload progress, and success/error state |
| Backup Details | Safe metadata, integrity verification, and recovery request action |
| Recovery Requests | Status, approval count, custodian decisions, expiry, and restore action when eligible |
| Custodian Queue | Relevant pending requests with approve/reject controls |
| Audit Viewer | Paginated events and a control to verify the hash chain |

Use a shared API helper in `frontend/assets/js/api.js` so authentication headers, response parsing, and error handling are consistent. Configure the backend base URL in one place. During local development, the frontend may run on a separate port; configure FastAPI CORS to allow only the exact local frontend origin(s) being used.

## 14. Non-Functional Requirements

- **Usability:** Users can complete the main backup and recovery demo through a browser.
- **Maintainability:** Keep API routes, services, models, cryptography, and storage separated.
- **Reliability:** Failed encryption, key reconstruction, approval checks, or decryption must never return partial plaintext.
- **Performance:** Begin with typical documents and small media files. A suggested initial upload limit is 10 MB.
- **Portability:** Local development should work on Windows, macOS, or Linux with a supported Python version.
- **Accessibility:** Forms need labels, visible errors, keyboard focus, and readable contrast.

## 15. Acceptance Criteria

- A user can register, log in, upload a file, and see the backup on the dashboard.
- Stored backup bytes are ciphertext and do not match the original plaintext bytes.
- A file can be restored byte-for-byte after two valid shares and two distinct approvals.
- One share alone is insufficient to reconstruct the DEK.
- A user cannot list, verify, delete, or restore another user's backup.
- A custodian cannot approve the same request twice or satisfy two approval slots with one account.
- Restoration is denied before the approval threshold is met.
- Modifying ciphertext or authenticated metadata makes verification/decryption fail safely.
- Changing or removing an audit event causes hash-chain verification to fail when the stored checkpoint is trusted.
- API responses, frontend pages, and logs do not expose DEKs or secret shares.
- The root README explains how to run the backend and frontend separately.

## 16. Implementation Roadmap

1. **Project setup:** Create the root folder, separate `backend/` and `frontend/`, set up the Python virtual environment, install dependencies, configure settings, and start the FastAPI app.
2. **Cryptographic core:** Implement AES-GCM helpers and a Shamir wrapper. Confirm the encrypt/decrypt and split/combine flows work before adding the UI.
3. **Database and authentication:** Add user models, password hashing, login, role checks, and database initialization with SQLAlchemy `create_all`.
4. **Backup workflow:** Implement validated uploads, encryption, ciphertext storage, share storage, backup metadata, listing, and ownership checks.
5. **Recovery workflow:** Implement request states, custodian approval rules, key reconstruction, authenticated restore, and download.
6. **Integrity and audit:** Add integrity verification, hash-chained audit events, audit listing, and chain verification.
7. **Frontend integration:** Build the pages, shared API helper, loading/error states, and role-specific views. Configure CORS for local development.
8. **Polish and demo readiness:** Improve error messages, write setup instructions, prepare sample files/accounts, and document the threat model and prototype limitations.

Build in this order and keep each step small. The frontend can start with simple HTML/CSS/JavaScript; no React or Flutter is required for the MVP.

## 17. Environment Configuration

Create `backend/.env.example` with placeholder values such as:

```dotenv
APP_NAME=VaultGuard
ENVIRONMENT=development
DATABASE_URL=sqlite:///./vaultguard.db
JWT_SECRET=replace-with-a-long-random-development-secret
ACCESS_TOKEN_EXPIRE_MINUTES=30
STORAGE_DIR=./data
MAX_UPLOAD_SIZE_MB=10
RECOVERY_REQUEST_TTL_HOURS=24
FRONTEND_ORIGINS=http://127.0.0.1:5500,http://localhost:5500
```

Never commit a real `.env` file. Add `.env`, database files, runtime ciphertext/share folders, Python caches, and virtual environments to `.gitignore`. Keep runtime files outside the frontend folder and never expose the `backend/data/` directory as static content.

## 18. Demo Walkthrough

1. Register an owner and three custodian accounts.
2. Upload a small text file and show that the stored version is encrypted.
3. Run integrity verification and show `VERIFIED`.
4. Create a recovery request and show that restore is not yet allowed.
5. Approve as Custodian A and show that one approval is insufficient.
6. Approve as Custodian B, restore the file, and compare it with the original.
7. In a disposable demo copy, alter one byte of a ciphertext file and show that verification/restore fails without returning plaintext.
8. Show the audit log and verify its hash chain. In a disposable test copy, alter an event and demonstrate that verification detects the change.

## 19. Risks and Limitations

| Risk | Mitigation / disclosure |
|---|---|
| Shares stored on one machine | Use separate storage paths and role-gated services for the prototype, but disclose that this is not independent physical custody. |
| Shamir library quality | Review maintenance and usage before selecting a package. Isolate it behind `backend/app/crypto/secret_sharing.py`. |
| Audit-chain trust | Explain that hash chaining is tamper-evident only relative to a trusted checkpoint; external signing/checkpoint storage is future work. |
| Large files | Use a modest upload limit initially; streaming encryption is out of MVP scope. |
| Security claims | Do not claim production-grade security, zero-knowledge encryption, or guaranteed physical erasure. |

## 20. Final MVP Scope

The MVP consists of a browser-based application with authentication, encrypted file backup, 2-of-3 Shamir key splitting, two-person recovery approval, authenticated restoration, tamper detection, and a hash-chained audit log.

Use **FastAPI + SQLAlchemy + SQLite** in the separate `backend/` folder and **HTML + CSS + vanilla JavaScript** in the separate `frontend/` folder. Keep cryptographic operations on the backend, keep the folder structure modular, and add features in the order described in the roadmap.
