"""
Manual test script for expense endpoints.
Run this after starting the server with: uvicorn app.main:app --reload
"""

import requests
import json
from datetime import date

BASE_URL = "http://localhost:8000"

def test_expense_workflow():
    """Test the complete expense workflow."""
    
    print("=" * 60)
    print("Testing Expense Management Workflow")
    print("=" * 60)
    
    # Step 1: Login as employee
    print("\n1. Logging in as employee...")
    login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "employee@test.com",
        "password": "password123"
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        print(login_response.text)
        return
    
    token = login_response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login successful")
    
    # Step 2: Create an expense
    print("\n2. Creating a new expense...")
    create_response = requests.post(
        f"{BASE_URL}/api/employee/expenses",
        headers=headers,
        json={
            "category": "Travel",
            "description": "Flight to NYC for conference",
            "expense_date": str(date.today()),
            "paid_by": "Credit Card",
            "currency_original": "USD",
            "amount_original": 500.0
        }
    )
    
    if create_response.status_code != 201:
        print(f"❌ Create expense failed: {create_response.status_code}")
        print(create_response.text)
        return
    
    expense = create_response.json()
    expense_id = expense["id"]
    print(f"✅ Expense created with ID: {expense_id}")
    print(f"   Status: {expense['status']}")
    print(f"   Amount: {expense['amount_original']} {expense['currency_original']}")
    print(f"   Converted: {expense['amount_company_currency']} (company currency)")
    
    # Step 3: Get all expenses
    print("\n3. Getting all expenses...")
    list_response = requests.get(
        f"{BASE_URL}/api/employee/expenses",
        headers=headers
    )
    
    if list_response.status_code != 200:
        print(f"❌ Get expenses failed: {list_response.status_code}")
        print(list_response.text)
        return
    
    expenses = list_response.json()["expenses"]
    print(f"✅ Found {len(expenses)} expense(s)")
    
    # Step 4: Get expenses filtered by status
    print("\n4. Getting DRAFT expenses...")
    draft_response = requests.get(
        f"{BASE_URL}/api/employee/expenses?status=DRAFT",
        headers=headers
    )
    
    if draft_response.status_code != 200:
        print(f"❌ Get DRAFT expenses failed: {draft_response.status_code}")
        print(draft_response.text)
        return
    
    draft_expenses = draft_response.json()["expenses"]
    print(f"✅ Found {len(draft_expenses)} DRAFT expense(s)")
    
    # Step 5: Update the expense
    print("\n5. Updating expense description...")
    update_response = requests.put(
        f"{BASE_URL}/api/employee/expenses/{expense_id}",
        headers=headers,
        json={
            "description": "Flight to NYC for conference - Updated"
        }
    )
    
    if update_response.status_code != 200:
        print(f"❌ Update expense failed: {update_response.status_code}")
        print(update_response.text)
        return
    
    updated_expense = update_response.json()
    print(f"✅ Expense updated")
    print(f"   New description: {updated_expense['description']}")
    
    # Step 6: Get single expense
    print("\n6. Getting expense details...")
    detail_response = requests.get(
        f"{BASE_URL}/api/employee/expenses/{expense_id}",
        headers=headers
    )
    
    if detail_response.status_code != 200:
        print(f"❌ Get expense detail failed: {detail_response.status_code}")
        print(detail_response.text)
        return
    
    expense_detail = detail_response.json()
    print(f"✅ Expense details retrieved")
    print(f"   ID: {expense_detail['id']}")
    print(f"   Description: {expense_detail['description']}")
    print(f"   Status: {expense_detail['status']}")
    print(f"   Approval steps: {len(expense_detail['approval_steps'])}")
    print(f"   Receipts: {len(expense_detail['receipts'])}")
    
    # Step 7: Try to submit (will fail if no approval rule configured)
    print("\n7. Attempting to submit expense...")
    submit_response = requests.post(
        f"{BASE_URL}/api/employee/expenses/{expense_id}/submit",
        headers=headers
    )
    
    if submit_response.status_code == 200:
        submitted_expense = submit_response.json()
        print(f"✅ Expense submitted")
        print(f"   New status: {submitted_expense['status']}")
        print(f"   Approval steps created: {len(submitted_expense['approval_steps'])}")
    else:
        print(f"⚠️  Submit failed (expected if no approval rule): {submit_response.status_code}")
        print(f"   Message: {submit_response.json().get('detail', 'Unknown error')}")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_expense_workflow()
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running:")
        print("   uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
