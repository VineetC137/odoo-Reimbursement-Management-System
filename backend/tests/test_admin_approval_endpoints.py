import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import Company, User, ApprovalRule, ApprovalRuleApprover
from app.services.auth_service import AuthService


# Create file-based SQLite database for testing
TEST_DATABASE_URL = "sqlite:///./test_admin_approval.db"
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
def manager_user(company):
    """Create a manager user."""
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
    db.close()
    return {"id": user_id}


def test_create_approval_rule_percentage_mode(admin_user, manager_user):
    """Test creating an approval rule in PERCENTAGE mode."""
    response = client.post(
        "/api/admin/approval-rules",
        json={
            "name": "Percentage Rule",
            "description": "Requires 50% approval",
            "mode": "PERCENTAGE",
            "percentage_threshold": 50.0,
            "is_manager_approver": False,
            "approvers": [
                {"approver_id": manager_user["id"], "sequence": 1, "is_required": True}
            ]
        },
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Percentage Rule"
    assert data["mode"] == "PERCENTAGE"
    assert data["percentage_threshold"] == 50.0
    assert len(data["approvers"]) == 1


def test_create_approval_rule_specific_mode(admin_user, manager_user):
    """Test creating an approval rule in SPECIFIC mode."""
    response = client.post(
        "/api/admin/approval-rules",
        json={
            "name": "Specific Rule",
            "description": "Requires specific approver",
            "mode": "SPECIFIC",
            "special_approver_id": manager_user["id"],
            "is_manager_approver": False,
            "approvers": []
        },
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Specific Rule"
    assert data["mode"] == "SPECIFIC"
    assert data["special_approver_id"] == manager_user["id"]


def test_create_approval_rule_hybrid_mode(admin_user, manager_user):
    """Test creating an approval rule in HYBRID mode."""
    response = client.post(
        "/api/admin/approval-rules",
        json={
            "name": "Hybrid Rule",
            "description": "Requires percentage OR specific approver",
            "mode": "HYBRID",
            "percentage_threshold": 60.0,
            "special_approver_id": manager_user["id"],
            "is_manager_approver": True,
            "approvers": [
                {"approver_id": manager_user["id"], "sequence": 1, "is_required": True}
            ]
        },
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Hybrid Rule"
    assert data["mode"] == "HYBRID"
    assert data["percentage_threshold"] == 60.0
    assert data["special_approver_id"] == manager_user["id"]
    assert data["is_manager_approver"] is True


def test_create_approval_rule_missing_percentage_threshold(admin_user):
    """Test that creating PERCENTAGE rule without threshold fails."""
    response = client.post(
        "/api/admin/approval-rules",
        json={
            "name": "Invalid Rule",
            "mode": "PERCENTAGE",
            "is_manager_approver": False,
            "approvers": []
        },
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    
    assert response.status_code == 400
    assert "percentage_threshold" in response.json()["detail"].lower()


def test_create_approval_rule_missing_special_approver(admin_user):
    """Test that creating SPECIFIC rule without special_approver_id fails."""
    response = client.post(
        "/api/admin/approval-rules",
        json={
            "name": "Invalid Rule",
            "mode": "SPECIFIC",
            "is_manager_approver": False,
            "approvers": []
        },
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    
    assert response.status_code == 400
    assert "special_approver_id" in response.json()["detail"].lower()


def test_get_current_approval_rule(admin_user, manager_user):
    """Test getting the current approval rule."""
    # First create a rule
    client.post(
        "/api/admin/approval-rules",
        json={
            "name": "Test Rule",
            "mode": "PERCENTAGE",
            "percentage_threshold": 50.0,
            "is_manager_approver": False,
            "approvers": [
                {"approver_id": manager_user["id"], "sequence": 1, "is_required": True}
            ]
        },
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    
    # Get current rule
    response = client.get(
        "/api/admin/approval-rules/current",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Rule"
    assert data["mode"] == "PERCENTAGE"


def test_get_current_approval_rule_not_found(admin_user):
    """Test getting current rule when none exists."""
    response = client.get(
        "/api/admin/approval-rules/current",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    
    assert response.status_code == 404


def test_create_approval_rule_requires_admin(manager_user):
    """Test that non-admin cannot create approval rules."""
    token = AuthService.create_token(
        user_id=manager_user["id"],
        company_id=1,
        role="MANAGER"
    )
    
    response = client.post(
        "/api/admin/approval-rules",
        json={
            "name": "Test Rule",
            "mode": "PERCENTAGE",
            "percentage_threshold": 50.0,
            "is_manager_approver": False,
            "approvers": []
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
