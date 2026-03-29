from sqlalchemy.orm import Session
from app.models import Company
from app.services.currency_service import CurrencyService


class CompanyService:
    """Service for managing company records."""
    
    @staticmethod
    def create_company(db: Session, name: str, country: str) -> Company:
        """
        Create a new company with base currency from REST Countries API.
        
        Args:
            db: Database session
            name: Company name
            country: Country name or code
            
        Returns:
            Created Company instance
            
        Raises:
            ValueError: If country is invalid or currency cannot be determined
            RuntimeError: If REST Countries API fails
        """
        # Get base currency for the country
        base_currency = CurrencyService.get_currency_for_country(country)
        
        # Create company record
        company = Company(
            name=name,
            country=country,
            base_currency=base_currency
        )
        
        db.add(company)
        db.flush()  # Get company.id without committing
        
        return company
    
    @staticmethod
    def get_company(db: Session, company_id: int) -> Company:
        """
        Get a company by ID.
        
        Args:
            db: Database session
            company_id: Company ID
            
        Returns:
            Company instance
            
        Raises:
            ValueError: If company not found
        """
        company = db.query(Company).filter(Company.id == company_id).first()
        
        if not company:
            raise ValueError(f"Company with ID {company_id} not found")
        
        return company
