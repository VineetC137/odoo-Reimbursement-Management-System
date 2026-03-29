"""
Simple verification script to test backend core functionality.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_signup():
    """Test signup endpoint."""
    print("\n1. Testing signup...")
    import time
    email = f"admin{int(time.time())}@test.com"
    response = requests.post(
        f"{BASE_URL}/api/auth/signup-initial",
        json={
            "name": "Admin User",
            "email": email,
            "password": "password123",
            "country": "United States"
        }
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Company created: {data['company']['name']}")
        print(f"   ✓ User created: {data['user']['name']} ({data['user']['role']})")
        return data['token'], email
    else:
        print(f"   ✗ Error: {response.text}")
        return None, None

def test_login(email):
    """Test login endpoint."""
    print("\n2. Testing login...")
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": email,
            "password": "password123"
        }
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Login successful: {data['user']['email']}")
        return data['token']
    else:
        print(f"   ✗ Error: {response.text}")
        return None

def test_create_user(token):
    """Test creating a user."""
    print("\n3. Testing user creation...")
    import time
    email = f"employee{int(time.time())}@test.com"
    response = requests.post(
        f"{BASE_URL}/api/admin/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "Employee User",
            "email": email,
            "password": "password123",
            "role": "EMPLOYEE"
        }
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(f"   ✓ User created: {data['name']} ({data['role']})")
        return data['id'], email
    else:
        print(f"   ✗ Error: {response.text}")
        return None, None

def test_create_expense(token):
    """Test creating an expense."""
    print("\n4. Testing expense creation...")
    response = requests.post(
        f"{BASE_URL}/api/employee/expenses",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "category": "Travel",
            "description": "Flight to NYC",
            "expense_date": "2024-01-15",
            "paid_by": "Credit Card",
            "currency_original": "USD",
            "amount_original": 500.0
        }
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        data = response.json()
        print(f"   ✓ Expense created: {data['description']} (${data['amount_original']})")
        return data['id']
    else:
        print(f"   ✗ Error: {response.text}")
        return None

def main():
    """Run all verification tests."""
    print("=" * 60)
    print("Backend Verification Tests")
    print("=" * 60)
    print("\nNote: Make sure the backend server is running on localhost:8000")
    print("Run: uvicorn app.main:app --reload")
    
    try:
        # Test signup
        token, admin_email = test_signup()
        if not token:
            print("\n✗ Signup failed. Stopping tests.")
            return
        
        # Test login
        login_token = test_login(admin_email)
        if not login_token:
            print("\n✗ Login failed. Stopping tests.")
            return
        
        # Test user creation
        user_id, employee_email = test_create_user(token)
        if not user_id:
            print("\n✗ User creation failed. Stopping tests.")
            return
        
        # Test expense creation (using employee token)
        # First login as employee
        print("\n5. Logging in as employee...")
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": employee_email,
                "password": "password123"
            }
        )
        if response.status_code == 200:
            employee_token = response.json()['token']
            print(f"   ✓ Employee login successful")
            
            expense_id = test_create_expense(employee_token)
            if expense_id:
                print("\n" + "=" * 60)
                print("✓ All core functionality tests passed!")
                print("=" * 60)
            else:
                print("\n✗ Expense creation failed.")
        else:
            print(f"   ✗ Employee login failed: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("\n✗ Error: Could not connect to backend server.")
        print("   Make sure the server is running: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")

if __name__ == "__main__":
    main()
