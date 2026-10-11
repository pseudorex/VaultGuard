# VaultGuard — Threshold-Based Secure Backup & Recovery Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-green.svg)](https://fastapi.tiangolo.com/)
[![Cryptography](https://img.shields.io/badge/Cryptography-AES--256--GCM-teal.svg)](https://cryptography.io/)
[![Security](https://img.shields.io/badge/Shamir-2--of--3%20Threshold-purple.svg)](https://en.wikipedia.org/wiki/Shamir%27s_Secret_Sharing)

VaultGuard is a threshold-based secure file backup and recovery platform designed for academic and portfolio demonstration. It solves single-point-of-failure and single-point-of-trust risks by combining **AES-256-GCM** authenticated encryption with **2-of-3 Shamir Secret Sharing** and a **dual-custodian governance quorum**.

---

## Key Features

1. **Authenticated Encryption (AES-256-GCM):** Fresh 256-bit Data Encryption Key (DEK) and unique 96-bit nonce generated per backup.
2. **2-of-3 Shamir Secret Sharing:** DEK is partitioned across 3 isolated key shares. Any 2 shares can reconstruct the key; 1 share alone yields zero mathematical information.
3. **Dual Custodian Quorum:** Restoration strictly requires 2 distinct custodian sign-offs before server-side key reconstruction.
4. **Tamper-Evident SHA-256 Audit Ledger:** All critical events (registration, uploads, verifications, approvals, restorations) are linked in a cryptographic hash chain ($H_i = \text{SHA256}(H_{i-1} \parallel \text{Event}_i)$).
5. **Interactive Cyber-Grade Web Console:** Built with modern CSS3 dark glassmorphism and vanilla JS.

---

## Architecture Overview

```
                       +-----------------------------------+
                       |         Frontend (Web UI)         |
                       | Vanilla JS, CSS3, Modern Dark UI  |
                       +-----------------+-----------------+
                                         | REST API / JWT
                                         v
+-----------------------------------------------------------------------------------+
|                            FastAPI Backend Application                            |
|                                                                                   |
|  [ Auth & RBAC ]        [ Backup Service ]        [ Recovery & Approval Engine ]  |
|  - Owner / Custodian    - AES-256-GCM Encrypt     - 2-of-3 Shamir Reconstruct     |
|  - JWT Bearer Tokens    - 2-of-3 Key Splitting    - 2 Custodian Approval Gate     |
|                                                                                   |
|  [ Integrity Service ]                            [ Audit Service ]               |
|  - AES-GCM Tag Verification                       - Hash-chained event log        |
+----------------------------------------+------------------------------------------+
                                         |
               +-------------------------+-------------------------+
               |                                                   |
               v                                                   v
+-----------------------------+                     +-------------------------------+
|       SQLite Database       |                     |     Local Storage Engine      |
| - Users & Passwords (Argon2)|                     | - Ciphertext Storage (.enc)   |
| - Backup Metadata           |                     | - Key Share Files (shares/)   |
| - Recovery & Approvals      |                     | - Safe path isolation         |
| - Hash-Chained Audit Logs   |                     +-------------------------------+
+-----------------------------+
```

---

## Quick Start Guide

### 1. Start the Backend API Server

```bash
# Navigate to backend and install requirements
cd backend
pip install -r requirements.txt

# Launch FastAPI with Uvicorn
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Interactive Swagger API Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check:** [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)

### 2. Start the Frontend Web UI

In a separate terminal:

```bash
cd frontend
python -m http.server 5500
```

Open [http://127.0.0.1:5500](http://127.0.0.1:5500) in your browser.

---

## Pre-seeded Demo Accounts

| Role | Email | Password | Description |
|---|---|---|---|
| **Data Owner** | `owner@demo.com` | `password123` | Uploads files, inspects metadata, requests recoveries |
| **Custodian 1** | `custodian1@demo.com` | `password123` | Security Custodian Alice (approves/rejects) |
| **Custodian 2** | `custodian2@demo.com` | `password123` | Compliance Custodian Bob (approves/rejects) |
| **Custodian 3** | `custodian3@demo.com` | `password123` | Infrastructure Custodian Carol (approves/rejects) |
| **Administrator** | `admin@demo.com` | `password123` | System Administrator |

---

## End-to-End Demonstration Walkthrough

1. **Sign In as Owner (`owner@demo.com`)**:
   - Go to `dashboard.html` and click **"New Secure Backup"**.
   - Upload any document (e.g. `secret.txt`).
   - The backend generates a fresh DEK, encrypts with AES-256-GCM, splits the DEK into 3 Shamir shares, and stores ciphertext and shares in separate directories.
2. **Run Cryptographic Integrity Check**:
   - Click **"Inspect"** on the backup.
   - Click **"Run Cryptographic Integrity Check"** -> observe the `VERIFIED` status badge.
3. **Initiate File Recovery**:
   - On the same page, submit a recovery request with a reason (e.g., *"Accidental deletion"*).
   - In `recovery.html`, note that status is `PENDING` (0 of 2 approvals).
4. **First Custodian Review**:
   - Log out and sign in as `custodian1@demo.com`.
   - Go to **"Custodian Queue"** (`custodian.html`) and click **"Approve"**.
   - Request status in `recovery.html` remains `PENDING` (1 of 2 approvals).
5. **Second Custodian Review & Quorum Threshold**:
   - Sign in as `custodian2@demo.com`.
   - Go to **"Custodian Queue"** and click **"Approve"**.
   - The approval threshold ($2 \ge 2$) is met; the request automatically transitions to `APPROVED`.
6. **Restore & Download**:
   - Sign in as `owner@demo.com` and visit `recovery.html`.
   - Click **"🔓 Restore & Download"**.
   - The backend combines 2 key shares to reconstruct the DEK, authenticates and decrypts the ciphertext, and triggers file download.
7. **Verify Tamper-Evident Hash Chain**:
   - Visit `audit.html` to view the cryptographic event timeline.
   - Click **"Verify Hash Chain Integrity"** to confirm that every log entry is linked and untampered.

---

## Project Structure

```text
VaultGuard/
├── PRD.md                         # Product Requirements Document
├── README.md                      # Comprehensive Architecture & Setup Guide
├── .gitignore
│
├── backend/
│   ├── requirements.txt           # Python dependencies
│   ├── .env.example               # Environment template
│   ├── .env                       # Local runtime config
│   ├── app/
│   │   ├── main.py                # FastAPI app initialization & CORS
│   │   ├── core/                  # Security, config, errors, permissions
│   │   ├── db/                    # SQLAlchemy engine & session
│   │   ├── models/                # User, Backup, KeyShare, Recovery, Approval, Audit
│   │   ├── schemas/               # Pydantic request/response validation
│   │   ├── api/routes/            # REST API endpoints
│   │   ├── services/              # Business logic (backup, recovery, audit, auth)
│   │   ├── crypto/                # AES-256-GCM and Galois Field GF(2^8) Shamir SSS
│   │   └── storage/               # Isolated ciphertext & share filesystem manager
│   └── data/                      # Local runtime data (git-ignored)
│
└── frontend/
    ├── index.html                 # Hero landing page
    ├── login.html                 # Login with demo switcher
    ├── register.html              # Account registration
    ├── dashboard.html             # Backups console & upload dropzone
    ├── backup-details.html        # Inspection & live integrity verification
    ├── recovery.html              # Quorum tracking & file restore download
    ├── custodian.html             # Custodian approval queue
    ├── audit.html                 # Tamper-evident audit ledger viewer
    └── assets/
        ├── css/styles.css         # Modern dark glassmorphism design system
        └── js/                    # Modular API client & page scripts
```
