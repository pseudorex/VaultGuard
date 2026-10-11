from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import AuthService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account (Owner or Custodian)."""
    user = AuthService.register_user(db, user_in)
    return user


@router.post("/login", response_model=TokenResponse)
def login(login_in: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate and obtain a JWT bearer token."""
    user, token = AuthService.authenticate_user(db, login_in.email, login_in.password)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Logout endpoint (clears client-side bearer tokens)."""
    return {"message": "Successfully logged out"}
