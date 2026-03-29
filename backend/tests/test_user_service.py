import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Company, User
from app.services.user_service import UserService


# Create in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def company(db):
    """Create a test company."""
    company = Company(
        name="Test Company",
        country="United States",
        base_currency="USD"
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@pytest.fixture
def manager_user(db, company):
    """Create a test manager user."""
    user = User(
        company_id=company.id,
        name="Manager User",
        email="manager@test.com",
        password_hash="hashed_password",
        role="MANAGER"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_create_user_success(db, company):
    """Test successful user creation."""
    user = UserService.create_user(
        db=db,
        company_id=company.id,
        name="John Doe",
        email="john@test.com",
        password="password123",
        role="EMPLOYEE"
    )
    
    assert user.id is not None
    assert user.name == "John Doe"
    assert user.email == "john@test.com"
    assert user.role == "EMPLOYEE"
    assert user.company_id == company.id
    assert user.password_hash != "password123"  # Password should be hashed


def test_create_user_with_manager(db, company, manager_user):
    """Test user creation with manager assignment."""
    user = UserService.create_user(
        db=db,
        company_id=company.id,
        name="Employee User",
        email="employee@test.com",
        password="password123",
        role="EMPLOYEE",
        manager_id=manager_user.id
    )
    
    assert user.manager_id == manager_user.id


def test_create_user_duplicate_email(db, company):
    """Test that creating user with duplicate email raises ValueError."""
    UserService.create_user(
        db=db,
        company_id=company.id,
        name="User One",
        email="duplicate@test.com",
        password="password123",
        role="EMPLOYEE"
    )
    db.commit()
    
    with pytest.raises(ValueError, match="already registered"):
        UserService.create_user(
            db=db,
            company_id=company.id,
            name="User Two",
            email="duplicate@test.com",
            password="password456",
            role="EMPLOYEE"
        )


def test_create_user_invalid_role(db, company):
    """Test that creating user with invalid role raises ValueError."""
    with pytest.raises(ValueError, match="Invalid role"):
        UserService.create_user(
            db=db,
            company_id=company.id,
            name="User",
            email="user@test.com",
            password="password123",
            role="INVALID_ROLE"
        )


def test_create_user_invalid_manager(db, company):
    """Test that creating user with non-existent manager raises ValueError."""
    with pytest.raises(ValueError, match="Manager with ID 999 not found"):
        UserService.create_user(
            db=db,
            company_id=company.id,
            name="User",
            email="user@test.com",
            password="password123",
            role="EMPLOYEE",
            manager_id=999
        )


def test_create_user_manager_not_manager_role(db, company):
    """Test that creating user with manager_id pointing to non-MANAGER raises ValueError."""
    admin_user = User(
        company_id=company.id,
        name="Admin User",
        email="admin@test.com",
        password_hash="hashed",
        role="ADMIN"
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    with pytest.raises(ValueError, match="is not a MANAGER"):
        UserService.create_user(
            db=db,
            company_id=company.id,
            name="User",
            email="user@test.com",
            password="password123",
            role="EMPLOYEE",
            manager_id=admin_user.id
        )


def test_update_user_name(db, company):
    """Test updating user name."""
    user = UserService.create_user(
        db=db,
        company_id=company.id,
        name="Original Name",
        email="user@test.com",
        password="password123",
        role="EMPLOYEE"
    )
    db.commit()
    
    updated_user = UserService.update_user(
        db=db,
        user_id=user.id,
        name="Updated Name"
    )
    
    assert updated_user.name == "Updated Name"
    assert updated_user.email == "user@test.com"  # Email unchanged


def test_update_user_email(db, company):
    """Test updating user email."""
    user = UserService.create_user(
        db=db,
        company_id=company.id,
        name="User",
        email="old@test.com",
        password="password123",
        role="EMPLOYEE"
    )
    db.commit()
    
    updated_user = UserService.update_user(
        db=db,
        user_id=user.id,
        email="new@test.com"
    )
    
    assert updated_user.email == "new@test.com"


def test_update_user_duplicate_email(db, company):
    """Test that updating to duplicate email raises ValueError."""
    UserService.create_user(
        db=db,
        company_id=company.id,
        name="User One",
        email="user1@test.com",
        password="password123",
        role="EMPLOYEE"
    )
    user2 = UserService.create_user(
        db=db,
        company_id=company.id,
        name="User Two",
        email="user2@test.com",
        password="password123",
        role="EMPLOYEE"
    )
    db.commit()
    
    with pytest.raises(ValueError, match="already registered"):
        UserService.update_user(
            db=db,
            user_id=user2.id,
            email="user1@test.com"
        )


def test_update_user_role(db, company):
    """Test updating user role."""
    user = UserService.create_user(
        db=db,
        company_id=company.id,
        name="User",
        email="user@test.com",
        password="password123",
        role="EMPLOYEE"
    )
    db.commit()
    
    updated_user = UserService.update_user(
        db=db,
        user_id=user.id,
        role="MANAGER"
    )
    
    assert updated_user.role == "MANAGER"


def test_update_user_manager(db, company, manager_user):
    """Test updating user manager."""
    user = UserService.create_user(
        db=db,
        company_id=company.id,
        name="User",
        email="user@test.com",
        password="password123",
        role="EMPLOYEE"
    )
    db.commit()
    
    updated_user = UserService.update_user(
        db=db,
        user_id=user.id,
        manager_id=manager_user.id
    )
    
    assert updated_user.manager_id == manager_user.id


def test_update_user_not_found(db):
    """Test that updating non-existent user raises ValueError."""
    with pytest.raises(ValueError, match="User with ID 999 not found"):
        UserService.update_user(
            db=db,
            user_id=999,
            name="New Name"
        )


def test_get_users_all(db, company):
    """Test getting all users."""
    UserService.create_user(
        db=db,
        company_id=company.id,
        name="User 1",
        email="user1@test.com",
        password="password123",
        role="ADMIN"
    )
    UserService.create_user(
        db=db,
        company_id=company.id,
        name="User 2",
        email="user2@test.com",
        password="password123",
        role="MANAGER"
    )
    UserService.create_user(
        db=db,
        company_id=company.id,
        name="User 3",
        email="user3@test.com",
        password="password123",
        role="EMPLOYEE"
    )
    db.commit()
    
    users = UserService.get_users(db=db, company_id=company.id)
    
    assert len(users) == 3


def test_get_users_filtered_by_role(db, company):
    """Test getting users filtered by role."""
    UserService.create_user(
        db=db,
        company_id=company.id,
        name="Admin",
        email="admin@test.com",
        password="password123",
        role="ADMIN"
    )
    UserService.create_user(
        db=db,
        company_id=company.id,
        name="Employee 1",
        email="emp1@test.com",
        password="password123",
        role="EMPLOYEE"
    )
    UserService.create_user(
        db=db,
        company_id=company.id,
        name="Employee 2",
        email="emp2@test.com",
        password="password123",
        role="EMPLOYEE"
    )
    db.commit()
    
    employees = UserService.get_users(db=db, company_id=company.id, role="EMPLOYEE")
    
    assert len(employees) == 2
    assert all(user.role == "EMPLOYEE" for user in employees)


def test_get_user_by_email_found(db, company):
    """Test getting user by email when user exists."""
    UserService.create_user(
        db=db,
        company_id=company.id,
        name="User",
        email="user@test.com",
        password="password123",
        role="EMPLOYEE"
    )
    db.commit()
    
    user = UserService.get_user_by_email(db=db, email="user@test.com")
    
    assert user is not None
    assert user.email == "user@test.com"


def test_get_user_by_email_not_found(db):
    """Test getting user by email when user does not exist."""
    user = UserService.get_user_by_email(db=db, email="nonexistent@test.com")
    
    assert user is None
