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

### Sprint 2 — Journal Voucher Engine ✅
- Journal Voucher / Journal Entry models with auto-generated voucher numbers
- Writable nested serializer for inline entry management
- Business validation: debit = credit, period must be open, account must be active
- Validate / Void workflow actions
- Excel upload for batch voucher creation via openpyxl
- Django admin with TabularInline for JournalEntry

### Sprint 3 ⏳
- Opening Balance
- Ledger Engine / GL Entries
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
├── common/               # Shared utilities, base models, constants
│   ├── models.py         # Abstract BaseModel (created_at, updated_at)
│   ├── constants.py      # Status, AccountType, NormalBalance, VoucherStatus, etc.
│   ├── mixins.py         # AuditLogMixin, SoftDeleteMixin
│   ├── permissions.py    # IsActive, ReadOnly permissions
│   ├── serializers.py    # BaseModelSerializer with formatted timestamps
│   ├── views.py          # BaseViewSet (ModelViewSet + filtering/search/pagination)
│   ├── admin.py          # BaseModelAdmin with readonly timestamps
│   └── urls.py           # Auth endpoints
├── master_data/          # Master reference data
│   ├── models.py         # Company, Branch, Currency
│   ├── serializers.py    # BaseModelSerializer subclasses
│   ├── views.py          # BaseViewSet subclasses with search_fields
│   ├── urls.py           # REST router: companies/, branches/, currencies/
│   └── admin.py          # Jazzmin admin with list_display/filter/search
├── accounting_period/    # Accounting period lifecycle
│   ├── models.py         # AccountingPeriod with date validation in clean()
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
├── chart_of_account/     # Chart of accounts hierarchy
│   ├── models.py         # ChartOfAccount (self-referential parent FK)
│   ├── serializers.py    # Includes parent_code, parent_name, children_count
│   ├── views.py
│   ├── urls.py
│   └── admin.py
├── vendor/               # Vendor/supplier management
│   ├── models.py         # Vendor with tax_id, bank_account, credit_limit
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
├── journal_voucher/      # Core journal engine (Sprint 2)
│   ├── models.py         # JournalVoucher, JournalEntry
│   ├── validators.py     # debit=credit, period open, account active
│   ├── serializers.py    # Nested writable entries, list serializer, Excel upload
│   ├── views.py          # CRUD + validate/void/upload_excel actions
│   ├── urls.py           # REST router at /api/journal-vouchers/
│   ├── admin.py          # Jazzmin admin with JournalEntryInline
│   ├── utils.py          # (reserved for future use)
│   └── tests.py          # 14 tests covering models, validators, edge cases
├── docs/
├── logs/
├── media/
├── static/
├── templates/
├── requirements.txt      # django, djangorestframework, jazzmin, openpyxl, etc.
└── .env
```

---

## Module Documentation

### 1. `common` — Shared Infrastructure

**Purpose:** Provides reusable base classes and constants used by all other apps.

#### `common/models.py`
- **`BaseModel`** — Abstract model adding `created_at` and `updated_at` auto-fields. Every model in the project inherits from this.

#### `common/constants.py`
- **`Status`** — `ACTIVE` / `INACTIVE` (for soft-delete and active flags)
- **`PeriodStatus`** — `OPEN` / `CLOSED` (for accounting periods)
- **`AccountType`** — `ASSET`, `LIABILITY`, `EQUITY`, `REVENUE`, `EXPENSE`
- **`NormalBalance`** — `DEBIT` / `CREDIT` (determines default balance side)
- **`VoucherStatus`** — `DRAFT`, `VALIDATED`, `POSTED`, `VOID` (voucher lifecycle)

#### `common/serializers.py`
- **`BaseModelSerializer`** — Extends `ModelSerializer`; exposes `created_at` and `updated_at` as read-only, formatted datetime fields.

#### `common/views.py`
- **`BaseViewSet`** — Extends `ModelViewSet`; enforces `IsAuthenticated`, includes `DjangoFilterBackend`, `SearchFilter`, `OrderingFilter`, and default ordering by `-created_at`.

#### `common/admin.py`
- **`BaseModelAdmin`** — Adds `created_at`/`updated_at` as readonly fields, sets `list_per_page = 25`.

---

### 2. `master_data` — Master Reference Data

**Purpose:** Stores companies, branches, and currencies used throughout the system.

#### Models (`master_data/models.py`)
- **`Company`** — `code`, `name`, `address`, `phone`, `email`, `is_active`
- **`Branch`** — FK to `Company`, `code`, `name`, `address`, `is_active`; unique together constraint on `(company, code)`
- **`Currency`** — `code`, `name`, `symbol`, `is_active`

All inherit from `BaseModel` and use `Status.ACTIVE` as default for `is_active`.

#### Serializers
- `CompanySerializer`, `BranchSerializer`, `CurrencySerializer` — standard `BaseModelSerializer` subclasses with `fields = '__all__'`.
- `BranchSerializer` adds `company_code` and `company_name` read-only fields via `source`.

#### Views
- `CompanyViewSet`, `BranchViewSet`, `CurrencyViewSet` — standard `BaseViewSet` subclasses with `search_fields` on code/name.

#### API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/master-data/companies/` | List / Create companies |
| GET/PUT/PATCH/DELETE | `/api/master-data/companies/{id}/` | Company detail |
| GET/POST | `/api/master-data/branches/` | List / Create branches |
| GET/PUT/PATCH/DELETE | `/api/master-data/branches/{id}/` | Branch detail |
| GET/POST | `/api/master-data/currencies/` | List / Create currencies |
| GET/PUT/PATCH/DELETE | `/api/master-data/currencies/{id}/` | Currency detail |

