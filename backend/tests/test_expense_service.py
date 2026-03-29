import pytest
from unittest.mock import patch, MagicMock
from datetime import date, datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.services.expense_service import ExpenseService
from app.models import Expense, Company, User, ExpenseReceipt


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_company():
    """Create a mock company."""
    company = MagicMock(spec=Company)
    company.id = 1
    company.name = "Test Company"
    company.base_currency = "USD"
    return company


@pytest.fixture
def mock_employee():
    """Create a mock employee user."""
    employee = MagicMock(spec=User)
    employee.id = 1
    employee.company_id = 1
    employee.role = "EMPLOYEE"
    employee.manager_id = 2
    return employee


class TestExpenseServiceCreate:
    """Tests for ExpenseService.create_expense."""
    
    def test_create_expense_success_same_currency(self, mock_db, mock_company):
        """Test creating expense when currency matches company base currency."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_company
        
        expense = ExpenseService.create_expense(
            db=mock_db,
            company_id=1,
            employee_id=1,
            category="Travel",
            description="Flight to NYC",
            expense_date=date(2024, 1, 15),
            paid_by="Credit Card",
            currency_original="USD",
            amount_original=500.0
        )
        
        # Verify expense was created with DRAFT status
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Get the expense that was added
        added_expense = mock_db.add.call_args[0][0]
        assert added_expense.status == "DRAFT"
        assert added_expense.amount_original == 500.0
        assert added_expense.amount_company_currency == 500.0  # Same currency
        assert added_expense.currency_original == "USD"
    
    def test_create_expense_success_with_fx_conversion(self, mock_db, mock_company):
        """Test creating expense with FX conversion."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_company
        
        with patch('app.services.expense_service.FXService.convert_amount') as mock_convert:
            mock_convert.return_value = 425.0  # 500 EUR = 425 USD
            
            expense = ExpenseService.create_expense(
                db=mock_db,
                company_id=1,
                employee_id=1,
                category="Travel",
                description="Flight to Paris",
                expense_date=date(2024, 1, 15),
                paid_by="Credit Card",
                currency_original="EUR",
                amount_original=500.0
            )
            
            # Verify FX conversion was called
            mock_convert.assert_called_once_with(500.0, "EUR", "USD")
            
            # Verify expense was created
            added_expense = mock_db.add.call_args[0][0]
            assert added_expense.amount_company_currency == 425.0
    
    def test_create_expense_empty_description(self, mock_db, mock_company):
        """Test error when description is empty."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_company
        
        with pytest.raises(ValueError, match="Description cannot be empty"):
            ExpenseService.create_expense(
                db=mock_db,
                company_id=1,
                employee_id=1,
                category="Travel",
                description="   ",
                expense_date=date(2024, 1, 15),
                paid_by="Credit Card",
                currency_original="USD",
                amount_original=500.0
            )
    
    def test_create_expense_negative_amount(self, mock_db, mock_company):
        """Test error when amount is negative."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_company
        
        with pytest.raises(ValueError, match="Amount must be positive"):
            ExpenseService.create_expense(
                db=mock_db,
                company_id=1,
                employee_id=1,
                category="Travel",
                description="Flight",
                expense_date=date(2024, 1, 15),
                paid_by="Credit Card",
                currency_original="USD",
                amount_original=-100.0
            )
    
    def test_create_expense_zero_amount(self, mock_db, mock_company):
        """Test error when amount is zero."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_company
        
        with pytest.raises(ValueError, match="Amount must be positive"):
            ExpenseService.create_expense(
                db=mock_db,
                company_id=1,
                employee_id=1,
                category="Travel",
                description="Flight",
                expense_date=date(2024, 1, 15),
                paid_by="Credit Card",
                currency_original="USD",
                amount_original=0.0
            )
    
    def test_create_expense_future_date(self, mock_db, mock_company):
        """Test error when expense date is in the future."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_company
        
        from datetime import timedelta
        future_date = date.today() + timedelta(days=1)
        
        with pytest.raises(ValueError, match="Expense date cannot be in the future"):
            ExpenseService.create_expense(
                db=mock_db,
                company_id=1,
                employee_id=1,
                category="Travel",
                description="Flight",
                expense_date=future_date,
                paid_by="Credit Card",
                currency_original="USD",
                amount_original=500.0
            )
    
    def test_create_expense_fx_api_failure(self, mock_db, mock_company):
        """Test error handling when FX API fails."""
        mock_db.query.return_value.filter.return_value.first.return_value = mock_company
        
        with patch('app.services.expense_service.FXService.convert_amount') as mock_convert:
            mock_convert.side_effect = RuntimeError("API unavailable")
            
            with pytest.raises(HTTPException) as exc_info:
                ExpenseService.create_expense(
                    db=mock_db,
                    company_id=1,
                    employee_id=1,
                    category="Travel",
                    description="Flight",
                    expense_date=date(2024, 1, 15),
                    paid_by="Credit Card",
                    currency_original="EUR",
                    amount_original=500.0
                )
            
            assert exc_info.value.status_code == 503
            assert "Currency conversion failed" in str(exc_info.value.detail)


