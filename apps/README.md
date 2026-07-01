#sprint module 
✅ Sprint 1
--------------------------------
✔ Jazzmin
✔ Master Data
✔ Accounting Period
✔ Chart of Account
✔ Vendor

✅ Sprint 2
--------------------------------
✔ Journal Voucher
✔ Journal Entry Inline
✔ Upload Excel
✔ Validation

✅ Sprint 3
--------------------------------
✔ Opening Balance
✔ Ledger Engine
✔ Posting Engine

✅ Sprint 4
--------------------------------
✔ Trial Balance
✔ Balance Sheet
✔ Income Statement
✔ Cash Flow

✅ Sprint 5
--------------------------------
✔ Dashboard
✔ Export Excel
✔ Export PDF
✔ Audit Log
✔ Closing Period
````
#Project Configuration
```
apps
├─ .env
├─ accounting_period
│  ├─ admin.py
│  ├─ apps.py
│  ├─ migrations
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ serializers.py
│  ├─ tests.py
│  ├─ urls.py
│  ├─ views.py
│  └─ __init__.py
├─ chart_of_account
│  ├─ admin.py
│  ├─ apps.py
│  ├─ migrations
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ serializers.py
│  ├─ tests.py
│  ├─ urls.py
│  ├─ views.py
│  └─ __init__.py
├─ common
│  ├─ admin.py
│  ├─ apps.py
│  ├─ constants.py
│  ├─ migrations
│  │  └─ __init__.py
│  ├─ mixins.py
│  ├─ models.py
│  ├─ permissions.py
│  ├─ serializers.py
│  ├─ tests.py
│  ├─ views.py
│  └─ __init__.py
├─ docs
├─ journal_voucher
│  ├─ admin.py
│  ├─ apps.py
│  ├─ migrations
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ serializers.py
│  ├─ tests.py
│  ├─ urls.py
│  ├─ utils.py
│  ├─ validators.py
│  ├─ views.py
│  └─ __init__.py
├─ logs
├─ master_data
│  ├─ admin.py
│  ├─ apps.py
│  ├─ migrations
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ serializers.py
│  ├─ tests.py
│  ├─ urls.py
│  ├─ views.py
│  └─ __init__.py
├─ media
├─ requirements.txt
├─ static
├─ templates
├─ vendor
│  ├─ admin.py
│  ├─ apps.py
│  ├─ migrations
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ serializers.py
│  ├─ tests.py
│  ├─ urls.py
│  ├─ views.py
│  └─ __init__.py
└─ __init__.py

```
Applications (apps/)
    common/ - BASE/UTILITY APP
    Purpose: Code shared by all applications

    Contents:
    models.py: Abstract BaseModel (created_at, updated_at, created_by)
    mixins.py: Mixin classes for reusable functionality
    constants.py: Global constants (status codes, choices)
    permissions.py: Custom permission classes
    serializers.py: Base serializers

master_data/ - MASTER DATA APP
    Purpose: Stores master data used by the system

    Functions:
    Stores reference data such as companies, branches, and currencies

    Data that rarely changes and is used by many modules

    To be populated later: Company, Branch, Currency, Unit, etc.

accounting_period/ - ACCOUNTING PERIOD
    Purpose: Manages accounting periods (months/years)

    Functions:
    Determines opening and closing periods
    Validates transaction dates
    Restricts postings in closed periods
    Model: AccountingPeriod (code, name, start_date, end_date, status)

chart_of_account/ - CHARTS OF ACCOUNTS 
    Purpose: Manage the Chart of Accounts (COA)

    Functions:
    Store a list of accounts with codes, names, and types
    Hierarchical structure (parent-child)
    Define normal balances (Debit/Credit)
    Model: ChartOfAccount (code, name, account_type, parent, normal_balance)

vendor/ - VENDOR MANAGEMENT
Purpose: Manage vendor/supplier data

Functions:
Store vendor information (name, address, contact)
Tax and bank account data
Credit limits and payment terms
Model: Vendor (code, name, address, phone, email, tax_id, bank_account)

journal_voucher/ - CORE BUSINESS 
Purpose: Main module for journal transactions
Functions:
Model:
    JournalVoucher: Voucher header (number, date, description, total)
    JournalEntry: Entry details (account, debit, credit)
Validation:
    Debit = Credit
    Accounting period is open
    Account is active
    Upload Excel: Import data from Excel
    Export: Export to Excel/PDF
    Status: DRAFT → VALIDATED → POSTED → VOID

Contents:
    API documentation
    User manual
    Database schema
    Deployment guide
logs/ - LOG FILES
    Purpose: Stores application log files
    Functions:
    Debugging
    Audit trail
    Error tracking
    Examples: app.log, error.log, access.log


```
User (Browser/API) 
    ↓
urls.py (Routing) 
    ↓
views.py (Logic) 
    ↓
serializers.py (Data Transformation) 
    ↓
models.py (Business Logic) 
    ↓
Database (PostgreSQL)