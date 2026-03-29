import pytest
from datetime import datetime, timedelta
from app.services.auth_service import AuthService
from app.config import settings


class TestAuthService:
    """Unit tests for AuthService."""
    
    def test_hash_password(self):
        """Test password hashing produces a valid hash."""
        password = "test_password_123"
        hashed = AuthService.hash_password(password)
        
        # Hash should be different from original password
        assert hashed != password
        # Hash should not be empty
        assert len(hashed) > 0
        # Hash should start with bcrypt identifier
        assert hashed.startswith("$2b$")
    
    def test_hash_password_different_hashes(self):
        """Test that hashing the same password twice produces different hashes."""
        password = "test_password_123"
        hash1 = AuthService.hash_password(password)
        hash2 = AuthService.hash_password(password)
        
        # Different hashes due to salt
        assert hash1 != hash2
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = AuthService.hash_password(password)
        
        # Verification should succeed
        assert AuthService.verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = AuthService.hash_password(password)
        
        # Verification should fail
        assert AuthService.verify_password(wrong_password, hashed) is False
    
    def test_create_token(self):
        """Test JWT token creation with user claims."""
        user_id = 1
        company_id = 10
        role = "EMPLOYEE"
        
        token = AuthService.create_token(user_id, company_id, role)
        
        # Token should not be empty
        assert len(token) > 0
        # Token should be a string
        assert isinstance(token, str)
        # Token should have JWT structure (3 parts separated by dots)
        assert token.count('.') == 2
    
    def test_verify_token_valid(self):
        """Test JWT token verification with valid token."""
        user_id = 1
        company_id = 10
        role = "MANAGER"
        
        token = AuthService.create_token(user_id, company_id, role)
        payload = AuthService.verify_token(token)
        
        # Payload should not be None
        assert payload is not None
        # Payload should contain correct claims
        assert payload["user_id"] == user_id
        assert payload["company_id"] == company_id
        assert payload["role"] == role
        # Payload should contain expiration
        assert "exp" in payload
    
    def test_verify_token_invalid(self):
        """Test JWT token verification with invalid token."""
        invalid_token = "invalid.token.string"
        
        payload = AuthService.verify_token(invalid_token)
        
        # Payload should be None for invalid token
        assert payload is None
    
    def test_verify_token_malformed(self):
        """Test JWT token verification with malformed token."""
        malformed_token = "not-a-valid-jwt"
        
        payload = AuthService.verify_token(malformed_token)
        
        # Payload should be None for malformed token
        assert payload is None
    
    def test_token_expiration(self):
        """Test that token expiration is set correctly."""
        user_id = 1
        company_id = 10
        role = "ADMIN"
        
        token = AuthService.create_token(user_id, company_id, role)
        payload = AuthService.verify_token(token)
        
        # Token should have an expiration claim
        assert "exp" in payload
        
        # Expiration should be a number (timestamp)
        assert isinstance(payload["exp"], (int, float))
        
        # Expiration should be in the future (more than current time)
        import time
        current_timestamp = time.time()
        assert payload["exp"] > current_timestamp
        
        # Expiration should be approximately jwt_expiration_hours from now
        # Allow 2 minutes tolerance for test execution time
        expected_exp = current_timestamp + (settings.jwt_expiration_hours * 3600)
        assert abs(payload["exp"] - expected_exp) < 120
