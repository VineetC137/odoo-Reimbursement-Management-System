from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Company(Base):
    __tablename__ = 'company'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    country = Column(String, nullable=False)
    base_currency = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users = relationship("User", back_populates="company")
    expenses = relationship("Expense", back_populates="company")
    approval_rules = relationship("ApprovalRule", back_populates="company")

class User(Base):
    __tablename__ = 'user'
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('company.id'), nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    manager_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("role IN ('ADMIN', 'MANAGER', 'EMPLOYEE')"),
    )
    
    company = relationship("Company", back_populates="users")
    manager = relationship("User", remote_side=[id], backref="subordinates")
    expenses = relationship("Expense", back_populates="employee", foreign_keys="Expense.employee_id")

class ApprovalRule(Base):
    __tablename__ = 'approval_rule'
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('company.id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    mode = Column(String, nullable=False)
    percentage_threshold = Column(Float, nullable=True)
    special_approver_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    is_manager_approver = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("mode IN ('PERCENTAGE', 'SPECIFIC', 'HYBRID')"),
    )
    
    company = relationship("Company", back_populates="approval_rules")
    special_approver = relationship("User", foreign_keys=[special_approver_id])
    approvers = relationship("ApprovalRuleApprover", back_populates="rule")

class ApprovalRuleApprover(Base):
    __tablename__ = 'approval_rule_approver'
    
    id = Column(Integer, primary_key=True, index=True)
    rule_id = Column(Integer, ForeignKey('approval_rule.id'), nullable=False)
    approver_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    sequence = Column(Integer, nullable=False)
    is_required = Column(Boolean, default=True)
    
    rule = relationship("ApprovalRule", back_populates="approvers")
    approver = relationship("User")

class Expense(Base):
    __tablename__ = 'expense'
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('company.id'), nullable=False)
    employee_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    category = Column(String, nullable=False)
    description = Column(String, nullable=False)
    expense_date = Column(Date, nullable=False)
    paid_by = Column(String, nullable=False)
    currency_original = Column(String, nullable=False)
    amount_original = Column(Float, nullable=False)
    amount_company_currency = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint("status IN ('DRAFT', 'WAITING_APPROVAL', 'IN_PROGRESS', 'APPROVED', 'REJECTED')"),
    )
    
    company = relationship("Company", back_populates="expenses")
    employee = relationship("User", back_populates="expenses", foreign_keys=[employee_id])
    approval_steps = relationship("ExpenseApprovalStep", back_populates="expense")
    receipts = relationship("ExpenseReceipt", back_populates="expense")

class ExpenseApprovalStep(Base):
    __tablename__ = 'expense_approval_step'
    
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey('expense.id'), nullable=False)
    approver_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    sequence = Column(Integer, nullable=False)
    status = Column(String, nullable=False)
    comment = Column(String, nullable=True)
    acted_at = Column(DateTime, nullable=True)
    
    __table_args__ = (
        CheckConstraint("status IN ('PENDING', 'APPROVED', 'REJECTED')"),
    )
    
    expense = relationship("Expense", back_populates="approval_steps")
    approver = relationship("User")

class ExpenseReceipt(Base):
    __tablename__ = 'expense_receipt'
    
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey('expense.id'), nullable=False)
    file_path = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    expense = relationship("Expense", back_populates="receipts")
