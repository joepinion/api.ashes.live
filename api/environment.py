"""Configuration settings, loaded from environment variables

Typical usage:

    from api.environment import settings
"""

from pydantic_settings import BaseSettings


class ApplicationSettings(BaseSettings):
    site_name: str = "Ashes Deckbuilder"
    env: str = "production"

    allow_exports: bool = False
    exports_per_request: int = 30

    postgres_user: str
    postgres_password: str = ""
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    debug: bool = False

    access_token_expiry_hours: int = 24
    access_token_remember_me_days: int = 365
    secret_key: str

    pagination_default_limit: int = 30
    pagination_max_limit: int = 100

    # Email properties
    mail_sender_address: str | None = None
    mail_debug_recipient: str | None = None

    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None

    sendgrid_api_key: str | None = None
    sendgrid_invite_template: str | None = None
    sendgrid_reset_template: str | None = None

    @property
    def access_token_expiry(self) -> int:
        """Token expiry in minutes"""
        return self.access_token_expiry_hours * 60

    @property
    def postgres_url(self) -> str:
        """Database connection URL"""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}"
            f":{self.postgres_port}/{self.postgres_db}"
        )


# Configure settings object from environment variables
settings = ApplicationSettings()
