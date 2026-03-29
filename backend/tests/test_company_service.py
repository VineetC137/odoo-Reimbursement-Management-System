import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Company
from app.services.company_service import CompanyService


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


class TestCompanyService:
    """Tests for CompanyService."""
    
    def test_create_company_success(self, db_session):
        """Test successful company creation with currency lookup."""
        with patch('app.services.company_service.CurrencyService.get_currency_for_country') as mock_currency:
            mock_currency.return_value = "USD"
            
            company = CompanyService.create_company(
                db=db_session,
                name="Test Company",
                country="United States"
            )
            
            assert company.name == "Test Company"
            assert company.country == "United States"
            assert company.base_currency == "USD"
            assert company.id is not None
            mock_currency.assert_called_once_with("United States")
    
    def test_create_company_currency_service_error(self, db_session):
        """Test error handling when CurrencyService fails."""
        with patch('app.services.company_service.CurrencyService.get_currency_for_country') as mock_currency:
            mock_currency.side_effect = ValueError("Country not found")
            
            with pytest.raises(ValueError, match="Country not found"):
                CompanyService.create_company(
                    db=db_session,
                    name="Test Company",
                    country="InvalidCountry"
                )
    
    def test_create_company_api_error(self, db_session):
        """Test error handling when REST Countries API fails."""
        with patch('app.services.company_service.CurrencyService.get_currency_for_country') as mock_currency:
            mock_currency.side_effect = RuntimeError("API connection failed")
            
            with pytest.raises(RuntimeError, match="API connection failed"):
                CompanyService.create_company(
                    db=db_session,
                    name="Test Company",
                    country="United States"
                )
    
    def test_get_company_success(self, db_session):
        """Test successful company retrieval."""
        # Create a company first
        company = Company(
            name="Test Company",
            country="United States",
            base_currency="USD"
        )
        db_session.add(company)
        db_session.commit()
        
        # Retrieve it
        retrieved = CompanyService.get_company(db_session, company.id)
        
        assert retrieved.id == company.id
        assert retrieved.name == "Test Company"
        assert retrieved.country == "United States"
        assert retrieved.base_currency == "USD"
    
    def test_get_company_not_found(self, db_session):
        """Test error handling when company doesn't exist."""
        with pytest.raises(ValueError, match="Company with ID 999 not found"):
            CompanyService.get_company(db_session, 999)
