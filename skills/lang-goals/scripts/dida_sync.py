#!/usr/bin/env python3
"""Push confirmed daily todos to DIDA and read their state back, via the official `dida` CLI.

Usage (JSON on stdin, JSON on stdout; exit 1 if any item failed):
  python3 dida_sync.py push < payload.json
  python3 dida_sync.py read < payload.json
  python3 dida_sync.py untracked < payload.json   # tasks the user added in DIDA, not pushed from the plan
  python3 dida_sync.py close < payload.json       # complete or abandon tasks, only after the user said 「行」

The CLI must be logged in on this machine; set DIDA_BIN if `dida` is not on PATH.
Never prints task content or CLI auth output.
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys
from zoneinfo import ZoneInfo

STATUS_TEXT = {0: "未完成", 2: "已完成", -1: "已放弃"}
UPDATABLE = ("title", "date", "priority", "content", "project", "subtasks")
MAX_SUBTASKS = 3
SORT_STEP = 65536  # DIDA lists siblings by ascending sortOrder; without it the newest child shows first
CLOSE_STATUS = {"complete": 2, "abandon": -1}


class CliError(Exception):
    pass


def short_error(text):
    line = (text or "").strip().splitlines()[0] if (text or "").strip() else "unknown error"
    return re.sub(r"(?i)(bearer|token)\S*\s*\S+", "<masked>", line)[:200]


def run_cli(args):
    proc = subprocess.run([os.environ.get("DIDA_BIN", "dida"), *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise CliError(short_error(proc.stderr or proc.stdout))
    return proc.stdout


def cli_json(runner, args):
    out = runner(args + ["--json"])
    return json.loads(out) if out.strip() else None


def as_list(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get("data") or data.get("tasks") or []
    return []


def local_date(value, zone):
    if not value:
        return None
    stamp = dt.datetime.strptime(re.sub(r"\.\d+", "", value), "%Y-%m-%dT%H:%M:%S%z")
    return stamp.astimezone(ZoneInfo(zone)).date().isoformat()


def due_arg(date, zone, clock="00:00:00"):
    day = dt.datetime.fromisoformat(f"{date}T{clock}").replace(tzinfo=ZoneInfo(zone))
    return day.strftime("%Y-%m-%dT%H:%M:%S%z")


def search_ids(runner, title):
    # Search lags a few seconds behind writes; only used to find tasks moved to another list.
    return {t.get("id"): t for t in as_list(cli_json(runner, ["task", "search", title, "--status=-1,0,2"]))}


def day_tasks(runner, project_id, date, zone):
    # Filter is consistent right after a write, includes finished tasks and skips deleted ones.
    # The CLI drops abandoned tasks when -1 is listed with other codes, so ask for them separately.
    found = {}
    for status in ("--status=0,2", "--status=-1"):
        args = ["task", "filter", "--projects", project_id, "--start-date", due_arg(date, zone),
                "--end-date", due_arg(date, zone, "23:59:59"), status]
        found.update({t.get("id"): t for t in as_list(cli_json(runner, args))})
    return found


def locate(runner, project_id, task_id, fallback_title, zone):
    """Return (task, moved, deleted). task is None when the ID cannot be found anywhere."""
    moved = False
    try:
        task = cli_json(runner, ["task", "get", project_id, task_id])
    except CliError as err:
        if "404" not in str(err) and "not found" not in str(err):
            raise
        hit = search_ids(runner, fallback_title).get(task_id)
        if not hit:
            return None, False, False
        task, moved = cli_json(runner, ["task", "get", hit["projectId"], task_id]), True
    # Deleted tasks stay readable by ID; they drop out of filter and search.
    due = local_date(task.get("dueDate"), task.get("timeZone") or zone)
    if due:
        visible = day_tasks(runner, task["projectId"], due, zone)
    else:
        visible = search_ids(runner, task.get("title") or fallback_title)
    return task, moved, task_id not in visible


def task_args(item, zone, fields):
    args = []
    if "title" in fields:
        args += ["--title", item["title"]]
    if "date" in fields:
        # Set start too: user-made tasks keep their own start date, and DIDA then shows a multi-day span.
        day = due_arg(item["date"], zone)
        args += ["--all-day", "--start-date", day, "--due-date", day, "--time-zone", zone]
    if "priority" in fields:
        args += ["--priority", str(item.get("priority", 0))]
    if "content" in fields and item.get("content"):
        args += ["--content", item["content"]]
    return args


def check_subtasks(subtasks, depth=1):
    """At most 3 per level and two levels deep (subtask, then sub-subtask)."""
    if not isinstance(subtasks, list) or len(subtasks) > MAX_SUBTASKS:
        raise ValueError(f"subtasks: at most {MAX_SUBTASKS} per level")
    for sub in subtasks:
        if not isinstance(sub, dict) or not str(sub.get("title", "")).strip():
            raise ValueError("subtasks: every subtask needs a title")
        nested = sub.get("subtasks") or []
        if nested and depth >= 2:
            raise ValueError("subtasks: at most two levels")
        check_subtasks(nested, depth + 1)


def checklist(subtasks):
    return json.dumps([{"title": s["title"], "status": 0} for s in subtasks], ensure_ascii=False)


def is_nested(subtasks):
    return any(s.get("subtasks") for s in subtasks)


def write_subtasks(runner, project_id, task_id, subtasks):
    """Flat lists become checklist items; nested ones become child tasks with their own checklists."""
    if not subtasks:
        return []
    if not is_nested(subtasks):
        runner(["task", "update", task_id, "--id", task_id, "--project", project_id, "--items", checklist(subtasks)])
        return []
    children = []
    for index, sub in enumerate(subtasks, 1):
        args = ["task", "create", "--project", project_id, "--parent-id", task_id, "--title", sub["title"],
                "--sort-order", str(index * SORT_STEP)]
        if sub.get("subtasks"):
            args += ["--items", checklist(sub["subtasks"])]
        children.append(cli_json(runner, args)["id"])
    return children


def mismatches(runner, task, item, zone, fields, children):
    bad = []
    if "title" in fields and task.get("title") != item["title"]:
        bad.append("title")
    task_zone = task.get("timeZone") or zone
    if "date" in fields and {local_date(task.get("dueDate"), task_zone), local_date(task.get("startDate"), task_zone)} != {item["date"]}:
        bad.append("date")
    if "priority" in fields and task.get("priority") != item.get("priority", 0):
        bad.append("priority")
    if "project" in fields and task.get("projectId") != item["project_id"]:
        bad.append("project")
    subtasks = item.get("subtasks") or []
    if "subtasks" in fields and subtasks:
        if not is_nested(subtasks) and len(task.get("items") or []) != len(subtasks):
            bad.append("subtasks")
        orders = []
        for child_id, sub in zip(children, subtasks):
            child = cli_json(runner, ["task", "get", task["projectId"], child_id])
            orders.append(child.get("sortOrder"))
            if child.get("parentId") != task["id"] or len(child.get("items") or []) != len(sub.get("subtasks") or []):
                bad.append("subtasks")
                break
        if "subtasks" not in bad and orders != sorted(orders, key=lambda n: n if n is not None else float("inf")):
            bad.append("subtasks")
    return bad


def push_one(runner, default_project, zone, item):
    item = {**item, "project_id": item.get("project_id") or default_project}
    check_subtasks(item.get("subtasks") or [])
    result = {"record_id": item["record_id"]}
    task_id, notes = item.get("dida_task_id"), []
    if task_id:
        task, moved, deleted = locate(runner, item["project_id"], task_id, item.get("old_title") or item["title"], zone)
        if task is None or deleted:
            return {**result, "result": "missing" if task is None else "deleted", "dida_task_id": task_id}
        fields = [f for f in item.get("fields", []) if f in UPDATABLE]
        if not fields:
            return {**result, "result": "exists", "dida_task_id": task_id, "project_id": task["projectId"], "moved": moved}
        pid = task["projectId"]
        if "project" in fields and pid != item["project_id"]:
            runner(["task", "move", "--from", pid, "--to", item["project_id"], "--task", task_id])
            pid = item["project_id"]
        args = task_args(item, zone, fields)
        if args:
            runner(["task", "update", task_id, "--id", task_id, "--project", pid, *args])
        children = []
        if "subtasks" in fields:
            if task.get("items") or task.get("childIds"):
                fields.remove("subtasks")
                notes.append("已有子任务，未覆盖")
            else:
                children = write_subtasks(runner, pid, task_id, item.get("subtasks") or [])
        action = "updated"
    else:
        fields = list(UPDATABLE)
        for hit in day_tasks(runner, item["project_id"], item["date"], zone).values():
            if hit.get("title") == item["title"]:
                return {**result, "result": "matched", "dida_task_id": hit["id"], "project_id": hit["projectId"]}
        pid = item["project_id"]
        subtasks = item.get("subtasks") or []
        args = ["task", "create", "--project", pid, *task_args(item, zone, fields)]
        if subtasks and not is_nested(subtasks):
            args += ["--items", checklist(subtasks)]
        task_id, action = cli_json(runner, args)["id"], "created"
        children = write_subtasks(runner, pid, task_id, subtasks) if is_nested(subtasks) else []
    task = cli_json(runner, ["task", "get", pid, task_id])
    out = {**result, "dida_task_id": task_id, "project_id": pid}
    if children:
        out["child_task_ids"] = children
    if notes:
        out["notes"] = notes
    bad = mismatches(runner, task, item, zone, fields, children)
    if bad:
        return {**out, "result": "readback_mismatch", "fields": sorted(set(bad))}
    return {**out, "result": action}


def read_one(runner, project_id, zone, item):
    result = {"record_id": item["record_id"], "dida_task_id": item["dida_task_id"]}
    task, moved, deleted = locate(runner, item.get("project_id") or project_id, item["dida_task_id"], item["title"], zone)
    if task is None:
        return {**result, "found": False}
    task_zone = task.get("timeZone") or zone
    status = task.get("status")
    due = local_date(task.get("dueDate"), task_zone)
    out = {
        **result,
        "found": True,
        "deleted": deleted,
        "moved": moved,
        "project_id": task.get("projectId"),
        "status": status,
        "status_text": STATUS_TEXT.get(status, str(status)),
        "due_date": due,
        "completed_date": local_date(task.get("completedTime"), task_zone),
        "date_changed": due != item.get("date"),
        "title_changed": task.get("title") != item["title"],
        "checklist_done": sum(1 for i in task.get("items") or [] if i.get("status") in (1, 2)),
        "checklist_total": len(task.get("items") or []),
    }
    if out["title_changed"]:
        out["dida_title"] = task.get("title")
    return out


def set_status(runner, project_id, task_id, target):
    if target == 2:
        runner(["task", "complete", project_id, task_id])
    else:
        runner(["task", "update", task_id, "--id", task_id, "--project", project_id, f"--status={target}"])
    return cli_json(runner, ["task", "get", project_id, task_id]).get("status") == target


def close_children(runner, task, target):
    """Close child tasks still open under a closed parent; leave ones the user already closed."""
    out = []
    for child_id in task.get("childIds") or []:
        child = cli_json(runner, ["task", "get", task["projectId"], child_id])
        if child.get("status") != 0:
            continue
        ok = set_status(runner, task["projectId"], child_id, target)
        out.append({"dida_task_id": child_id, "title": child.get("title"),
                    "result": ("completed" if target == 2 else "abandoned") if ok else "readback_mismatch"})
    return out


def close_one(runner, project_id, zone, item):
    """Complete or abandon one task the user has just confirmed, plus its open child tasks; never reopen or override a closed task."""
    target = CLOSE_STATUS[item["action"]]
    result = {"record_id": item["record_id"], "dida_task_id": item["dida_task_id"], "action": item["action"]}
    task, moved, deleted = locate(runner, item.get("project_id") or project_id, item["dida_task_id"], item["title"], zone)
    if task is None or deleted:
        return {**result, "result": "missing" if task is None else "deleted"}
    pid = task["projectId"]
    if task.get("status") not in (0, target):
        return {**result, "result": "conflict", "status_text": STATUS_TEXT.get(task.get("status"), str(task.get("status")))}
    if task.get("status") == target:
        out = {**result, "result": "exists", "project_id": pid}
    elif set_status(runner, pid, item["dida_task_id"], target):
        out = {**result, "result": "completed" if target == 2 else "abandoned", "project_id": pid, "moved": moved}
    else:
        return {**result, "result": "readback_mismatch", "fields": ["status"]}
    children = close_children(runner, task, target)
    if children:
        out["children"] = children
        if any(c["result"] == "readback_mismatch" for c in children):
            out["result"] = "readback_mismatch"
            out["fields"] = ["children"]
    return out


def untracked(runner, payload):
    """Open tasks in the given lists that are not known plan tasks: dated inside the window, or undated but created in it."""
    zone, start, end = payload.get("time_zone", "Asia/Shanghai"), payload["from"], payload["to"]
    known = set(payload.get("known_ids") or [])
    found = {}
    for project_id in payload["project_ids"]:
        args = ["task", "filter", "--projects", project_id, "--start-date", due_arg(start, zone),
                "--end-date", due_arg(end, zone, "23:59:59"), "--status", "0"]
        dated = as_list(cli_json(runner, args))
        data = cli_json(runner, ["project", "data", project_id]) or {}
        undated = [t for t in data.get("tasks", []) if not t.get("dueDate")
                   and start <= (local_date(t.get("createdTime"), zone) or "") <= end]
        for task in dated + undated:
            if task.get("id") in known or task.get("parentId") in known or task.get("status", 0) != 0:
                continue
            found[task["id"]] = {
                "dida_task_id": task["id"],
                "project_id": task.get("projectId"),
                "title": task.get("title"),
                "due_date": local_date(task.get("dueDate"), task.get("timeZone") or zone),
                "created_date": local_date(task.get("createdTime"), zone),
            }
    return sorted(found.values(), key=lambda t: (t["due_date"] or "9999", t["title"] or ""))


def main(argv, stdin=sys.stdin, runner=run_cli):
    if len(argv) != 2 or argv[1] not in ("push", "read", "untracked", "close"):
        print(__doc__, file=sys.stderr)
        return 2
    payload = json.load(stdin)
    if argv[1] == "untracked":
        try:
            print(json.dumps(untracked(runner, payload), ensure_ascii=False, indent=2))
            return 0
        except (CliError, KeyError, ValueError) as err:
            print(json.dumps({"result": "error", "error": short_error(str(err))}, ensure_ascii=False))
            return 1
    project_id, zone = payload["project_id"], payload.get("time_zone", "Asia/Shanghai")
    handler = {"push": push_one, "read": read_one, "close": close_one}[argv[1]]
    results, failed = [], False
    for item in payload["items"]:
        try:
            results.append(handler(runner, project_id, zone, item))
        except (CliError, KeyError, ValueError) as err:
            failed = True
            results.append({"record_id": item.get("record_id"), "result": "error", "error": short_error(str(err))})
    failed = failed or any(r.get("result") == "readback_mismatch" for r in results)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
