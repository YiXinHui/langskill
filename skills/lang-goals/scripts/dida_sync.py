#!/usr/bin/env python3
"""Push confirmed daily todos to DIDA and read their state back, via the official `dida` CLI.

Usage (JSON on stdin, JSON on stdout; exit 1 if any item failed):
  python3 dida_sync.py push < payload.json       # parent_dida_task_id: today's step under a long-term main task
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

from schedule import datetime_value, schedule

STATUS_TEXT = {0: "未完成", 2: "已完成", -1: "已放弃"}
UPDATABLE = ("title", "date", "time", "end_time", "priority", "content", "project", "subtasks")
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
    if {"date", "time", "end_time"}.intersection(fields):
        start, end, all_day = schedule(item, zone)
        # Set both endpoints, including when rescheduling an existing task.
        if all_day:
            args += ["--all-day"]
        args += ["--start-date", start.strftime("%Y-%m-%dT%H:%M:%S%z"),
                 "--due-date", end.strftime("%Y-%m-%dT%H:%M:%S%z"), "--time-zone", zone]
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


# DIDA turns "#" followed by text into a tag (2026-10-26: "#11、#43" became three tags).
# Markdown headings ("## 做什么") pass; "C#语言" is blocked too, since DIDA's exact rule is unverified.
# URLs are skipped so section anchors in links still work.
HASH_TAG = re.compile(r"#+(?=[^\s#])")
URL = re.compile(r"https?://[^\s)\]）】」>]+")


def check_no_tags(item, fields):
    """Refuse to write text DIDA would parse as tags; numbers go without #, like 「教程 11」."""
    texts = []
    if "title" in fields:
        texts.append(("title", item.get("title")))
    if "content" in fields:
        texts.append(("content", item.get("content")))
    if "subtasks" in fields:
        for sub in item.get("subtasks") or []:
            texts.append(("subtasks", sub.get("title")))
            texts += [("subtasks", nested.get("title")) for nested in sub.get("subtasks") or []]
    for name, text in texts:
        hit = HASH_TAG.search(URL.sub("", str(text or "")))
        if hit:
            word = re.match(r"#+\S{0,8}", hit.string[hit.start():]).group()
            raise ValueError(f"{name}: 「{word}」 would become a DIDA tag; drop the #, e.g. write 「教程 11」")


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
    if {"date", "time", "end_time"}.intersection(fields):
        start, end, all_day = schedule(item, zone)
        if all_day:
            if {local_date(task.get("dueDate"), task_zone), local_date(task.get("startDate"), task_zone)} != {item["date"]}:
                bad.append("date")
        else:
            for key, expected in (("startDate", start), ("dueDate", end)):
                if not task.get(key) or datetime_value(task[key], task_zone) != expected:
                    bad.append("time" if key == "startDate" else "end_time")
        if task.get("isAllDay") is not all_day:
            bad.append("isAllDay")
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


def step_parent(runner, item, zone):
    """The open long-term main task that today's step goes under, or a result explaining why not."""
    parent_id = item["parent_dida_task_id"]
    if is_nested(item.get("subtasks") or []):
        raise ValueError("a step under a main task takes a flat checklist only")
    parent, _, deleted = locate(runner, item["project_id"], parent_id, item.get("parent_title") or item["title"], zone)
    if parent is None or deleted:
        return None, "parent_missing" if parent is None else "parent_deleted"
    if parent.get("status") != 0:
        return None, "parent_closed"  # never reopen it here; the user decides
    return parent, None


def children_of(runner, parent):
    return [cli_json(runner, ["task", "get", parent["projectId"], c]) for c in parent.get("childIds") or []]


def existing_step(children, item, zone):
    """A child of the main task with the same title and day: retries must not add a second one."""
    for child in children:
        child_day = local_date(child.get("startDate") or child.get("dueDate"), child.get("timeZone") or zone)
        if child.get("title") == item["title"] and child_day == item["date"]:
            return child
    return None


def next_sort_order(children):
    return max([c.get("sortOrder") for c in children if isinstance(c.get("sortOrder"), int)] + [0]) + SORT_STEP


