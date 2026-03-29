import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import Company, User
from app.services.auth_service import AuthService


# Create file-based SQLite database for testing (in-memory doesn't work with FastAPI TestClient)
TEST_DATABASE_URL = "sqlite:///./test_admin.db"
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
    
    # Return a dict with the ID so we can recreate the object in other fixtures
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
    user_email = user.email
    db.close()
    return {"id": user_id, "email": user_email}


def test_get_users_success(admin_user, employee_user):
    """Test getting all users as admin."""
    response = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert len(data["users"]) == 2  # admin and employee


def test_get_users_filtered_by_role(admin_user, employee_user):
    """Test getting users filtered by role."""
    response = client.get(
        "/api/admin/users?role=EMPLOYEE",
        headers={"Authorization": f"Bearer {admin_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["users"]) == 1
    assert data["users"][0]["role"] == "EMPLOYEE"


def test_get_users_unauthorized(employee_user, company):
    """Test that non-admin cannot get users."""
    # Create token for employee
    token = AuthService.create_token(
        user_id=employee_user["id"],
        company_id=company["id"],
        role="EMPLOYEE"
    )
    
    response = client.get(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403


def test_get_users_no_token():
    """Test that request without token is rejected."""
    response = client.get("/api/admin/users")
    
    assert response.status_code == 403


def test_create_user_success(admin_user):
    """Test creating a new user as admin."""
    response = client.post(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_user['token']}"},
        json={
            "name": "New User",
            "email": "newuser@test.com",
            "password": "password123",
            "role": "EMPLOYEE"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New User"
    assert data["email"] == "newuser@test.com"
    assert data["role"] == "EMPLOYEE"
    assert "id" in data


def test_create_user_with_manager(admin_user, manager_user):
    """Test creating user with manager assignment."""
    response = client.post(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_user['token']}"},
        json={
            "name": "New Employee",
            "email": "newemp@test.com",
            "password": "password123",
            "role": "EMPLOYEE",
            "manager_id": manager_user["user_id"]
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["manager_id"] == manager_user["user_id"]


def test_create_user_duplicate_email(admin_user, employee_user):
    """Test that creating user with duplicate email fails."""
    response = client.post(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_user['token']}"},
        json={
            "name": "Duplicate User",
            "email": employee_user["email"],
            "password": "password123",
            "role": "EMPLOYEE"
        }
    )
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_create_user_invalid_role(admin_user):
    """Test that creating user with invalid role fails."""
    response = client.post(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_user['token']}"},
        json={
            "name": "User",
            "email": "user@test.com",
            "password": "password123",
            "role": "INVALID"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_create_user_invalid_manager(admin_user):
    """Test that creating user with invalid manager_id fails."""
    response = client.post(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {admin_user['token']}"},
        json={
            "name": "User",
            "email": "user@test.com",
            "password": "password123",
            "role": "EMPLOYEE",
            "manager_id": 999
        }
    )
    
    assert response.status_code == 400
    assert "not found" in response.json()["detail"]


def test_create_user_unauthorized(manager_user):
    """Test that non-admin cannot create users."""
    response = client.post(
        "/api/admin/users",
        headers={"Authorization": f"Bearer {manager_user['token']}"},
        json={
            "name": "User",
            "email": "user@test.com",
            "password": "password123",
            "role": "EMPLOYEE"
        }
    )
    
    assert response.status_code == 403


def test_update_user_success(admin_user, employee_user):
    """Test updating a user as admin."""
    response = client.put(
        f"/api/admin/users/{employee_user['id']}",
        headers={"Authorization": f"Bearer {admin_user['token']}"},
        json={
            "name": "Updated Name"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["email"] == employee_user["email"]  # Email unchanged


def test_update_user_email(admin_user, employee_user):
    """Test updating user email."""
    response = client.put(
        f"/api/admin/users/{employee_user['id']}",
        headers={"Authorization": f"Bearer {admin_user['token']}"},
        json={
            "email": "newemail@test.com"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "newemail@test.com"


def test_update_user_role(admin_user, employee_user):
    """Test updating user role."""
    response = client.put(
        f"/api/admin/users/{employee_user['id']}",
        headers={"Authorization": f"Bearer {admin_user['token']}"},
        json={
            "role": "MANAGER"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "MANAGER"


def test_update_user_manager(admin_user, employee_user, manager_user):
    """Test updating user manager."""
    response = client.put(
        f"/api/admin/users/{employee_user['id']}",
        headers={"Authorization": f"Bearer {admin_user['token']}"},
        json={
            "manager_id": manager_user["user_id"]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["manager_id"] == manager_user["user_id"]


def test_update_user_not_found(admin_user):
    """Test updating non-existent user."""
    response = client.put(
        "/api/admin/users/999",
        headers={"Authorization": f"Bearer {admin_user['token']}"},
        json={
            "name": "New Name"
        }
    )
    
    assert response.status_code == 400
    assert "not found" in response.json()["detail"]


def test_update_user_duplicate_email(admin_user, employee_user):
    """Test that updating to duplicate email fails."""
    # Create another user
    db = TestingSessionLocal()
    password_hash = AuthService.hash_password("password123")
    user2 = User(
        company_id=admin_user["company_id"],
        name="User 2",
        email="user2@test.com",
        password_hash=password_hash,
        role="EMPLOYEE"
    )
    db.add(user2)
    db.commit()
    db.refresh(user2)
    user2_id = user2.id
    db.close()
    
    response = client.put(
        f"/api/admin/users/{user2_id}",
        headers={"Authorization": f"Bearer {admin_user['token']}"},
        json={
            "email": employee_user["email"]
        }
    )
    
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


def test_update_user_unauthorized(manager_user, employee_user):
    """Test that non-admin cannot update users."""
    response = client.put(
        f"/api/admin/users/{employee_user['id']}",
        headers={"Authorization": f"Bearer {manager_user['token']}"},
        json={
            "name": "New Name"
        }
    )
    
    assert response.status_code == 403
