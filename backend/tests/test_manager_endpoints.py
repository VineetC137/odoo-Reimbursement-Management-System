import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date
from app.main import app
from app.database import Base, get_db
from app.models import Company, User, Expense, ExpenseApprovalStep
from app.services.auth_service import AuthService


# Create file-based SQLite database for testing
TEST_DATABASE_URL = "sqlite:///./test_manager.db"
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
def manager_user(company):
    """Create a manager user and return user with token."""
    db = TestingSessionLocal()
    password_hash = AuthService.hash_password("password123")
    user = User(
        company_id=company["id"],
        name="Manager User",
        email="manager@test.com",
        password_hash=password_hash,
        role="MANAGER"
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
def expense_with_pending_approval(company, employee_user, manager_user):
    """Create an expense with a pending approval step."""
    db = TestingSessionLocal()
    
    # Create expense
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
        status="WAITING_APPROVAL"
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    
    # Create approval step
    step = ExpenseApprovalStep(
        expense_id=expense.id,
        approver_id=manager_user["user_id"],
        sequence=1,
        status="PENDING"
    )
    db.add(step)
    db.commit()
    db.refresh(step)
    
    expense_id = expense.id
    step_id = step.id
    db.close()
    
    return {"expense_id": expense_id, "step_id": step_id}


def test_get_pending_approvals(manager_user, expense_with_pending_approval):
    """Test getting pending approvals for a manager."""
    response = client.get(
        "/api/manager/approvals/pending",
        headers={"Authorization": f"Bearer {manager_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["approvals"]) == 1
    assert data["approvals"][0]["step_id"] == expense_with_pending_approval["step_id"]
    assert data["approvals"][0]["expense"]["id"] == expense_with_pending_approval["expense_id"]


def test_get_pending_approvals_empty(manager_user):
    """Test getting pending approvals when there are none."""
    response = client.get(
        "/api/manager/approvals/pending",
        headers={"Authorization": f"Bearer {manager_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["approvals"]) == 0


def test_approve_step(manager_user, expense_with_pending_approval):
    """Test approving an approval step."""
    response = client.post(
        f"/api/manager/approvals/{expense_with_pending_approval['step_id']}/approve",
        headers={"Authorization": f"Bearer {manager_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["step"]["id"] == expense_with_pending_approval["step_id"]
    assert data["step"]["status"] == "APPROVED"
    assert data["step"]["acted_at"] is not None


def test_reject_step(manager_user, expense_with_pending_approval):
    """Test rejecting an approval step with a comment."""
    response = client.post(
        f"/api/manager/approvals/{expense_with_pending_approval['step_id']}/reject",
        json={"comment": "Insufficient documentation"},
        headers={"Authorization": f"Bearer {manager_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["step"]["id"] == expense_with_pending_approval["step_id"]
    assert data["step"]["status"] == "REJECTED"
    assert data["step"]["comment"] == "Insufficient documentation"
    assert data["step"]["acted_at"] is not None


def test_reject_step_without_comment(manager_user, expense_with_pending_approval):
    """Test that rejecting without a comment fails."""
    response = client.post(
        f"/api/manager/approvals/{expense_with_pending_approval['step_id']}/reject",
        json={"comment": ""},
        headers={"Authorization": f"Bearer {manager_user['token']}"}
    )
    
    assert response.status_code == 422  # Validation error


def test_approve_nonexistent_step(manager_user):
    """Test approving a non-existent step."""
    response = client.post(
        "/api/manager/approvals/99999/approve",
        headers={"Authorization": f"Bearer {manager_user['token']}"}
    )
    
    assert response.status_code == 404


def test_reject_nonexistent_step(manager_user):
    """Test rejecting a non-existent step."""
    response = client.post(
        "/api/manager/approvals/99999/reject",
        json={"comment": "Test comment"},
        headers={"Authorization": f"Bearer {manager_user['token']}"}
    )
    
    assert response.status_code == 404


def test_approve_step_wrong_approver(expense_with_pending_approval):
    """Test that a different manager cannot approve another manager's step."""
    # Create a different manager
    db = TestingSessionLocal()
    password_hash = AuthService.hash_password("password123")
    other_manager = User(
        company_id=1,
        name="Other Manager",
        email="other@test.com",
        password_hash=password_hash,
        role="MANAGER"
    )
    db.add(other_manager)
    db.commit()
    db.refresh(other_manager)
    
    token = AuthService.create_token(
        user_id=other_manager.id,
        company_id=other_manager.company_id,
        role=other_manager.role
    )
    db.close()
    
    response = client.post(
        f"/api/manager/approvals/{expense_with_pending_approval['step_id']}/approve",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403


def test_approve_already_processed_step(manager_user, expense_with_pending_approval):
    """Test that approving an already processed step fails."""
    # First approve the step
    client.post(
        f"/api/manager/approvals/{expense_with_pending_approval['step_id']}/approve",
        headers={"Authorization": f"Bearer {manager_user['token']}"}
    )
    
    # Try to approve again
    response = client.post(
        f"/api/manager/approvals/{expense_with_pending_approval['step_id']}/approve",
        headers={"Authorization": f"Bearer {manager_user['token']}"}
    )
    
    assert response.status_code == 400


def test_manager_endpoints_require_manager_role(employee_user, expense_with_pending_approval):
    """Test that non-manager cannot access manager endpoints."""
    token = AuthService.create_token(
        user_id=employee_user["id"],
        company_id=1,
        role="EMPLOYEE"
    )
    
    # Test get pending approvals
    response = client.get(
        "/api/manager/approvals/pending",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    
    # Test approve
    response = client.post(
        f"/api/manager/approvals/{expense_with_pending_approval['step_id']}/approve",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    
    # Test reject
    response = client.post(
        f"/api/manager/approvals/{expense_with_pending_approval['step_id']}/reject",
        json={"comment": "Test"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