def push_step(runner, zone, item, result):
    """Create today's step as a child task of the long-term main task, which keeps its title and stays open."""
    parent, problem = step_parent(runner, item, zone)
    if problem:
        return {**result, "result": problem, "parent_dida_task_id": item["parent_dida_task_id"]}
    pid, parent_id = parent["projectId"], parent["id"]
    children = children_of(runner, parent)
    found = existing_step(children, item, zone)
    if found:
        return {**result, "result": "matched", "dida_task_id": found["id"], "project_id": pid,
                "parent_dida_task_id": parent_id}
    if sum(1 for c in children if c.get("status") == 0) >= MAX_SUBTASKS:
        return {**result, "result": "too_many_steps", "parent_dida_task_id": parent_id}
    fields = list(UPDATABLE)
    args = ["task", "create", "--project", pid, "--parent-id", parent_id,
            "--sort-order", str(next_sort_order(children)), *task_args(item, zone, fields)]
    if item.get("subtasks"):
        args += ["--items", checklist(item["subtasks"])]
    task_id = cli_json(runner, args)["id"]
    task = cli_json(runner, ["task", "get", pid, task_id])
    after = cli_json(runner, ["task", "get", pid, parent_id])
    out = {**result, "dida_task_id": task_id, "project_id": pid, "parent_dida_task_id": parent_id}
    bad = mismatches(runner, task, {**item, "project_id": pid}, zone, fields, [])
    if task.get("parentId") != parent_id or after.get("status") != 0 or after.get("title") != parent.get("title"):
        bad.append("parent")
    if bad:
        return {**out, "result": "readback_mismatch", "fields": sorted(set(bad))}
    return {**out, "result": "created"}


def push_one(runner, default_project, zone, item):
    item = {**item, "project_id": item.get("project_id") or default_project}
    check_subtasks(item.get("subtasks") or [])
    schedule(item, zone)  # Reject malformed or reversed time ranges before any write.
    result = {"record_id": item["record_id"]}
    task_id, notes = item.get("dida_task_id"), []
    check_no_tags(item, item.get("fields", []) if task_id else UPDATABLE)
    if item.get("parent_dida_task_id"):
        if task_id == item["parent_dida_task_id"]:
            raise ValueError("today's step must not reuse the main task's DIDA ID")
        if not task_id:
            return push_step(runner, zone, item, result)
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
        candidates = day_tasks(runner, item["project_id"], item["date"], zone)
        _, end, all_day = schedule(item, zone)
        if not all_day and end.date().isoformat() != item["date"]:
            # Filters may index by dueDate; an overnight task ends outside its start day.
            candidates.update(day_tasks(runner, item["project_id"], end.date().isoformat(), zone))
        for hit in candidates.values():
            hit_day = local_date(hit.get("startDate") or hit.get("dueDate"), zone)
            if hit.get("title") == item["title"] and (all_day or hit_day == item["date"]):
                if item.get("time"):
                    existing = cli_json(runner, ["task", "get", hit["projectId"], hit["id"]])
                    if mismatches(runner, existing, item, zone, ["date"], []):
                        return {**result, "result": "schedule_conflict", "dida_task_id": hit["id"],
                                "project_id": hit["projectId"]}
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
    timed = task.get("isAllDay") is False and bool(task.get("startDate"))
    start_time = datetime_value(task["startDate"], task_zone).isoformat() if timed else None
    end_time = datetime_value(task["dueDate"], task_zone).isoformat() if timed and task.get("dueDate") else None
    start_date = local_date(task.get("startDate"), task_zone) if timed else due
    expected_time = datetime_value(item["time"], task_zone).isoformat() if item.get("time") else None
    expected_end = datetime_value(item["end_time"], task_zone).isoformat() if item.get("end_time") else expected_time
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
        "start_date": start_date,
        "time": start_time,
        "end_time": end_time,
        "time_changed": (start_time, end_time) != (expected_time, expected_end),
        "date_changed": start_date != item.get("date"),
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
    failed = failed or any(r.get("result") in ("readback_mismatch", "schedule_conflict") for r in results)
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
