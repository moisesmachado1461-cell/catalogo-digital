from urllib.parse import urlsplit

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
    storage_provider: str = "local"  # local | s3 | cloudinary
    s3_endpoint_url: str | None = None
    s3_region: str = "auto"
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_bucket_name: str | None = None
    s3_public_base_url: str | None = None

    # Cloudinary (alternativa simples para produção)
    cloudinary_cloud_name: str | None = None
    cloudinary_api_key: str | None = None
    cloudinary_api_secret: str | None = None

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

    # Cobrança das assinaturas do próprio SaaS
    billing_default_currency: str = "BRL"
    billing_invoice_lead_days: int = 7
    billing_grace_days: int = 5

    # Mercado Pago — cobrança SaaS via Pix imediato
    mercado_pago_access_token: str | None = None
    mercado_pago_webhook_secret: str | None = None
    mercado_pago_webhook_url: str | None = None
    mercado_pago_test_mode: bool = False

    # Pagamentos dos clientes das lojas via Marketplace/OAuth
    mercado_pago_marketplace_app_id: str | None = None
    mercado_pago_marketplace_client_id: str | None = None
    mercado_pago_marketplace_client_secret: str | None = None
    mercado_pago_marketplace_redirect_uri: str | None = None
    mercado_pago_marketplace_webhook_secret: str | None = None
    store_payment_credentials_key: str | None = None
    store_payments_test_mode: bool = False
    frontend_public_url: str | None = None

    # Assistente IA — compatível com APIs no formato Chat Completions
    assistant_ai_enabled: bool = False
    assistant_ai_api_url: str | None = None
    assistant_ai_api_key: str | None = None
    assistant_ai_model: str | None = None
    assistant_ai_timeout_seconds: int = 20
    assistant_ai_max_tokens: int = 320
    assistant_ai_temperature: float = 0.2
    assistant_ai_requests_per_minute: int = 12

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

    @property
    def cloudinary_configuration_complete(self) -> bool:
        return all(
            [
                self.cloudinary_cloud_name,
                self.cloudinary_api_key,
                self.cloudinary_api_secret,
            ]
        )

    @property
    def store_payment_marketplace_configuration_complete(self) -> bool:
        return all(
            [
                self.mercado_pago_marketplace_app_id,
                self.mercado_pago_marketplace_client_id,
                self.mercado_pago_marketplace_client_secret,
                self.mercado_pago_marketplace_redirect_uri,
                self.mercado_pago_marketplace_webhook_secret,
                self.store_payment_credentials_key,
            ]
        )

    @property
    def public_frontend_base_url(self) -> str | None:
        if self.frontend_public_url:
            return self.frontend_public_url.rstrip("/")
        return self.allowed_origins[0] if self.allowed_origins else None

    @property
    def assistant_ai_configuration_complete(self) -> bool:
        return bool(
            self.assistant_ai_enabled
            and self.assistant_ai_api_url
            and self.assistant_ai_api_key
            and self.assistant_ai_model
        )

    def validate_for_runtime(self) -> None:
        if self.storage_provider_normalized not in {"local", "s3", "cloudinary"}:
            raise RuntimeError("STORAGE_PROVIDER deve ser 'local', 's3' ou 'cloudinary'.")

        if self.storage_provider_normalized == "s3" and not self.s3_configuration_complete:
            raise RuntimeError(
                "STORAGE_PROVIDER=s3 exige S3_ENDPOINT_URL, S3_ACCESS_KEY_ID, "
                "S3_SECRET_ACCESS_KEY, S3_BUCKET_NAME e S3_PUBLIC_BASE_URL."
            )

        if self.storage_provider_normalized == "cloudinary" and not self.cloudinary_configuration_complete:
            raise RuntimeError(
                "STORAGE_PROVIDER=cloudinary exige CLOUDINARY_CLOUD_NAME, "
                "CLOUDINARY_API_KEY e CLOUDINARY_API_SECRET."
            )

        if not 0 <= self.sentry_traces_sample_rate <= 1:
            raise RuntimeError("SENTRY_TRACES_SAMPLE_RATE deve ficar entre 0 e 1.")
        if not 0 <= self.billing_invoice_lead_days <= 60:
            raise RuntimeError("BILLING_INVOICE_LEAD_DAYS deve ficar entre 0 e 60.")
        if not 0 <= self.billing_grace_days <= 60:
            raise RuntimeError("BILLING_GRACE_DAYS deve ficar entre 0 e 60.")
        if bool(self.mercado_pago_access_token) != bool(self.mercado_pago_webhook_secret):
            raise RuntimeError("Configure MERCADO_PAGO_ACCESS_TOKEN e MERCADO_PAGO_WEBHOOK_SECRET juntos.")
        marketplace_values = [
            self.mercado_pago_marketplace_client_id,
            self.mercado_pago_marketplace_client_secret,
            self.mercado_pago_marketplace_redirect_uri,
            self.mercado_pago_marketplace_webhook_secret,
            self.store_payment_credentials_key,
        ]
        if any(marketplace_values) and not all(marketplace_values):
            raise RuntimeError(
                "Marketplace Mercado Pago exige CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, WEBHOOK_SECRET e STORE_PAYMENT_CREDENTIALS_KEY."
            )
        if self.mercado_pago_marketplace_app_id and not str(self.mercado_pago_marketplace_app_id).strip().isdigit():
            raise RuntimeError("MERCADO_PAGO_MARKETPLACE_APP_ID deve ser o ID numérico da aplicação Mercado Pago.")
        if self.mercado_pago_marketplace_redirect_uri:
            parsed_marketplace_redirect = urlsplit(self.mercado_pago_marketplace_redirect_uri)
            if parsed_marketplace_redirect.scheme not in {"http", "https"} or not parsed_marketplace_redirect.netloc:
                raise RuntimeError("MERCADO_PAGO_MARKETPLACE_REDIRECT_URI deve ser uma URL HTTP/HTTPS válida.")
        if self.frontend_public_url:
            parsed_frontend = urlsplit(self.frontend_public_url)
            if parsed_frontend.scheme not in {"http", "https"} or not parsed_frontend.netloc:
                raise RuntimeError("FRONTEND_PUBLIC_URL deve ser uma URL HTTP/HTTPS válida.")
        if self.store_payment_credentials_key:
            try:
                from cryptography.fernet import Fernet
                Fernet(self.store_payment_credentials_key.encode("utf-8"))
            except Exception as exc:
                raise RuntimeError("STORE_PAYMENT_CREDENTIALS_KEY deve ser uma chave Fernet válida.") from exc
        if self.mercado_pago_webhook_url:
            parsed_webhook = urlsplit(self.mercado_pago_webhook_url)
            if parsed_webhook.scheme not in {"http", "https"} or not parsed_webhook.netloc:
                raise RuntimeError("MERCADO_PAGO_WEBHOOK_URL deve ser uma URL HTTP/HTTPS válida.")
        if self.assistant_ai_enabled:
            if not self.assistant_ai_api_url or not self.assistant_ai_api_key or not self.assistant_ai_model:
                raise RuntimeError(
                    "ASSISTANT_AI_ENABLED=true exige ASSISTANT_AI_API_URL, ASSISTANT_AI_API_KEY e ASSISTANT_AI_MODEL."
                )
            parsed_ai_url = urlsplit(self.assistant_ai_api_url)
            if parsed_ai_url.scheme not in {"http", "https"} or not parsed_ai_url.netloc:
                raise RuntimeError("ASSISTANT_AI_API_URL deve ser uma URL HTTP/HTTPS válida.")
        if not 5 <= self.assistant_ai_timeout_seconds <= 60:
            raise RuntimeError("ASSISTANT_AI_TIMEOUT_SECONDS deve ficar entre 5 e 60.")
        if not 100 <= self.assistant_ai_max_tokens <= 800:
            raise RuntimeError("ASSISTANT_AI_MAX_TOKENS deve ficar entre 100 e 800.")
        if not 0 <= self.assistant_ai_temperature <= 1:
            raise RuntimeError("ASSISTANT_AI_TEMPERATURE deve ficar entre 0 e 1.")
        if not 1 <= self.assistant_ai_requests_per_minute <= 60:
            raise RuntimeError("ASSISTANT_AI_REQUESTS_PER_MINUTE deve ficar entre 1 e 60.")
        if self.jwt_algorithm not in {"HS256", "HS384", "HS512"}:
            raise RuntimeError("JWT_ALGORITHM deve usar HS256, HS384 ou HS512.")
        if not 5 <= self.access_token_expire_minutes <= 1440:
            raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES deve ficar entre 5 e 1440.")
        if not 3 <= self.max_login_attempts <= 20:
            raise RuntimeError("MAX_LOGIN_ATTEMPTS deve ficar entre 3 e 20.")
        if not 1 <= self.login_lock_minutes <= 1440:
            raise RuntimeError("LOGIN_LOCK_MINUTES deve ficar entre 1 e 1440.")
        if not 3 <= self.login_rate_limit_per_minute <= 120:
            raise RuntimeError("LOGIN_RATE_LIMIT_PER_MINUTE deve ficar entre 3 e 120.")

        if self.environment.lower() == "production":
            if self.jwt_secret in {"change-me", "", None} or len(self.jwt_secret) < 32:
                raise RuntimeError("Em produção, defina JWT_SECRET forte com pelo menos 32 caracteres.")
            if "*" in self.allowed_origins:
                raise RuntimeError("Em produção, CORS_ORIGINS não pode usar '*'.")
            if self.database_url.startswith("sqlite"):
                raise RuntimeError("Em produção, use PostgreSQL em DATABASE_URL; SQLite fica somente no desenvolvimento.")
            if self.mercado_pago_webhook_url and not self.mercado_pago_webhook_url.startswith("https://"):
                raise RuntimeError("Em produção, MERCADO_PAGO_WEBHOOK_URL deve usar HTTPS.")
            if self.mercado_pago_marketplace_redirect_uri and not self.mercado_pago_marketplace_redirect_uri.startswith("https://"):
                raise RuntimeError("Em produção, MERCADO_PAGO_MARKETPLACE_REDIRECT_URI deve usar HTTPS.")
            if self.frontend_public_url and not self.frontend_public_url.startswith("https://"):
                raise RuntimeError("Em produção, FRONTEND_PUBLIC_URL deve usar HTTPS.")
            if self.assistant_ai_enabled and not self.assistant_ai_api_url.startswith("https://"):
                raise RuntimeError("Em produção, ASSISTANT_AI_API_URL deve usar HTTPS.")
            if not self.allowed_origins:
                raise RuntimeError("Em produção, informe pelo menos uma origem HTTPS em CORS_ORIGINS.")
            invalid_origins = [origin for origin in self.allowed_origins if not origin.startswith("https://")]
            if invalid_origins:
                raise RuntimeError("Em produção, CORS_ORIGINS deve conter apenas endereços HTTPS.")
            for origin in self.allowed_origins:
                parsed = urlsplit(origin)
                if (
                    parsed.scheme != "https"
                    or not parsed.netloc
                    or parsed.username
                    or parsed.password
                    or parsed.query
                    or parsed.fragment
                    or parsed.path not in {"", "/"}
                ):
                    raise RuntimeError(
                        "CORS_ORIGINS deve conter apenas origens HTTPS, sem caminho, credenciais, query ou fragmento."
                    )


settings = Settings()
