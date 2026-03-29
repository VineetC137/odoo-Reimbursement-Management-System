from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.services.auth_service import AuthService
from app.models import User


security = HTTPBearer()


class TokenPayload:
    """Token payload data class."""
    def __init__(self, user_id: int, company_id: int, role: str):
        self.user_id = user_id
        self.company_id = company_id
        self.role = role


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> TokenPayload:
    """
    Dependency to get current authenticated user from JWT token.
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
        
    Returns:
        TokenPayload with user_id, company_id, and role
        
    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    token = credentials.credentials
    payload = AuthService.verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return TokenPayload(
        user_id=payload["user_id"],
        company_id=payload["company_id"],
        role=payload["role"]
    )


def require_role(required_role: str):
    """
    Dependency factory to require a specific role.
    
    Args:
        required_role: Required role (ADMIN, MANAGER, EMPLOYEE)
        
    Returns:
        Dependency function that validates role
    """
    def role_checker(current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. {required_role} role required."
            )
        return current_user
    
    return role_checker


def require_admin(current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
    """Dependency to require ADMIN role."""
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. ADMIN role required."
        )
    return current_user


def require_manager(current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
    """Dependency to require MANAGER role."""
    if current_user.role != "MANAGER":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. MANAGER role required."
        )
    return current_user


def require_employee(current_user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
    """Dependency to require EMPLOYEE role."""
    if current_user.role != "EMPLOYEE":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. EMPLOYEE role required."
        )
    return current_user
