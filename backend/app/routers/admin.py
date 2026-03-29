from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.dependencies import require_admin, TokenPayload
from app.schemas import (
    CreateUserRequest,
    UpdateUserRequest,
    UserProfile,
    UserListResponse
)
from app.services.user_service import UserService


router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=UserListResponse)
def get_users(
    role: Optional[str] = Query(None, pattern="^(ADMIN|MANAGER|EMPLOYEE)$"),
    current_user: TokenPayload = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get all users with optional role filtering.
    
    Requires ADMIN role.
    
    Query Parameters:
        role: Optional role filter (ADMIN, MANAGER, EMPLOYEE)
    
    Returns:
        List of users with their details
    """
    users = UserService.get_users(
        db=db,
        company_id=current_user.company_id,
        role=role
    )
    
    user_profiles = [UserProfile.model_validate(user) for user in users]
    
    return UserListResponse(users=user_profiles)


@router.post("/users", response_model=UserProfile, status_code=201)
def create_user(
    request: CreateUserRequest,
    current_user: TokenPayload = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create a new user.
    
    Requires ADMIN role.
    
    Request Body:
        name: User's full name
        email: User's email address (must be unique)
        password: User's password (min 8 characters)
        role: User role (ADMIN, MANAGER, EMPLOYEE)
        manager_id: Optional manager user ID (must be a MANAGER)
    
    Returns:
        Created user profile
    
    Raises:
        400: If email already exists or manager_id is invalid
    """
    try:
        user = UserService.create_user(
            db=db,
            company_id=current_user.company_id,
            name=request.name,
            email=request.email,
            password=request.password,
            role=request.role,
            manager_id=request.manager_id
        )
        db.commit()
        db.refresh(user)
        
        return UserProfile.model_validate(user)
    
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/users/{user_id}", response_model=UserProfile)
def update_user(
    user_id: int,
    request: UpdateUserRequest,
    current_user: TokenPayload = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update an existing user.
    
    Requires ADMIN role.
    
    Path Parameters:
        user_id: ID of the user to update
    
    Request Body:
        name: Optional new name
        email: Optional new email (must be unique)
        role: Optional new role (ADMIN, MANAGER, EMPLOYEE)
        manager_id: Optional new manager ID (must be a MANAGER)
    
    Returns:
        Updated user profile
    
    Raises:
        400: If user not found, email already exists, or manager_id is invalid
    """
    try:
        user = UserService.update_user(
            db=db,
            user_id=user_id,
            name=request.name,
            email=request.email,
            role=request.role,
            manager_id=request.manager_id
        )
        db.commit()
        db.refresh(user)
        
        return UserProfile.model_validate(user)
    
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


# Approval Rule Endpoints
from app.schemas import CreateApprovalRuleRequest, ApprovalRuleConfig, ApproverConfig
from app.services.approval_service import ApprovalService
from app.models import User as UserModel


@router.get("/approval-rules/current", response_model=ApprovalRuleConfig)
def get_current_approval_rule(
    current_user: TokenPayload = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get the current active approval rule.
    
    Requires ADMIN role.
    
    Returns:
        Current approval rule configuration with approvers
    
    Raises:
        404: If no approval rule is configured
    """
    rule = ApprovalService.get_current_rule(db, current_user.company_id)
    
    if not rule:
        raise HTTPException(status_code=404, detail="No approval rule configured")
    
    # Build approver configs
    approver_configs = []
    for approver_record in rule.approvers:
        approver_user = db.query(UserModel).filter(UserModel.id == approver_record.approver_id).first()
        approver_configs.append(ApproverConfig(
            approver_id=approver_record.approver_id,
            approver_name=approver_user.name if approver_user else "Unknown",
            sequence=approver_record.sequence,
            is_required=approver_record.is_required
        ))
    
    return ApprovalRuleConfig(
        id=rule.id,
        company_id=rule.company_id,
        name=rule.name,
        description=rule.description,
        mode=rule.mode,
        percentage_threshold=rule.percentage_threshold,
        special_approver_id=rule.special_approver_id,
        is_manager_approver=rule.is_manager_approver,
        approvers=approver_configs,
        created_at=rule.created_at
    )


@router.post("/approval-rules", response_model=ApprovalRuleConfig, status_code=201)
def create_approval_rule(
    request: CreateApprovalRuleRequest,
    current_user: TokenPayload = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Create or update an approval rule.
    
    Requires ADMIN role.
    
    Request Body:
        name: Rule name
        description: Optional rule description
        mode: Approval mode (PERCENTAGE, SPECIFIC, HYBRID)
        percentage_threshold: Required for PERCENTAGE/HYBRID mode (0-100)
        special_approver_id: Required for SPECIFIC/HYBRID mode
        is_manager_approver: Whether to include employee's manager as approver
        approvers: List of approver configurations
    
    Returns:
        Created approval rule configuration
    
    Raises:
        400: If validation fails
    """
    try:
        # Convert approvers to dict format
        approvers_list = [
            {
                "approver_id": a.approver_id,
                "sequence": a.sequence,
                "is_required": a.is_required
            }
            for a in request.approvers
        ]
        
        rule = ApprovalService.create_approval_rule(
            db=db,
            company_id=current_user.company_id,
            name=request.name,
            description=request.description,
            mode=request.mode,
            percentage_threshold=request.percentage_threshold,
            special_approver_id=request.special_approver_id,
            is_manager_approver=request.is_manager_approver,
            approvers=approvers_list
        )
        
        # Build response
        approver_configs = []
        for approver_record in rule.approvers:
            approver_user = db.query(UserModel).filter(UserModel.id == approver_record.approver_id).first()
            approver_configs.append(ApproverConfig(
                approver_id=approver_record.approver_id,
                approver_name=approver_user.name if approver_user else "Unknown",
                sequence=approver_record.sequence,
                is_required=approver_record.is_required
            ))
        
        return ApprovalRuleConfig(
            id=rule.id,
            company_id=rule.company_id,
            name=rule.name,
            description=rule.description,
            mode=rule.mode,
            percentage_threshold=rule.percentage_threshold,
            special_approver_id=rule.special_approver_id,
            is_manager_approver=rule.is_manager_approver,
            approvers=approver_configs,
            created_at=rule.created_at
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Expense Management Endpoints
from app.schemas import ExpenseListResponse, ExpenseDetail, ApprovalStepDetail, ReceiptDetail
from app.services.expense_service import ExpenseService
from datetime import date as date_type


@router.get("/expenses", response_model=ExpenseListResponse)
def get_all_expenses(
    status: Optional[str] = Query(None, pattern="^(DRAFT|WAITING_APPROVAL|IN_PROGRESS|APPROVED|REJECTED)$"),
    employee_id: Optional[int] = Query(None),
    date_from: Optional[date_type] = Query(None),
    date_to: Optional[date_type] = Query(None),
    current_user: TokenPayload = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Get all expenses with optional filtering.
    
    Requires ADMIN role.
    
    Query Parameters:
        status: Optional status filter
        employee_id: Optional employee filter
        date_from: Optional start date filter
        date_to: Optional end date filter
    
    Returns:
        List of expenses with details
    """
    expenses = ExpenseService.get_expenses(
        db=db,
        company_id=current_user.company_id,
        employee_id=employee_id,
        status=status,
        date_from=date_from,
        date_to=date_to
    )
    
    # Build expense details
    expense_details = []
    for expense in expenses:
        # Get employee name
        employee = db.query(UserModel).filter(UserModel.id == expense.employee_id).first()
        employee_name = employee.name if employee else "Unknown"
        
        # Get approval steps
        approval_steps = []
        for step in expense.approval_steps:
            approver = db.query(UserModel).filter(UserModel.id == step.approver_id).first()
            approval_steps.append(ApprovalStepDetail(
                id=step.id,
                expense_id=step.expense_id,
                approver_id=step.approver_id,
                approver_name=approver.name if approver else "Unknown",
                sequence=step.sequence,
                status=step.status,
                comment=step.comment,
                acted_at=step.acted_at
            ))
        
        # Get receipts
        receipts = [
            ReceiptDetail(
                id=r.id,
                expense_id=r.expense_id,
                file_path=r.file_path,
                original_filename=r.original_filename,
                uploaded_at=r.uploaded_at
            )
            for r in expense.receipts
        ]
        
        expense_details.append(ExpenseDetail(
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
        ))
    
    return ExpenseListResponse(expenses=expense_details)


@router.post("/expenses/{expense_id}/force-approve", response_model=ExpenseDetail)
def force_approve_expense(
    expense_id: int,
    current_user: TokenPayload = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Force approve an expense regardless of approval workflow.
    
    Requires ADMIN role.
    
    Path Parameters:
        expense_id: ID of the expense to approve
    
    Returns:
        Updated expense detail
    
    Raises:
        404: If expense not found
    """
    expense = ExpenseService.force_approve(db, expense_id, current_user.company_id)
    
    # Get employee name
    employee = db.query(UserModel).filter(UserModel.id == expense.employee_id).first()
    employee_name = employee.name if employee else "Unknown"
    
    # Get approval steps
    approval_steps = []
    for step in expense.approval_steps:
        approver = db.query(UserModel).filter(UserModel.id == step.approver_id).first()
        approval_steps.append(ApprovalStepDetail(
            id=step.id,
            expense_id=step.expense_id,
            approver_id=step.approver_id,
            approver_name=approver.name if approver else "Unknown",
            sequence=step.sequence,
            status=step.status,
            comment=step.comment,
            acted_at=step.acted_at
        ))
    
    # Get receipts
    receipts = [
        ReceiptDetail(
            id=r.id,
            expense_id=r.expense_id,
            file_path=r.file_path,
            original_filename=r.original_filename,
            uploaded_at=r.uploaded_at
        )
        for r in expense.receipts
    ]
    
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


@router.post("/expenses/{expense_id}/force-reject", response_model=ExpenseDetail)
def force_reject_expense(
    expense_id: int,
    current_user: TokenPayload = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Force reject an expense regardless of approval workflow.
    
    Requires ADMIN role.
    
    Path Parameters:
        expense_id: ID of the expense to reject
    
    Returns:
        Updated expense detail
    
    Raises:
        404: If expense not found
    """
    expense = ExpenseService.force_reject(db, expense_id, current_user.company_id)
    
    # Get employee name
    employee = db.query(UserModel).filter(UserModel.id == expense.employee_id).first()
    employee_name = employee.name if employee else "Unknown"
    
    # Get approval steps
    approval_steps = []
    for step in expense.approval_steps:
        approver = db.query(UserModel).filter(UserModel.id == step.approver_id).first()
        approval_steps.append(ApprovalStepDetail(
            id=step.id,
            expense_id=step.expense_id,
            approver_id=step.approver_id,
            approver_name=approver.name if approver else "Unknown",
            sequence=step.sequence,
            status=step.status,
            comment=step.comment,
            acted_at=step.acted_at
        ))
    
    # Get receipts
    receipts = [
        ReceiptDetail(
            id=r.id,
            expense_id=r.expense_id,
            file_path=r.file_path,
            original_filename=r.original_filename,
            uploaded_at=r.uploaded_at
        )
        for r in expense.receipts
    ]
    
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