---

### 3. `accounting_period` — Period Lifecycle

**Purpose:** Defines accounting periods with date boundaries and open/close status.

#### Model (`accounting_period/models.py`)
- **`AccountingPeriod`** inherits `BaseModel`
- Fields: `code` (unique), `name`, `start_date`, `end_date`, `status` (OPEN/CLOSED), `notes`
- Validates `start_date <= end_date` in `clean()`, called automatically by `save()`
- Ordered by `-start_date`

#### API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/accounting-periods/` | List / Create periods |
| GET/PUT/PATCH/DELETE | `/api/accounting-periods/{id}/` | Period detail |

---

### 4. `chart_of_account` — Chart of Accounts

**Purpose:** Hierarchical account structure supporting parent-child relationships.

#### Model (`chart_of_account/models.py`)
- **`ChartOfAccount`** inherits `BaseModel`
- Fields: `code` (unique), `name`, `account_type` (ASSET/LIABILITY/EQUITY/REVENUE/EXPENSE), `parent` (self-referential FK, nullable), `normal_balance` (DEBIT/CREDIT), `is_active`, `description`
- Ordered by `code`

#### Serializer
- `ChartOfAccountSerializer` — adds `parent_code`, `parent_name` (via `source`), and `children_count` (via `SerializerMethodField`)

#### API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/chart-of-accounts/` | List / Create accounts |
| GET/PUT/PATCH/DELETE | `/api/chart-of-accounts/{id}/` | Account detail |

---

### 5. `vendor` — Vendor Management

**Purpose:** Stores vendor/supplier information including financial details.

#### Model (`vendor/models.py`)
- **`Vendor`** inherits `BaseModel`
- Fields: `code` (unique), `name`, `address`, `phone`, `email`, `tax_id`, `bank_account`, `credit_limit`, `payment_terms`, `is_active`
- Ordered by `code`

#### API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/api/vendors/` | List / Create vendors |
| GET/PUT/PATCH/DELETE | `/api/vendors/{id}/` | Vendor detail |

---

### 6. `journal_voucher` — Journal Voucher Engine (Sprint 2)

**Purpose:** Core journal entry system — create, validate, and manage journal vouchers with inline accounting entries.

---

#### Models (`journal_voucher/models.py`)

##### `JournalVoucher`
| Field | Type | Description |
|-------|------|-------------|
| `voucher_number` | CharField (unique) | Auto-generated as `JV-YYYYMMDD-NNNN` |
| `accounting_period` | FK → `AccountingPeriod` | Period the voucher belongs to (PROTECT) |
| `transaction_date` | DateField | Must fall within the period's start/end dates |
| `description` | TextField | Voucher description |
| `bl_number` | CharField (blank) | Bill of lading number |
| `invoice_number` | CharField (blank) | Invoice reference |
| `vendor` | FK → `Vendor` (nullable, PROTECT) | Optional vendor association |
| `status` | CharField (choices) | `DRAFT` → `VALIDATED` → `POSTED` → `VOID` |
| `total_debit` | DecimalField | Auto-computed sum of entry debits |
| `total_credit` | DecimalField | Auto-computed sum of entry credits |
| `created_by` | FK → `auth.User` (nullable) | User who created the voucher |

