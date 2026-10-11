import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "VaultGuard"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = ""
    JWT_SECRET: str = "vaultguard-super-secret-development-key-32bytes-secure-2026!"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    STORAGE_DIR: str = ""
    MAX_UPLOAD_SIZE_MB: int = 10
    RECOVERY_REQUEST_TTL_HOURS: int = 24
    FRONTEND_ORIGINS: str = "http://127.0.0.1:5500,http://localhost:5500,http://127.0.0.1:3000,http://localhost:3000,http://127.0.0.1:8000,http://localhost:8000"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.FRONTEND_ORIGINS.split(",") if origin.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def storage_path(self) -> Path:
        if self.STORAGE_DIR:
            base = Path(self.STORAGE_DIR)
            if not base.is_absolute():
                base = (BACKEND_DIR / base).resolve()
        else:
            base = (BACKEND_DIR / "data").resolve()
        base.mkdir(parents=True, exist_ok=True)
        return base

    @property
    def db_url(self) -> str:
        if self.DATABASE_URL and not self.DATABASE_URL.startswith("sqlite:///./"):
            return self.DATABASE_URL
        
        # Ensure data dir exists
        db_file = self.storage_path / "vaultguard.db"
        db_file.parent.mkdir(parents=True, exist_ok=True)
        # Convert to standard SQLite absolute URI (e.g. sqlite:///D:/VaultGuard/backend/data/vaultguard.db)
        posix_path = db_file.as_posix()
        return f"sqlite:///{posix_path}"

    @property
    def ciphertext_path(self) -> Path:
        path = self.storage_path / "ciphertext"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def shares_path(self) -> Path:
        path = self.storage_path / "shares"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def temp_path(self) -> Path:
        path = self.storage_path / "temp"
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
