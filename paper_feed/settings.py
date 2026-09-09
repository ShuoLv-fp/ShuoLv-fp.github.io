"""Configuration for the private paper-feed ingestion job."""

from __future__ import annotations

from dataclasses import dataclass, field
import os


class SettingsError(ValueError):
    """Required configuration is absent or invalid."""


def _csv_setting(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    value = os.getenv(name)
    if value is None:
        return default
    return tuple(item.strip() for item in value.split(",") if item.strip())


@dataclass(frozen=True)
class Settings:
    foxmail_username: str = field(default="", repr=False)
    foxmail_imap_auth_code: str = field(default="", repr=False)
    deepseek_api_key: str = field(default="", repr=False)
    imap_host: str = "imap.qq.com"
    imap_port: int = 993
    imap_folder: str = "INBOX"
    model: str = "deepseek-v4-flash-vision-exp"
    deepseek_base_url: str = "https://api.deepseek.com"
    allowed_senders: tuple[str, ...] = ("scholaralerts-noreply@google.com",)
    subject_terms: tuple[str, ...] = ("Scholar Alert", "Google Scholar")
    recurring_lookback_days: int = 7
    first_run_lookback_days: int = 30
    timeout_seconds: int = 20
    model_attempts: int = 3

    @classmethod
    def from_env(cls, require_credentials: bool) -> "Settings":
        username = os.getenv("FOXMAIL_USERNAME", "")
        auth_code = os.getenv("FOXMAIL_IMAP_AUTH_CODE", "")
        api_key = os.getenv("DEEPSEEK_API_KEY", "")
        if require_credentials:
            missing = tuple(name for name, value in (
                ("FOXMAIL_USERNAME", username),
                ("FOXMAIL_IMAP_AUTH_CODE", auth_code),
                ("DEEPSEEK_API_KEY", api_key),
            ) if not value)
            if missing:
                raise SettingsError("missing required environment variables: " + ", ".join(missing))
        return cls(
            foxmail_username=username,
            foxmail_imap_auth_code=auth_code,
            deepseek_api_key=api_key,
            imap_host=os.getenv("FOXMAIL_IMAP_HOST", "imap.qq.com"),
            imap_port=int(os.getenv("FOXMAIL_IMAP_PORT", "993")),
            imap_folder=os.getenv("FOXMAIL_IMAP_FOLDER", "INBOX"),
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash-vision-exp"),
            deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            allowed_senders=_csv_setting("PAPER_FEED_ALLOWED_SENDERS", ("scholaralerts-noreply@google.com",)),
            subject_terms=_csv_setting("PAPER_FEED_SUBJECT_TERMS", ("Scholar Alert", "Google Scholar")),
            recurring_lookback_days=int(os.getenv("PAPER_FEED_RECURRING_LOOKBACK_DAYS", "7")),
            first_run_lookback_days=int(os.getenv("PAPER_FEED_FIRST_RUN_LOOKBACK_DAYS", "30")),
            timeout_seconds=int(os.getenv("PAPER_FEED_TIMEOUT_SECONDS", "20")),
            model_attempts=int(os.getenv("PAPER_FEED_MODEL_ATTEMPTS", "3")),
        )