class TestExpenseServiceUpdate:
    """Tests for ExpenseService.update_expense."""
    
    def test_update_expense_success(self, mock_db, mock_company):
        """Test updating a DRAFT expense."""
        mock_expense = MagicMock(spec=Expense)
        mock_expense.id = 1
        mock_expense.status = "DRAFT"
        mock_expense.company_id = 1
        mock_expense.employee_id = 1
        mock_expense.currency_original = "USD"
        mock_expense.amount_original = 500.0
        
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            mock_expense,  # First call for expense lookup
            mock_company   # Second call for company lookup
        ]
        
        updated = ExpenseService.update_expense(
            db=mock_db,
            expense_id=1,
            employee_id=1,
            description="Updated description"
        )
        
        assert mock_expense.description == "Updated description"
        mock_db.commit.assert_called_once()
    
    def test_update_expense_not_found(self, mock_db):
        """Test error when expense not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            ExpenseService.update_expense(
                db=mock_db,
                expense_id=999,
                employee_id=1,
                description="Updated"
            )
        
        assert exc_info.value.status_code == 404
    
    def test_update_expense_not_draft(self, mock_db):
        """Test error when trying to update non-DRAFT expense."""
        mock_expense = MagicMock(spec=Expense)
        mock_expense.status = "APPROVED"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_expense
        
        with pytest.raises(HTTPException) as exc_info:
            ExpenseService.update_expense(
                db=mock_db,
                expense_id=1,
                employee_id=1,
                description="Updated"
            )
        
        assert exc_info.value.status_code == 400
        assert "Only DRAFT expenses can be edited" in str(exc_info.value.detail)


class TestExpenseServiceGet:
    """Tests for ExpenseService.get_expense and get_expenses."""
    
    def test_get_expense_success(self, mock_db):
        """Test getting a single expense."""
        mock_expense = MagicMock(spec=Expense)
        mock_expense.id = 1
        mock_expense.employee_id = 1
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_expense
        
        expense = ExpenseService.get_expense(db=mock_db, expense_id=1, user_id=1)
        
        assert expense == mock_expense
    
    def test_get_expense_not_found(self, mock_db):
        """Test error when expense not found."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            ExpenseService.get_expense(db=mock_db, expense_id=999, user_id=1)
        
        assert exc_info.value.status_code == 404
    
    def test_get_expense_unauthorized(self, mock_db):
        """Test error when user tries to access another user's expense."""
        mock_expense = MagicMock(spec=Expense)
        mock_expense.employee_id = 2  # Different employee
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_expense
        
        with pytest.raises(HTTPException) as exc_info:
            ExpenseService.get_expense(db=mock_db, expense_id=1, user_id=1)
        
        assert exc_info.value.status_code == 404
    
    def test_get_expenses_with_filters(self, mock_db):
        """Test getting expenses with filters."""
        mock_query = MagicMock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        
        expenses = ExpenseService.get_expenses(
            db=mock_db,
            company_id=1,
            employee_id=1,
            status="DRAFT",
            date_from=date(2024, 1, 1),
            date_to=date(2024, 1, 31)
        )
        
        # Verify filters were applied
        assert mock_query.filter.call_count >= 4  # company, employee, status, dates
        assert expenses == []


