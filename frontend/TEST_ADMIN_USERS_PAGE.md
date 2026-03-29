# Admin Users Page - Manual Test Guide

## Test Setup
1. Backend is running on http://localhost:8000
2. Frontend is running on http://localhost:5173
3. Database is seeded with test data

## Test Credentials
- Admin: admin@acme.com / admin123

## Test Cases

### 1. View Users List
**Steps:**
1. Login as admin@acme.com
2. Navigate to Admin > Users
3. Verify table displays all users with columns:
   - Name
   - Email
   - Role (with colored badges)
   - Manager
   - Created Date
   - Actions (Edit button)

**Expected Result:**
- Should see 4 users: Admin User, Manager User, John Doe, Jane Smith
- Role badges should be colored (purple for ADMIN, blue for MANAGER, gray for EMPLOYEE)
- Manager column shows "Manager User" for employees, "-" for admin/manager
- Created dates are formatted properly

### 2. Filter by Role
**Steps:**
1. Select "Manager" from role filter dropdown
2. Verify only Manager User is displayed
3. Select "Employee" from role filter
4. Verify only John Doe and Jane Smith are displayed
5. Select "All Roles"
6. Verify all users are displayed again

**Expected Result:**
- Filtering works correctly for each role
- Table updates without page reload

### 3. Create New User - Employee
**Steps:**
1. Click "Create User" button
2. Fill in form:
   - Name: "Test Employee"
   - Email: "test.employee@acme.com"
   - Password: "password123"
   - Role: "Employee"
   - Manager: "Manager User"
3. Click "Create User"

**Expected Result:**
- Modal closes
- New user appears in the table
- User has correct manager assigned

### 4. Create New User - Manager
**Steps:**
1. Click "Create User" button
2. Fill in form:
   - Name: "Test Manager"
   - Email: "test.manager@acme.com"
   - Password: "password123"
   - Role: "Manager"
   - Manager: (leave as "No Manager")
3. Click "Create User"

**Expected Result:**
- Modal closes
- New manager appears in the table
- Manager column shows "-"

### 5. Form Validation - Create User
**Steps:**
1. Click "Create User" button
2. Try to submit empty form
3. Verify validation errors appear for required fields
4. Enter invalid email (e.g., "notanemail")
5. Verify email validation error
6. Enter password less than 8 characters
7. Verify password validation error

**Expected Result:**
- Form shows inline validation errors
- Submit button is enabled but form doesn't submit until valid
- Error messages are clear and helpful

### 6. Edit User
**Steps:**
1. Click "Edit" button for "John Doe"
2. Change name to "John Updated"
3. Change role to "Manager"
4. Click "Save Changes"

**Expected Result:**
- Modal closes
- User's name and role are updated in the table
- Changes persist after page refresh

### 7. Edit User - Manager Assignment
**Steps:**
1. Click "Edit" button for "Jane Smith"
2. Change manager to "No Manager"
3. Click "Save Changes"
4. Verify Manager column shows "-"

**Expected Result:**
- Manager assignment is removed
- Table updates correctly

### 8. Email Uniqueness Validation
**Steps:**
1. Click "Create User" button
2. Try to create user with email "admin@acme.com" (already exists)
3. Click "Create User"

**Expected Result:**
- Error message appears: "Email already exists" or similar
- User is not created

### 9. Manager Role Validation
**Steps:**
1. Click "Create User" button
2. Select role "Admin"
3. Try to select a manager from dropdown

**Expected Result:**
- Manager dropdown should be disabled for Admin role
- If somehow submitted, validation error should appear

### 10. Loading States
**Steps:**
1. Refresh the page
2. Observe loading spinner while data loads
3. Create a new user and observe "Creating..." button text
4. Edit a user and observe "Saving..." button text

**Expected Result:**
- Loading spinner appears during data fetch
- Button text changes during submission
- Buttons are disabled during submission

## API Endpoints Tested
- GET /api/admin/users (with and without role filter)
- POST /api/admin/users
- PUT /api/admin/users/:id

## Implementation Checklist
✅ User table with all required columns
✅ Role filter dropdown (All, Admin, Manager, Employee)
✅ Create User button and modal
✅ Create user form with validation
✅ Edit User button and modal
✅ Edit user form with validation
✅ Email format validation
✅ Password length validation (min 8 chars)
✅ Manager dropdown (only shows MANAGER role users)
✅ Manager dropdown disabled for Admin role
✅ API integration with error handling
✅ Loading states
✅ Error messages display
✅ Clean, modern design with Tailwind CSS
✅ Responsive layout
✅ Date formatting
✅ Role badges with colors
