from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password, create_access_token
from app.core.errors import ConflictException, UnauthorizedException, BadRequestException
from app.services.audit_service import AuditService


class AuthService:
    @staticmethod
    def register_user(db: Session, user_in: UserCreate) -> User:
        """Register a new user account."""
        # Check if email exists
        existing_user = db.execute(select(User).where(User.email == user_in.email.lower())).scalar_one_or_none()
        if existing_user:
            raise ConflictException(f"User with email '{user_in.email}' already exists")

        if len(user_in.password) < 6:
            raise BadRequestException("Password must be at least 6 characters long")

        user = User(
            email=user_in.email.lower().strip(),
            password_hash=hash_password(user_in.password),
            display_name=user_in.display_name.strip(),
            role=user_in.role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Record in audit log
        AuditService.log_event(
            db=db,
            actor_id=user.id,
            action="USER_REGISTERED",
            target_type="USER",
            target_id=user.id,
            outcome="SUCCESS",
            metadata={"email": user.email, "role": user.role.value, "display_name": user.display_name}
        )

        return user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> tuple[User, str]:
        """Authenticate user by email and password, return user and JWT token."""
        user = db.execute(select(User).where(User.email == email.lower().strip())).scalar_one_or_none()
        
        if not user or not verify_password(password, user.password_hash):
            AuditService.log_event(
                db=db,
                actor_id=user.id if user else None,
                action="USER_LOGIN_FAILED",
                target_type="AUTH",
                target_id=email,
                outcome="FAILURE",
                metadata={"attempted_email": email}
            )
            raise UnauthorizedException("Invalid email or password")

        if not user.is_active:
            raise UnauthorizedException("User account is inactive")

        token = create_access_token(
            subject=user.id,
            role=user.role.value,
            extra_claims={"email": user.email, "name": user.display_name}
        )

        AuditService.log_event(
            db=db,
            actor_id=user.id,
            action="USER_LOGIN_SUCCESS",
            target_type="AUTH",
            target_id=user.id,
            outcome="SUCCESS",
            metadata={"email": user.email, "role": user.role.value}
        )

        return user, token
