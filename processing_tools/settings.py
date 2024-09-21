import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    debug: bool = bool(os.environ.get("DEBUG", False))
    browserless_server_endpoint: str = os.environ.get(
        "BROWSERLESS_SERVER_ENDPOINT_URL", "http://localhost:3000"
    )
    browserless_token: str = ""
    iter_chunk_size: int = 512
    environment: str = os.environ.get("ENVIRONMENT", "local")

    # Sentry config
    sentry_dsn: str = os.environ.get("SENTRY_DSN", "")
    git_sha: str = os.environ.get("GIT_SHA", "local")
    sentry_release: str = f"{environment}-processing-tools@{git_sha}"

    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    # recommend adjusting this value in production.
    sentry_sample_rate: float = float(os.environ.get("SENTRY_SAMPLE_RATE", 1))


settings = Settings()
