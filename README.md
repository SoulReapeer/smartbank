# 💳 SmartBank — Full Stack Banking System

A portfolio-quality, full-stack digital banking web application built with **Flask**, **SQLAlchemy**, and **Bootstrap-free vanilla CSS**.

---

## Features

### Customer
- Register & login with hashed passwords
- Auto-generated unique account number on signup
- Dashboard with balance, stats, and recent activity
- Deposit, Withdraw, Transfer funds
- Full transaction history with filtering & search
- Profile management & password change

### Admin
- Admin dashboard with platform statistics
- View all customers and their accounts
- Freeze / Unfreeze accounts
- Monitor all transactions with filtering & search

---

## Tech Stack

| Layer      | Technology                        |
|------------|-----------------------------------|
| Backend    | Python 3.10+, Flask 3.0           |
| ORM        | Flask-SQLAlchemy, Flask-Migrate   |
| Auth       | Flask-Login, Werkzeug Security    |
| Database   | SQLite (dev) / PostgreSQL (prod)  |
| Frontend   | HTML5, CSS3 (custom), JavaScript  |
| Fonts      | Plus Jakarta Sans, DM Mono        |

---

## Project Structure

```
smartbank/
├── backend/
│   ├── app.py              # App factory, entry point
│   ├── config.py           # Configuration
│   ├── models.py           # SQLAlchemy models
│   ├── requirements.txt
│   ├── routes/
│   │   ├── auth.py         # Register, Login, Logout, Change Password
│   │   ├── dashboard.py    # Dashboard, Profile
│   │   ├── banking.py      # Deposit, Withdraw, Transfer, Transactions
│   │   └── admin.py        # Admin panel
│   ├── static/
│   │   ├── css/main.css    # Full design system
│   │   └── js/main.js
│   └── templates/
│       ├── base.html
│       ├── landing.html
│       ├── partials/sidebar.html
│       ├── auth/           # login, register, change_password
│       ├── customer/       # dashboard, profile, deposit, withdraw, transfer, transactions
│       └── admin/          # dashboard, users, transactions
└── database/
    └── banking.db          # Auto-created on first run
```

---

## Setup & Run

### 1. Clone / unzip the project

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

### 4. Run the application

```bash
python app.py
```

The app will:
- Auto-create the `database/banking.db` SQLite file
- Create a default **admin** account on first run
- Start at `http://127.0.0.1:5000`

---

## Default Credentials

| Role     | Email                    | Password   |
|----------|--------------------------|------------|
| Admin    | admin@smartbank.com      | admin123   |
| Demo     | demo@smartbank.com       | demo123    |

> ⚠️ Change all default passwords before any deployment.

---

## URL Reference

| URL                    | Description                        |
|------------------------|------------------------------------|
| `/`                    | Landing page                       |
| `/register`            | Customer registration              |
| `/login`               | Login (customer + admin)           |
| `/logout`              | Logout                             |
| `/dashboard`           | Customer dashboard                 |
| `/deposit`             | Deposit funds                      |
| `/withdraw`            | Withdraw funds                     |
| `/transfer`            | Transfer to another account        |
| `/transactions`        | Transaction history                |
| `/profile`             | View & edit profile                |
| `/change-password`     | Change password                    |
| `/admin/`              | Admin dashboard                    |
| `/admin/users`         | Manage users & freeze accounts     |
| `/admin/transactions`  | Monitor all transactions           |

---

## Database Schema

### `users`
| Column        | Type    | Notes                     |
|---------------|---------|---------------------------|
| id            | Integer | Primary key               |
| full_name     | String  |                           |
| email         | String  | Unique                    |
| phone         | String  |                           |
| password_hash | String  | Werkzeug hashed           |
| role          | String  | `customer` or `admin`     |
| created_at    | DateTime|                           |

### `accounts`
| Column         | Type    | Notes                          |
|----------------|---------|--------------------------------|
| id             | Integer | Primary key                    |
| user_id        | Integer | FK → users.id                  |
| account_number | String  | Unique, e.g. `ACC20261337`     |
| balance        | Float   | Default 0.0                    |
| status         | String  | `active` or `frozen`           |
| created_at     | DateTime|                                |

### `transactions`
| Column           | Type    | Notes                              |
|------------------|---------|------------------------------------|
| id               | Integer | Primary key                        |
| sender_account   | String  | Nullable (deposits have no sender) |
| receiver_account | String  | Nullable (withdrawals have no rcvr)|
| transaction_type | String  | `deposit`, `withdrawal`, `transfer`|
| amount           | Float   |                                    |
| reference        | String  |                                    |
| timestamp        | DateTime|                                    |

---

## Business Rules

1. Frozen accounts **cannot** deposit, withdraw, or transfer
2. Users **cannot** transfer money to themselves
3. Users **cannot** withdraw more than their available balance
4. Every financial action creates a **transaction record**
5. Every registered user gets an **account number automatically**
6. Only **admins** can freeze or unfreeze accounts

---

## Deployment (Render)

1. Set `DATABASE_URL` environment variable to a PostgreSQL URL
2. Set `SECRET_KEY` to a strong random string
3. Add `gunicorn` to `requirements.txt`
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `gunicorn app:app`

---

## Screenshots

| Page            | Description                        |
|-----------------|------------------------------------|
| Landing         | Hero + features + security section |
| Login/Register  | Split-panel auth layout            |
| Dashboard       | Balance card + stats + quick actions |
| Transactions    | Filterable, searchable table       |
| Admin Panel     | Stats + user freeze controls       |

---

*Built as a university software engineering portfolio project.*
