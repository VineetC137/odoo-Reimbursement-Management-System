"""
Demo Data Script for Screen Recording
Creates realistic expense data for demonstration purposes
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, Company, User, Expense, ApprovalRule, ApprovalRuleApprover, ExpenseApprovalStep
from app.services.auth_service import AuthService
from app.services.fx_service import FXService
import random

def clear_demo_data(db: Session):
    """Clear existing demo data"""
    print("Clearing existing data...")
    db.query(ExpenseApprovalStep).delete()
    db.query(Expense).delete()
    db.query(ApprovalRuleApprover).delete()
    db.query(ApprovalRule).delete()
    db.query(User).delete()
    db.query(Company).delete()
    db.commit()
    print("✓ Data cleared")

def create_demo_data():
    """Create comprehensive demo data for screen recording"""
    db = SessionLocal()
    
    try:
        # Clear existing data
        clear_demo_data(db)
        
        # Create company
        print("\n1. Creating company...")
        company = Company(
            name="TechCorp Solutions",
            country="United States",
            base_currency="USD"
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        print(f"✓ Company created: {company.name}")
        
        # Create users
        print("\n2. Creating users...")
        users_data = [
            {
                "name": "Sarah Johnson",
                "email": "admin@techcorp.com",
                "password": "admin123",
                "role": "ADMIN",
                "manager_id": None
            },
            {
                "name": "Michael Chen",
                "email": "manager@techcorp.com",
                "password": "manager123",
                "role": "MANAGER",
                "manager_id": None
            },
            {
                "name": "Emily Rodriguez",
                "email": "emily@techcorp.com",
                "password": "employee123",
                "role": "EMPLOYEE",
                "manager_id": None  # Will be set after manager is created
            },
            {
                "name": "David Kim",
                "email": "david@techcorp.com",
                "password": "employee123",
                "role": "EMPLOYEE",
                "manager_id": None
            },
            {
                "name": "Jessica Martinez",
                "email": "jessica@techcorp.com",
                "password": "employee123",
                "role": "EMPLOYEE",
                "manager_id": None
            },
            {
                "name": "Robert Taylor",
                "email": "robert@techcorp.com",
                "password": "employee123",
                "role": "EMPLOYEE",
                "manager_id": None
            }
        ]
        
        created_users = {}
        for user_data in users_data:
            password_hash = AuthService.hash_password(user_data["password"])
            user = User(
                company_id=company.id,
                name=user_data["name"],
                email=user_data["email"],
                password_hash=password_hash,
                role=user_data["role"],
                manager_id=user_data["manager_id"]
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            created_users[user_data["email"]] = user
            print(f"✓ User created: {user.name} ({user.role})")
        
        # Assign manager to employees
        manager = created_users["manager@techcorp.com"]
        for email in ["emily@techcorp.com", "david@techcorp.com", "jessica@techcorp.com", "robert@techcorp.com"]:
            user = created_users[email]
            user.manager_id = manager.id
        db.commit()
        print("✓ Manager assigned to employees")
        
        # Create approval rule
        print("\n3. Creating approval rule...")
        approval_rule = ApprovalRule(
            company_id=company.id,
            name="Standard Approval Workflow",
            description="All expenses require manager approval",
            mode="PERCENTAGE",
            percentage_threshold=100.0,
            is_manager_approver=True
        )
        db.add(approval_rule)
        db.commit()
        db.refresh(approval_rule)
        
        # Add manager as approver
        approver = ApprovalRuleApprover(
            rule_id=approval_rule.id,
            approver_id=manager.id,
            sequence=1,
            is_required=True
        )
        db.add(approver)
        db.commit()
        print(f"✓ Approval rule created: {approval_rule.name}")
        
        # Create diverse expenses
        print("\n4. Creating demo expenses...")
        
        # Get FX rates for conversion
        fx_service = FXService()
        
        expenses_data = [
            # Emily's expenses
            {
                "employee": "emily@techcorp.com",
                "category": "Travel",
                "description": "Flight tickets to San Francisco for client meeting",
                "paid_by": "Personal Card",
                "currency": "USD",
                "amount": 450.00,
                "days_ago": 5,
                "status": "APPROVED"
            },
            {
                "employee": "emily@techcorp.com",
                "category": "Meals",
                "description": "Team dinner with clients at The Steakhouse",
                "paid_by": "Company Card",
                "currency": "USD",
                "amount": 285.50,
                "days_ago": 4,
                "status": "APPROVED"
            },
            {
                "employee": "emily@techcorp.com",
                "category": "Travel",
                "description": "Hotel accommodation in San Francisco (3 nights)",
                "paid_by": "Personal Card",
                "currency": "USD",
                "amount": 720.00,
                "days_ago": 3,
                "status": "WAITING_APPROVAL"
            },
            {
                "employee": "emily@techcorp.com",
                "category": "Office Supplies",
                "description": "Ergonomic keyboard and mouse",
                "paid_by": "Personal Card",
                "currency": "USD",
                "amount": 125.99,
                "days_ago": 1,
                "status": "DRAFT"
            },
            
            # David's expenses
            {
                "employee": "david@techcorp.com",
                "category": "Software",
                "description": "Adobe Creative Cloud annual subscription",
                "paid_by": "Company Card",
                "currency": "USD",
                "amount": 599.88,
                "days_ago": 7,
                "status": "APPROVED"
            },
            {
                "employee": "david@techcorp.com",
                "category": "Travel",
                "description": "Uber rides to client offices",
                "paid_by": "Personal Card",
                "currency": "USD",
                "amount": 87.50,
                "days_ago": 6,
                "status": "APPROVED"
            },
            {
                "employee": "david@techcorp.com",
                "category": "Meals",
                "description": "Business lunch with potential client",
                "paid_by": "Personal Card",
                "currency": "USD",
                "amount": 95.00,
                "days_ago": 2,
                "status": "WAITING_APPROVAL"
            },
            {
                "employee": "david@techcorp.com",
                "category": "Office Supplies",
                "description": "Whiteboard markers and sticky notes",
                "paid_by": "Cash",
                "currency": "USD",
                "amount": 42.75,
                "days_ago": 1,
                "status": "DRAFT"
            },
            
            # Jessica's expenses
            {
                "employee": "jessica@techcorp.com",
                "category": "Travel",
                "description": "Conference registration - Tech Summit 2024",
                "paid_by": "Personal Card",
                "currency": "USD",
                "amount": 899.00,
                "days_ago": 10,
                "status": "APPROVED"
            },
            {
                "employee": "jessica@techcorp.com",
                "category": "Travel",
                "description": "Flight to Austin for Tech Summit",
                "paid_by": "Personal Card",
                "currency": "USD",
                "amount": 320.00,
                "days_ago": 8,
                "status": "APPROVED"
            },
            {
                "employee": "jessica@techcorp.com",
                "category": "Meals",
                "description": "Networking dinner at conference",
                "paid_by": "Personal Card",
                "currency": "USD",
                "amount": 78.50,
                "days_ago": 3,
                "status": "WAITING_APPROVAL"
            },
            {
                "employee": "jessica@techcorp.com",
                "category": "Software",
                "description": "Figma professional plan (1 year)",
                "paid_by": "Company Card",
                "currency": "USD",
                "amount": 144.00,
                "days_ago": 2,
                "status": "WAITING_APPROVAL"
            },
            
            # Robert's expenses
            {
                "employee": "robert@techcorp.com",
                "category": "Travel",
                "description": "Parking fees at client site",
                "paid_by": "Cash",
                "currency": "USD",
                "amount": 35.00,
                "days_ago": 5,
                "status": "APPROVED"
            },
            {
                "employee": "robert@techcorp.com",
                "category": "Meals",
                "description": "Coffee meeting with vendor",
                "paid_by": "Personal Card",
                "currency": "USD",
                "amount": 18.50,
                "days_ago": 4,
                "status": "REJECTED"
            },
            {
                "employee": "robert@techcorp.com",
                "category": "Office Supplies",
                "description": "External monitor and HDMI cable",
                "paid_by": "Personal Card",
                "currency": "USD",
                "amount": 289.99,
                "days_ago": 2,
                "status": "WAITING_APPROVAL"
            },
            {
                "employee": "robert@techcorp.com",
                "category": "Travel",
                "description": "Train tickets to New York",
                "paid_by": "Personal Card",
                "currency": "USD",
                "amount": 156.00,
                "days_ago": 0,
                "status": "DRAFT"
            },
            
            # International expenses with different currencies
            {
                "employee": "emily@techcorp.com",
                "category": "Travel",
                "description": "Hotel in London for international client meeting",
                "paid_by": "Company Card",
                "currency": "GBP",
                "amount": 450.00,
                "days_ago": 15,
                "status": "APPROVED"
            },
            {
                "employee": "david@techcorp.com",
                "category": "Meals",
                "description": "Business dinner in Paris",
                "paid_by": "Personal Card",
                "currency": "EUR",
                "amount": 125.00,
                "days_ago": 12,
                "status": "APPROVED"
            },
            {
                "employee": "jessica@techcorp.com",
                "category": "Travel",
                "description": "Taxi from Tokyo airport",
                "paid_by": "Cash",
                "currency": "JPY",
                "amount": 8500.00,
                "days_ago": 20,
                "status": "APPROVED"
            }
        ]
        
        for expense_data in expenses_data:
            employee = created_users[expense_data["employee"]]
            expense_date = datetime.now().date() - timedelta(days=expense_data["days_ago"])
            
            # Convert to company currency
            if expense_data["currency"] == company.base_currency:
                amount_company_currency = expense_data["amount"]
            else:
                try:
                    amount_company_currency = fx_service.convert_amount(
                        expense_data["amount"],
                        expense_data["currency"],
                        company.base_currency
                    )
                except:
                    # Fallback if FX API fails
                    amount_company_currency = expense_data["amount"]
            
            expense = Expense(
                company_id=company.id,
                employee_id=employee.id,
                category=expense_data["category"],
                description=expense_data["description"],
                expense_date=expense_date,
                paid_by=expense_data["paid_by"],
                currency_original=expense_data["currency"],
                amount_original=expense_data["amount"],
                amount_company_currency=amount_company_currency,
                status=expense_data["status"]
            )
            db.add(expense)
            db.commit()
            db.refresh(expense)
            
            # Create approval steps for non-draft expenses
            if expense_data["status"] != "DRAFT":
                approval_step = ExpenseApprovalStep(
                    expense_id=expense.id,
                    approver_id=manager.id,
                    sequence=1,
                    status="APPROVED" if expense_data["status"] == "APPROVED" else 
                           "REJECTED" if expense_data["status"] == "REJECTED" else "PENDING",
                    comment="Approved - valid business expense" if expense_data["status"] == "APPROVED" else
                            "Please provide receipt for reimbursement" if expense_data["status"] == "REJECTED" else None,
                    acted_at=datetime.now() if expense_data["status"] in ["APPROVED", "REJECTED"] else None
                )
                db.add(approval_step)
                db.commit()
            
            print(f"✓ Expense created: {expense.description[:50]}... ({expense.status})")
        
        print(f"\n✅ Demo data created successfully!")
        print(f"\n📊 Summary:")
        print(f"   - Company: {company.name}")
        print(f"   - Users: {len(created_users)} (1 Admin, 1 Manager, 4 Employees)")
        print(f"   - Expenses: {len(expenses_data)}")
        print(f"   - Approved: {sum(1 for e in expenses_data if e['status'] == 'APPROVED')}")
        print(f"   - Pending: {sum(1 for e in expenses_data if e['status'] == 'WAITING_APPROVAL')}")
        print(f"   - Draft: {sum(1 for e in expenses_data if e['status'] == 'DRAFT')}")
        print(f"   - Rejected: {sum(1 for e in expenses_data if e['status'] == 'REJECTED')}")
        
        print(f"\n🔐 Login Credentials:")
        print(f"   Admin:    admin@techcorp.com / admin123")
        print(f"   Manager:  manager@techcorp.com / manager123")
        print(f"   Employee: emily@techcorp.com / employee123")
        print(f"   Employee: david@techcorp.com / employee123")
        print(f"   Employee: jessica@techcorp.com / employee123")
        print(f"   Employee: robert@techcorp.com / employee123")
        
    except Exception as e:
        print(f"\n❌ Error creating demo data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Creating Demo Data for Screen Recording")
    print("=" * 60)
    create_demo_data()
    print("\n" + "=" * 60)
    print("Demo data ready! Start your screen recording.")
    print("=" * 60)
