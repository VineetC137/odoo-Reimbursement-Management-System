from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import date, datetime
from typing import Optional


# Authentication Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class SignupInitialRequest(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=8)
    country: str = Field(..., min_length=1)


class UserProfile(BaseModel):
    id: int
    company_id: int
    name: str
    email: str
    role: str
    manager_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CompanyProfile(BaseModel):
    id: int
    name: str
    country: str
    base_currency: str
    created_at: datetime

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    token: str
    user: UserProfile


class SignupInitialResponse(BaseModel):
    token: str
    user: UserProfile
    company: CompanyProfile


# Expense Schemas
class CreateExpenseRequest(BaseModel):
    category: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    expense_date: date
    paid_by: str = Field(..., min_length=1)
    currency_original: str = Field(..., min_length=3, max_length=3)
    amount_original: float = Field(..., gt=0)


class UpdateExpenseRequest(BaseModel):
    category: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, min_length=1)
    expense_date: Optional[date] = None
    paid_by: Optional[str] = Field(None, min_length=1)
    currency_original: Optional[str] = Field(None, min_length=3, max_length=3)
    amount_original: Optional[float] = Field(None, gt=0)


class ExpenseDetail(BaseModel):
    id: int
    company_id: int
    employee_id: int
    employee_name: str
    category: str
    description: str
    expense_date: date
    paid_by: str
    currency_original: str
    amount_original: float
    amount_company_currency: float
    status: str
    created_at: datetime
    approval_steps: list['ApprovalStepDetail'] = []
    receipts: list['ReceiptDetail'] = []

    class Config:
        from_attributes = True


class ExpenseListResponse(BaseModel):
    expenses: list[ExpenseDetail]


class ApprovalStepDetail(BaseModel):
    id: int
    expense_id: int
    approver_id: int
    approver_name: str
    sequence: int
    status: str
    comment: Optional[str] = None
    acted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReceiptDetail(BaseModel):
    id: int
    expense_id: int
    file_path: str
    original_filename: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


# Approval Rule Schemas
class ApproverConfigInput(BaseModel):
    approver_id: int
    sequence: int
    is_required: bool = True


class CreateApprovalRuleRequest(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    mode: str = Field(..., pattern="^(PERCENTAGE|SPECIFIC|HYBRID)$")
    percentage_threshold: Optional[float] = Field(None, ge=0, le=100)
    special_approver_id: Optional[int] = None
    is_manager_approver: bool = False
    approvers: list[ApproverConfigInput] = []


class ApproverConfig(BaseModel):
    approver_id: int
    approver_name: str
    sequence: int
    is_required: bool

    class Config:
        from_attributes = True


class ApprovalRuleConfig(BaseModel):
    id: int
    company_id: int
    name: str
    description: Optional[str] = None
    mode: str
    percentage_threshold: Optional[float] = None
    special_approver_id: Optional[int] = None
    is_manager_approver: bool
    approvers: list[ApproverConfig] = []
    created_at: datetime

    class Config:
        from_attributes = True


# User Management Schemas
class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: str = Field(..., pattern="^(ADMIN|MANAGER|EMPLOYEE)$")
    manager_id: Optional[int] = None


class UpdateUserRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, pattern="^(ADMIN|MANAGER|EMPLOYEE)$")
    manager_id: Optional[int] = None


class UserListResponse(BaseModel):
    users: list[UserProfile]


# OCR Schemas
class ParsedReceipt(BaseModel):
    raw_text: str
    amount: Optional[float] = None
    currency_guess: Optional[str] = None
    date: Optional[str] = None
    merchant: Optional[str] = None
