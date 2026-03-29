"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table('company',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('country', sa.String(), nullable=False),
        sa.Column('base_currency', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_company_id'), 'company', ['id'], unique=False)
    
    op.create_table('user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('manager_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("role IN ('ADMIN', 'MANAGER', 'EMPLOYEE')"),
        sa.ForeignKeyConstraint(['company_id'], ['company.id'], ),
        sa.ForeignKeyConstraint(['manager_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_user_email'), 'user', ['email'], unique=True)
    op.create_index(op.f('ix_user_id'), 'user', ['id'], unique=False)
    
    op.create_table('approval_rule',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('mode', sa.String(), nullable=False),
        sa.Column('percentage_threshold', sa.Float(), nullable=True),
        sa.Column('special_approver_id', sa.Integer(), nullable=True),
        sa.Column('is_manager_approver', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("mode IN ('PERCENTAGE', 'SPECIFIC', 'HYBRID')"),
        sa.ForeignKeyConstraint(['company_id'], ['company.id'], ),
        sa.ForeignKeyConstraint(['special_approver_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_approval_rule_id'), 'approval_rule', ['id'], unique=False)
    
    op.create_table('approval_rule_approver',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('approver_id', sa.Integer(), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('is_required', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['approver_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['rule_id'], ['approval_rule.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_approval_rule_approver_id'), 'approval_rule_approver', ['id'], unique=False)
    
    op.create_table('expense',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('expense_date', sa.Date(), nullable=False),
        sa.Column('paid_by', sa.String(), nullable=False),
        sa.Column('currency_original', sa.String(), nullable=False),
        sa.Column('amount_original', sa.Float(), nullable=False),
        sa.Column('amount_company_currency', sa.Float(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("status IN ('DRAFT', 'WAITING_APPROVAL', 'IN_PROGRESS', 'APPROVED', 'REJECTED')"),
        sa.ForeignKeyConstraint(['company_id'], ['company.id'], ),
        sa.ForeignKeyConstraint(['employee_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_expense_id'), 'expense', ['id'], unique=False)
    
    op.create_table('expense_approval_step',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('expense_id', sa.Integer(), nullable=False),
        sa.Column('approver_id', sa.Integer(), nullable=False),
        sa.Column('sequence', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('comment', sa.String(), nullable=True),
        sa.Column('acted_at', sa.DateTime(), nullable=True),
        sa.CheckConstraint("status IN ('PENDING', 'APPROVED', 'REJECTED')"),
        sa.ForeignKeyConstraint(['approver_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['expense_id'], ['expense.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_expense_approval_step_id'), 'expense_approval_step', ['id'], unique=False)
    
    op.create_table('expense_receipt',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('expense_id', sa.Integer(), nullable=False),
        sa.Column('file_path', sa.String(), nullable=False),
        sa.Column('original_filename', sa.String(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['expense_id'], ['expense.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_expense_receipt_id'), 'expense_receipt', ['id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_expense_receipt_id'), table_name='expense_receipt')
    op.drop_table('expense_receipt')
    op.drop_index(op.f('ix_expense_approval_step_id'), table_name='expense_approval_step')
    op.drop_table('expense_approval_step')
    op.drop_index(op.f('ix_expense_id'), table_name='expense')
    op.drop_table('expense')
    op.drop_index(op.f('ix_approval_rule_approver_id'), table_name='approval_rule_approver')
    op.drop_table('approval_rule_approver')
    op.drop_index(op.f('ix_approval_rule_id'), table_name='approval_rule')
    op.drop_table('approval_rule')
    op.drop_index(op.f('ix_user_id'), table_name='user')
    op.drop_index(op.f('ix_user_email'), table_name='user')
    op.drop_table('user')
    op.drop_index(op.f('ix_company_id'), table_name='company')
    op.drop_table('company')
