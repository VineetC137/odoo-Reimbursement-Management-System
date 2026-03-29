from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List
from datetime import date, datetime
from fastapi import HTTPException, UploadFile
import os
import uuid

from app.models import Expense, ExpenseReceipt, User
from app.services.fx_service import FXService


class ExpenseService:
    """Service for managing expenses."""
    
    # Directory for storing receipt files
    UPLOAD_DIR = "uploads/receipts"
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    
    @classmethod
    def _ensure_upload_dir(cls):
        """Ensure upload directory exists."""
        os.makedirs(cls.UPLOAD_DIR, exist_ok=True)
    
    @classmethod
    def create_expense(
        cls,
        db: Session,
        company_id: int,
        employee_id: int,
        category: str,
        description: str,
        expense_date: date,
        paid_by: str,
        currency_original: str,
        amount_original: float
    ) -> Expense:
        """
        Create a new expense with DRAFT status and FX conversion.
        
        Args:
            db: Database session
            company_id: Company ID
            employee_id: Employee user ID
            category: Expense category
            description: Expense description
            expense_date: Date of expense
            paid_by: Payment method
            currency_original: Original currency ISO code
            amount_original: Original amount
            
        Returns:
            Created Expense object
            
        Raises:
            ValueError: If validation fails
            HTTPException: If FX conversion fails (503)
        """
        # Validate inputs
        if not description or not description.strip():
            raise ValueError("Description cannot be empty")
        
        if amount_original <= 0:
            raise ValueError("Amount must be positive")
        
        if expense_date > date.today():
            raise ValueError("Expense date cannot be in the future")
        
        # Get company base currency
        from app.models import Company
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise ValueError("Company not found")
        
        base_currency = company.base_currency
        
        # Convert amount to company currency
        try:
            if currency_original.upper() == base_currency.upper():
                amount_company_currency = amount_original
            else:
                amount_company_currency = FXService.convert_amount(
                    amount_original,
                    currency_original,
                    base_currency
                )
        except (ValueError, RuntimeError) as e:
            raise HTTPException(
                status_code=503,
                detail=f"Currency conversion failed: {str(e)}"
            )
        
        # Create expense with DRAFT status
        expense = Expense(
            company_id=company_id,
            employee_id=employee_id,
            category=category,
            description=description.strip(),
            expense_date=expense_date,
            paid_by=paid_by,
            currency_original=currency_original.upper(),
            amount_original=amount_original,
            amount_company_currency=amount_company_currency,
            status="DRAFT"
        )
        
        db.add(expense)
        db.commit()
        db.refresh(expense)
        
        return expense
    
    @classmethod
    def update_expense(
        cls,
        db: Session,
        expense_id: int,
        employee_id: int,
        category: Optional[str] = None,
        description: Optional[str] = None,
        expense_date: Optional[date] = None,
        paid_by: Optional[str] = None,
        currency_original: Optional[str] = None,
        amount_original: Optional[float] = None
    ) -> Expense:
        """
        Update an existing expense. Only allowed for DRAFT status.
        
        Args:
            db: Database session
            expense_id: Expense ID to update
            employee_id: Employee user ID (for authorization)
            category: New category (optional)
            description: New description (optional)
            expense_date: New expense date (optional)
            paid_by: New payment method (optional)
            currency_original: New currency (optional)
            amount_original: New amount (optional)
            
        Returns:
            Updated Expense object
            
        Raises:
            HTTPException: 404 if not found, 400 if not DRAFT, 503 if FX fails
        """
        # Get expense
        expense = db.query(Expense).filter(
            and_(
                Expense.id == expense_id,
                Expense.employee_id == employee_id
            )
        ).first()
        
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")
        
        # Check status
        if expense.status != "DRAFT":
            raise HTTPException(
                status_code=400,
                detail="Only DRAFT expenses can be edited"
            )
        
        # Update fields
        if category is not None:
            expense.category = category
        
        if description is not None:
            if not description.strip():
                raise ValueError("Description cannot be empty")
            expense.description = description.strip()
        
        if expense_date is not None:
            if expense_date > date.today():
                raise ValueError("Expense date cannot be in the future")
            expense.expense_date = expense_date
        
        if paid_by is not None:
            expense.paid_by = paid_by
        
        # If currency or amount changed, recalculate conversion
        currency_changed = currency_original is not None and currency_original.upper() != expense.currency_original
        amount_changed = amount_original is not None and amount_original != expense.amount_original
        
        if currency_original is not None:
            expense.currency_original = currency_original.upper()
        
        if amount_original is not None:
            if amount_original <= 0:
                raise ValueError("Amount must be positive")
            expense.amount_original = amount_original
        
        if currency_changed or amount_changed:
            # Get company base currency
            from app.models import Company
            company = db.query(Company).filter(Company.id == expense.company_id).first()
            base_currency = company.base_currency
            
            # Recalculate conversion
            try:
                if expense.currency_original == base_currency.upper():
                    expense.amount_company_currency = expense.amount_original
                else:
                    expense.amount_company_currency = FXService.convert_amount(
                        expense.amount_original,
                        expense.currency_original,
                        base_currency
                    )
            except (ValueError, RuntimeError) as e:
                raise HTTPException(
                    status_code=503,
                    detail=f"Currency conversion failed: {str(e)}"
                )
        
        db.commit()
        db.refresh(expense)
        
        return expense
    
    @classmethod
    def get_expense(cls, db: Session, expense_id: int, user_id: int) -> Expense:
        """
        Get a single expense by ID.
        
        Args:
            db: Database session
            expense_id: Expense ID
            user_id: User ID (for authorization check)
            
        Returns:
            Expense object
            
        Raises:
            HTTPException: 404 if not found or unauthorized
        """
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")
        
        # Check authorization (employee can only see their own expenses)
        if expense.employee_id != user_id:
            raise HTTPException(status_code=404, detail="Expense not found")
        
        return expense
    
    @classmethod
    def get_expenses(
        cls,
        db: Session,
        company_id: int,
        employee_id: Optional[int] = None,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> List[Expense]:
        """
        Get expenses with optional filtering.
        
        Args:
            db: Database session
            company_id: Company ID
            employee_id: Filter by employee (optional)
            status: Filter by status (optional)
            date_from: Filter by start date (optional)
            date_to: Filter by end date (optional)
            
        Returns:
            List of Expense objects
        """
        query = db.query(Expense).filter(Expense.company_id == company_id)
        
        if employee_id is not None:
            query = query.filter(Expense.employee_id == employee_id)
        
        if status is not None:
            query = query.filter(Expense.status == status)
        
        if date_from is not None:
            query = query.filter(Expense.expense_date >= date_from)
        
        if date_to is not None:
            query = query.filter(Expense.expense_date <= date_to)
        
        return query.order_by(Expense.created_at.desc()).all()
    
    @classmethod
    def submit_expense(cls, db: Session, expense_id: int, employee_id: int) -> Expense:
        """
        Submit an expense for approval. Changes status and triggers approval workflow.
        
        Args:
            db: Database session
            expense_id: Expense ID
            employee_id: Employee user ID (for authorization)
            
        Returns:
            Updated Expense object
            
        Raises:
            HTTPException: 404 if not found, 400 if not DRAFT
        """
        # Get expense
        expense = db.query(Expense).filter(
            and_(
                Expense.id == expense_id,
                Expense.employee_id == employee_id
            )
        ).first()
        
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")
        
        # Check status
        if expense.status != "DRAFT":
            raise HTTPException(
                status_code=400,
                detail="Only DRAFT expenses can be submitted"
            )
        
        # Get approval rule and create approval steps
        from app.services.approval_service import ApprovalService
        from app.models import ApprovalRule
        
        rule = ApprovalService.get_current_rule(db, expense.company_id)
        
        if not rule:
            raise HTTPException(
                status_code=400,
                detail="No approval rule configured for this company"
            )
        
        # Get employee for manager lookup
        employee = db.query(User).filter(User.id == employee_id).first()
        
        # Create approval steps
        steps = ApprovalService.create_approval_steps(db, expense_id, rule, employee)
        
        # Update expense status based on number of approvers
        if len(steps) == 1:
            expense.status = "WAITING_APPROVAL"
        else:
            expense.status = "IN_PROGRESS"
        
        db.commit()
        db.refresh(expense)
        
        return expense
    
    @classmethod
    def upload_receipt(
        cls,
        db: Session,
        expense_id: int,
        employee_id: int,
        file: UploadFile
    ) -> ExpenseReceipt:
        """
        Upload a receipt file for an expense.
        
        Args:
            db: Database session
            expense_id: Expense ID
            employee_id: Employee user ID (for authorization)
            file: Uploaded file
            
        Returns:
            Created ExpenseReceipt object
            
        Raises:
            HTTPException: 404 if not found, 400 if validation fails
        """
        # Get expense
        expense = db.query(Expense).filter(
            and_(
                Expense.id == expense_id,
                Expense.employee_id == employee_id
            )
        ).first()
        
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")
        
        # Validate file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning
        
        if file_size > cls.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File size exceeds maximum of {cls.MAX_FILE_SIZE / 1024 / 1024} MB"
            )
        
        # Validate file format
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file format. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Ensure upload directory exists
        cls._ensure_upload_dir()
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = os.path.join(cls.UPLOAD_DIR, unique_filename)
        
        # Save file
        try:
            with open(file_path, "wb") as f:
                content = file.file.read()
                f.write(content)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}"
            )
        
        # Create receipt record
        receipt = ExpenseReceipt(
            expense_id=expense_id,
            file_path=file_path,
            original_filename=file.filename
        )
        
        db.add(receipt)
        db.commit()
        db.refresh(receipt)
        
        return receipt

    @classmethod
    def force_approve(cls, db: Session, expense_id: int, company_id: int) -> Expense:
        """
        Force approve an expense (admin only). Changes status to APPROVED regardless of workflow.
        
        Args:
            db: Database session
            expense_id: Expense ID
            company_id: Company ID (for authorization)
            
        Returns:
            Updated Expense object
            
        Raises:
            HTTPException: 404 if not found
        """
        expense = db.query(Expense).filter(
            and_(
                Expense.id == expense_id,
                Expense.company_id == company_id
            )
        ).first()
        
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")
        
        expense.status = "APPROVED"
        db.commit()
        db.refresh(expense)
        
        return expense
    
    @classmethod
    def force_reject(cls, db: Session, expense_id: int, company_id: int) -> Expense:
        """
        Force reject an expense (admin only). Changes status to REJECTED regardless of workflow.
        
        Args:
            db: Database session
            expense_id: Expense ID
            company_id: Company ID (for authorization)
            
        Returns:
            Updated Expense object
            
        Raises:
            HTTPException: 404 if not found
        """
        expense = db.query(Expense).filter(
            and_(
                Expense.id == expense_id,
                Expense.company_id == company_id
            )
        ).first()
        
        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")
        
        expense.status = "REJECTED"
        db.commit()
        db.refresh(expense)
        
        return expense