**Key behavior:**
- `voucher_number` is auto-generated on first save if not provided. Format: `JV-{YYYYMMDD}-{0001}` (sequential per day).
- `clean()` validates that `transaction_date` falls within the linked accounting period's range.
- `save()` calls `clean()` before persisting.

##### `JournalEntry`
| Field | Type | Description |
|-------|------|-------------|
| `voucher` | FK → `JournalVoucher` (CASCADE) | Parent voucher |
| `account` | FK → `ChartOfAccount` (PROTECT) | Account being debited or credited |
| `debit` | DecimalField | Debit amount (0 if credit entry) |
| `credit` | DecimalField | Credit amount (0 if debit entry) |
| `description` | CharField (blank) | Line-item description |
| `line_order` | PositiveIntegerField | Display order within the voucher |

**Constraints (enforced in `clean()` / `save()`):**
- An entry cannot have both `debit > 0` and `credit > 0`.
- An entry must have either `debit > 0` or `credit > 0` (not both zero).

---

#### Validators (`journal_voucher/validators.py`)

Three standalone validation functions, each raising `ValidationError` on failure:

| Function | Input | Rule |
|----------|-------|------|
| `validate_debit_credit_balance(entries)` | List of dicts or model objects | Sum of debits must equal sum of credits |
| `validate_period_open(period)` | `AccountingPeriod` instance | `period.status` must be `OPEN` |
| `validate_account_active(account)` | `ChartOfAccount` instance | `account.is_active` must be `ACTIVE` |

`validate_debit_credit_balance` accepts both dicts (with `debit`/`credit` keys) and objects (with `.debit`/`.credit` attributes), making it usable both in serializer validation and model-level checks.

---

#### Serializers (`journal_voucher/serializers.py`)

##### `JournalEntrySerializer`
- Full serializer for journal entries
- Includes read-only `account_code` and `account_name` via `source`
- `voucher` is read-only (set automatically by parent)

##### `JournalEntryCreateSerializer`
- Lightweight serializer for creating entries as part of a nested write
- Fields: `account`, `debit`, `credit`, `description`, `line_order`

##### `JournalVoucherListSerializer`
- Used for `list` action (lighter payload)
- Adds read-only `accounting_period_name`, `vendor_name`, `created_by_username`
- Read-only fields: `voucher_number`, `total_debit`, `total_credit`

##### `JournalVoucherSerializer`
- Used for `create`/`retrieve`/`update` actions
- Contains a writable nested `entries` field (list of `JournalEntryCreateSerializer`)
- **Validation:**
  - `validate_entries()` — ensures at least one entry, no entry has both debit/credit, each entry has at least one amount
- **`create()`:**
  1. Pops `entries` from validated data
  2. Sets `created_by` from request user
  3. Creates the `JournalVoucher`
  4. Creates each `JournalEntry` linked to the voucher
  5. Recalculates and saves `total_debit` / `total_credit`
- **`update()`:**
  1. Updates voucher fields
  2. If `entries` included: deletes all existing entries, recreates from payload
  3. Recalculates totals

##### `ExcelUploadSerializer`
- Simple serializer accepting a single `file` field (the Excel file to upload)

---

#### Views (`journal_voucher/views.py`)

##### `JournalVoucherViewSet`
Extends `BaseViewSet`. Uses `JournalVoucherListSerializer` for `list` and `JournalVoucherSerializer` for all other actions.

