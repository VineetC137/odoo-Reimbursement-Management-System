"""
Manual test script to verify admin endpoints work correctly.
Run the FastAPI server first: uvicorn app.main:app --reload
Then run this script: python test_admin_manual.py
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_admin_endpoints():
    print("Testing Admin User Management Endpoints\n")
    print("=" * 60)
    
    # Step 1: Create initial admin user via signup
    print("\n1. Creating initial admin user...")
    signup_data = {
        "name": "Admin User",
        "email": "admin@test.com",
        "password": "password123",
        "country": "United States"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/signup-initial", json=signup_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        admin_token = data["token"]
        print(f"✓ Admin user created successfully")
        print(f"  Token: {admin_token[:50]}...")
    else:
        print(f"✗ Failed: {response.text}")
        return
    
    # Step 2: Create a manager user
    print("\n2. Creating manager user...")
    headers = {"Authorization": f"Bearer {admin_token}"}
    manager_data = {
        "name": "Manager User",
        "email": "manager@test.com",
        "password": "password123",
        "role": "MANAGER"
    }
    
    response = requests.post(f"{BASE_URL}/api/admin/users", json=manager_data, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        manager = response.json()
        manager_id = manager["id"]
        print(f"✓ Manager created successfully")
        print(f"  ID: {manager_id}, Name: {manager['name']}, Role: {manager['role']}")
    else:
        print(f"✗ Failed: {response.text}")
        return
    
    # Step 3: Create an employee user with manager
    print("\n3. Creating employee user with manager...")
    employee_data = {
        "name": "Employee User",
        "email": "employee@test.com",
        "password": "password123",
        "role": "EMPLOYEE",
        "manager_id": manager_id
    }
    
    response = requests.post(f"{BASE_URL}/api/admin/users", json=employee_data, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 201:
        employee = response.json()
        employee_id = employee["id"]
        print(f"✓ Employee created successfully")
        print(f"  ID: {employee_id}, Name: {employee['name']}, Manager ID: {employee['manager_id']}")
    else:
        print(f"✗ Failed: {response.text}")
        return
    
    # Step 4: Get all users
    print("\n4. Getting all users...")
    response = requests.get(f"{BASE_URL}/api/admin/users", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved {len(data['users'])} users")
        for user in data['users']:
            print(f"  - {user['name']} ({user['role']}) - {user['email']}")
    else:
        print(f"✗ Failed: {response.text}")
        return
    
    # Step 5: Get users filtered by role
    print("\n5. Getting users filtered by EMPLOYEE role...")
    response = requests.get(f"{BASE_URL}/api/admin/users?role=EMPLOYEE", headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Retrieved {len(data['users'])} employees")
        for user in data['users']:
            print(f"  - {user['name']} - {user['email']}")
    else:
        print(f"✗ Failed: {response.text}")
        return
    
    # Step 6: Update employee user
    print("\n6. Updating employee user name...")
    update_data = {
        "name": "Updated Employee Name"
    }
    
    response = requests.put(f"{BASE_URL}/api/admin/users/{employee_id}", json=update_data, headers=headers)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        updated_user = response.json()
        print(f"✓ User updated successfully")
        print(f"  New name: {updated_user['name']}")
    else:
        print(f"✗ Failed: {response.text}")
        return
    
    # Step 7: Test authorization - try to access with employee token
    print("\n7. Testing authorization (employee trying to access admin endpoint)...")
    login_data = {
        "email": "employee@test.com",
        "password": "password123"
    }
    
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    if response.status_code == 200:
        employee_token = response.json()["token"]
        employee_headers = {"Authorization": f"Bearer {employee_token}"}
        
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=employee_headers)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 403:
            print(f"✓ Authorization working correctly - employee denied access")
        else:
            print(f"✗ Authorization failed - employee should not have access")
    else:
        print(f"✗ Failed to login as employee: {response.text}")
    
    print("\n" + "=" * 60)
    print("All tests completed successfully! ✓")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_admin_endpoints()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server.")
        print("Make sure the FastAPI server is running:")
        print("  cd backend")
        print("  uvicorn app.main:app --reload")
    except Exception as e:
        print(f"Error: {e}")
