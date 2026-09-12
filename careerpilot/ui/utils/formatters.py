from datetime import datetime
from typing import Optional, Union


def format_datetime(
    val: Optional[Union[datetime, str]],
    fmt: str = "%Y-%m-%d %H:%M",
    fallback: str = "Unknown date",
) -> str:
    """
    Safely formats a datetime object or ISO datetime string into a human-readable display string.
    Handles datetime instances, ISO string timestamps, None, and unexpected formats without crashing.
    """
    if val is None:
        return fallback
    if isinstance(val, datetime):
        return val.strftime(fmt)
    if isinstance(val, str):
        val_clean = val.strip()
        if not val_clean:
            return fallback
        try:
            dt = datetime.fromisoformat(val_clean.replace("Z", "+00:00"))
            return dt.strftime(fmt)
        except Exception:
            return val_clean[:16].replace("T", " ")
    return str(val)


def format_date(
    val: Optional[Union[datetime, str]],
    fmt: str = "%Y-%m-%d",
    fallback: str = "N/A",
) -> str:
    """Safely formats a date/datetime into a YYYY-MM-DD string."""
    return format_datetime(val, fmt=fmt, fallback=fallback)
