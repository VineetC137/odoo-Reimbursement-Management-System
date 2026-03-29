import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date
from app.main import app
from app.database import Base, get_db
from app.models import Company, User, Expense
from app.services.auth_service import AuthService


# Create file-based SQLite database for testing
TEST_DATABASE_URL = "sqlite:///./test_admin_expense.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def company(setup_database):
    """Create a test company."""
    db = TestingSessionLocal()
    company = Company(
        name="Test Company",
        country="United States",
        base_currency="USD"
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    company_id = company.id
    db.close()
    return {"id": company_id}


@pytest.fixture
def admin_user(company):
    """Create an admin user and return user with token."""
    db = TestingSessionLocal()
    password_hash = AuthService.hash_password("password123")
    user = User(
        company_id=company["id"],
        name="Admin User",
        email="admin@test.com",
        password_hash=password_hash,
        role="ADMIN"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    user_id = user.id
    user_company_id = user.company_id
    user_role = user.role
    
    token = AuthService.create_token(
        user_id=user_id,
        company_id=user_company_id,
        role=user_role
    )
    
    db.close()
    return {"user_id": user_id, "company_id": user_company_id, "role": user_role, "token": token}


@pytest.fixture
def employee_user(company):
    """Create an employee user."""
    db = TestingSessionLocal()
    password_hash = AuthService.hash_password("password123")
    user = User(
        company_id=company["id"],
        name="Employee User",
        email="employee@test.com",
        password_hash=password_hash,
        role="EMPLOYEE"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    user_id = user.id
    db.close()
    return {"id": user_id}


@pytest.fixture
def draft_expense(company, employee_user):
    """Create a draft expense."""
    db = TestingSessionLocal()
    expense = Expense(
        company_id=company["id"],
        employee_id=employee_user["id"],
        category="Travel",
        description="Test expense",
        expense_date=date(2024, 1, 15),
        paid_by="Credit Card",
        currency_original="USD",
        amount_original=100.0,
        amount_company_currency=100.0,
        status="DRAFT"
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    expense_id = expense.id
    db.close()
    return {"id": expense_id}


@pytest.fixture
def approved_expense(company, employee_user):
    """Create an approved expense."""
    db = TestingSessionLocal()
    expense = Expense(
        company_id=company["id"],
        employee_id=employee_user["id"],
        category="Meals",
        description="Approved expense",
        expense_date=date(2024, 1, 20),
        paid_by="Cash",
        currency_original="USD",
        amount_original=50.0,
        amount_company_currency=50.0,
        status="APPROVED"
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    expense_id = expense.id
    db.close()
    return {"id": expense_id}


def test_get_all_expenses(admin_user, draft_expense, approved_expense):
    """Test getting all expenses."""
    response = client.get(
        "/api/admin/expenses",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["expenses"]) == 2


def test_get_expenses_filter_by_status(admin_user, draft_expense, approved_expense):
    """Test filtering expenses by status."""
    response = client.get(
        "/api/admin/expenses?status=DRAFT",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["expenses"]) == 1
    assert data["expenses"][0]["status"] == "DRAFT"


def test_get_expenses_filter_by_employee(admin_user, employee_user, draft_expense):
    """Test filtering expenses by employee."""
    response = client.get(
        f"/api/admin/expenses?employee_id={employee_user['id']}",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["expenses"]) >= 1
    assert all(e["employee_id"] == employee_user["id"] for e in data["expenses"])


def test_get_expenses_filter_by_date_range(admin_user, draft_expense, approved_expense):
    """Test filtering expenses by date range."""
    response = client.get(
        "/api/admin/expenses?date_from=2024-01-01&date_to=2024-01-16",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["expenses"]) == 1
    assert data["expenses"][0]["expense_date"] == "2024-01-15"


def test_force_approve_expense(admin_user, draft_expense):
    """Test force approving an expense."""
    response = client.post(
        f"/api/admin/expenses/{draft_expense['id']}/force-approve",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == draft_expense["id"]
    assert data["status"] == "APPROVED"


def test_force_reject_expense(admin_user, draft_expense):
    """Test force rejecting an expense."""
    response = client.post(
        f"/api/admin/expenses/{draft_expense['id']}/force-reject",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == draft_expense["id"]
    assert data["status"] == "REJECTED"


def test_force_approve_nonexistent_expense(admin_user):
    """Test force approving a non-existent expense."""
    response = client.post(
        "/api/admin/expenses/99999/force-approve",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    
    assert response.status_code == 404


def test_force_reject_nonexistent_expense(admin_user):
    """Test force rejecting a non-existent expense."""
    response = client.post(
        "/api/admin/expenses/99999/force-reject",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    
    assert response.status_code == 404


def test_admin_expense_endpoints_require_admin(employee_user, draft_expense):
    """Test that non-admin cannot access admin expense endpoints."""
    token = AuthService.create_token(
        user_id=employee_user["id"],
        company_id=1,
        role="EMPLOYEE"
    )
    
    # Test get all expenses
    response = client.get(
        "/api/admin/expenses",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    
    # Test force approve
    response = client.post(
        f"/api/admin/expenses/{draft_expense['id']}/force-approve",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    
    # Test force reject
    response = client.post(
        f"/api/admin/expenses/{draft_expense['id']}/force-reject",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
