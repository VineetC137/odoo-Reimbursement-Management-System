import pytest
from unittest.mock import patch, MagicMock
from datetime import date, datetime

from app.main import app
from app.models import Expense, User
from app.dependencies import TokenPayload, require_employee


@pytest.fixture
def mock_token_payload():
    """Create a mock token payload for an employee."""
    payload = TokenPayload(user_id=1, company_id=1, role="EMPLOYEE")
    return payload


@pytest.fixture
def mock_employee_auth(mock_token_payload):
    """Override the require_employee dependency."""
    def override_require_employee():
        return mock_token_payload
    
    app.dependency_overrides[require_employee] = override_require_employee
    yield
    app.dependency_overrides.pop(require_employee, None)


@pytest.fixture
def mock_expense():
    """Create a mock expense."""
    expense = MagicMock(spec=Expense)
    expense.id = 1
    expense.company_id = 1
    expense.employee_id = 1
    expense.category = "Travel"
    expense.description = "Flight to NYC"
    expense.expense_date = date(2024, 1, 15)
    expense.paid_by = "Credit Card"
    expense.currency_original = "USD"
    expense.amount_original = 500.0
    expense.amount_company_currency = 500.0
    expense.status = "DRAFT"
    expense.created_at = datetime(2024, 1, 15, 10, 0, 0)
    expense.approval_steps = []
    expense.receipts = []
    return expense


