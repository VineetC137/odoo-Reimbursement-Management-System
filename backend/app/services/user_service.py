from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional
from app.models import User
from app.services.auth_service import AuthService


class UserService:
    """Service for managing user records."""
    
    @staticmethod
    def create_user(
        db: Session,
        company_id: int,
        name: str,
        email: str,
        password: str,
        role: str,
        manager_id: Optional[int] = None
    ) -> User:
        """
        Create a new user with email uniqueness validation.
        
        Args:
            db: Database session
            company_id: Company ID
            name: User's full name
            email: User's email address (must be unique)
            password: Plain text password (will be hashed)
            role: User role (ADMIN, MANAGER, EMPLOYEE)
            manager_id: Optional manager user ID
            
        Returns:
            Created User instance
            
        Raises:
            ValueError: If email already exists, manager_id is invalid, or role is invalid
        """
        # Validate role
        valid_roles = ['ADMIN', 'MANAGER', 'EMPLOYEE']
        if role not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
        
        # Check email uniqueness
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            raise ValueError(f"Email {email} is already registered")
        
        # Validate manager_id if provided
        if manager_id is not None:
            manager = db.query(User).filter(User.id == manager_id).first()
            if not manager:
                raise ValueError(f"Manager with ID {manager_id} not found")
            if manager.role != 'MANAGER':
                raise ValueError(f"User with ID {manager_id} is not a MANAGER")
            if manager.company_id != company_id:
                raise ValueError(f"Manager must belong to the same company")
        
        # Hash password
        password_hash = AuthService.hash_password(password)
        
        # Create user
        user = User(
            company_id=company_id,
            name=name,
            email=email,
            password_hash=password_hash,
            role=role,
            manager_id=manager_id
        )
        
        try:
            db.add(user)
            db.flush()
            return user
        except IntegrityError:
            db.rollback()
            raise ValueError(f"Email {email} is already registered")
    
    @staticmethod
    def update_user(
        db: Session,
        user_id: int,
        name: Optional[str] = None,
        email: Optional[str] = None,
        role: Optional[str] = None,
        manager_id: Optional[int] = None
    ) -> User:
        """
        Update an existing user with manager_id validation.
        
        Args:
            db: Database session
            user_id: User ID to update
            name: Optional new name
            email: Optional new email (must be unique)
            role: Optional new role (ADMIN, MANAGER, EMPLOYEE)
            manager_id: Optional new manager ID
            
        Returns:
            Updated User instance
            
        Raises:
            ValueError: If user not found, email already exists, manager_id is invalid, or role is invalid
        """
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Update name if provided
        if name is not None:
            user.name = name
        
        # Update email if provided
        if email is not None and email != user.email:
            existing_user = db.query(User).filter(User.email == email).first()
            if existing_user:
                raise ValueError(f"Email {email} is already registered")
            user.email = email
        
        # Update role if provided
        if role is not None:
            valid_roles = ['ADMIN', 'MANAGER', 'EMPLOYEE']
            if role not in valid_roles:
                raise ValueError(f"Invalid role. Must be one of: {', '.join(valid_roles)}")
            user.role = role
        
        # Update manager_id if provided (including None to clear manager)
        if manager_id is not None:
            manager = db.query(User).filter(User.id == manager_id).first()
            if not manager:
                raise ValueError(f"Manager with ID {manager_id} not found")
            if manager.role != 'MANAGER':
                raise ValueError(f"User with ID {manager_id} is not a MANAGER")
            if manager.company_id != user.company_id:
                raise ValueError(f"Manager must belong to the same company")
            user.manager_id = manager_id
        
        try:
            db.flush()
            return user
        except IntegrityError:
            db.rollback()
            raise ValueError(f"Email {email} is already registered")
    
    @staticmethod
    def get_users(
        db: Session,
        company_id: int,
        role: Optional[str] = None
    ) -> list[User]:
        """
        Get users with optional role filtering.
        
        Args:
            db: Database session
            company_id: Company ID to filter by
            role: Optional role filter (ADMIN, MANAGER, EMPLOYEE)
            
        Returns:
            List of User instances
        """
        query = db.query(User).filter(User.company_id == company_id)
        
        if role is not None:
            query = query.filter(User.role == role)
        
        return query.order_by(User.created_at.desc()).all()
    
    @staticmethod
    def get_user_by_email(db: Session, email: str) -> Optional[User]:
        """
        Get a user by email for login lookup.
        
        Args:
            db: Database session
            email: User's email address
            
        Returns:
            User instance if found, None otherwise
        """
        return db.query(User).filter(User.email == email).first()
