from __future__ import annotations

import calendar
from datetime import UTC, datetime
from datetime import timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def _parse_hhmm(v: str) -> tuple[int, int]:
    hh, mm = v.split(":")
    h = int(hh)
    m = int(mm)
    if h < 0 or h > 23 or m < 0 or m > 59:
        raise ValueError("Invalid time format")
    return h, m


def _next_daily(now_local: datetime, hhmm: str) -> datetime:
    h, m = _parse_hhmm(hhmm)
    candidate = now_local.replace(hour=h, minute=m, second=0, microsecond=0)
    if candidate <= now_local:
        candidate = candidate + timedelta(days=1)
    return candidate.astimezone(UTC)


def _next_weekly(now_local: datetime, weekday_iso: int, hhmm: str) -> datetime:
    if weekday_iso < 1 or weekday_iso > 7:
        raise ValueError("weekly_day must be in range 1..7")
    h, m = _parse_hhmm(hhmm)
    days_ahead = weekday_iso - now_local.isoweekday()
    candidate = now_local.replace(hour=h, minute=m, second=0, microsecond=0)
    if days_ahead < 0:
        days_ahead += 7
    candidate = candidate + timedelta(days=days_ahead)
    if candidate <= now_local:
        candidate = candidate + timedelta(days=7)
    return candidate.astimezone(UTC)


def _next_monthly(now_local: datetime, day: int, hhmm: str) -> datetime:
    """Next run on calendar day `day` (1..31) each month, clamped to the month's length.

    e.g. day=31 → Jan 31, Feb 28/29, Mar 31, Apr 30 — never skip a month.
    """
    h, m = _parse_hhmm(hhmm)
    year = now_local.year
    month = now_local.month
    tz = now_local.tzinfo
    for _ in range(14):
        last = calendar.monthrange(year, month)[1]
        eff = min(day, last)
        candidate = datetime(year, month, eff, h, m, tzinfo=tz)
        if candidate > now_local:
            return candidate.astimezone(UTC)
        month += 1
        if month > 12:
            month = 1
            year += 1
    raise ValueError("Unable to compute next monthly run")


def _next_yearly(now_local: datetime, date_ddmm: str, hhmm: str) -> datetime:
    dd_s, mm_s = date_ddmm.split(":")
    day = int(dd_s)
    month = int(mm_s)
    h, m = _parse_hhmm(hhmm)
    tz = now_local.tzinfo
    for year in (now_local.year, now_local.year + 1):
        last = calendar.monthrange(year, month)[1]
        eff = min(day, last)
        candidate = datetime(year, month, eff, h, m, tzinfo=tz)
        if candidate > now_local:
            return candidate.astimezone(UTC)
    raise ValueError("Unable to compute next yearly run")


def calculate_next_run(
    schedule_type: str,
    *,
    timezone: str | None,
    once_at: datetime | None,
    daily_time: str | None,
    weekly_day: int | None,
    weekly_time: str | None,
    monthly_day: int | None,
    monthly_time: str | None,
    yearly_date_ddmm: str | None,
    yearly_time: str | None,
    now: datetime | None = None,
) -> datetime | None:
    now_utc = (now or datetime.now(UTC)).astimezone(UTC)
    tz_name = (timezone or "UTC").strip() or "UTC"
    try:
        tz = ZoneInfo(tz_name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"Unsupported timezone: {tz_name}") from exc
    now_local = now_utc.astimezone(tz)
    if schedule_type == "once":
        if not once_at:
            raise ValueError("once_at required")
        dt = once_at if once_at.tzinfo else once_at.replace(tzinfo=tz)
        return dt.astimezone(UTC) if dt > now_utc else None
    if schedule_type == "daily":
        if not daily_time:
            raise ValueError("daily_time required")
        return _next_daily(now_local, daily_time)
    if schedule_type == "weekly":
        if weekly_day is None or not weekly_time:
            raise ValueError("weekly_day/weekly_time required")
        return _next_weekly(now_local, weekly_day, weekly_time)
    if schedule_type == "monthly":
        if monthly_day is None or not monthly_time:
            raise ValueError("monthly_day/monthly_time required")
        return _next_monthly(now_local, monthly_day, monthly_time)
    if schedule_type == "yearly":
        if not yearly_date_ddmm or not yearly_time:
            raise ValueError("yearly_date_ddmm/yearly_time required")
        return _next_yearly(now_local, yearly_date_ddmm, yearly_time)
    raise ValueError("Unsupported schedule_type")
