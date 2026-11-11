#!/usr/bin/env python3
"""Read-only coverage candidates from complete Base snapshots on stdin; never schedules tasks."""
import json
import sys
from datetime import date, timedelta

from module_sync import source_key

CLOSED = {"已完成", "取消"}


def state(row):
    value = row.get("状态") or []
    return value[0] if isinstance(value, list) and len(value) == 1 else value if isinstance(value, str) else None


def ids(row, field):
    return {item["id"] for item in row.get(field) or []}


def same_source(expected, actual):
    if not actual:
        return False
    try:
        return source_key(expected) == source_key(actual)
    except ValueError:
        return expected == actual


def check(data):
    today = date.fromisoformat(data["date"])
    monday = today - timedelta(days=today.weekday())
    end = (monday + timedelta(days=6)).isoformat()
    if data.get("complete") is not True:
        raise ValueError("complete=true requires fully paginated month/week/day snapshots")
    months, weeks, daily = (data[k] for k in ("months", "weeks", "daily"))
    covered = data.get("coverage", {})
    reminders = data.get("dida_readback")
    candidates = []

    def add(kind, rid, **extra):
        candidates.append({"kind": kind, "record_id": rid, **extra})

    def accounted(rid):
        receipt = covered.get(rid, {})
        # Exemptions need evidence and an explicit check date; they expire.
        return (bool(receipt.get("evidence")) and bool(receipt.get("next_check"))
                and date.fromisoformat(receipt["next_check"]) > today)

    def remaining(row):
        stamp = str(row.get("日期") or "")[:10]
        return state(row) not in CLOSED and today.isoformat() <= stamp <= end

    current = {rid: row for rid, row in weeks.items()
               if str(row.get("周一") or "")[:10] == monday.isoformat()}
    active_months = {rid: row for rid, row in months.items()
                     if str(row.get("截止日期") or "")[:7] == today.isoformat()[:7]
                     and state(row) not in CLOSED}
    for rid, row in active_months.items():
        children = [w for w in weeks.values() if rid in ids(w, "关联月目标")]
        current_children = [w for w in current.values() if rid in ids(w, "关联月目标")
                            and state(w) not in CLOSED]
        direct = [d for d in daily.values() if rid in ids(d, "关联月目标") and remaining(d)]
        if not current_children and not direct and not accounted(rid):
            add("month_needs_next_action_review", rid)
        if state(row) == "未开始" and any(state(w) in {"进行中", "已完成"} for w in children):
            add("parent_progress_needs_verification", rid)
    for rid, row in current.items():
        parents = ids(row, "关联月目标")
        if state(row) not in CLOSED and (not parents or parents - months.keys()):
            add("week_month_link_missing", rid)
        if state(row) not in CLOSED and not accounted(rid):
            actions = [d for d in daily.values() if rid in ids(d, "关联周计划") and remaining(d)]
            if not actions:
                add("week_needs_next_action_review", rid)
    for rid, row in daily.items():
        parents = ids(row, "关联周计划")
        if remaining(row) and not row.get("来源记录"):
            targets = ids(row, "关联月目标")
            for parent in parents & weeks.keys():
                targets |= ids(weeks[parent], "关联月目标")
            lists = {name for target in targets for name in (months.get(target, {}).get("滴答清单") or [])}
            if lists - {"不推"}:
                task_id = (row.get("滴答任务ID") or "").strip()
                if not task_id:
                    add("daily_reminder_id_missing", rid)
                elif reminders is not None:
                    receipt = reminders.get(rid, {})
                    if (receipt.get("dida_task_id") != task_id or receipt.get("found") is not True
                            or receipt.get("deleted") is not False
                            or receipt.get("date_changed") is not False
                            or receipt.get("time_changed") is not False):
                        add("daily_reminder_unverified", rid, task_id=task_id)
        if state(row) not in CLOSED and parents and not row.get("日期"):
            if all(p in weeks and state(weeks[p]) in CLOSED for p in parents):
                add("undated_action_under_closed_week", rid)
    # Callers provide only authorized module actions whose personal reference should exist.
    # Either identifier can locate a candidate. Both must agree to verify the reference.
    for source in data.get("expected_module_actions", []):
        url, task = source.get("source_url"), source.get("task_id")
        if not url or not task:
            raise ValueError("expected module actions require source_url and task_id")
        found = []
        for rid, row in daily.items():
            wrong = []
            if not same_source(url, row.get("来源记录")):
                wrong.append("来源记录")
            if row.get("滴答任务ID") != task:
                wrong.append("滴答任务ID")
            if len(wrong) < 2:
                found.append((rid, wrong))
        if not found:
            add("module_reference_missing", source["record_id"], source_url=url, task_id=task)
        elif len(found) > 1:
            add("module_reference_duplicate_review", source["record_id"], references=[rid for rid, _ in found])
        elif found[0][1]:
            rid, wrong = found[0]
            add("module_reference_mismatch", source["record_id"], reference=rid, fields=wrong,
                source_url=url, task_id=task)
    return {"date": today.isoformat(), "active_months": len(active_months),
            "current_weeks": len(current), "candidates": candidates,
            "note": "Candidates require evidence review; no dates, completion or business acceptance inferred."}


if __name__ == "__main__":
    try:
        print(json.dumps(check(json.load(sys.stdin)), ensure_ascii=False))
    except (KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False))
        sys.exit(1)
