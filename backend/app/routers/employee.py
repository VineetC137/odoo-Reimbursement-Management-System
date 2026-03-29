from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.dependencies import require_employee, TokenPayload
from app.services.expense_service import ExpenseService
from app.schemas import (
    CreateExpenseRequest,
    UpdateExpenseRequest,
    ExpenseDetail,
    ExpenseListResponse,
    ReceiptDetail
)
from app.models import User


router = APIRouter(prefix="/api/employee", tags=["employee"])


def _expense_to_detail(expense, db: Session) -> ExpenseDetail:
    """Convert Expense model to ExpenseDetail schema."""
    # Get employee name
    employee = db.query(User).filter(User.id == expense.employee_id).first()
    employee_name = employee.name if employee else "Unknown"
    
    # Convert approval steps
    approval_steps = []
    for step in expense.approval_steps:
        approver = db.query(User).filter(User.id == step.approver_id).first()
        approval_steps.append({
            "id": step.id,
            "expense_id": step.expense_id,
            "approver_id": step.approver_id,
            "approver_name": approver.name if approver else "Unknown",
            "sequence": step.sequence,
            "status": step.status,
            "comment": step.comment,
            "acted_at": step.acted_at
        })
    
    # Convert receipts
    receipts = []
    for receipt in expense.receipts:
        receipts.append({
            "id": receipt.id,
            "expense_id": receipt.expense_id,
            "file_path": receipt.file_path,
            "original_filename": receipt.original_filename,
            "uploaded_at": receipt.uploaded_at
        })
    
    return ExpenseDetail(
        id=expense.id,
        company_id=expense.company_id,
        employee_id=expense.employee_id,
        employee_name=employee_name,
        category=expense.category,
        description=expense.description,
        expense_date=expense.expense_date,
        paid_by=expense.paid_by,
        currency_original=expense.currency_original,
        amount_original=expense.amount_original,
        amount_company_currency=expense.amount_company_currency,
        status=expense.status,
        created_at=expense.created_at,
        approval_steps=approval_steps,
        receipts=receipts
    )


@router.get("/expenses", response_model=ExpenseListResponse)
def get_expenses(
    status: Optional[str] = None,
    current_user: TokenPayload = Depends(require_employee),
    db: Session = Depends(get_db)
):
    """
    Get all expenses for the current employee with optional status filter.
    
    Query Parameters:
        status: Filter by expense status (optional)
    
    Returns:
        List of expenses
    """
    expenses = ExpenseService.get_expenses(
        db=db,
        company_id=current_user.company_id,
        employee_id=current_user.user_id,
        status=status
    )
    
    expense_details = [_expense_to_detail(exp, db) for exp in expenses]
    
    return ExpenseListResponse(expenses=expense_details)


@router.get("/expenses/{expense_id}", response_model=ExpenseDetail)
def get_expense(
    expense_id: int,
    current_user: TokenPayload = Depends(require_employee),
    db: Session = Depends(get_db)
):
    """
    Get a single expense by ID with approval steps and receipts.
    
    Path Parameters:
        expense_id: Expense ID
    
    Returns:
        Expense detail with approval steps and receipts
    """
    expense = ExpenseService.get_expense(
        db=db,
        expense_id=expense_id,
        user_id=current_user.user_id
    )
    
    return _expense_to_detail(expense, db)


@router.post("/expenses", response_model=ExpenseDetail, status_code=201)
def create_expense(
    request: CreateExpenseRequest,
    current_user: TokenPayload = Depends(require_employee),
    db: Session = Depends(get_db)
):
    """
    Create a new expense with DRAFT status.
    
    Request Body:
        category: Expense category
        description: Expense description
        expense_date: Date of expense
        paid_by: Payment method
        currency_original: Original currency ISO code
        amount_original: Original amount
    
    Returns:
        Created expense detail
    """
    try:
        expense = ExpenseService.create_expense(
            db=db,
            company_id=current_user.company_id,
            employee_id=current_user.user_id,
            category=request.category,
            description=request.description,
            expense_date=request.expense_date,
            paid_by=request.paid_by,
            currency_original=request.currency_original,
            amount_original=request.amount_original
        )
        
        return _expense_to_detail(expense, db)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/expenses/{expense_id}", response_model=ExpenseDetail)
def update_expense(
    expense_id: int,
    request: UpdateExpenseRequest,
    current_user: TokenPayload = Depends(require_employee),
    db: Session = Depends(get_db)
):
    """
    Update an existing expense. Only allowed for DRAFT status.
    
    Path Parameters:
        expense_id: Expense ID
    
    Request Body:
        category: New category (optional)
        description: New description (optional)
        expense_date: New expense date (optional)
        paid_by: New payment method (optional)
        currency_original: New currency (optional)
        amount_original: New amount (optional)
    
    Returns:
        Updated expense detail
    """
    try:
        expense = ExpenseService.update_expense(
            db=db,
            expense_id=expense_id,
            employee_id=current_user.user_id,
            category=request.category,
            description=request.description,
            expense_date=request.expense_date,
            paid_by=request.paid_by,
            currency_original=request.currency_original,
            amount_original=request.amount_original
        )
        
        return _expense_to_detail(expense, db)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/expenses/{expense_id}/submit", response_model=ExpenseDetail)
def submit_expense(
    expense_id: int,
    current_user: TokenPayload = Depends(require_employee),
    db: Session = Depends(get_db)
):
    """
    Submit an expense for approval. Changes status and triggers approval workflow.
    
    Path Parameters:
        expense_id: Expense ID
    
    Returns:
        Updated expense detail with approval steps
    """
    expense = ExpenseService.submit_expense(
        db=db,
        expense_id=expense_id,
        employee_id=current_user.user_id
    )
    
    return _expense_to_detail(expense, db)


@router.post("/expenses/{expense_id}/upload-receipt", response_model=ReceiptDetail)
def upload_receipt(
    expense_id: int,
    file: UploadFile = File(...),
    current_user: TokenPayload = Depends(require_employee),
    db: Session = Depends(get_db)
):
    """
    Upload a receipt file for an expense.
    
    Path Parameters:
        expense_id: Expense ID
    
    Request Body:
        file: Receipt image file (JPEG, PNG, or PDF, max 10 MB)
    
    Returns:
        Created receipt detail
    """
    receipt = ExpenseService.upload_receipt(
        db=db,
        expense_id=expense_id,
        employee_id=current_user.user_id,
        file=file
    )
    
    return ReceiptDetail(
        id=receipt.id,
        expense_id=receipt.expense_id,
        file_path=receipt.file_path,
        original_filename=receipt.original_filename,
        uploaded_at=receipt.uploaded_at
    )
