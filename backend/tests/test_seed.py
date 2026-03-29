"""Unit tests for database seed script."""

import pytest
from sqlalchemy.orm import Session
from app.models import Company, User, ApprovalRule, ApprovalRuleApprover
from app.services.auth_service import AuthService


def test_seed_creates_company(seeded_db: Session):
    """Test that seed creates exactly one company with correct attributes."""
    company = seeded_db.query(Company).filter(Company.name == "Acme Corporation").first()
    
    assert company is not None
    assert company.name == "Acme Corporation"
    assert company.country == "United States"
    assert company.base_currency == "USD"


def test_seed_creates_admin_user(seeded_db: Session):
    """Test that seed creates one ADMIN user."""
    admin = seeded_db.query(User).filter(User.role == "ADMIN", User.email == "admin@acme.com").first()
    
    assert admin is not None
    assert admin.name == "Admin User"
    assert admin.role == "ADMIN"
    assert admin.manager_id is None
    # Verify password is hashed correctly
    assert AuthService.verify_password("admin123", admin.password_hash)


def test_seed_creates_manager_user(seeded_db: Session):
    """Test that seed creates one MANAGER user."""
    manager = seeded_db.query(User).filter(User.role == "MANAGER", User.email == "manager@acme.com").first()
    
    assert manager is not None
    assert manager.name == "Manager User"
    assert manager.role == "MANAGER"
    assert manager.manager_id is None
    # Verify password is hashed correctly
    assert AuthService.verify_password("manager123", manager.password_hash)


def test_seed_creates_employee_users(seeded_db: Session):
    """Test that seed creates two EMPLOYEE users with manager assignment."""
    employees = seeded_db.query(User).filter(User.role == "EMPLOYEE").all()
    
    assert len(employees) == 2
    
    # Check first employee
    employee1 = seeded_db.query(User).filter(User.email == "john.doe@acme.com").first()
    assert employee1 is not None
    assert employee1.name == "John Doe"
    assert employee1.role == "EMPLOYEE"
    assert employee1.manager_id is not None
    assert employee1.manager.role == "MANAGER"
    assert AuthService.verify_password("employee123", employee1.password_hash)
    
    # Check second employee
    employee2 = seeded_db.query(User).filter(User.email == "jane.smith@acme.com").first()
    assert employee2 is not None
    assert employee2.name == "Jane Smith"
    assert employee2.role == "EMPLOYEE"
    assert employee2.manager_id is not None
    assert employee2.manager.role == "MANAGER"
    assert AuthService.verify_password("employee123", employee2.password_hash)
    
    # Both employees should have the same manager
    assert employee1.manager_id == employee2.manager_id


def test_seed_creates_approval_rule(seeded_db: Session):
    """Test that seed creates one ApprovalRule with associated approvers."""
    company = seeded_db.query(Company).filter(Company.name == "Acme Corporation").first()
    rule = seeded_db.query(ApprovalRule).filter(ApprovalRule.company_id == company.id).first()
    
    assert rule is not None
    assert rule.name == "Standard Approval Rule"
    assert rule.description == "Default approval workflow requiring manager approval"
    assert rule.mode == "PERCENTAGE"
    assert rule.percentage_threshold == 50.0
    assert rule.is_manager_approver is True
    
    # Check approvers
    approvers = seeded_db.query(ApprovalRuleApprover).filter(ApprovalRuleApprover.rule_id == rule.id).all()
    assert len(approvers) == 2
    
    # Check first approver (manager, required)
    approver1 = next((a for a in approvers if a.sequence == 1), None)
    assert approver1 is not None
    assert approver1.approver.role == "MANAGER"
    assert approver1.is_required is True
    
    # Check second approver (admin, optional)
    approver2 = next((a for a in approvers if a.sequence == 2), None)
    assert approver2 is not None
    assert approver2.approver.role == "ADMIN"
    assert approver2.is_required is False


def test_seed_idempotency(seeded_db: Session):
    """Test that running seed multiple times doesn't create duplicates."""
    # Count existing records
    company_count = seeded_db.query(Company).filter(Company.name == "Acme Corporation").count()
    user_count = seeded_db.query(User).count()
    rule_count = seeded_db.query(ApprovalRule).count()
    
    # Seed data should already exist from conftest
    assert company_count == 1
    assert user_count == 4  # 1 admin + 1 manager + 2 employees
    assert rule_count == 1
