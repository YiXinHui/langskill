#!/usr/bin/env python3
"""Deterministic regressions for review evidence handling; no account required."""
import importlib.util
import json
from pathlib import Path
import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

path = Path(__file__).resolve().parents[1] / "scripts/review_snapshot.py"
spec = importlib.util.spec_from_file_location("snapshot", path)
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)
START = datetime(2026, 9, 1, tzinfo=ZoneInfo("Asia/Shanghai"))
END = datetime(2026, 10, 1, tzinfo=START.tzinfo)


def task(task_id="synthetic-a", title="复盘", when=None, items=None):
    return {"id": task_id, "projectId": "synthetic-project", "title": title, "status": 2,
            "completedTime": (when or START + timedelta(days=2)).isoformat(), "items": items or []}


class EvidenceChecks(unittest.TestCase):
    def test_parent_does_not_complete_items(self):
        result = snapshot.summarize([task(items=[{"title": "未完成", "status": 0}])], START, END)
        self.assertEqual(result["marked_items_in_period"], 0)
        self.assertEqual(result["tasks"][0]["items"][0]["status"], 0)

    def test_item_time_and_status(self):
        items = [{"title": "已标记", "status": status, "completedTime": when}
                 for status, when in [(1, START.isoformat()), (2, START.isoformat()),
                                      (1, (START - timedelta(days=1)).isoformat()), (2, None)]]
        result = snapshot.summarize([task(items=items)], START, END)
        self.assertEqual(result["marked_items_in_period"], 2)
        self.assertEqual(result["marked_items_without_time"], 1)

    def test_id_dedup_keeps_recurrences(self):
        result = snapshot.summarize([task(), task(), task("synthetic-b")], START, END)
        self.assertEqual(result["task_count"], 2)

    def test_local_month_boundary(self):
        rows = [task("before", when=START - timedelta(milliseconds=1)), task("first", when=START),
                task("last", when=END - timedelta(milliseconds=1)), task("next", when=END)]
        self.assertEqual(snapshot.summarize(rows, START, END)["task_count"], 2)

    def test_credentials_and_body_omitted(self):
        row = task(title="API_KEY=synthetic-value", items=[{"title": "密码 synthetic", "status": 0}])
        row["content"] = "private-body-synthetic"
        result = snapshot.summarize([row, task("normal", "普通任务")], START, END)
        encoded = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("synthetic-value", encoded)
        self.assertNotIn("private-body-synthetic", encoded)
        self.assertIn("普通任务", encoded)

    def test_query_failure_does_not_return_partial_snapshot(self):
        calls = []
        def reader(args):
            calls.append(args)
            if len(calls) == 2:
                raise ValueError("synthetic failure")
            return [task()]
        with self.assertRaises(ValueError):
            snapshot.collect(START, END, reader)

    def test_ten_day_windows_and_overlap(self):
        calls = []
        def reader(args):
            calls.append(args)
            return [task()]
        result = snapshot.collect(START, END, reader)
        self.assertEqual(len(calls), 3)
        self.assertEqual(calls[-1][-1], "2026-10-01T00:00:00+0800")
        self.assertEqual(result["task_count"], 1)


if __name__ == "__main__":
    unittest.main()
