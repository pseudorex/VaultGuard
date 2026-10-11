from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.errors import VaultGuardException
from app.db.session import init_db, SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password
from app.services.audit_service import AuditService

from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.backups import router as backups_router
from app.api.routes.recovery import router as recovery_router
from app.api.routes.approvals import router as approvals_router
from app.api.routes.integrity import router as integrity_router
from app.api.routes.audit import router as audit_router


def seed_demo_users():
    """Seed initial demo accounts if not present."""
    db = SessionLocal()
    try:
        demo_accounts = [
            ("owner@demo.com", "Owner Demo", "password123", UserRole.OWNER),
            ("custodian1@demo.com", "Alice (Security Custodian)", "password123", UserRole.CUSTODIAN),
            ("custodian2@demo.com", "Bob (Compliance Custodian)", "password123", UserRole.CUSTODIAN),
            ("custodian3@demo.com", "Carol (Infra Custodian)", "password123", UserRole.CUSTODIAN),
            ("admin@demo.com", "System Admin", "password123", UserRole.ADMIN),
        ]
        for email, name, password, role in demo_accounts:
            existing = db.query(User).filter(User.email == email).first()
            if not existing:
                user = User(
                    email=email,
                    display_name=name,
                    password_hash=hash_password(password),
                    role=role,
                    is_active=True,
                )
                db.add(user)
                db.flush()
                AuditService.log_event(
                    db=db,
                    actor_id=user.id,
                    action="SYSTEM_INIT_SEED_USER",
                    target_type="USER",
                    target_id=user.id,
                    outcome="SUCCESS",
                    metadata={"email": email, "role": role.value}
                )
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    seed_demo_users()
    yield
    # Shutdown (cleanup if needed)


app = FastAPI(
    title=settings.APP_NAME,
    description="Threshold-Based Secure Backup & Recovery Platform using AES-256-GCM, Shamir Secret Sharing (2-of-3), and Hash-Chained Audit Ledger.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "X-Restored-Filename"],
)

# Global Exception Handler
@app.exception_handler(VaultGuardException)
async def vaultguard_exception_handler(request: Request, exc: VaultGuardException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_code": exc.error_code,
            "detail": exc.detail,
        },
        headers=exc.headers,
    )


# Register Routers
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")
app.include_router(backups_router, prefix="/api")
app.include_router(recovery_router, prefix="/api")
app.include_router(approvals_router, prefix="/api")
app.include_router(integrity_router, prefix="/api")
app.include_router(audit_router, prefix="/api")


@app.get("/api/health", tags=["Health"])
def health_check():
    return {
        "status": "online",
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "threshold": "2-of-3",
        "crypto": "AES-256-GCM + Shamir Secret Sharing",
    }