class TestExpenseServiceSubmit:
    """Tests for ExpenseService.submit_expense."""
    
    def test_submit_expense_success(self, mock_db, mock_employee):
        """Test submitting a DRAFT expense."""
        mock_expense = MagicMock(spec=Expense)
        mock_expense.id = 1
        mock_expense.status = "DRAFT"
        mock_expense.employee_id = 1
        mock_expense.company_id = 1
        
        mock_rule = MagicMock()
        mock_rule.id = 1
        
        # Setup query mocks
        query_results = [mock_expense, mock_employee]
        mock_db.query.return_value.filter.return_value.first.side_effect = query_results
        
        with patch('app.services.approval_service.ApprovalService.get_current_rule') as mock_get_rule:
            with patch('app.services.approval_service.ApprovalService.create_approval_steps') as mock_create_steps:
                mock_get_rule.return_value = mock_rule
                mock_create_steps.return_value = [MagicMock()]  # One step
                
                expense = ExpenseService.submit_expense(
                    db=mock_db,
                    expense_id=1,
                    employee_id=1
                )
                
                # Verify approval workflow was triggered
                mock_get_rule.assert_called_once()
                mock_create_steps.assert_called_once()
                
                # Verify status was updated
                assert mock_expense.status == "WAITING_APPROVAL"
    
    def test_submit_expense_not_draft(self, mock_db):
        """Test error when trying to submit non-DRAFT expense."""
        mock_expense = MagicMock(spec=Expense)
        mock_expense.status = "APPROVED"
        mock_expense.employee_id = 1
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_expense
        
        with pytest.raises(HTTPException) as exc_info:
            ExpenseService.submit_expense(
                db=mock_db,
                expense_id=1,
                employee_id=1
            )
        
        assert exc_info.value.status_code == 400
        assert "Only DRAFT expenses can be submitted" in str(exc_info.value.detail)
    
    def test_submit_expense_no_approval_rule(self, mock_db):
        """Test error when no approval rule is configured."""
        mock_expense = MagicMock(spec=Expense)
        mock_expense.status = "DRAFT"
        mock_expense.employee_id = 1
        mock_expense.company_id = 1
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_expense
        
        with patch('app.services.approval_service.ApprovalService.get_current_rule') as mock_get_rule:
            mock_get_rule.return_value = None
            
            with pytest.raises(HTTPException) as exc_info:
                ExpenseService.submit_expense(
                    db=mock_db,
                    expense_id=1,
                    employee_id=1
                )
            
            assert exc_info.value.status_code == 400
            assert "No approval rule configured" in str(exc_info.value.detail)


class TestExpenseServiceUploadReceipt:
    """Tests for ExpenseService.upload_receipt."""
    
    def test_upload_receipt_success(self, mock_db):
        """Test uploading a receipt file."""
        mock_expense = MagicMock(spec=Expense)
        mock_expense.id = 1
        mock_expense.employee_id = 1
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_expense
        
        mock_file = MagicMock()
        mock_file.filename = "receipt.jpg"
        mock_file.file.tell.return_value = 1024  # 1 KB
        mock_file.file.read.return_value = b"fake image data"
        
        with patch('os.makedirs'), patch('builtins.open', MagicMock()):
            receipt = ExpenseService.upload_receipt(
                db=mock_db,
                expense_id=1,
                employee_id=1,
                file=mock_file
            )
            
            mock_db.add.assert_called_once()
            mock_db.commit.assert_called_once()
    
    def test_upload_receipt_file_too_large(self, mock_db):
        """Test error when file exceeds size limit."""
        mock_expense = MagicMock(spec=Expense)
        mock_expense.employee_id = 1
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_expense
        
        mock_file = MagicMock()
        mock_file.filename = "receipt.jpg"
        mock_file.file.tell.return_value = 11 * 1024 * 1024  # 11 MB
        
        with pytest.raises(HTTPException) as exc_info:
            ExpenseService.upload_receipt(
                db=mock_db,
                expense_id=1,
                employee_id=1,
                file=mock_file
            )
        
        assert exc_info.value.status_code == 400
        assert "File size exceeds maximum" in str(exc_info.value.detail)
    
    def test_upload_receipt_invalid_format(self, mock_db):
        """Test error when file format is not allowed."""
        mock_expense = MagicMock(spec=Expense)
        mock_expense.employee_id = 1
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_expense
        
        mock_file = MagicMock()
        mock_file.filename = "receipt.txt"
        mock_file.file.tell.return_value = 1024
        
        with pytest.raises(HTTPException) as exc_info:
            ExpenseService.upload_receipt(
                db=mock_db,
                expense_id=1,
                employee_id=1,
                file=mock_file
            )
        
        assert exc_info.value.status_code == 400
        assert "Invalid file format" in str(exc_info.value.detail)
