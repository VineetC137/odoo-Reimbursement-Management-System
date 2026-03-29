# Testing Guide - Reimbursement Management System

## 🚀 Quick Start

Your application is now running!

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📋 Test Accounts

The database has been seeded with the following test accounts:

| Role | Email | Password | Description |
|------|-------|----------|-------------|
| **Admin** | admin@acme.com | admin123 | Full system access, user management, approval rules |
| **Manager** | manager@acme.com | manager123 | Approve/reject expenses, view team expenses |
| **Employee 1** | john.doe@acme.com | employee123 | Create and submit expenses |
| **Employee 2** | jane.smith@acme.com | employee123 | Create and submit expenses |

## 🧪 Complete Testing Workflow

### Phase 1: Authentication & User Management (Admin)

#### 1.1 Login as Admin
1. Open http://localhost:5173
2. Login with: `admin@acme.com` / `admin123`
3. ✅ Verify you're redirected to Admin Dashboard
4. ✅ Check sidebar shows: Dashboard, Users, Approval Rules, Expenses

#### 1.2 User Management
1. Click **"Users"** in sidebar
2. ✅ Verify you see 4 users (1 admin, 1 manager, 2 employees)
3. Click **"Create User"** button
4. Fill in form:
   - Name: `Test Employee`
   - Email: `test@acme.com`
   - Password: `test123456`
   - Role: `Employee`
   - Manager: Select `manager@acme.com`
5. Click **"Create User"**
6. ✅ Verify new user appears in table
7. Click **"Edit"** on the new user
8. Change name to `Test Employee Updated`
9. ✅ Verify name updates in table

#### 1.3 Approval Rules Configuration
1. Click **"Approval Rules"** in sidebar
2. ✅ Verify current approval rule is displayed
3. Modify the rule:
   - Name: `Updated Approval Rule`
   - Mode: Select `PERCENTAGE`
   - Percentage Threshold: Set to `50%`
   - Toggle **"Include Manager as Approver"** ON
4. In approvers table:
   - ✅ Verify manager appears in list
   - Set sequence numbers (1, 2, 3...)
   - Check/uncheck "Required" as needed
5. Click **"Save Approval Rule"**
6. ✅ Verify success message appears

#### 1.4 Admin Expense Overview
1. Click **"Expenses"** in sidebar
2. ✅ Verify you see all expenses from all employees
3. Test filters:
   - Filter by Status: Select `DRAFT`
   - Filter by Employee: Select an employee
   - ✅ Verify table updates
4. For an expense with status `WAITING_APPROVAL`:
   - Click **"Force Approve"**
   - ✅ Verify status changes to `APPROVED`
5. Logout (click user menu → Logout)

---

### Phase 2: Employee Expense Creation & Submission

#### 2.1 Login as Employee
1. Login with: `john.doe@acme.com` / `employee123`
2. ✅ Verify you're redirected to Employee Dashboard
3. ✅ Check sidebar shows: Dashboard, My Expenses

#### 2.2 Create Draft Expense
1. Click **"My Expenses"** in sidebar
2. Click **"Create Expense"** button
3. Fill in the form:
   - Description: `Team lunch at restaurant`
   - Category: `Meals`
   - Paid By: `Personal Card`
   - Expense Date: Select today's date
   - Currency: `USD`
   - Amount: `150.50`
4. Click **"Save Draft"**
5. ✅ Verify redirected to expenses list
6. ✅ Verify new expense appears with status `DRAFT`

#### 2.3 Edit Draft Expense
1. Click on the draft expense row
2. ✅ Verify form is editable (fields not disabled)
3. Change amount to `175.75`
4. Click **"Save Draft"**
5. ✅ Verify amount updated in list

#### 2.4 Submit Expense for Approval
1. Click on the draft expense again
2. Click **"Submit for Approval"**
3. ✅ Verify redirected to expenses list
4. ✅ Verify status changed to `WAITING_APPROVAL` or `IN_PROGRESS`
5. Click on the submitted expense
6. ✅ Verify form fields are now disabled (read-only)
7. ✅ Verify **Approval Timeline** section appears below form
8. ✅ Check approval steps show:
   - Approver names
   - Status badges (PENDING)
   - Sequence numbers

