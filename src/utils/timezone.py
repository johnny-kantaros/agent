from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from src.db.database import db_cursor

DEFAULT_TZ_NAME = "America/Los_Angeles"
_SETTINGS_KEY = "timezone"


def get_timezone_name() -> str:
    with db_cursor() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (_SETTINGS_KEY,)).fetchone()
    return row["value"] if row else DEFAULT_TZ_NAME


def set_timezone_name(tz_name: str) -> None:
    try:
        ZoneInfo(tz_name)
    except ZoneInfoNotFoundError as e:
        raise ValueError(f"Unknown IANA timezone: {tz_name}") from e
    with db_cursor() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (_SETTINGS_KEY, tz_name),
        )


def get_local_tz() -> ZoneInfo:
    return ZoneInfo(get_timezone_name())


def local_to_utc_iso(value: str | None) -> str | None:
    """Interpret a naive ISO timestamp as local time and convert it to a UTC ISO string."""
    if not value:
        return value
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=get_local_tz())
    return dt.astimezone(UTC).isoformat()


def utc_to_local_iso(value: str | None) -> str | None:
    """Convert a stored UTC ISO timestamp back to local time for display."""
    if not value:
        return value
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(get_local_tz()).isoformat()
