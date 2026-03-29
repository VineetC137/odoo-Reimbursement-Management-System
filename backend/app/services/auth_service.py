import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from app.config import settings


class AuthService:
    """Authentication service for password hashing and JWT token management."""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a plain text password using bcrypt.
        
        Args:
            password: Plain text password to hash
            
        Returns:
            Hashed password string
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain text password against a hashed password.
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against
            
        Returns:
            True if password matches, False otherwise
        """
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    
    @staticmethod
    def create_token(user_id: int, company_id: int, role: str) -> str:
        """
        Create a JWT token with user claims.
        
        Args:
            user_id: User's database ID
            company_id: Company's database ID
            role: User's role (ADMIN, MANAGER, EMPLOYEE)
            
        Returns:
            JWT token string
        """
        expiration = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
        
        payload = {
            "user_id": user_id,
            "company_id": company_id,
            "role": role,
            "exp": expiration
        }
        
        token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
        return token
    
    @staticmethod
    def verify_token(token: str) -> Optional[dict]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string to verify
            
        Returns:
            Dictionary containing token payload (user_id, company_id, role) if valid,
            None if token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token, 
                settings.jwt_secret, 
                algorithms=[settings.jwt_algorithm]
            )
            return payload
        except JWTError:
            return None
