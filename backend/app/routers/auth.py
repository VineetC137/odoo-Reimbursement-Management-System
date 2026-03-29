from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    LoginRequest, 
    LoginResponse, 
    SignupInitialRequest, 
    SignupInitialResponse,
    UserProfile,
    CompanyProfile
)
from app.services.auth_service import AuthService
from app.services.company_service import CompanyService
from app.models import User, Company

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user with email and password.
    
    Returns JWT token and user profile on success.
    Returns 401 error if credentials are invalid.
    """
    # Find user by email
    user = db.query(User).filter(User.email == request.email).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password
    if not AuthService.verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create JWT token
    token = AuthService.create_token(
        user_id=user.id,
        company_id=user.company_id,
        role=user.role
    )
    
    # Return token and user profile
    user_profile = UserProfile.model_validate(user)
    
    return LoginResponse(token=token, user=user_profile)


@router.post("/signup-initial", response_model=SignupInitialResponse)
def signup_initial(request: SignupInitialRequest, db: Session = Depends(get_db)):
    """
    Create initial company and admin user account.
    
    This endpoint:
    1. Calls REST Countries API to get base currency for the country
    2. Creates a Company record
    3. Creates an admin User record
    4. Returns JWT token, user profile, and company profile
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create company using CompanyService (integrates with REST Countries API)
    try:
        company = CompanyService.create_company(
            db=db,
            name=f"{request.name}'s Company",
            country=request.country
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    
    # Hash password
    password_hash = AuthService.hash_password(request.password)
    
    # Create admin user
    user = User(
        company_id=company.id,
        name=request.name,
        email=request.email,
        password_hash=password_hash,
        role="ADMIN",
        manager_id=None
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.refresh(company)
    
    # Create JWT token
    token = AuthService.create_token(
        user_id=user.id,
        company_id=user.company_id,
        role=user.role
    )
    
    # Return token, user profile, and company profile
    user_profile = UserProfile.model_validate(user)
    company_profile = CompanyProfile.model_validate(company)
    
    return SignupInitialResponse(
        token=token,
        user=user_profile,
        company=company_profile
    )
