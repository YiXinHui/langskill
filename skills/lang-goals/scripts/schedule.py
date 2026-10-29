"""Shared local date/time contract for daily plans, DIDA and module references."""
import datetime as dt
import re
from zoneinfo import ZoneInfo


def datetime_value(value, zone):
    if not isinstance(value, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?", value):
        raise ValueError("time must be a full datetime with hours and minutes")
    stamp = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    tz = ZoneInfo(zone)
    return stamp.replace(tzinfo=tz) if stamp.tzinfo is None else stamp.astimezone(tz)


def schedule(item, zone):
    """Return (start, end, all_day); explicit end requires a start and must be later."""
    date = item["date"]
    if not isinstance(date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise ValueError("date must be YYYY-MM-DD")
    day = dt.date.fromisoformat(date)
    start, end = item.get("time"), item.get("end_time")
    if not start:
        if end:
            raise ValueError("end_time requires time")
        midnight = dt.datetime.combine(day, dt.time(), ZoneInfo(zone))
        return midnight, midnight, True
    start = datetime_value(start, zone)
    if start.date() != day:
        raise ValueError("time date must match the plan date in time_zone")
    if end:
        end = datetime_value(end, zone)
        if end <= start:
            raise ValueError("end_time must be later than time")
    else:
        end = start
    return start, end, False
