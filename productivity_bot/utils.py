from __future__ import annotations

from datetime import datetime, date, time, timedelta
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def today_bounds(tz_name: str) -> tuple[datetime, datetime]:
    tz = ZoneInfo(tz_name)
    now = datetime.now(tz)
    start = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=tz)
    end = start + timedelta(days=1)
    return start, end


def fmt_hhmm(dt: datetime) -> str:
    return dt.strftime("%H:%M")


def ensure_tz(dt: datetime, tz_name: str):
    tz = ZoneInfo(tz_name)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tz)
    return dt.astimezone(tz)
