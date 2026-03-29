from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from app.models import ApprovalRule, ApprovalRuleApprover, ExpenseApprovalStep, User, Expense


class ApprovalService:
    """Service for managing approval rules and workflows."""
    
    @classmethod
    def create_approval_rule(
        cls,
        db: Session,
        company_id: int,
        name: str,
        description: Optional[str],
        mode: str,
        percentage_threshold: Optional[float],
        special_approver_id: Optional[int],
        is_manager_approver: bool,
        approvers: List[dict]
    ) -> ApprovalRule:
        """
        Create or update an approval rule for a company.
        
        Args:
            db: Database session
            company_id: Company ID
            name: Rule name
            description: Rule description
            mode: Approval mode (PERCENTAGE, SPECIFIC, HYBRID)
            percentage_threshold: Percentage threshold for PERCENTAGE/HYBRID mode
            special_approver_id: Special approver user ID for SPECIFIC/HYBRID mode
            is_manager_approver: Whether to include manager as approver
            approvers: List of approver configs with approver_id, sequence, is_required
            
        Returns:
            Created ApprovalRule object
            
        Raises:
            ValueError: If validation fails
        """
        # Validate mode
        if mode not in ["PERCENTAGE", "SPECIFIC", "HYBRID"]:
            raise ValueError("Mode must be PERCENTAGE, SPECIFIC, or HYBRID")
        
        # Validate percentage_threshold for PERCENTAGE/HYBRID mode
        if mode in ["PERCENTAGE", "HYBRID"]:
            if percentage_threshold is None:
                raise ValueError(f"percentage_threshold is required for {mode} mode")
            if not (0 <= percentage_threshold <= 100):
                raise ValueError("percentage_threshold must be between 0 and 100")
        
        # Validate special_approver_id for SPECIFIC/HYBRID mode
        if mode in ["SPECIFIC", "HYBRID"]:
            if special_approver_id is None:
                raise ValueError(f"special_approver_id is required for {mode} mode")
            # Verify user exists
            special_approver = db.query(User).filter(User.id == special_approver_id).first()
            if not special_approver:
                raise ValueError("special_approver_id references non-existent user")
        
        # Validate approvers
        for approver_config in approvers:
            approver = db.query(User).filter(User.id == approver_config["approver_id"]).first()
            if not approver:
                raise ValueError(f"Approver ID {approver_config['approver_id']} does not exist")
        
        # Create new approval rule (replaces any existing rule)
        rule = ApprovalRule(
            company_id=company_id,
            name=name,
            description=description,
            mode=mode,
            percentage_threshold=percentage_threshold,
            special_approver_id=special_approver_id,
            is_manager_approver=is_manager_approver
        )
        
        db.add(rule)
        db.flush()  # Get rule.id
        
        # Create approver records
        for approver_config in approvers:
            approver_record = ApprovalRuleApprover(
                rule_id=rule.id,
                approver_id=approver_config["approver_id"],
                sequence=approver_config["sequence"],
                is_required=approver_config.get("is_required", True)
            )
            db.add(approver_record)
        
        db.commit()
        db.refresh(rule)
        
        return rule
    
    @classmethod
    def get_current_rule(cls, db: Session, company_id: int) -> Optional[ApprovalRule]:
        """
        Get the current active approval rule for a company.
        
        Args:
            db: Database session
            company_id: Company ID
            
        Returns:
            ApprovalRule object or None if not found
        """
        return db.query(ApprovalRule).filter(
            ApprovalRule.company_id == company_id
        ).order_by(ApprovalRule.created_at.desc()).first()
    
    @classmethod
    def create_approval_steps(
        cls,
        db: Session,
        expense_id: int,
        rule: ApprovalRule,
        employee: User
    ) -> List[ExpenseApprovalStep]:
        """
        Create approval steps for an expense based on the approval rule.
        
        Args:
            db: Database session
            expense_id: Expense ID
            rule: ApprovalRule to apply
            employee: Employee who submitted the expense
            
        Returns:
            List of created ExpenseApprovalStep objects
        """
        steps = []
        
        # Add manager approver if configured and employee has a manager
        if rule.is_manager_approver and employee.manager_id:
            step = ExpenseApprovalStep(
                expense_id=expense_id,
                approver_id=employee.manager_id,
                sequence=0,
                status="PENDING"
            )
            db.add(step)
            steps.append(step)
        
        # Add rule approvers
        for approver_config in rule.approvers:
            step = ExpenseApprovalStep(
                expense_id=expense_id,
                approver_id=approver_config.approver_id,
                sequence=approver_config.sequence,
                status="PENDING"
            )
            db.add(step)
            steps.append(step)
        
        # Add special approver if in SPECIFIC or HYBRID mode
        if rule.mode in ["SPECIFIC", "HYBRID"] and rule.special_approver_id:
            # Check if special approver is not already in the list
            existing_approver_ids = [s.approver_id for s in steps]
            if rule.special_approver_id not in existing_approver_ids:
                max_sequence = max([s.sequence for s in steps]) if steps else 0
                step = ExpenseApprovalStep(
                    expense_id=expense_id,
                    approver_id=rule.special_approver_id,
                    sequence=max_sequence + 1,
                    status="PENDING"
                )
                db.add(step)
                steps.append(step)
        
        db.commit()
        
        # Refresh all steps
        for step in steps:
            db.refresh(step)
        
        return steps
    
    @classmethod
    def approve_step(
        cls,
        db: Session,
        step_id: int,
        approver_id: int
    ) -> ExpenseApprovalStep:
        """
        Approve an expense approval step.
        
        Args:
            db: Database session
            step_id: ExpenseApprovalStep ID
            approver_id: Approver user ID (for authorization)
            
        Returns:
            Updated ExpenseApprovalStep object
            
        Raises:
            ValueError: If validation fails
        """
        from fastapi import HTTPException
        
        step = db.query(ExpenseApprovalStep).filter(
            ExpenseApprovalStep.id == step_id
        ).first()
        
        if not step:
            raise HTTPException(status_code=404, detail="Approval step not found")
        
        # Validate approver
        if step.approver_id != approver_id:
            raise HTTPException(
                status_code=403,
                detail="You are not authorized to approve this step"
            )
        
        # Check status
        if step.status != "PENDING":
            raise HTTPException(
                status_code=400,
                detail="This approval step has already been processed"
            )
        
        # Update step
        step.status = "APPROVED"
        step.acted_at = datetime.utcnow()
        
        db.commit()
        db.refresh(step)
        
        # Evaluate workflow
        cls.evaluate_workflow(db, step.expense_id)
        
        return step
    
    @classmethod
    def reject_step(
        cls,
        db: Session,
        step_id: int,
        approver_id: int,
        comment: str
    ) -> ExpenseApprovalStep:
        """
        Reject an expense approval step.
        
        Args:
            db: Database session
            step_id: ExpenseApprovalStep ID
            approver_id: Approver user ID (for authorization)
            comment: Rejection comment
            
        Returns:
            Updated ExpenseApprovalStep object
            
        Raises:
            ValueError: If validation fails
        """
        from fastapi import HTTPException
        
        step = db.query(ExpenseApprovalStep).filter(
            ExpenseApprovalStep.id == step_id
        ).first()
        
        if not step:
            raise HTTPException(status_code=404, detail="Approval step not found")
        
        # Validate approver
        if step.approver_id != approver_id:
            raise HTTPException(
                status_code=403,
                detail="You are not authorized to reject this step"
            )
        
        # Check status
        if step.status != "PENDING":
            raise HTTPException(
                status_code=400,
                detail="This approval step has already been processed"
            )
        
        # Update step
        step.status = "REJECTED"
        step.comment = comment
        step.acted_at = datetime.utcnow()
        
        db.commit()
        db.refresh(step)
        
        # Evaluate workflow
        cls.evaluate_workflow(db, step.expense_id)
        
        return step
    
    @classmethod
    def evaluate_workflow(cls, db: Session, expense_id: int) -> Expense:
        """
        Evaluate the approval workflow for an expense and update its status.
        
        Args:
            db: Database session
            expense_id: Expense ID
            
        Returns:
            Updated Expense object
        """
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        
        if not expense:
            return None
        
        # Get all approval steps
        steps = db.query(ExpenseApprovalStep).filter(
            ExpenseApprovalStep.expense_id == expense_id
        ).all()
        
        if not steps:
            return expense
        
        # Check if any step is rejected
        rejected_steps = [s for s in steps if s.status == "REJECTED"]
        if rejected_steps:
            expense.status = "REJECTED"
            db.commit()
            db.refresh(expense)
            return expense
        
        # Get approval rule
        rule = cls.get_current_rule(db, expense.company_id)
        
        if not rule:
            return expense
        
        # Count approved and total steps
        approved_steps = [s for s in steps if s.status == "APPROVED"]
        total_steps = len(steps)
        approved_count = len(approved_steps)
        
        # Evaluate based on mode
        if rule.mode == "PERCENTAGE":
            # Check if percentage threshold is met
            if total_steps > 0:
                approval_percentage = (approved_count / total_steps) * 100
                if approval_percentage >= rule.percentage_threshold:
                    expense.status = "APPROVED"
        
        elif rule.mode == "SPECIFIC":
            # Check if special approver has approved
            special_approver_steps = [
                s for s in steps 
                if s.approver_id == rule.special_approver_id and s.status == "APPROVED"
            ]
            if special_approver_steps:
                expense.status = "APPROVED"
        
        elif rule.mode == "HYBRID":
            # Check if either percentage OR special approver condition is met
            approved_by_percentage = False
            approved_by_special = False
            
            if total_steps > 0:
                approval_percentage = (approved_count / total_steps) * 100
                if approval_percentage >= rule.percentage_threshold:
                    approved_by_percentage = True
            
            special_approver_steps = [
                s for s in steps 
                if s.approver_id == rule.special_approver_id and s.status == "APPROVED"
            ]
            if special_approver_steps:
                approved_by_special = True
            
            if approved_by_percentage or approved_by_special:
                expense.status = "APPROVED"
        
        db.commit()
        db.refresh(expense)
        
        return expense
    
    @classmethod
    def get_pending_approvals(
        cls,
        db: Session,
        approver_id: int
    ) -> List[ExpenseApprovalStep]:
        """
        Get all pending approval steps for a specific approver.
        
        Args:
            db: Database session
            approver_id: Approver user ID
            
        Returns:
            List of ExpenseApprovalStep objects with status PENDING
        """
        return db.query(ExpenseApprovalStep).filter(
            ExpenseApprovalStep.approver_id == approver_id,
            ExpenseApprovalStep.status == "PENDING"
        ).order_by(ExpenseApprovalStep.expense_id).all()
