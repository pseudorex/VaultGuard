from typing import Annotated, Generator
from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, UserRole
from app.core.security import decode_access_token
from app.core.errors import UnauthorizedException, ForbiddenException

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    token_auth: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """Dependency that authenticates the user via Bearer JWT token."""
    if not token_auth or not token_auth.credentials:
        raise UnauthorizedException("Authentication token is required")

    payload = decode_access_token(token_auth.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException("Invalid token payload")

    user = db.get(User, user_id)
    if not user:
        raise UnauthorizedException("User no longer exists")
    if not user.is_active:
        raise UnauthorizedException("User account is inactive")

    return user


def require_role(*roles: UserRole):
    """Dependency factory ensuring current user possesses one of the allowed roles."""
    def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role != UserRole.ADMIN and current_user.role not in roles:
            raise ForbiddenException(
                f"Access denied. Requires one of roles: {[r.value for r in roles]}"
            )
        return current_user
    return role_checker
