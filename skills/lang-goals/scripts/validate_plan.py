#!/usr/bin/env python3
"""Validate one complete month/week/day plan read from stdin. No API calls, no writes.

333 = three frogs: hard limit of 3 🐸 per period; totals only get a soft warning."""
import datetime as dt
import json
import re
import sys

STATUSES = {"未开始", "进行中", "已完成", "未完成", "取消"}
MAX_FROGS = 3
SOFT_LIMITS = {"week": 5, "day": 5}
FROG = "🐸"


def parse_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("date must be YYYY-MM-DD")
    return dt.date.fromisoformat(value)


def check_period(level, period):
    if level == "month":
        if not isinstance(period, str) or not re.fullmatch(r"\d{4}-\d{2}", period):
            raise ValueError("month period must be YYYY-MM")
        parse_date(period + "-01")
        return
    day = parse_date(period)
    if level == "week" and day.weekday() != 0:
        raise ValueError("week period must be a Monday")


def has_text(item, key):
    value = item.get(key)
    return isinstance(value, str) and value.strip() != ""


def dimensions(item):
    value = item.get("dimension")
    values = [value] if isinstance(value, str) else value
    if not isinstance(values, list):
        return []
    return [v.strip() for v in values if isinstance(v, str) and v.strip()]


def is_frog(item):
    return str(item.get("title") or "").strip().startswith(FROG)


def check_limits(level, items):
    """333 means three frogs: at most 3 🐸 per month, week or day. Totals are not capped."""
    frogs = sum(1 for item in items if is_frog(item))
    if frogs > MAX_FROGS:
        return [f"333 limit: {frogs} frog items in this {level}, max {MAX_FROGS} (completed and cancelled frogs count)"]
    return []


def soft_warnings(plan):
    """Not errors: remind the user when a week or day gets crowded; the user decides."""
    items = [item for item in plan.get("items") or [] if isinstance(item, dict)]
    limit = SOFT_LIMITS.get(plan.get("level"))
    if limit and len(items) > limit:
        return [f"{len(items)} items in this {plan['level']}, more than {limit}: ask whether to trim"]
    return []


def check_frog_title(item, label):
    if not isinstance(item.get("frog"), bool):
        return [f"{label}: frog must be true or false (is the parent chain under a 🐸 goal?)"]
    titled = str(item.get("title") or "").strip().startswith(FROG)
    if item["frog"] and not titled:
        return [f"{label}: under a 🐸 goal, so the title must start with 🐸"]
    if titled and not item["frog"]:
        return [f"{label}: title starts with 🐸 but the parent chain is not a 🐸 goal"]
    return []


def check_day_item(item, label):
    """A todo hangs on a weekly plan, or directly on a monthly goal when it is a one-off."""
    errors = []
    if item.get("parent_type") not in ("周计划", "月目标"):
        errors.append(f"{label}: parent_type must be 周计划 (normal) or 月目标 (one-off)")
    errors.extend(check_frog_title(item, label))
    if not has_text(item, "dida_list"):
        errors.append(f"{label}: dida_list is required (the parent monthly goal's 滴答清单, or 不推)")
    return errors


def check_item(level, period, item, label):
    if not isinstance(item, dict):
        return [f"{label}: must be an object"]
    errors = []
    for key in ("title", "parent"):
        if not has_text(item, key):
            errors.append(f"{label}: {key} is required")
    if level == "month" and not dimensions(item):
        errors.append(f"{label}: dimension is required")
    if level in ("month", "week") and not has_text(item, "done_when"):
        errors.append(f"{label}: done_when is required")
    status = item.get("status", "未开始")
    if status not in STATUSES:
        errors.append(f"{label}: invalid status {status!r}")
    if level in ("month", "week") and status == "已完成" and not has_text(item, "actual_result"):
        errors.append(f"{label}: completed item requires actual_result")
    if level == "day":
        errors.extend(check_day_item(item, label))
    elif "frog" in item:
        errors.extend(check_frog_title(item, label))
    if level == "month" and "due" in item:
        try:
            if parse_date(item["due"]).strftime("%Y-%m") != period:
                errors.append(f"{label}: due date is outside {period}")
        except ValueError as exc:
            errors.append(f"{label}: due {exc}")
    return errors


def validate(plan):
    if not isinstance(plan, dict):
        return ["plan must be an object"]
    level, period = plan.get("level"), plan.get("period")
    if level not in ("month", "week", "day"):
        return ["level must be month, week or day"]
    try:
        check_period(level, period)
    except ValueError as exc:
        return [str(exc)]
    items = plan.get("items")
    if not isinstance(items, list):
        return ["items must be the complete list for this period"]
    errors = []
    errors.extend(check_limits(level, [item for item in items if isinstance(item, dict)]))
    titles = [item.get("title", "").strip() for item in items if isinstance(item, dict)]
    if len(set(titles)) != len(titles):
        errors.append("duplicate titles in this period")
    for index, item in enumerate(items, 1):
        errors.extend(check_item(level, period, item, f"item {index}"))
    return errors


def main():
    try:
        plan = json.load(sys.stdin)
        errors = validate(plan)
        warnings = soft_warnings(plan) if isinstance(plan, dict) else []
    except (ValueError, TypeError) as exc:
        errors, warnings = [f"invalid JSON: {exc}"], []
    print(json.dumps({"ok": not errors, "errors": errors, "warnings": warnings}, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
