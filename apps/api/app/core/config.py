from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """ForgeMind API settings loaded from environment variables."""

    # General
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")  # H-15: default off
    secret_key: str = Field(default="change-me-to-a-random-secret", alias="SECRET_KEY")

    # Server
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_workers: int = Field(default=1, alias="API_WORKERS")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    # Database
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="forgemind", alias="POSTGRES_DB")
    postgres_user: str = Field(default="forgemind", alias="POSTGRES_USER")
    postgres_password: str = Field(default="change-me", alias="POSTGRES_PASSWORD")
    database_url: str = Field(default="", alias="DATABASE_URL")

    # Redis
    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_url: str = Field(default="", alias="REDIS_URL")

    # GitHub Integration
    github_webhook_secret: str = Field(default="", alias="GITHUB_WEBHOOK_SECRET")
    github_app_id: str = Field(default="", alias="GITHUB_APP_ID")
    github_private_key: str = Field(default="", alias="GITHUB_PRIVATE_KEY")
    github_api_token: str = Field(default="", alias="GITHUB_API_TOKEN")

    # LLM / Planner
    planner_model: str = Field(default="gpt-4o", alias="PLANNER_MODEL")
    planner_temperature: float = Field(default=0.4, alias="PLANNER_TEMPERATURE")
    planner_max_tokens: int = Field(default=4096, alias="PLANNER_MAX_TOKENS")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    google_api_key: str = Field(default="", alias="GOOGLE_API_KEY")

    # Project metadata
    project_name: str = "ForgeMind API"
    version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]

    def model_post_init(self, __context: object) -> None:
        if not self.database_url:
            self.database_url = (
                f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
                f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
            )
        if not self.redis_url:
            self.redis_url = f"redis://{self.redis_host}:{self.redis_port}/0"

        # M-22: Expanded safety gate — enforce strong secrets in any non-development
        # environment. "staging" and "test" are internet-accessible in many deployments
        # and must not start with default credentials.
        _unsafe_envs = {"production", "staging", "test"}
        if self.app_env in _unsafe_envs:
            default_secret = "change-me-to-a-random-secret"
            if self.secret_key == default_secret:
                raise RuntimeError(
                    f"SECRET_KEY is set to the built-in default while "
                    f"APP_ENV={self.app_env}. Refusing to start. Generate a "
                    'secure value with: python -c "import secrets; '
                    'print(secrets.token_urlsafe(48))"'
                )
            if len(self.secret_key) < 32:
                raise RuntimeError(
                    f"SECRET_KEY must be at least 32 characters in "
                    f"{self.app_env} (got {len(self.secret_key)}). Refusing "
                    "to start."
                )
            default_db_password = "change-me"
            if self.postgres_password == default_db_password:
                raise RuntimeError(
                    f"POSTGRES_PASSWORD is set to the built-in default "
                    f"while APP_ENV={self.app_env}. Refusing to start."
                )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
