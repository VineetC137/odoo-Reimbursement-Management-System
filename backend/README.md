# Reimbursement Management System - Backend

FastAPI backend for the Reimbursement Management System.

## Prerequisites

- Python 3.11+
- pip

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate the virtual environment:
- Windows: `venv\Scripts\activate`
- Unix/MacOS: `source venv/bin/activate`

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. (Optional) Seed the database with sample data:
```bash
python seed.py
```

This will create:
- 1 Company (Acme Corporation)
- 1 Admin user (admin@acme.com / admin123)
- 1 Manager user (manager@acme.com / manager123)
- 2 Employee users (john.doe@acme.com / employee123, jane.smith@acme.com / employee123)
- 1 Approval Rule with 2 approvers

The seed script is idempotent and can be run multiple times without creating duplicates.

## Running the Application

Start the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## Database Migrations

Create a new migration:
```bash
alembic revision --autogenerate -m "Description"
```

Apply migrations:
```bash
alembic upgrade head
```

Rollback migration:
```bash
alembic downgrade -1
```
