import re
from datetime import datetime, timezone
from typing import Optional, List, Tuple, Union

from careerpilot.core.logging import get_logger

logger = get_logger(__name__)


def parse_date_string(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parses various date string formats into a datetime object.
    Supports:
    - 'MM/YYYY' (e.g. '11/2024')
    - 'YYYY-MM' (e.g. '2024-11')
    - 'YYYY-MM-DD' (e.g. '2024-11-01')
    - 'Month YYYY' (e.g. 'November 2024', 'Nov 2024')
    - 'YYYY' (e.g. '2024')
    - 'Present', 'Current', 'Now' -> returns current UTC datetime
    """
    if not date_str or not str(date_str).strip():
        return None

    cleaned = str(date_str).strip()
    if cleaned.lower() in ("present", "current", "now", "ongoing"):
        return datetime.now(timezone.utc)

    # 1. MM/YYYY
    m = re.match(r"^(\d{1,2})[/.-](\d{4})$", cleaned)
    if m:
        month, year = int(m.group(1)), int(m.group(2))
        return datetime(year, month, 1, tzinfo=timezone.utc)

    # 2. YYYY-MM
    m = re.match(r"^(\d{4})[/.-](\d{1,2})$", cleaned)
    if m:
        year, month = int(m.group(1)), int(m.group(2))
        return datetime(year, month, 1, tzinfo=timezone.utc)

    # 3. YYYY-MM-DD
    m = re.match(r"^(\d{4})[/.-](\d{1,2})[/.-](\d{1,2})$", cleaned)
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return datetime(year, month, day, tzinfo=timezone.utc)

    # 4. Month YYYY (e.g. Nov 2024, November 2024)
    for fmt in ("%b %Y", "%B %Y", "%b, %Y", "%B, %Y"):
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    # 5. YYYY only
    m = re.match(r"^(\d{4})$", cleaned)
    if m:
        year = int(m.group(1))
        return datetime(year, 1, 1, tzinfo=timezone.utc)

    logger.warning("Could not parse date string: '%s'", date_str)
    return None


def calculate_experience_duration_months(start_str: str, end_str: Optional[str] = "Present") -> float:
    """Calculates duration in months between start and end date strings."""
    start_dt = parse_date_string(start_str)
    end_dt = parse_date_string(end_str) or datetime.now(timezone.utc)

    if not start_dt:
        return 0.0

    if end_dt < start_dt:
        return 0.0

    # Calculate month difference
    months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
    # Include starting month as 1 full month of experience
    return max(1.0, float(months + 1))


def calculate_total_experience_years(experiences: List[Any]) -> float:
    """
    Deterministically computes total years of professional experience across all experience records.
    Merges overlapping date intervals to avoid double-counting concurrent roles.
    """
    if not experiences:
        return 0.0

    intervals: List[Tuple[datetime, datetime]] = []
    now_dt = datetime.now(timezone.utc)

    for exp in experiences:
        start_str = getattr(exp, "start_date", None)
        end_str = getattr(exp, "end_date", None) or "Present"
        if getattr(exp, "is_current", False):
            end_str = "Present"

        s_dt = parse_date_string(start_str)
        e_dt = parse_date_string(end_str) or now_dt

        if s_dt and e_dt and e_dt >= s_dt:
            intervals.append((s_dt, e_dt))

    if not intervals:
        return 0.0

    # Sort intervals by start date
    intervals.sort(key=lambda x: x[0])

    # Merge overlapping intervals
    merged: List[Tuple[datetime, datetime]] = [intervals[0]]
    for current in intervals[1:]:
        prev_start, prev_end = merged[-1]
        if current[0] <= prev_end:
            # Overlapping or contiguous
            merged[-1] = (prev_start, max(prev_end, current[1]))
        else:
            merged.append(current)

    # Calculate total days from merged intervals
    total_days = sum((end - start).days for start, end in merged)
    years = total_days / 365.25
    return round(years, 1)


def format_experience_duration_string(total_years: float) -> str:
    """
    Formats calculated years of experience into standard professional wording.
    Examples:
    - 1.9 -> '1.9+ years'
    - 2.0 -> '2+ years'
    - 0.8 -> 'Under 1 year'
    """
    if total_years <= 0.0:
        return "Early Career"
    if total_years < 1.0:
        months = max(1, int(total_years * 12))
        return f"{months} months"
    return f"{total_years:.1f}+ years"