#### 2.5 Create Multiple Expenses
1. Create 2-3 more expenses with different:
   - Categories (Travel, Office Supplies, Software)
   - Currencies (EUR, GBP, JPY)
   - Amounts
2. Submit at least 2 of them for approval
3. Leave 1 as draft

#### 2.6 Test Expense Tabs
1. Click **"Drafts"** tab
   - ✅ Verify only draft expenses show
2. Click **"Waiting approval"** tab
   - ✅ Verify only submitted expenses show
3. Click **"All"** tab
   - ✅ Verify all expenses show
4. Logout

---

### Phase 3: Manager Approval Workflow

#### 3.1 Login as Manager
1. Login with: `manager@acme.com` / `manager123`
2. ✅ Verify you're redirected to Manager Dashboard
3. ✅ Check sidebar shows: Dashboard, Approvals

#### 3.2 View Pending Approvals
1. Click **"Approvals"** in sidebar
2. ✅ Verify you see pending expenses from employees
3. ✅ Check table shows:
   - Employee name
   - Description
   - Amount with currency
   - Expense date
   - Approve/Reject buttons

#### 3.3 Approve an Expense
1. Find an expense to approve
2. Click **"Approve"** button
3. ✅ Verify success message appears
4. ✅ Verify expense disappears from pending list (or status updates)

#### 3.4 Reject an Expense
1. Find another expense
2. Click **"Reject"** button
3. ✅ Verify modal opens asking for comment
4. Try clicking **"Reject Expense"** without entering comment
   - ✅ Verify validation error appears
5. Enter comment: `Missing receipt, please resubmit with documentation`
6. Click **"Reject Expense"**
7. ✅ Verify success message appears
8. ✅ Verify expense disappears from pending list

#### 3.5 Verify Approval Workflow
1. Logout and login as employee (`john.doe@acme.com`)
2. Go to **"My Expenses"**
3. Click **"Approved"** tab
   - ✅ Verify approved expense appears
4. Click **"Rejected"** tab
   - ✅ Verify rejected expense appears
5. Click on rejected expense
6. ✅ Verify approval timeline shows:
   - Manager name
   - Status: REJECTED (red badge)
   - Rejection comment
   - Timestamp
7. Logout

---

### Phase 4: Multi-Currency & FX Conversion

#### 4.1 Test Currency Conversion
1. Login as admin (`admin@acme.com`)
2. Go to **"Expenses"**
3. ✅ Look for expenses with different currencies
4. ✅ Verify each expense shows:
   - Original amount in original currency
   - Converted amount in company base currency (if different)

#### 4.2 Create Expense in Foreign Currency
1. Logout and login as employee
2. Create new expense:
   - Description: `Conference in Europe`
   - Category: `Travel`
   - Currency: `EUR`
   - Amount: `500.00`
3. Submit for approval
4. ✅ Verify expense is created successfully
5. ✅ Backend should convert EUR to company base currency (USD)

---

### Phase 5: Admin Force Actions

#### 5.1 Force Approve
1. Login as admin
2. Go to **"Expenses"**
3. Find an expense with status `WAITING_APPROVAL`
4. Click **"Force Approve"**
5. ✅ Verify status immediately changes to `APPROVED`
6. ✅ Verify no manager approval was needed

#### 5.2 Force Reject
1. Find another expense with status `WAITING_APPROVAL`
2. Click **"Force Reject"**
3. ✅ Verify status immediately changes to `REJECTED`

---

### Phase 6: Edge Cases & Validation

#### 6.1 Form Validation
1. Login as employee
2. Try to create expense with:
   - Empty description → ✅ Should show error
   - Amount = 0 → ✅ Should show error
   - Amount = -10 → ✅ Should show error
   - Future date → ✅ Should show error
3. ✅ Verify submit button is disabled until form is valid

