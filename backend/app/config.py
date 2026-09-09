from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Catálogo Digital"
    environment: str = "development"
    database_url: str = "sqlite:///./catalogo.db"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://127.0.0.1:5500,http://localhost:5500"
    upload_dir: str = "uploads"
    max_login_attempts: int = 5
    login_lock_minutes: int = 15
    api_public_url: str | None = None
    render_external_url: str | None = None
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def allowed_origins(self) -> list[str]:
        return [x.strip().rstrip("/") for x in self.cors_origins.split(",") if x.strip()]

    @property
    def sqlalchemy_database_url(self) -> str:
        """Normaliza URLs de PostgreSQL para o driver psycopg 3 no SQLAlchemy."""
        url = self.database_url.strip()
        if url.startswith("postgres://"):
            return "postgresql+psycopg://" + url[len("postgres://"):]
        if url.startswith("postgresql://"):
            return "postgresql+psycopg://" + url[len("postgresql://"):]
        return url

    @property
    def public_api_base_url(self) -> str | None:
        value = self.api_public_url or self.render_external_url
        return value.rstrip("/") if value else None

    def validate_for_runtime(self) -> None:
        if self.environment.lower() == "production":
            if self.jwt_secret in {"change-me", "", None} or len(self.jwt_secret) < 32:
                raise RuntimeError("Em produção, defina JWT_SECRET forte com pelo menos 32 caracteres.")
            if "*" in self.allowed_origins:
                raise RuntimeError("Em produção, CORS_ORIGINS não pode usar '*'.")
            if self.database_url.startswith("sqlite"):
                raise RuntimeError("Em produção, use PostgreSQL em DATABASE_URL; SQLite fica somente no desenvolvimento.")
            if not self.allowed_origins:
                raise RuntimeError("Em produção, informe pelo menos uma origem HTTPS em CORS_ORIGINS.")
            invalid_origins = [origin for origin in self.allowed_origins if not origin.startswith("https://")]
            if invalid_origins:
                raise RuntimeError("Em produção, CORS_ORIGINS deve conter apenas endereços HTTPS.")


settings = Settings()
