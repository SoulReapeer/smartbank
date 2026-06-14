# 💳 SmartBank — Full Stack Digital Banking Platform

A portfolio-quality, full-stack banking web application built with **Flask**, **SQLAlchemy**, and a custom design system. SmartBank simulates a real digital banking platform — covering authentication, money management, QR transfers, notifications, audit logging, statements, and a business-intelligence admin dashboard.

This project has been developed across **3 phases**, each adding production-style features on top of the previous one.

---

## ✨ Features Overview

### 🔐 Authentication & Security
- Register, Login, Logout
- Email verification (required before login)
- Resend verification email
- Forgot / Reset password (token-based, expires in 1 hour)
- Change password
- Werkzeug password hashing
- Session-based authentication (Flask-Login)
- Full audit trail of all sensitive actions

### 🏦 Core Banking
- Deposit funds
- Withdraw funds (with balance validation)
- Transfer funds — **manual entry or QR code**
- Transaction history with filtering & search
- Frozen-account protection on all banking actions

### 👤 Customer Features
- Dashboard with balance card, stats, and interactive charts
- Profile management (edit name/phone)
- **Personal QR code** for receiving transfers (downloadable)
- Transaction history (filter by type, search by reference)
- **PDF bank statements** (ReportLab)
- **Excel exports** of transaction history (Pandas + OpenPyXL)
- **Notification center** — in-app bell + dedicated page
- Email notifications for every transaction

### 🛡️ Admin Features
- Business-intelligence dashboard with 7 stat cards
- Manage users — freeze / unfreeze accounts
- Monitor all transactions (filter & search)
- **Audit logs** — searchable, filterable, paginated
- **Most Active Customers** ranking table
- **Largest Transfers** table
- Export all transactions to Excel
- 4 interactive Chart.js analytics charts

### 📊 Charts & Analytics
**Customer Dashboard:**
- Transaction distribution (doughnut)
- Monthly activity (bar)
- Balance trend (line)

**Admin Dashboard:**
- Daily transaction volume (last 14 days)
- Monthly deposits vs withdrawals
- User growth (registrations per month)
- Top customer activity (horizontal bar)

### 🔔 Hybrid Notifications
Every deposit, withdrawal, transfer (sent & received), password change, and account freeze/unfreeze triggers:
1. An **in-app notification** (bell icon, auto-refreshing dropdown)
2. An **email notification** (console output in dev mode, real SMTP in prod)

Email failures never block a transaction — in-app notifications always work.

### 📱 QR Transfer System
- Every account has a unique QR code (encodes the account number)
- Profile page displays and lets you download your QR code
- Transfer page supports **two methods**:
  - **Manual entry** — type the receiver's account number (unchanged, original behavior)
  - **QR upload** — upload a QR image, auto-decode, preview receiver name/account/status before confirming
- Self-transfers and frozen-account transfers are blocked at decode time

---

## 🧱 Tech Stack

| Layer       | Technology                                    |
|-------------|------------------------------------------------|
| Backend     | Python 3.10+, Flask 3.0                        |
| ORM         | Flask-SQLAlchemy, Flask-Migrate                |
| Auth        | Flask-Login, Werkzeug Security                 |
| Database    | SQLite (dev) / PostgreSQL (prod-ready)         |
| Frontend    | HTML5, custom CSS3, vanilla JavaScript         |
| Charts      | Chart.js 4                                     |
| PDF         | ReportLab                                      |
| Excel       | Pandas + OpenPyXL                              |
| QR Codes    | `qrcode` (generate), OpenCV + Pillow (decode)  |
| Email       | smtplib (console output in dev mode)           |
| Fonts       | Plus Jakarta Sans, DM Mono                     |

---

## 📁 Project Structure