#### 6.2 Edit Restrictions
1. Create and submit an expense
2. Try to click on the submitted expense
3. ✅ Verify all form fields are disabled
4. ✅ Verify only "Back to Expenses" button is shown
5. ✅ Verify no Save/Submit buttons appear

#### 6.3 Role-Based Access
1. Login as employee
2. Try to manually navigate to:
   - http://localhost:5173/admin/users
   - ✅ Should redirect or show access denied
3. Login as manager
4. Try to navigate to:
   - http://localhost:5173/admin/approval-rules
   - ✅ Should redirect or show access denied

---

### Phase 7: API Testing (Optional)

#### 7.1 Test API Documentation
1. Open http://localhost:8000/docs
2. ✅ Verify Swagger UI loads
3. Expand **"auth"** section
4. Try **POST /api/auth/login**:
   - Click "Try it out"
   - Enter: `{"email": "admin@acme.com", "password": "admin123"}`
   - Click "Execute"
   - ✅ Verify you get a token in response

#### 7.2 Test Authenticated Endpoints
1. Copy the token from login response
2. Click **"Authorize"** button at top
3. Enter: `Bearer <your-token>`
4. Try **GET /api/admin/users**
5. ✅ Verify you get list of users

---

## 🐛 Common Issues & Solutions

### Backend Issues

**Issue**: Backend won't start
```bash
# Solution: Check if port 8000 is already in use
netstat -ano | findstr :8000
# Kill the process if needed
```

**Issue**: Database errors
```bash
# Solution: Reset database
cd backend
rm reimbursement.db
alembic upgrade head
python seed.py
```

### Frontend Issues

**Issue**: "Network Error" or "ECONNREFUSED"
- ✅ Verify backend is running on http://localhost:8000
- ✅ Check `frontend/.env` has correct `VITE_API_BASE_URL`

**Issue**: Login doesn't work
- ✅ Verify database is seeded with test users
- ✅ Check browser console for errors (F12)

---

## 📊 Success Criteria Checklist

### Core Functionality
- [ ] Users can login with different roles
- [ ] Admin can create/edit users
- [ ] Admin can configure approval rules
- [ ] Employees can create draft expenses
- [ ] Employees can edit draft expenses
- [ ] Employees can submit expenses for approval
- [ ] Managers can see pending approvals
- [ ] Managers can approve expenses
- [ ] Managers can reject expenses with comments
- [ ] Admin can force approve/reject expenses
- [ ] Multi-currency support works
- [ ] Approval timeline displays correctly
- [ ] Role-based access control works

### UI/UX
- [ ] All pages load without errors
- [ ] Forms validate input correctly
- [ ] Loading spinners show during API calls
- [ ] Success/error messages display
- [ ] Tables are sortable/filterable
- [ ] Navigation works correctly
- [ ] Logout works properly

### Data Integrity
- [ ] Draft expenses can be edited
- [ ] Submitted expenses cannot be edited
- [ ] Approval workflow follows rules
- [ ] Currency conversion is accurate
- [ ] Timestamps are recorded correctly

---

## 🎯 Quick Test Scenarios

### Scenario 1: Complete Expense Flow (5 minutes)
1. Login as employee → Create expense → Submit
2. Login as manager → Approve expense
3. Login as employee → Verify approved status

### Scenario 2: Rejection Flow (3 minutes)
1. Login as employee → Create and submit expense
2. Login as manager → Reject with comment
3. Login as employee → View rejection reason

### Scenario 3: Admin Override (2 minutes)
1. Login as employee → Submit expense
2. Login as admin → Force approve
3. Verify status changed immediately

---

## 📝 Notes

- All test data is in SQLite database: `backend/reimbursement.db`
- To reset everything: Delete database and run `python seed.py`
- Check browser console (F12) for any JavaScript errors
- Check backend terminal for API errors
- API docs available at: http://localhost:8000/docs

---

## 🎉 You're All Set!

Your Reimbursement Management System is fully functional. Follow the testing phases above to verify all features work correctly. Good luck with your hackathon! 🚀
