# Journal Voucher System

A Django-based journal voucher and accounting management REST API with an admin dashboard. Supports voucher creation, validation, posting workflows, and Excel batch uploads.

## Tech stack

| Layer | Technology |
|-------|-----------|
| Framework | Django 5.2, Django REST Framework 3.15 |
| Admin UI | Jazzmin 3.0 (with custom sidebar, icons, theming) |
| Database | SQLite (dev) / PostgreSQL (production) |
| WSGI server | Gunicorn 23 |
| Static files | WhiteNoise 6 |
| Other | django-cors-headers, django-filter, openpyxl |

## Features

### Sprint 1 — Master Data & Base Setup

| Feature | Description |
|---------|-------------|
| Master Data API | CRUD for Company, Branch, Currency |
| Accounting Period API | Period lifecycle with date validation (start ≤ end) |
| Chart of Accounts API | Hierarchical account structure with parent-child |
| Vendor API | Vendor/supplier management with tax ID, bank accounts |
| Jazzmin Admin | Themed admin UI with sidebar navigation and icons |
| DRF REST API | Full CRUD with search, ordering, pagination (25/page) |

### Sprint 2 — Journal Voucher Engine

| Feature | Description |
|---------|-------------|
| Journal Voucher | Auto-generated voucher numbers (`JV-YYYYMMDD-NNNN`) |
| Journal Entries | Writable nested serializer with debit/credit validation |
| Business Rules | Debit = credit enforced, period must be open, account must be active |
| Validate / Void | `POST /{id}/validate/` checks all rules; `POST /{id}/void/` marks VOID |
| Excel Upload | `POST /upload_excel/` — batch create vouchers from `.xlsx` |
| Admin Inline | TabularInline for JournalEntry under JournalVoucher |

### Sprint 3 (planned)

Opening Balance, Ledger Engine / GL Entries, Posting Engine

## Quick start

```bash
# Clone and enter the project
git clone <repo-url> journal_voucher_system
cd journal_voucher_system

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r apps/requirements.txt

# Run migrations
python manage.py migrate

# Create superuser (optional, for admin access)
python manage.py createsuperuser

# Start dev server
python manage.py runserver
```

Open http://localhost:8000/admin/ for the admin panel or http://localhost:8000/api/ for the browsable API.

## Project structure

```
journal_voucher_system/
├── manage.py                        # Django CLI entry point
├── Procfile                         # Production process definition
├── build.sh                         # Build script (collectstatic + migrate + gunicorn)
├── gunicorn.conf.py                 # Gunicorn configuration
├── .env.example                     # Environment variable reference
├── journal_voucher_system/
│   ├── settings.py                  # Dev settings (shared base)
│   ├── settings_production.py       # Production settings (imports base)
│   ├── urls.py                      # Root URL configuration
│   ├── wsgi.py                      # WSGI entry point for Gunicorn
│   └── asgi.py                      # ASGI entry point
├── apps/
│   ├── requirements.txt             # Python dependencies
│   ├── common/                      # Shared: BaseModel, constants, mixins, permissions
│   ├── master_data/                 # Company, Branch, Currency CRUD
│   ├── accounting_period/           # Period lifecycle and validation
│   ├── chart_of_account/            # Hierarchical account structure
│   ├── vendor/                      # Vendor and supplier management
│   ├── journal_voucher/             # Core voucher engine (Sprint 2)
│   ├── docs/                        # Additional documentation
│   ├── logs/                        # Application logs
│   ├── media/                       # User-uploaded files
│   ├── static/                      # Static assets
│   └── templates/                   # Django templates
├── staticfiles/                     # Collected static files (production)
└── db.sqlite3                       # SQLite database (dev only)
```

## API reference

All endpoints require authentication. Use `?search=`, `?ordering=`, and `?page=` for filtering.