```
smartbank/
├── backend/
│   ├── app.py                      # App factory, entry point
│   ├── config.py                   # Configuration (DB, mail, secret key)
│   ├── models.py                   # SQLAlchemy models
│   ├── requirements.txt
│   ├── migrate_phase2.py           # One-time migration for Phase 2 tables
│   ├── migrate_phase3.py           # One-time migration for Phase 3 tables
│   │
│   ├── routes/
│   │   ├── auth.py                 # Register, Login, Logout, Verify, Forgot/Reset Password
│   │   ├── dashboard.py            # Dashboard, Profile (+ chart data)
│   │   ├── banking.py              # Deposit, Withdraw, Transfer, QR, Statements
│   │   ├── admin.py                # Admin panel, analytics, audit logs
│   │   └── notifications.py        # Notification center + bell API
│   │
│   ├── services/
│   │   ├── email_service.py        # Verification, reset & transaction emails
│   │   ├── audit_service.py        # Audit log helper + action constants
│   │   ├── pdf_service.py          # PDF statement generator (ReportLab)
│   │   ├── excel_service.py        # Excel export generator (Pandas/OpenPyXL)
│   │   ├── qr_service.py           # QR generation & decoding
│   │   └── notification_service.py # In-app + email hybrid notifications
│   │
│   ├── static/
│   │   ├── css/main.css            # Full design system
│   │   └── js/main.js
│   │
│   └── templates/
│       ├── base.html
│       ├── landing.html
│       ├── partials/
│       │   └── sidebar.html        # Customer sidebar (with notification badge)
│       ├── auth/
│       │   ├── login.html
│       │   ├── register.html
│       │   ├── change_password.html
│       │   ├── forgot_password.html
│       │   ├── reset_password.html
│       │   └── resend_verification.html
│       ├── customer/
│       │   ├── layout.html         # Topbar + notification bell dropdown
│       │   ├── dashboard.html      # Balance, stats, charts, downloads
│       │   ├── profile.html        # Profile + My QR Code
│       │   ├── deposit.html
│       │   ├── withdraw.html
│       │   ├── transfer.html       # Manual + QR transfer tabs
│       │   ├── transactions.html   # History + PDF/Excel downloads
│       │   └── notifications.html  # Full notification center
│       └── admin/
│           ├── layout.html
│           ├── dashboard.html      # Analytics dashboard
│           ├── users.html
│           ├── transactions.html
│           └── audit_logs.html
│
└── database/
    └── banking.db                  # Auto-created on first run
```

---

## 🚀 Setup & Run

### 1. Navigate to the backend folder

```bash
cd smartbank/backend
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

> Note: `opencv-python-headless` (used for QR decoding) is a larger package (~60-90MB), so this step may take a minute.

### 4. Run the application

```bash
python app.py
```

On first run, the app will:
- Auto-create `database/banking.db`
- Create all tables (users, accounts, transactions, audit_logs, password_reset_tokens, notifications)
- Create a default **admin** account
- Start at `http://127.0.0.1:5000`

### 5. (Existing databases only) Run migrations

If you're upgrading an existing SmartBank database from an earlier phase, run these **once**, in order:

```bash
python migrate_phase2.py   # adds email verification, password reset, audit logs
python migrate_phase3.py   # adds notifications table
```

---

## 🌐 Accessing from Your Phone / Other Devices

By default, Flask only listens on `127.0.0.1` (your computer only). To access SmartBank from your phone on the same Wi-Fi network:

1. In `app.py`, change the last line to:
   ```python
   app.run(debug=True, host='0.0.0.0', port=5000)
   ```
2. Find your computer's local IP address (`ipconfig` on Windows, `ifconfig` on Mac/Linux) — looks like `192.168.x.x`
3. On your phone, visit `http://192.168.x.x:5000`

Both devices must be on the same network, and your firewall must allow incoming connections on port 5000.

---

## 🔑 Default Credentials

| Role     | Email                  | Password   | Notes                          |
|----------|------------------------|------------|--------------------------------|
| Admin    | admin@smartbank.com    | admin123   | Pre-verified                    |
| Demo     | demo@smartbank.com     | demo123    | Pre-verified, seeded with funds |

> ⚠️ Change all default passwords before any real deployment.

New users registered after Phase 2 **must verify their email** before logging in. In development mode (no SMTP configured), verification links are printed to the terminal console.

---

## 📧 Email Configuration

By default, no SMTP server is configured — all emails (verification, password reset, transaction notifications) are printed to the **terminal console** in dev mode. This requires zero setup.

To send real emails, set these environment variables:

```bash
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=noreply@smartbank.com
```

---

## 🗺️ URL Reference

### Public
| URL | Description |
|---|---|
| `/` | Landing page |
| `/register` | Customer registration |
| `/login` | Login (customer + admin) |
| `/logout` | Logout |
| `/verify-email/<token>` | Email verification link |
| `/resend-verification` | Resend verification email |
| `/forgot-password` | Request password reset |
| `/reset-password/<token>` | Reset password form |

### Customer
| URL | Description |
|---|---|
| `/dashboard` | Balance, stats, charts, quick actions |
| `/deposit` | Deposit funds |
| `/withdraw` | Withdraw funds |
| `/transfer` | Transfer funds (manual or QR) |
| `/transfer/qr-decode` | POST — decode uploaded QR image |
| `/transactions` | Transaction history |
| `/profile` | View/edit profile + QR code |
| `/change-password` | Change password |
| `/qr-code` | Inline PNG of account QR |
| `/qr-code/download` | Downloadable PNG of account QR |
| `/statement/pdf` | Download PDF statement |
| `/statement/excel` | Download Excel export |
| `/notifications` | Notification center |
| `/notifications/mark-all-read` | POST — mark all read |
| `/notifications/<id>/read` | POST — mark one read |
| `/api/notifications` | JSON — bell dropdown data |

