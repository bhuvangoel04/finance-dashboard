# Finance Dashboard

A role-based financial records management backend built with Django and Django REST Framework.

---

## Project Structure

```
finance_dashboard/
├── finance_dashboard/       # Project config
│   ├── settings.py
│   ├── urls.py
│   └── exceptions.py        # Uniform error envelope
├── users/                   # User & role management
│   ├── models.py            # Custom User with Role choices
│   ├── permissions.py       # IsAdmin, IsAnalystOrAbove, IsAdminOrReadOnly
│   ├── serializers.py
│   ├── views.py
│   └── management/
│       └── commands/
│           └── seed_data.py
├── records/                 # Financial records CRUD
│   ├── models.py            # FinancialRecord
│   ├── filters.py           # Date range, category, type filters
│   ├── serializers.py
│   └── views.py
├── dashboard/               # Analytics & summary APIs
│   ├── services.py          # All aggregation logic (DashboardService)
│   └── views.py
├── tests.py                 # Full test suite
├── manage.py
└── requirements.txt
```

---

## Quick Start

```bash
# 1. Clone and enter the project
cd finance_dashboard

# 2. Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Seed sample data (creates 3 users + 50 financial records)
python manage.py seed_data

# 6. (Optional) Create a Django superuser for /admin panel
python manage.py createsuperuser

# 7. Start the development server
python manage.py runserver
```

### Seeded credentials

| Email                    | Password    | Role    |
|--------------------------|-------------|---------|
| admin@example.com        | password123 | Admin   |
| analyst@example.com      | password123 | Analyst |
| viewer@example.com       | password123 | Viewer  |

---

## Running Tests

```bash
python manage.py test
```

Covers: authentication, role enforcement, record CRUD, validation, dashboard analytics.

---

## Role Permissions Matrix

| Action                          | Viewer | Analyst | Admin |
|---------------------------------|--------|---------|-------|
| Login                           | Yes    | Yes     | Yes   |
| View own profile (`/me/`)       | Yes    | Yes     | Yes   |
| List financial records          | Yes    | Yes     | Yes   |
| View a record's detail          | Yes    | Yes     | Yes   |
| Create a record                 | No     | No      | Yes   |
| Update a record                 | No     | No      | Yes   |
| Delete a record                 | No     | No      | Yes   |
| Bulk delete records             | No     | No      | Yes   |
| Dashboard overview              | No     | Yes     | Yes   |
| Category breakdown              | No     | Yes     | Yes   |
| Monthly / weekly trends         | No     | Yes     | Yes   |
| Recent activity                 | No     | Yes     | Yes   |
| Top categories                  | No     | Yes     | Yes   |
| List / create users             | No     | No      | Yes   |
| Update user role / status       | No     | No      | Yes   |
| Deactivate / activate users     | No     | No      | Yes   |
| Reset another user's password   | No     | No      | Yes   |

---

## Design Decisions

**Custom User model** — Extending `AbstractBaseUser` allows email-based auth from day one without migrations headaches later.

**Role on the User model (not a separate table)** — For three fixed roles, a `TextChoices` field is simpler and faster than a many-to-many Role table. Upgrade to a separate model if roles become dynamic.

**Permission classes over per-view if/else** — `IsAdmin`, `IsAnalystOrAbove`, `IsAdminOrReadOnly` are composable and reusable across any view without repeating logic.

**DashboardService as a standalone class** — Keeps all aggregation SQL in one testable place, separate from HTTP concerns. The service can be called by Celery tasks, management commands, or websocket handlers without touching views.

**One DB query per overview** — `get_overview()` uses `.aggregate()` with conditional `Sum` and `Count` so income + expense totals + counts are fetched in a single SQL statement.

**Consistent response envelope** — Every endpoint returns `{ success, data }` or `{ success, error }`. Frontends never need to guess response shape.