**Standard CRUD actions:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/journal-vouchers/` | List (paginated, searchable) |
| POST | `/api/journal-vouchers/` | Create with nested entries |
| GET | `/api/journal-vouchers/{id}/` | Retrieve with all entries |
| PUT/PATCH | `/api/journal-vouchers/{id}/` | Update voucher + replace entries |
| DELETE | `/api/journal-vouchers/{id}/` | Delete voucher (and entries via CASCADE) |

**Custom actions:**

###### `POST /api/journal-vouchers/{id}/validate/`
1. Checks voucher status is `DRAFT` (rejects if already validated/posted/void)
2. Checks voucher has at least one entry
3. Runs all three validators:
   - `validate_period_open` — period must be OPEN
   - `validate_debit_credit_balance` — total debit = total credit
   - `validate_account_active` — every entry's account must be ACTIVE
4. On success: sets status to `VALIDATED` and returns updated voucher

###### `POST /api/journal-vouchers/{id}/void/`
1. Checks voucher is not already void
2. Sets status to `VOID`

---

#### Excel Upload (`POST /api/journal-vouchers/upload_excel/`)

Accepts a multipart POST with an `.xlsx` file. Uses `openpyxl` for parsing.

**Expected Excel format:**

| Column | Header | Required | Description |
|--------|--------|----------|-------------|
| A | Voucher Description | Yes | Groups rows into one voucher |
| B | Account Code | Yes | Must match an existing `ChartOfAccount.code` |
| C | Debit | Conditional | Debit amount (0 if credit entry) |
| D | Credit | Conditional | Credit amount (0 if debit entry) |
| E | Line Description | No | Line-item description |
| F | Transaction Date | No | Date (defaults to today if missing) |
| G | Accounting Period Code | Yes | Must match an existing `AccountingPeriod.code` |

**Processing logic:**
1. Rows are read starting from row 2 (row 1 is header, currently ignored)
2. Rows are grouped by column A (Voucher Description)
3. Each group creates one `JournalVoucher` with multiple `JournalEntry` lines
4. Within each group: debit = credit is enforced
5. Each entry's account is validated to exist
6. All processing happens inside a single `transaction.atomic()` block

**Response:**
```json
{
  "created": 3,
  "errors": [
    "Voucher X: error description"
  ]
}
```

---

#### Admin (`journal_voucher/admin.py`)

##### `JournalVoucherAdmin`
- `list_display`: voucher_number, transaction_date, accounting_period, vendor, status, total_debit, total_credit, created_at
- `list_filter`: status, accounting_period
- `search_fields`: voucher_number, description, bl_number, invoice_number
- `readonly_fields`: voucher_number, total_debit, total_credit, created_by, timestamps
- `inlines`: `[JournalEntryInline]`
- `date_hierarchy`: transaction_date

##### `JournalEntryInline`
- Tabular inline with fields: account, debit, credit, description, line_order
- Adds 1 extra empty row by default

##### `JournalEntryAdmin`
- Standalone admin for browsing entries directly
- `list_display`: voucher, account, debit, credit, description, line_order
- `list_filter`: account
- `search_fields`: voucher__voucher_number, account__code, account__name, description

---

## API Endpoints Summary

| Prefix | Endpoints |
|--------|-----------|
| `/api/master-data/` | `companies/`, `branches/`, `currencies/` |
| `/api/accounting-periods/` | (root) |
| `/api/chart-of-accounts/` | (root) |
| `/api/vendors/` | (root) |
| `/api/journal-vouchers/` | (root), `{id}/validate/`, `{id}/void/`, `upload_excel/` |
| `/api/auth/` | DRF browsable API login |

All endpoints support:
- **Search** via `?search=` across configurable fields
- **Ordering** via `?ordering=` on any field
- **Pagination** (25 per page) via `?page=`

## API Usage Examples

### Create a Journal Voucher

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

### Validate a Voucher

```http
POST /api/journal-vouchers/1/validate/
```

### Void a Voucher

```http
POST /api/journal-vouchers/1/void/
```

### Upload Excel

```http
POST /api/journal-vouchers/upload_excel/
Content-Type: multipart/form-data

file: @vouchers.xlsx
```

## Development Commands

```bash
pip install -r apps/requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py test          # Run all tests (currently 25 passing)
python manage.py runserver
```

## Test Coverage

| App | Tests | Focus |
|-----|-------|-------|
| `common` | 2 | BaseModel abstract, constants choices |
| `master_data` | 3 | Company, Branch, Currency creation |
| `accounting_period` | 2 | Creation, start <= end validation |
| `chart_of_account` | 2 | Creation, parent-child hierarchy |
| `vendor` | 2 | Creation, default credit_limit |
| `journal_voucher` | 14 | Voucher number generation, date validation, entry constraints, validators (debit=credit, period open, account active), dict support |

Run all tests with:
```bash
python manage.py test
```