### Admin
| URL | Description |
|---|---|
| `/admin/` | Analytics dashboard |
| `/admin/users` | Manage users & accounts |
| `/admin/freeze/<id>` | Freeze account |
| `/admin/unfreeze/<id>` | Unfreeze account |
| `/admin/transactions` | Monitor all transactions |
| `/admin/audit-logs` | Searchable audit trail |
| `/admin/export/excel` | Export all transactions to Excel |

---

## 🗄️ Database Schema

### `users`
| Column | Type | Notes |
|---|---|---|
| id | Integer | Primary key |
| full_name | String | |
| email | String | Unique |
| phone | String | |
| password_hash | String | Werkzeug hashed |
| role | String | `customer` or `admin` |
| is_verified | Boolean | Must be true to log in |
| verification_token | String | Nullable, cleared after verification |
| created_at | DateTime | |

### `accounts`
| Column | Type | Notes |
|---|---|---|
| id | Integer | Primary key |
| user_id | Integer | FK → users.id |
| account_number | String | Unique, e.g. `ACC20261337` |
| balance | Float | Default 0.0 |
| status | String | `active` or `frozen` |
| created_at | DateTime | |

### `transactions`
| Column | Type | Notes |
|---|---|---|
| id | Integer | Primary key |
| sender_account | String | Nullable (deposits have no sender) |
| receiver_account | String | Nullable (withdrawals have no receiver) |
| transaction_type | String | `deposit`, `withdrawal`, `transfer` |
| amount | Float | |
| reference | String | |
| timestamp | DateTime | |

### `password_reset_tokens`
| Column | Type | Notes |
|---|---|---|
| id | Integer | Primary key |
| user_id | Integer | FK → users.id |
| token | String | Unique |
| expires_at | DateTime | 1 hour from creation |
| used | Boolean | Prevents token reuse |
| created_at | DateTime | |

### `audit_logs`
| Column | Type | Notes |
|---|---|---|
| id | Integer | Primary key |
| user_id | Integer | FK → users.id, nullable |
| action | String | e.g. `login`, `deposit`, `account_freeze` |
| details | String | Human-readable description |
| ip_address | String | Request IP |
| timestamp | DateTime | |

### `notifications`
| Column | Type | Notes |
|---|---|---|
| id | Integer | Primary key |
| user_id | Integer | FK → users.id |
| title | String | e.g. "Deposit Successful" |
| message | String | Full notification text |
| type | String | `deposit`, `transfer_sent`, `account_frozen`, etc. |
| is_read | Boolean | |
| created_at | DateTime | |

---

## 📜 Business Rules

1. Frozen accounts **cannot** deposit, withdraw, or transfer
2. Users **cannot** transfer money to themselves (manual or QR)
3. Users **cannot** withdraw more than their available balance
4. Every financial action creates a **transaction record**, an **audit log**, and a **notification**
5. Every registered user gets an **account number automatically**
6. Only **admins** can freeze or unfreeze accounts
7. Users **cannot log in** until their email is verified
8. Password reset tokens **expire after 1 hour** and cannot be reused
9. QR transfers validate receiver existence, account status, and self-transfer — same as manual transfers
10. Email delivery failures **never block** a transaction or notification — in-app notifications always succeed

---

## 🔍 Audit Log Actions

| Action | Triggered by |
|---|---|
| `register` | New user registration |
| `email_verified` | Email verification link clicked |
| `login` / `logout` | Authentication |
| `password_change` | Change password (logged in) |
| `password_reset` | Password reset via email link |
| `deposit` / `withdrawal` / `transfer` | Banking operations |
| `profile_update` | Profile edits |
| `account_freeze` / `account_unfreeze` | Admin account actions |
| `statement_download` | PDF statement downloaded |
| `excel_export` | Excel export downloaded |

---

## 🚢 Deployment (Render / Production)

1. Set `DATABASE_URL` to a PostgreSQL connection string
2. Set `SECRET_KEY` to a strong random string
3. Configure `MAIL_SERVER`, `MAIL_USERNAME`, `MAIL_PASSWORD` for real email delivery
4. Add `gunicorn` to `requirements.txt`
5. Build command: `pip install -r requirements.txt`
6. Start command: `gunicorn app:app`
7. Remove `debug=True` and `host='0.0.0.0'` from the dev `app.run()` block — gunicorn handles serving

---

## 🛠️ Development Notes

- **QR format**: QR codes encode `SMARTBANK:<account_number>`. The decoder also accepts raw account numbers for compatibility with externally generated codes.
- **Notification polling**: The bell dropdown polls `/api/notifications` every 30 seconds.
- **Chart data**: All chart data is computed server-side in `routes/dashboard.py` and `routes/admin.py`, then passed to Chart.js via `tojson`.
- **PDF/Excel generation**: Both run entirely in-memory (`io.BytesIO`) — no temp files are written to disk.

---

*Built as a full-stack software engineering portfolio project — developed iteratively across three feature phases.*
