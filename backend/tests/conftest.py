"""
Shared pytest configuration and fixtures for all tests.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db


# Create test database engine
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the get_db dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create a database session for tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def db():
    """Create a database session for tests (alias for db_session)."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def seeded_db():
    """Create a database session with seed data."""
    from app.models import Company, User, ApprovalRule, ApprovalRuleApprover
    from app.services.auth_service import AuthService
    from datetime import datetime
    
    db = TestingSessionLocal()
    
    try:
        # Check if data already exists (idempotency check)
        existing_company = db.query(Company).filter(Company.name == "Acme Corporation").first()
        if not existing_company:
            # Create Company record
            company = Company(
                name="Acme Corporation",
                country="United States",
                base_currency="USD",
                created_at=datetime.utcnow()
            )
            db.add(company)
            db.flush()
            
            # Create ADMIN user
            admin = User(
                company_id=company.id,
                name="Admin User",
                email="admin@acme.com",
                password_hash=AuthService.hash_password("admin123"),
                role="ADMIN",
                manager_id=None,
                created_at=datetime.utcnow()
            )
            db.add(admin)
            db.flush()
            
            # Create MANAGER user
            manager = User(
                company_id=company.id,
                name="Manager User",
                email="manager@acme.com",
                password_hash=AuthService.hash_password("manager123"),
                role="MANAGER",
                manager_id=None,
                created_at=datetime.utcnow()
            )
            db.add(manager)
            db.flush()
            
            # Create two EMPLOYEE users with manager assignment
            employee1 = User(
                company_id=company.id,
                name="John Doe",
                email="john.doe@acme.com",
                password_hash=AuthService.hash_password("employee123"),
                role="EMPLOYEE",
                manager_id=manager.id,
                created_at=datetime.utcnow()
            )
            db.add(employee1)
            
            employee2 = User(
                company_id=company.id,
                name="Jane Smith",
                email="jane.smith@acme.com",
                password_hash=AuthService.hash_password("employee123"),
                role="EMPLOYEE",
                manager_id=manager.id,
                created_at=datetime.utcnow()
            )
            db.add(employee2)
            db.flush()
            
            # Create ApprovalRule with associated approvers
            approval_rule = ApprovalRule(
                company_id=company.id,
                name="Standard Approval Rule",
                description="Default approval workflow requiring manager approval",
                mode="PERCENTAGE",
                percentage_threshold=50.0,
                special_approver_id=None,
                is_manager_approver=True,
                created_at=datetime.utcnow()
            )
            db.add(approval_rule)
            db.flush()
            
            # Create approval rule approvers
            approver1 = ApprovalRuleApprover(
                rule_id=approval_rule.id,
                approver_id=manager.id,
                sequence=1,
                is_required=True
            )
            db.add(approver1)
            
            approver2 = ApprovalRuleApprover(
                rule_id=approval_rule.id,
                approver_id=admin.id,
                sequence=2,
                is_required=False
            )
            db.add(approver2)
            
            db.commit()
        
        yield db
    finally:
        db.close()