### Master Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET, POST | `/api/master-data/companies/` | List / Create companies |
| GET, PUT, PATCH, DELETE | `/api/master-data/companies/{id}/` | Company detail |
| GET, POST | `/api/master-data/branches/` | List / Create branches |
| GET, PUT, PATCH, DELETE | `/api/master-data/branches/{id}/` | Branch detail |
| GET, POST | `/api/master-data/currencies/` | List / Create currencies |
| GET, PUT, PATCH, DELETE | `/api/master-data/currencies/{id}/` | Currency detail |

### Accounting Periods

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET, POST | `/api/accounting-periods/` | List / Create periods |
| GET, PUT, PATCH, DELETE | `/api/accounting-periods/{id}/` | Period detail |

### Chart of Accounts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET, POST | `/api/chart-of-accounts/` | List / Create accounts |
| GET, PUT, PATCH, DELETE | `/api/chart-of-accounts/{id}/` | Account detail |

### Vendors

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET, POST | `/api/vendors/` | List / Create vendors |
| GET, PUT, PATCH, DELETE | `/api/vendors/{id}/` | Vendor detail |

### Journal Vouchers

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/journal-vouchers/` | List vouchers (paginated) |
| POST | `/api/journal-vouchers/` | Create voucher with nested entries |
| GET | `/api/journal-vouchers/{id}/` | Retrieve voucher with entries |
| PUT, PATCH | `/api/journal-vouchers/{id}/` | Update voucher and replace entries |
| DELETE | `/api/journal-vouchers/{id}/` | Delete voucher (entries cascade) |
| POST | `/api/journal-vouchers/{id}/validate/` | Validate DRAFT voucher |
| POST | `/api/journal-vouchers/{id}/void/` | Void a voucher |
| POST | `/api/journal-vouchers/upload_excel/` | Batch create from `.xlsx` |

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET, POST | `/api/auth/` | DRF browsable API login |

### Example: Create a journal voucher

```json
POST /api/journal-vouchers/
{
  "accounting_period": 1,
  "transaction_date": "2026-01-15",
  "description": "January revenue entry",
  "vendor": 1,
  "entries": [
    {"account": 1, "debit": 1000.00, "credit": 0, "description": "Cash debit"},
    {"account": 2, "debit": 0, "credit": 1000.00, "description": "Revenue credit"}
  ]
}
```

### Example: Validate a voucher

```http
POST /api/journal-vouchers/1/validate/
```

### Example: Upload Excel

```http
POST /api/journal-vouchers/upload_excel/
Content-Type: multipart/form-data

file: @vouchers.xlsx
```

**Expected Excel columns:**

| Column | Header | Required |
|--------|--------|----------|
| A | Voucher Description | Yes |
| B | Account Code | Yes |
| C | Debit | Conditional |
| D | Credit | Conditional |
| E | Line Description | No |
| F | Transaction Date | No (defaults to today) |
| G | Accounting Period Code | Yes |

Rows with the same description are grouped into one balanced voucher.

## Production deployment

### Environment variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | Yes | — | Django secret key |
| `DJANGO_ALLOWED_HOSTS` | Yes | — | Comma-separated hostnames |
| `DJANGO_DEBUG` | No | `False` | Debug mode (set to `True` only for troubleshooting) |
| `DB_NAME` | Yes | — | PostgreSQL database name |
| `DB_USER` | Yes | — | Database user |
| `DB_PASSWORD` | Yes | — | Database password |
| `DB_HOST` | No | `localhost` | Database host |
| `DB_PORT` | No | `5432` | Database port |
| `DB_CONN_MAX_AGE` | No | `600` | Persistent connection lifetime (seconds) |
| `CORS_ALLOWED_ORIGINS` | No | — | Comma-separated allowed CORS origins |
| `DJANGO_SECURE_SSL_REDIRECT` | No | `True` | Redirect HTTP to HTTPS |
| `DJANGO_HSTS_SECONDS` | No | `31536000` | HSTS max-age |
| `GUNICORN_WORKERS` | No | `4` | Number of worker processes |
| `GUNICORN_THREADS` | No | `2` | Threads per worker |
| `GUNICORN_TIMEOUT` | No | `120` | Worker timeout (seconds) |

### Start production server

```bash
# Switch to production settings
export DJANGO_SETTINGS_MODULE=journal_voucher_system.settings_production

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate

