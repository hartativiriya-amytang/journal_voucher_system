# Journal Voucher System — Apps

## Sprint Status

### Sprint 1 — Base Setup & Master Data ✅
- Jazzmin admin theming — configured
- Master Data — Company, Branch, Currency models + API
- Accounting Period — period lifecycle with validation
- Chart of Account — hierarchical account structure + API
- Vendor — vendor/supplier management + API
- REST API with DRF — full CRUD endpoints for all Sprint 1 models
- Django admin integration with Jazzmin UI

### Sprint 2 ⏳
- Journal Voucher
- Journal Entry Inline
- Upload Excel
- Validation

### Sprint 3 ⏳
- Opening Balance
- Ledger Engine
- Posting Engine

### Sprint 4 ⏳
- Trial Balance
- Balance Sheet
- Income Statement
- Cash Flow

### Sprint 5 ⏳
- Dashboard
- Export Excel
- Export PDF
- Audit Log
- Closing Period

## Project Structure

```
apps/
├── common/              # Shared utilities, base models, constants
│   ├── models.py        # Abstract BaseModel (created_at, updated_at)
│   ├── constants.py     # Status, AccountType, NormalBalance, etc.
│   ├── mixins.py        # AuditLogMixin, SoftDeleteMixin
│   ├── permissions.py   # IsActive, ReadOnly permissions
│   ├── serializers.py   # BaseModelSerializer
│   └── views.py         # BaseViewSet with filtering/search/pagination
├── master_data/         # Master reference data
│   ├── models.py        # Company, Branch, Currency
│   ├── serializers.py
│   ├── views.py         # CRUD ViewSets
│   ├── urls.py          # REST router
│   └── admin.py         # Jazzmin admin registration
├── accounting_period/   # Accounting period lifecycle
│   ├── models.py        # AccountingPeriod with date validation
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
├── chart_of_account/    # Chart of accounts hierarchy
│   ├── models.py        # ChartOfAccount (self-referential parent)
│   ├── serializers.py   # Includes parent_code, children_count
│   ├── views.py
│   ├── urls.py
│   └── admin.py
├── vendor/              # Vendor/supplier management
│   ├── models.py        # Vendor with tax, bank, credit fields
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
├── journal_voucher/     # Core journal engine (Sprint 2+)
├── docs/                # Documentation
├── logs/                # Application logs
├── media/               # Uploaded media files
├── static/              # Static assets
├── templates/           # Django templates
├── requirements.txt
└── .env
```

## API Endpoints

| Prefix | Endpoints |
|--------|-----------|
| `/api/master-data/` | `companies/`, `branches/`, `currencies/` |
| `/api/accounting-periods/` | `accountingperiods/` |
| `/api/chart-of-accounts/` | `chartofaccounts/` |
| `/api/vendors/` | `vendors/` |
| `/api/auth/` | DRF browsable API login |

All endpoints support:
- **Search** via `?search=` across configurable fields
- **Ordering** via `?ordering=` on any field
- **Pagination** (25 per page) via `?page=`

## Development Commands

```bash
pip install -r apps/requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```