class TestEmployeeExpenseEndpoints:
    """Tests for employee expense endpoints."""
    
    def test_get_expenses_success(self, client, mock_employee_auth, mock_expense, db_session):
        """Test getting expenses list."""
        with patch('app.routers.employee.ExpenseService.get_expenses') as mock_get:
            mock_get.return_value = [mock_expense]
            
            # Create a test user in the database
            from app.models import User, Company
            company = Company(id=1, name="Test Company", country="US", base_currency="USD")
            user = User(id=1, company_id=1, name="John Doe", email="john@example.com", 
                       password_hash="hash", role="EMPLOYEE")
            db_session.add(company)
            db_session.add(user)
            db_session.commit()
            
            response = client.get("/api/employee/expenses")
            
            assert response.status_code == 200
            data = response.json()
            assert "expenses" in data
            assert len(data["expenses"]) == 1
    
    def test_get_expenses_with_status_filter(self, client, mock_employee_auth, mock_expense, db_session):
        """Test getting expenses with status filter."""
        with patch('app.routers.employee.ExpenseService.get_expenses') as mock_get:
            mock_get.return_value = [mock_expense]
            
            # Create a test user in the database
            from app.models import User, Company
            company = Company(id=1, name="Test Company", country="US", base_currency="USD")
            user = User(id=1, company_id=1, name="John Doe", email="john@example.com", 
                       password_hash="hash", role="EMPLOYEE")
            db_session.add(company)
            db_session.add(user)
            db_session.commit()
                            response = client.get("/api/employee/expenses?status=DRAFT")
                        
                        assert response.status_code == 200
                        mock_get.assert_called_once()
                        # Verify status filter was passed
                        call_kwargs = mock_get.call_args[1]
                        assert call_kwargs['status'] == 'DRAFT'
    
    def test_get_expense_by_id_success(self, mock_token_payload, mock_expense):
        """Test getting a single expense by ID."""
        with patch('app.routers.employee.require_employee', return_value=mock_token_payload):
            with patch('app.routers.employee.get_db'):
                with patch('app.routers.employee.ExpenseService.get_expense') as mock_get:
                    with patch('app.routers.employee.User') as mock_user_class:
                        mock_get.return_value = mock_expense
                        
                        mock_user = MagicMock()
                        mock_user.name = "John Doe"
                        mock_db = MagicMock()
                        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
                        
                        with patch('app.routers.employee.get_db', return_value=mock_db):
                            response = client.get("/api/employee/expenses/1")
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert data["id"] == 1
                        assert data["description"] == "Flight to NYC"
    
    def test_create_expense_success(self, mock_token_payload, mock_expense):
        """Test creating a new expense."""
        with patch('app.routers.employee.require_employee', return_value=mock_token_payload):
            with patch('app.routers.employee.get_db'):
                with patch('app.routers.employee.ExpenseService.create_expense') as mock_create:
                    with patch('app.routers.employee.User') as mock_user_class:
                        mock_create.return_value = mock_expense
                        
                        mock_user = MagicMock()
                        mock_user.name = "John Doe"
                        mock_db = MagicMock()
                        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
                        
                        with patch('app.routers.employee.get_db', return_value=mock_db):
                            response = client.post("/api/employee/expenses", json={
                                "category": "Travel",
                                "description": "Flight to NYC",
                                "expense_date": "2024-01-15",
                                "paid_by": "Credit Card",
                                "currency_original": "USD",
                                "amount_original": 500.0
                            })
                        
                        assert response.status_code == 201
                        data = response.json()
                        assert data["description"] == "Flight to NYC"
    
    def test_create_expense_validation_error(self, mock_token_payload):
        """Test creating expense with invalid data."""
        with patch('app.routers.employee.require_employee', return_value=mock_token_payload):
            with patch('app.routers.employee.get_db'):
                response = client.post("/api/employee/expenses", json={
                    "category": "Travel",
                    "description": "",  # Empty description
                    "expense_date": "2024-01-15",
                    "paid_by": "Credit Card",
                    "currency_original": "USD",
                    "amount_original": 500.0
                })
                
                assert response.status_code == 422  # Validation error
    
    def test_update_expense_success(self, mock_token_payload, mock_expense):
        """Test updating an expense."""
        with patch('app.routers.employee.require_employee', return_value=mock_token_payload):
            with patch('app.routers.employee.get_db'):
                with patch('app.routers.employee.ExpenseService.update_expense') as mock_update:
                    with patch('app.routers.employee.User') as mock_user_class:
                        mock_expense.description = "Updated description"
                        mock_update.return_value = mock_expense
                        
                        mock_user = MagicMock()
                        mock_user.name = "John Doe"
                        mock_db = MagicMock()
                        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
                        
                        with patch('app.routers.employee.get_db', return_value=mock_db):
                            response = client.put("/api/employee/expenses/1", json={
                                "description": "Updated description"
                            })
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert data["description"] == "Updated description"
    
    def test_submit_expense_success(self, mock_token_payload, mock_expense):
        """Test submitting an expense."""
        with patch('app.routers.employee.require_employee', return_value=mock_token_payload):
            with patch('app.routers.employee.get_db'):
                with patch('app.routers.employee.ExpenseService.submit_expense') as mock_submit:
                    with patch('app.routers.employee.User') as mock_user_class:
                        mock_expense.status = "WAITING_APPROVAL"
                        mock_submit.return_value = mock_expense
                        
                        mock_user = MagicMock()
                        mock_user.name = "John Doe"
                        mock_db = MagicMock()
                        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
                        
                        with patch('app.routers.employee.get_db', return_value=mock_db):
                            response = client.post("/api/employee/expenses/1/submit")
                        
                        assert response.status_code == 200
                        data = response.json()
                        assert data["status"] == "WAITING_APPROVAL"
    
    def test_upload_receipt_success(self, mock_token_payload):
        """Test uploading a receipt."""
        with patch('app.routers.employee.require_employee', return_value=mock_token_payload):
            with patch('app.routers.employee.get_db'):
                with patch('app.routers.employee.ExpenseService.upload_receipt') as mock_upload:
                    mock_receipt = MagicMock()
                    mock_receipt.id = 1
                    mock_receipt.expense_id = 1
                    mock_receipt.file_path = "uploads/receipts/test.jpg"
                    mock_receipt.original_filename = "receipt.jpg"
                    mock_receipt.uploaded_at = datetime(2024, 1, 15, 10, 0, 0)
                    mock_upload.return_value = mock_receipt
                    
                    response = client.post(
                        "/api/employee/expenses/1/upload-receipt",
                        files={"file": ("receipt.jpg", b"fake image data", "image/jpeg")}
                    )
                    
                    assert response.status_code == 200
                    data = response.json()
                    assert data["original_filename"] == "receipt.jpg"
    
    def test_unauthorized_access(self):
        """Test that endpoints require authentication."""
        response = client.get("/api/employee/expenses")
        assert response.status_code == 403  # No auth token
    
    def test_wrong_role_access(self):
        """Test that endpoints require EMPLOYEE role."""
        from app.dependencies import TokenPayload
        admin_payload = TokenPayload(user_id=1, company_id=1, role="ADMIN")
        
        with patch('app.routers.employee.get_current_user', return_value=admin_payload):
            response = client.get("/api/employee/expenses")
            assert response.status_code == 403  # Wrong role
