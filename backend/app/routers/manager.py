from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import require_manager, TokenPayload
from app.schemas import ExpenseDetail, ApprovalStepDetail, ReceiptDetail
from app.services.approval_service import ApprovalService
from app.models import User as UserModel
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/manager", tags=["manager"])


class PendingApprovalResponse(BaseModel):
    step_id: int
    expense: ExpenseDetail
    sequence: int


class PendingApprovalsListResponse(BaseModel):
    approvals: list[PendingApprovalResponse]


class RejectApprovalRequest(BaseModel):
    comment: str = Field(..., min_length=1)


class ApprovalActionResponse(BaseModel):
    step: ApprovalStepDetail
    expense: ExpenseDetail


@router.get("/approvals/pending", response_model=PendingApprovalsListResponse)
def get_pending_approvals(
    current_user: TokenPayload = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """
    Get all pending approval steps for the current manager.
    
    Requires MANAGER role.
    
    Returns:
        List of pending approvals with expense details
    """
    steps = ApprovalService.get_pending_approvals(db, current_user.user_id)
    
    approvals = []
    for step in steps:
        expense = step.expense
        
        # Get employee name
        employee = db.query(UserModel).filter(UserModel.id == expense.employee_id).first()
        employee_name = employee.name if employee else "Unknown"
        
        # Get all approval steps for this expense
        approval_steps = []
        for s in expense.approval_steps:
            approver = db.query(UserModel).filter(UserModel.id == s.approver_id).first()
            approval_steps.append(ApprovalStepDetail(
                id=s.id,
                expense_id=s.expense_id,
                approver_id=s.approver_id,
                approver_name=approver.name if approver else "Unknown",
                sequence=s.sequence,
                status=s.status,
                comment=s.comment,
                acted_at=s.acted_at
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
        
        expense_detail = ExpenseDetail(
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
        
        approvals.append(PendingApprovalResponse(
            step_id=step.id,
            expense=expense_detail,
            sequence=step.sequence
        ))
    
    return PendingApprovalsListResponse(approvals=approvals)


@router.post("/approvals/{step_id}/approve", response_model=ApprovalActionResponse)
def approve_step(
    step_id: int,
    current_user: TokenPayload = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """
    Approve an expense approval step.
    
    Requires MANAGER role.
    
    Path Parameters:
        step_id: ID of the approval step to approve
    
    Returns:
        Updated approval step and expense details
    
    Raises:
        403: If not authorized to approve this step
        400: If step has already been processed
        404: If step not found
    """
    step = ApprovalService.approve_step(db, step_id, current_user.user_id)
    
    # Get updated expense
    expense = step.expense
    
    # Get employee name
    employee = db.query(UserModel).filter(UserModel.id == expense.employee_id).first()
    employee_name = employee.name if employee else "Unknown"
    
    # Get approver name for the step
    approver = db.query(UserModel).filter(UserModel.id == step.approver_id).first()
    
    step_detail = ApprovalStepDetail(
        id=step.id,
        expense_id=step.expense_id,
        approver_id=step.approver_id,
        approver_name=approver.name if approver else "Unknown",
        sequence=step.sequence,
        status=step.status,
        comment=step.comment,
        acted_at=step.acted_at
    )
    
    # Get all approval steps
    approval_steps = []
    for s in expense.approval_steps:
        approver = db.query(UserModel).filter(UserModel.id == s.approver_id).first()
        approval_steps.append(ApprovalStepDetail(
            id=s.id,
            expense_id=s.expense_id,
            approver_id=s.approver_id,
            approver_name=approver.name if approver else "Unknown",
            sequence=s.sequence,
            status=s.status,
            comment=s.comment,
            acted_at=s.acted_at
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
    
    expense_detail = ExpenseDetail(
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
    
    return ApprovalActionResponse(step=step_detail, expense=expense_detail)


@router.post("/approvals/{step_id}/reject", response_model=ApprovalActionResponse)
def reject_step(
    step_id: int,
    request: RejectApprovalRequest,
    current_user: TokenPayload = Depends(require_manager),
    db: Session = Depends(get_db)
):
    """
    Reject an expense approval step with a comment.
    
    Requires MANAGER role.
    
    Path Parameters:
        step_id: ID of the approval step to reject
    
    Request Body:
        comment: Rejection comment (required)
    
    Returns:
        Updated approval step and expense details
    
    Raises:
        403: If not authorized to reject this step
        400: If step has already been processed
        404: If step not found
    """
    step = ApprovalService.reject_step(db, step_id, current_user.user_id, request.comment)
    
    # Get updated expense
    expense = step.expense
    
    # Get employee name
    employee = db.query(UserModel).filter(UserModel.id == expense.employee_id).first()
    employee_name = employee.name if employee else "Unknown"
    
    # Get approver name for the step
    approver = db.query(UserModel).filter(UserModel.id == step.approver_id).first()
    
    step_detail = ApprovalStepDetail(
        id=step.id,
        expense_id=step.expense_id,
        approver_id=step.approver_id,
        approver_name=approver.name if approver else "Unknown",
        sequence=step.sequence,
        status=step.status,
        comment=step.comment,
        acted_at=step.acted_at
    )
    
    # Get all approval steps
    approval_steps = []
    for s in expense.approval_steps:
        approver = db.query(UserModel).filter(UserModel.id == s.approver_id).first()
        approval_steps.append(ApprovalStepDetail(
            id=s.id,
            expense_id=s.expense_id,
            approver_id=s.approver_id,
            approver_name=approver.name if approver else "Unknown",
            sequence=s.sequence,
            status=s.status,
            comment=s.comment,
            acted_at=s.acted_at
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
    
    expense_detail = ExpenseDetail(
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
    
    return ApprovalActionResponse(step=step_detail, expense=expense_detail)
