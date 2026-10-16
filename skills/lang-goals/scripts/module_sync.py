#!/usr/bin/env python3
"""Refresh existing personal reference rows from module records. Never writes a source or DIDA.

Usage: python3 module_sync.py --config references/personal-module-sync.json [--apply]
Without --apply, reports changed fields only. Configuration contains resource mappings, not credentials.
"""
import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from urllib.parse import parse_qs, urlsplit

FIELDS = {"title": "待办", "date": "日期", "status": "状态", "task_id": "滴答任务ID"}
SOURCE_FIELD = "来源记录"
STATUSES = {"未开始", "进行中", "已完成", "未完成", "取消"}


def cli(args):
    p = subprocess.run([os.environ.get("LARK_CLI_BIN", "lark-cli"), "base", *args, "--as", "user"],
                       capture_output=True, text=True)
    if p.returncode:
        # Do not print auth output or a full business response.
        raise ValueError(f"lark-cli {args[0]} failed (exit {p.returncode}); inspect CLI permissions or resource schema")
    d = json.loads(p.stdout)
    if d.get("ok") is not True:
        raise ValueError(f"lark-cli {args[0]} did not confirm success")
    return d["data"]


def matrix(data):
    names, ids, rows = data["fields"], data["record_id_list"], data["data"]
    if len(ids) != len(rows) or any(len(row) != len(names) for row in rows):
        raise ValueError("incomplete record matrix")
    return {rid: dict(zip(names, row)) for rid, row in zip(ids, rows)}


def list_rows(target, runner):
    rows, offset = {}, 0
    while True:
        page = runner(["+record-list", "--base-token", target["base_token"], "--table-id", target["table_id"],
                       "--limit", "200", "--offset", str(offset), "--json"])
        if not {SOURCE_FIELD, *FIELDS.values()}.issubset(page["fields"]):
            raise ValueError("personal daily table is missing reference fields; do not create schema automatically")
        batch = matrix(page)
        if rows.keys() & batch.keys():
            raise ValueError("overlapping target pages")
        rows.update(batch)
        if not page["has_more"]:
            return rows
        if not batch:
            raise ValueError("empty page with has_more")
        offset += len(batch)


def source_key(value):
    value = str(value or "").strip()
    markdown = re.fullmatch(r"\[[^\]]*\]\((https?://\S+)\)", value)
    if markdown:
        value = markdown.group(1)
    u = urlsplit(value)
    path = re.fullmatch(r"/base/([A-Za-z0-9]+)", u.path.rstrip("/"))
    query = parse_qs(u.query)
    table, record = query.get("table", []), query.get("record", [])
    if (u.scheme != "https" or not u.hostname or u.username or not path or len(table) != 1 or len(record) != 1
            or not re.fullmatch(r"tbl[A-Za-z0-9]+", table[0]) or not re.fullmatch(r"rec[A-Za-z0-9]+", record[0])):
        raise ValueError("source must be a full HTTPS Base record URL")
    return u.hostname, path.group(1), table[0], record[0]


def get_rows(base, table, ids, fields, runner):
    rows = {}
    for start in range(0, len(ids), 100):
        chunk = ids[start:start + 100]
        args = ["+record-get", "--base-token", base, "--table-id", table, "--format", "json"]
        for rid in chunk:
            args += ["--record-id", rid]
        for field in fields:
            args += ["--field-id", field]
        page = runner(args)
        batch = matrix(page)
        if page["has_more"] or set(batch) != set(chunk) or not set(fields).issubset(page["fields"]):
            raise ValueError("source or readback records/fields are missing; keep personal rows unchanged")
        rows.update(batch)
    return rows


def desired_values(source, module, current):
    f = module["fields"]
    title = str(source[f["title"]] or "").strip()
    status = source[f["status"]]
    if not title or not isinstance(status, list) or len(status) != 1:
        raise ValueError("source title or status is empty/ambiguous")
    mapped = module["status_map"].get(status[0])
    if mapped not in STATUSES:
        raise ValueError("unmapped source status; do not infer completion")
    task_id = source[f["task_id"]] or None
    if current.get(FIELDS["task_id"]) and not task_id:
        raise ValueError("source reminder ID is missing; preserve the existing binding")
    return {FIELDS["title"]: title.splitlines()[0].strip(), FIELDS["date"]: source[f["date"]] or None,
            FIELDS["status"]: [mapped], FIELDS["task_id"]: task_id}


def sync(config, apply=False, runner=cli):
    target = config["target"]
    modules = {}
    for m in config["modules"]:
        key = (m["host"], m["base_token"], m["table_id"])
        if key in modules or key[1:] == (target["base_token"], target["table_id"]):
            raise ValueError("duplicate module mapping or source equals target")
        modules[key] = m
    rows = list_rows(target, runner)
    refs, seen, groups = {}, set(), defaultdict(list)
    for rid, row in rows.items():
        if not row.get(SOURCE_FIELD):
            continue
        key = source_key(row[SOURCE_FIELD])
        if key in seen:
            raise ValueError("duplicate references to one source; do not merge or create rows")
        if key[:3] not in modules:
            raise ValueError("source module is not configured; keep the reference unchanged")
        seen.add(key)
        refs[rid] = key
        groups[key[:3]].append(key[3])
    sources = {}
    for key, ids in groups.items():
        module = modules[key]
        fetched = get_rows(key[1], key[2], ids, list(module["fields"].values()), runner)
        sources.update({(*key, rid): row for rid, row in fetched.items()})
    # Validate all sources before any write. A failed/missing source never clears a mirror.
    changes = {}
    for rid, key in refs.items():
        wanted = desired_values(sources[key], modules[key[:3]], rows[rid])
        delta = {f: value for f, value in wanted.items() if (rows[rid].get(f) or None) != value}
        if delta:
            changes[rid] = delta
    if apply:
        ids = list(changes)
        for start in range(0, len(ids), 200):
            chunk = ids[start:start + 200]
            runner(["+record-batch-update", "--base-token", target["base_token"], "--table-id", target["table_id"],
                    "--json", json.dumps({"update_records": {rid: changes[rid] for rid in chunk}}, ensure_ascii=False)])
            back = get_rows(target["base_token"], target["table_id"], chunk, list(FIELDS.values()), runner)
            if any((back[rid].get(f) or None) != v for rid in chunk for f, v in changes[rid].items()):
                raise ValueError("personal write readback mismatch; report partial completion, do not recreate rows")
    return {"ok": True, "applied": apply, "references": len(refs), "changed": len(changes),
            "changes": [{"record_id": rid, "fields": list(delta)} for rid, delta in changes.items()]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        with open(args.config, encoding="utf-8") as stream:
            result = sync(json.load(stream), apply=args.apply)
    except (ValueError, KeyError, OSError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
