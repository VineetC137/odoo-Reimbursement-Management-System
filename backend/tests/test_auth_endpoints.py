import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app.models import User, Company

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override get_db dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test and drop after"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def test_signup_initial_creates_company_and_user():
    """Test that signup-initial endpoint creates company and admin user"""
    from unittest.mock import patch
    
    # Mock CurrencyService to avoid actual API call
    with patch('app.services.company_service.CurrencyService.get_currency_for_country') as mock_currency:
        mock_currency.return_value = "USD"
        
        response = client.post(
            "/api/auth/signup-initial",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "password": "password123",
                "country": "United States"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "token" in data
        assert "user" in data
        assert "company" in data
        
        # Check user data
        assert data["user"]["name"] == "John Doe"
        assert data["user"]["email"] == "john@example.com"
        assert data["user"]["role"] == "ADMIN"
        
        # Check company data
        assert data["company"]["country"] == "United States"
        assert data["company"]["base_currency"] == "USD"
        
        # Verify CurrencyService was called
        mock_currency.assert_called_once_with("United States")


def test_signup_initial_rejects_duplicate_email():
    """Test that signup-initial rejects duplicate email"""
    from unittest.mock import patch
    
    with patch('app.services.company_service.CurrencyService.get_currency_for_country') as mock_currency:
        mock_currency.return_value = "USD"
        
        # First signup
        client.post(
            "/api/auth/signup-initial",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "password": "password123",
                "country": "United States"
            }
        )
        
        # Second signup with same email
        response = client.post(
            "/api/auth/signup-initial",
            json={
                "name": "Jane Doe",
                "email": "john@example.com",
                "password": "password456",
                "country": "Canada"
            }
        )
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]


def test_login_with_valid_credentials():
    """Test login with valid credentials returns token and user"""
    from unittest.mock import patch
    
    with patch('app.services.company_service.CurrencyService.get_currency_for_country') as mock_currency:
        mock_currency.return_value = "USD"
        
        # First create a user
        client.post(
            "/api/auth/signup-initial",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "password": "password123",
                "country": "United States"
            }
        )
        
        # Now login
        response = client.post(
            "/api/auth/login",
            json={
                "email": "john@example.com",
                "password": "password123"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Check response structure
        assert "token" in data
        assert "user" in data
        
        # Check user data
        assert data["user"]["email"] == "john@example.com"
        assert data["user"]["role"] == "ADMIN"


def test_login_with_invalid_email():
    """Test login with non-existent email returns 401"""
    response = client.post(
        "/api/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


def test_login_with_invalid_password():
    """Test login with wrong password returns 401"""
    from unittest.mock import patch
    
    with patch('app.services.company_service.CurrencyService.get_currency_for_country') as mock_currency:
        mock_currency.return_value = "USD"
        
        # First create a user
        client.post(
            "/api/auth/signup-initial",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "password": "password123",
                "country": "United States"
            }
        )
        
        # Try to login with wrong password
        response = client.post(
            "/api/auth/login",
            json={
                "email": "john@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]


def test_signup_validates_password_length():
    """Test that signup validates minimum password length"""
    response = client.post(
        "/api/auth/signup-initial",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "password": "short",  # Less than 8 characters
            "country": "United States"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_signup_validates_email_format():
    """Test that signup validates email format"""
    response = client.post(
        "/api/auth/signup-initial",
        json={
            "name": "John Doe",
            "email": "invalid-email",  # Invalid email format
            "password": "password123",
            "country": "United States"
        }
    )
    
    assert response.status_code == 422  # Validation error


def test_signup_handles_invalid_country():
    """Test that signup returns 400 when country is invalid"""
    from unittest.mock import patch
    
    with patch('app.services.company_service.CurrencyService.get_currency_for_country') as mock_currency:
        mock_currency.side_effect = ValueError("Country 'InvalidCountry' not found")
        
        response = client.post(
            "/api/auth/signup-initial",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "password": "password123",
                "country": "InvalidCountry"
            }
        )
        
        assert response.status_code == 400
        assert "not found" in response.json()["detail"]


def test_signup_handles_api_failure():
    """Test that signup returns 503 when REST Countries API fails"""
    from unittest.mock import patch
    
    with patch('app.services.company_service.CurrencyService.get_currency_for_country') as mock_currency:
        mock_currency.side_effect = RuntimeError("Failed to connect to REST Countries API")
        
        response = client.post(
            "/api/auth/signup-initial",
            json={
                "name": "John Doe",
                "email": "john@example.com",
                "password": "password123",
                "country": "United States"
            }
        )
        
        assert response.status_code == 503
        assert "REST Countries API" in response.json()["detail"]
