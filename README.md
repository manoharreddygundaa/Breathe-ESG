# Breathe ESG — Emissions Data Review Platform

Django REST + React prototype for ingesting, normalising, and analyst-reviewing emissions data from SAP, utility, and corporate travel sources.

---

## Project layout

```
breathe_esg/
├── backend/                  Django project
│   ├── manage.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── breathe/              Django project package
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   └── emissions/            Main app
│       ├── __init__.py
│       ├── models.py         Company, DataSource, EmissionRecord, AuditLog
│       ├── serializers.py
│       ├── views.py          Upload + review API endpoints
│       ├── parsers.py        SAP / utility / travel CSV parsers
│       ├── urls.py
│       ├── admin.py
│       ├── migrations/
│       │   ├── __init__.py
│       │   └── 0001_initial.py
│       └── management/commands/
│           └── seed_demo.py  Creates demo user + company
│
├── frontend/                 React + Vite + Tailwind
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── .env.example
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── index.css
│       ├── services/api.js
│       ├── hooks/useAuth.jsx
│       ├── pages/
│       │   ├── LoginPage.jsx
│       │   ├── DashboardPage.jsx
│       │   └── UploadPage.jsx
│       └── components/
│           ├── shared/Layout.jsx
│           └── dashboard/
│               ├── StatsBar.jsx
│               ├── FilterBar.jsx
│               ├── RecordTable.jsx
│               └── RecordModal.jsx
│
└── docs/
    ├── MODEL.md
    ├── DECISIONS.md
    ├── TRADEOFFS.md
    ├── SOURCES.md
    ├── sample_sap.csv
    ├── sample_utility.csv
    └── sample_travel.csv
```

---

## Prerequisites

- Python 3.11+
- PostgreSQL 14+ running locally
- Node.js 18+

---

## Backend setup

```bash
cd backend

# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create the database
createdb breathe_esg
#    If createdb isn't available:
#    psql -U postgres -c "CREATE DATABASE breathe_esg;"

# 4. Configure environment (optional — defaults work for local dev)
cp .env.example .env
#    Edit .env if your Postgres credentials differ from the defaults.
#    To load it: export $(cat .env | xargs)

# 5. Run migrations  (schema is already generated — no makemigrations needed)
python manage.py migrate

# 6. Create the demo analyst account
python manage.py seed_demo
#    Creates: username=analyst  password=password123  company=Acme Corporation

# 7. Start the development server
python manage.py runserver
#    API available at http://localhost:8000/api/
#    Admin panel at  http://localhost:8000/admin/
```

### Superuser (optional, for Django admin)

```bash
python manage.py createsuperuser
```

---

## Frontend setup

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. (Optional) configure the API base URL
cp .env.example .env.local
#    Default uses Vite's proxy → no CORS config needed in dev.
#    Only change VITE_API_URL if your backend runs on a different host/port.

# 3. Start the dev server
npm run dev
#    App at http://localhost:5173
```

Log in with **analyst / password123**.

---

## API reference

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/login/` | ✗ | Get JWT access + refresh tokens |
| POST | `/api/auth/refresh/` | ✗ | Refresh access token |
| GET | `/api/me/` | ✓ | Current user + company |
| GET | `/api/dashboard/stats/` | ✓ | Summary counts by status/scope |
| POST | `/api/upload/` | ✓ | Upload CSV (multipart: `file`, `source_type`) |
| GET | `/api/sources/` | ✓ | List upload batches |
| GET | `/api/records/` | ✓ | Records — filter by `status`, `scope`, `flag`, `data_source` |
| GET | `/api/records/<id>/` | ✓ | Record detail including `raw_data` |
| PATCH | `/api/records/<id>/` | ✓ | Edit pending record fields |
| POST | `/api/records/<id>/review/` | ✓ | Approve or reject (`action`, `analyst_note`) |
| GET | `/api/records/<id>/audit/` | ✓ | Audit log for one record |

### Example: login + upload

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"analyst","password":"password123"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access'])")

# Upload a SAP CSV
curl -X POST http://localhost:8000/api/upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@docs/sample_sap.csv" \
  -F "source_type=sap_fuel"
```

---

## Sample CSV files

Three sample files in `docs/` — all include intentionally bad rows to exercise the flagging logic:

| File | Source type | What to expect |
|------|-------------|----------------|
| `sample_sap.csv` | `sap_fuel` | Negative quantity (suspicious), unknown material (failed), unusually high value (suspicious) |
| `sample_utility.csv` | `utility` | Negative consumption (suspicious), non-numeric value (failed), bad date (failed) |
| `sample_travel.csv` | `travel` | Unknown IATA codes (suspicious), missing distance for hotel (suspicious), unknown travel type (failed) |

---

## Deployment (Render)

### Backend — Web Service

| Field | Value |
|-------|-------|
| Runtime | Python 3 |
| Build command | `pip install -r requirements.txt && python manage.py migrate && python manage.py seed_demo && python manage.py collectstatic --noinput` |
| Start command | `gunicorn breathe.wsgi:application` |
| Root directory | `backend` |

Environment variables to set in Render dashboard:

```
SECRET_KEY          = <generate a long random string>
DEBUG               = False
ALLOWED_HOSTS       = your-app.onrender.com
DB_NAME             = (from Render Postgres add-on)
DB_USER             = (from Render Postgres add-on)
DB_PASSWORD         = (from Render Postgres add-on)
DB_HOST             = (from Render Postgres add-on)
DB_PORT             = 5432
CORS_ALLOWED_ORIGINS = https://your-frontend.onrender.com
```

### Frontend — Static Site

| Field | Value |
|-------|-------|
| Build command | `npm install && npm run build` |
| Publish directory | `dist` |
| Root directory | `frontend` |

Environment variable:

```
VITE_API_URL = https://your-backend.onrender.com/api
```

---

## Docs

- `docs/MODEL.md` — data model decisions and rationale  
- `docs/DECISIONS.md` — ambiguities resolved, assumptions made  
- `docs/TRADEOFFS.md` — three things deliberately not built  
- `docs/SOURCES.md` — real-world format research for each source  