# Start Gunicorn (uses gunicorn.conf.py)
gunicorn
```

Or with explicit arguments:

```bash
gunicorn journal_voucher_system.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --threads 2 \
  --worker-class gthread \
  --timeout 120
```

### Architecture notes

- **Gunicorn** is configured in `gunicorn.conf.py` (all values overridable via environment variables).
- **WhiteNoise** serves static files — place Gunicorn behind Nginx or Caddy for TLS termination and caching.
- **Logging** writes to stdout (captured by the platform) and to `apps/logs/django.log`.
- **Health check** — the app listens on the configured bind address (default `0.0.0.0:8000`).

## Development commands

| Command | Purpose |
|---------|---------|
| `python manage.py makemigrations` | Create new migrations |
| `python manage.py migrate` | Apply migrations |
| `python manage.py createsuperuser` | Create admin user |
| `python manage.py test` | Run all tests (25 passing) |
| `python manage.py runserver` | Start dev server |

## Testing

```bash
python manage.py test
```

| App | Tests | Coverage |
|-----|-------|----------|
| common | 2 | BaseModel, constants choices |
| master_data | 3 | Company, Branch, Currency |
| accounting_period | 2 | Creation, start ≤ end validation |
| chart_of_account | 2 | Creation, parent-child hierarchy |
| vendor | 2 | Creation, default credit limit |
| journal_voucher | 14 | Voucher numbering, date validation, entry constraints, validators, dict support |

## ERD

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│ AccountingPeriod│     │  ChartOfAccount  │     │      Vendor         │
├─────────────────┤     ├──────────────────┤     ├─────────────────────┤
│ id              │     │ id               │     │ id                  │
│ code            │     │ code             │     │ code                │
│ name            │     │ name             │     │ name                │
│ start_date      │     │ account_type     │     │ address             │
│ end_date        │     │ parent (self)    │     │ phone               │
│ status          │     │ normal_balance   │     │ email               │
└─────────────────┘     └──────────────────┘     └─────────────────────┘
         │                        │                         │
         │                        │                         │
         └────────────────────────┼─────────────────────────┘
                                  │
                     ┌────────────┴────────────┐
                     │   JournalVoucher        │
                     ├─────────────────────────┤
                     │ id                      │
                     │ voucher_number          │
                     │ accounting_period (FK)  │◄──┐
                     │ transaction_date        │   │
                     │ description             │   │
                     │ bl_number               │   │
                     │ invoice_number          │   │
                     │ vendor (FK)             │───┘
                     │ status                  │
                     │ total_debit             │
                     │ total_credit            │
                     └─────────────────────────┘
                                  │
                                  │
                     ┌────────────┴────────────┐
                     │    JournalEntry         │
                     ├─────────────────────────┤
                     │ id                      │
                     │ voucher (FK)            │◄──┐
                     │ account (FK)            │───┼──┐
                     │ debit                   │   │  │
                     │ credit                  │   │  │
                     │ description             │   │  │
                     │ line_order              │   │  │
                     └─────────────────────────┘   │  │
                                                   │  │
┌──────────────────┐                               │  │
│      User        │                               │  │
├──────────────────┤                               │  │
│ id               │                               │  │
│ username         │                               │  │
│ email            │                               │  │
│ password         │                               │  │
└──────────────────┘                               │  │
         │                                         │  │
         └─────────────────────────────────────────┘  │
                                                      │
                                    ┌─────────────────┘
                                    │
                           ┌────────┴────────┐
                           │   GL Entries    │
                           ├─────────────────┤
                           │ id              │
                           │ voucher (FK)    │
                           │ account (FK)    │
                           │ debit           │
                           │ credit          │
                           │ period (FK)     │
                           └─────────────────┘
```
