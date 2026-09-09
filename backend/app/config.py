from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Catálogo Digital"
    environment: str = "development"
    database_url: str = "sqlite:///./catalogo.db"
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: str = "http://127.0.0.1:5500,http://localhost:5500"

    # Uploads e armazenamento
    upload_dir: str = "uploads"
    storage_provider: str = "local"  # local | s3
    s3_endpoint_url: str | None = None
    s3_region: str = "auto"
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_bucket_name: str | None = None
    s3_public_base_url: str | None = None

    # Segurança / operação
    max_login_attempts: int = 5
    login_lock_minutes: int = 15
    login_rate_limit_per_minute: int = 15
    log_level: str = "INFO"

    # Observabilidade opcional
    sentry_dsn: str | None = None
    sentry_traces_sample_rate: float = 0.05

    # URLs públicas / Render
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

    @property
    def storage_provider_normalized(self) -> str:
        return self.storage_provider.strip().lower()

    @property
    def s3_configuration_complete(self) -> bool:
        return all(
            [
                self.s3_endpoint_url,
                self.s3_access_key_id,
                self.s3_secret_access_key,
                self.s3_bucket_name,
                self.s3_public_base_url,
            ]
        )

    def validate_for_runtime(self) -> None:
        if self.storage_provider_normalized not in {"local", "s3"}:
            raise RuntimeError("STORAGE_PROVIDER deve ser 'local' ou 's3'.")

        if self.storage_provider_normalized == "s3" and not self.s3_configuration_complete:
            raise RuntimeError(
                "STORAGE_PROVIDER=s3 exige S3_ENDPOINT_URL, S3_ACCESS_KEY_ID, "
                "S3_SECRET_ACCESS_KEY, S3_BUCKET_NAME e S3_PUBLIC_BASE_URL."
            )

        if not 0 <= self.sentry_traces_sample_rate <= 1:
            raise RuntimeError("SENTRY_TRACES_SAMPLE_RATE deve ficar entre 0 e 1.")

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
