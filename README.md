# Journal Voucher System (under construction 🚧)

This repository contains a Django-based journal voucher and accounting management project. The application is organized into reusable Django apps under the apps directory, with the main project configuration in the journal_voucher_system package.

## Project purpose

The system is intended to support:
- journal voucher creation and validation
- accounting period management
- chart of accounts management
- vendor management
- reporting and future posting workflows

## Repository structure

```text
journal_voucher_system/
├── manage.py
├── README.md
├── journal_voucher_system/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
└── apps/
    ├── __init__.py
    ├── README.md
    ├── requirements.txt
    ├── accounting_period/
    ├── chart_of_account/
    ├── common/
    ├── journal_voucher/
    ├── master_data/
    ├── vendor/
    ├── docs/
    ├── logs/
    ├── media/
    ├── static/
    └── templates/
```

## Main application modules
```text
- apps/common/: shared utilities, mixins, base models, constants, and permissions
- apps/master_data/: master reference data such as companies, branches, and currencies
- apps/accounting_period/: accounting period lifecycle and validation rules
- apps/chart_of_account/: chart of accounts structure and account types
- apps/vendor/: vendor and supplier data management
- apps/journal_voucher/: core voucher, entry, and validation logic

## Requirements
```text
- Python 3.10 or newer
- Django 5.2.x (as configured in the project)
- pip

## Local setup

From the project root, run:

```bash
python -m venv .venv

# Windows
```bash
.venv\Scripts\activate

# macOS / Linux
```bash
source .venv/bin/activate

pip install -r apps/requirements.txt
python manage.py migrate
python manage.py runserver
```

## Common development commands

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py test
python manage.py runserver
```

## Development notes

- Keep business logic inside the relevant app package under apps/.
- Add or update tests in each app's tests.py file when changing behavior.
- Use environment variables for secrets and configuration in a real deployment setup.

## Current status — Sprint 1 complete

Sprint 1 has been implemented:

| Feature | Status |
|---------|--------|
| Jazzmin admin UI | Configured with custom sidebar, icons, and theme |
| Master Data (Company, Branch, Currency) | Models, API, and admin done |
| Accounting Period | Model with date validation, API, and admin done |
| Chart of Account | Hierarchical model with parent-child, API, and admin done |
| Vendor | Full vendor management, API, and admin done |
| REST API with DRF | Complete CRUD endpoints with search, ordering, pagination |

See [apps/README.md](apps/README.md) for detailed API documentation.

## Next steps (Sprint 2)

- Journal Voucher creation and validation
- Journal Entry inline management
- Excel upload for batch voucher creation
- Business validation rules (debit = credit, period open, account active)

## ERD 
```text
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
