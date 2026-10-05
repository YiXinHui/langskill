#!/usr/bin/env python3
"""Read a bounded completed-task snapshot through the official DIDA CLI."""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

SENSITIVE = re.compile(r"密码|口令|密钥|令牌|token|secret|password|api[ _-]?key|bearer", re.I)


def cli_json(args):
    result = subprocess.run(["dida", *args, "--json"], capture_output=True,
                            text=True, timeout=60)
    if result.returncode:
        raise ValueError("DIDA CLI 查询失败；请核对登录与命令帮助，未输出原始错误。")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        raise ValueError("DIDA CLI 返回格式无法解析。") from None


def safe_title(value):
    value = str(value or "")
    return "[疑似凭据标题已遮蔽]" if SENSITIVE.search(value) else value[:160]


def timestamp(value):
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return datetime.fromtimestamp(value / 1000, timezone.utc)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo:
            return parsed
    raise ValueError("完成时间缺少时区或格式不受支持。")


def summarize(rows, start, end):
    tasks, seen = [], set()
    marked, undated = 0, 0
    for task in rows:
        done = timestamp(task.get("completedTime"))
        if task.get("status") != 2 or not done or not start <= done < end:
            continue
        task_id = task.get("id")
        if not task_id:
            raise ValueError("任务缺少 ID，无法可靠去重。")
        if task_id in seen:
            continue
        seen.add(task_id)
        items = []
        for item in task.get("items") or []:
            item_done = timestamp(item.get("completedTime"))
            is_marked = item.get("status") in (1, 2)
            in_period = bool(is_marked and item_done and start <= item_done < end)
            marked += int(in_period)
            undated += int(is_marked and not item_done)
            items.append({"title": safe_title(item.get("title")),
                          "status": item.get("status"),
                          "completed_time": item_done.astimezone(start.tzinfo).isoformat() if item_done else None,
                          "completed_in_period": in_period})
        tasks.append({"id": task_id, "project_id": task.get("projectId"),
                      "title": safe_title(task.get("title")), "status": task.get("status"),
                      "completed_time": done.astimezone(start.tzinfo).isoformat(), "items": items})
    return {"task_count": len(tasks), "marked_items_in_period": marked,
            "marked_items_without_time": undated, "tasks": tasks}


def collect(start, end, reader=cli_json):
    rows, windows, cursor = [], [], start
    while cursor < end:
        boundary = min(cursor + timedelta(days=10), end)
        batch = reader(["task", "completed", "--start-date", cursor.strftime("%Y-%m-%dT%H:%M:%S%z"),
                        "--end-date", boundary.strftime("%Y-%m-%dT%H:%M:%S%z")])
        if not isinstance(batch, list) or any(not isinstance(row, dict) for row in batch):
            raise ValueError("完成任务返回结构发生变化。")
        rows.extend(batch)
        windows.append({"from": cursor.isoformat(), "to": boundary.isoformat(),
                        "returned_rows": len(batch)})
        cursor = boundary
    return {"source": "https://dida365.com/webapp/", "timezone": str(start.tzinfo),
            "from": start.isoformat(), "to_exclusive": end.isoformat(),
            "queried_at": datetime.now(timezone.utc).isoformat(), "windows": windows,
            "coverage": "仅覆盖该接口本次返回的记录；不保证全部历史记录。",
            **summarize(rows, start, end)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--from", dest="date_from", required=True)
    parser.add_argument("--to", dest="date_to", required=True)
    parser.add_argument("--timezone", help="IANA timezone; defaults to the account preference")
    args = parser.parse_args()
    try:
        zone_name = args.timezone
        if not zone_name:
            preference = cli_json(["preference", "get"])
            zone_name = preference.get("timeZone")
            if not zone_name:
                raise ValueError("账号未返回时区；请显式指定 --timezone。")
        zone = ZoneInfo(zone_name)
        start = datetime.strptime(args.date_from, "%Y-%m-%d").replace(tzinfo=zone)
        last = datetime.strptime(args.date_to, "%Y-%m-%d").replace(tzinfo=zone)
        if last < start:
            raise ValueError("结束日期不能早于开始日期。")
        snapshot = collect(start, last + timedelta(days=1))
        print(json.dumps(snapshot, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, subprocess.TimeoutExpired, KeyError, TypeError, OverflowError):
        print("查询未完成：请核对登录、日期、时区和 CLI 返回结构；未输出部分记录或原始错误。", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
