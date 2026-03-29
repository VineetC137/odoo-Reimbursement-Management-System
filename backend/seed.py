"""
Database seed script for Reimbursement Management System.

This script populates the database with sample data for development and testing.
It is idempotent and can be run multiple times without creating duplicates.

Usage:
    python seed.py
"""

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, Company, User, ApprovalRule, ApprovalRuleApprover
from app.services.auth_service import AuthService
from datetime import datetime


def seed_database():
    """Seed the database with sample data."""
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    
    try:
        print("Starting database seed...")
        
        # Check if data already exists (idempotency check)
        existing_company = db.query(Company).filter(Company.name == "Acme Corporation").first()
        if existing_company:
            print("Seed data already exists. Skipping...")
            return
        
        # 1. Create Company record
        print("Creating company...")
        company = Company(
            name="Acme Corporation",
            country="United States",
            base_currency="USD",
            created_at=datetime.utcnow()
        )
        db.add(company)
        db.flush()  # Get company.id without committing
        
        # 2. Create ADMIN user
        print("Creating admin user...")
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
        
        # 3. Create MANAGER user
        print("Creating manager user...")
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
        
        # 4. Create two EMPLOYEE users with manager assignment
        print("Creating employee users...")
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
        
        # 5. Create ApprovalRule with associated approvers
        print("Creating approval rule...")
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
        print("Creating approval rule approvers...")
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
        
        # Commit all changes
        db.commit()
        
        print("\n" + "="*60)
        print("Database seeded successfully!")
        print("="*60)
        print("\nCreated accounts:")
        print(f"  Admin:     {admin.email} / admin123")
        print(f"  Manager:   {manager.email} / manager123")
        print(f"  Employee1: {employee1.email} / employee123")
        print(f"  Employee2: {employee2.email} / employee123")
        print("\nCompany:")
        print(f"  Name: {company.name}")
        print(f"  Country: {company.country}")
        print(f"  Base Currency: {company.base_currency}")
        print("\nApproval Rule:")
        print(f"  Name: {approval_rule.name}")
        print(f"  Mode: {approval_rule.mode}")
        print(f"  Threshold: {approval_rule.percentage_threshold}%")
        print(f"  Manager Approver: {approval_rule.is_manager_approver}")
        print(f"  Approvers: {len([approver1, approver2])}")
        print("="*60)
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
