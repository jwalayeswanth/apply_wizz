from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_model: str

    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    email_from: str
    email_to: str
    smtp_use_ssl: bool
    smtp_use_tls: bool

    dry_run: bool


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_settings() -> Settings:
    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not openai_api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in environment.")

    openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini").strip()

    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_username = os.getenv("SMTP_USERNAME", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    email_from = os.getenv("EMAIL_FROM", "").strip()
    email_to = os.getenv("EMAIL_TO", "").strip()
    smtp_use_ssl = _env_bool("SMTP_USE_SSL", default=False)
    smtp_use_tls = _env_bool("SMTP_USE_TLS", default=True)

    if not (smtp_host and smtp_username and smtp_password and email_from and email_to):
        # Allow running without email credentials if DRY_RUN=true (we'll still build .eml files).
        # If DRY_RUN=false, we require full SMTP credentials.
        dry_run = _env_bool("DRY_RUN", default=False)
        if not dry_run:
            raise RuntimeError(
                "Missing SMTP/email configuration. Set SMTP_HOST, SMTP_PORT, SMTP_USERNAME, "
                "SMTP_PASSWORD, EMAIL_FROM, EMAIL_TO (or set DRY_RUN=true to avoid sending)."
            )

    return Settings(
        openai_api_key=openai_api_key,
        openai_model=openai_model,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password,
        email_from=email_from,
        email_to=email_to,
        smtp_use_ssl=smtp_use_ssl,
        smtp_use_tls=smtp_use_tls,
        dry_run=_env_bool("DRY_RUN", default=False),
    )

