#!/usr/bin/env python3
"""Regressions for the 333 validator and a privacy scan of the public skill files."""
import importlib.util
import io
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validate_plan", ROOT / "scripts/validate_plan.py")
vp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vp)
dspec = importlib.util.spec_from_file_location("dida_sync", ROOT / "scripts/dida_sync.py")
ds = importlib.util.module_from_spec(dspec)
dspec.loader.exec_module(ds)


def day(title, **extra):
    base = {"title": title, "parent": "rec-week", "parent_type": "周计划", "frog": False, "dida_list": "写作"}
    base.update(extra)
    return {k: v for k, v in base.items() if v is not None}


def item(title, **extra):
    base = {"title": title, "parent": "rec-synthetic-parent", "done_when": "可检查的结果", "dimension": "工作事业"}
    base.update(extra)
    return base


class PlanChecks(unittest.TestCase):
    def test_three_items_pass(self):
        plan = {"level": "month", "period": "2026-10", "items": [item("甲"), item("乙"), item("丙", due="2026-10-31")]}
        self.assertEqual(vp.validate(plan), [])

    def test_fourth_item_in_one_dimension_is_fine(self):
        # 2026-10-07: 333 means three frogs, not three goals; non-frog totals are not capped.
        plan = {"level": "month", "period": "2026-10", "items": [item(t) for t in "甲乙丙丁"]}
        self.assertEqual(vp.validate(plan), [])

    def test_month_non_frogs_across_dimensions_pass(self):
        dims = ["工作事业", "工作事业", "体验突破", "财务理财", "学习成长", "人际社交"]
        titles = ["🐸甲", "🐸乙", "🐸丙", "丁", "戊", "己"]
        plan = {"level": "month", "period": "2026-10", "items": [item(t, dimension=d) for t, d in zip(titles, dims)]}
        self.assertEqual(vp.validate(plan), [])

    def test_fourth_frog_fails_even_across_dimensions(self):
        dims = ["工作事业", "体验突破", "财务理财", "学习成长"]
        plan = {"level": "month", "period": "2026-10", "items": [item("🐸" + t, dimension=d) for t, d in zip("甲乙丙丁", dims)]}
        self.assertTrue(any("frog" in e for e in vp.validate(plan)))

    def test_frogs_capped_in_week_and_day_too(self):
        week = {"level": "week", "period": "2026-10-05", "items": [item("🐸" + t) for t in "甲乙丙丁"]}
        self.assertTrue(any("frog" in e for e in vp.validate(week)))
        today = {"level": "day", "period": "2026-10-07", "items": [day("🐸" + t, frog=True) for t in "甲乙丙丁"]}
        self.assertTrue(any("frog" in e for e in vp.validate(today)))

    def test_month_needs_dimension(self):
        plan = {"level": "month", "period": "2026-10", "items": [item("甲", dimension=None)]}
        self.assertTrue(any("dimension" in e for e in vp.validate(plan)))

    def test_crowded_week_or_day_only_warns(self):
        # Counter-example: six items is allowed, but the user gets a soft reminder.
        week = {"level": "week", "period": "2026-10-05", "items": [item(t) for t in "甲乙丙丁戊己"]}
        self.assertEqual(vp.validate(week), [])
        self.assertTrue(vp.soft_warnings(week))
        five = {"level": "day", "period": "2026-10-07", "items": [day(t) for t in "甲乙丙丁戊"]}
        self.assertEqual((vp.validate(five), vp.soft_warnings(five)), ([], []))

    def test_completed_and_cancelled_frogs_still_count(self):
        items = [item("🐸甲", status="已完成", actual_result="做成了"), item("🐸乙", status="取消"), item("🐸丙"), item("🐸丁")]
        self.assertTrue(any("frog" in e for e in vp.validate({"level": "week", "period": "2026-10-05", "items": items})))

    def test_week_must_start_monday(self):
        self.assertEqual(vp.validate({"level": "week", "period": "2026-10-06", "items": []}), ["week period must be a Monday"])

    def test_due_outside_month(self):
        plan = {"level": "month", "period": "2026-10", "items": [item("甲", due="2026-11-01")]}
        self.assertTrue(any("outside" in e for e in vp.validate(plan)))

    def test_completed_needs_actual_result(self):
        plan = {"level": "month", "period": "2026-10", "items": [item("甲", status="已完成")]}
        self.assertTrue(any("actual_result" in e for e in vp.validate(plan)))

    def test_day_needs_parent_not_done_when(self):
        ok = {"level": "day", "period": "2026-10-07", "items": [day("写完提纲")]}
        self.assertEqual(vp.validate(ok), [])
        orphan = {"level": "day", "period": "2026-10-07", "items": [day("写完提纲", parent=None)]}
        self.assertTrue(any("parent" in e for e in vp.validate(orphan)))

    def test_day_todo_must_say_where_it_hangs(self):
        # 2026-10-07 original failure: todos written with no weekly plan link at all.
        bad = {"level": "day", "period": "2026-10-07", "items": [day("写完提纲", parent_type=None)]}
        self.assertTrue(any("parent_type" in e for e in vp.validate(bad)))
        one_off = {"level": "day", "period": "2026-10-07", "items": [day("约人见面", parent_type="月目标")]}
        self.assertEqual(vp.validate(one_off), [])

    def test_frog_chain_needs_frog_title(self):
        # 2026-10-07 original failure: a todo under the 🐸 writing plan was titled without 🐸.
        bad = {"level": "day", "period": "2026-10-07", "items": [day("公众号日更一篇", frog=True)]}
        self.assertTrue(any("must start with 🐸" in e for e in vp.validate(bad)))
        wrong = {"level": "day", "period": "2026-10-07", "items": [day("🐸约人见面", frog=False)]}
        self.assertTrue(any("not a 🐸 goal" in e for e in vp.validate(wrong)))

    def test_day_todo_needs_dida_list(self):
        bad = {"level": "day", "period": "2026-10-07", "items": [day("写完提纲", dida_list="")]}
        self.assertTrue(any("dida_list" in e for e in vp.validate(bad)))

    def test_old_status_rejected(self):
        plan = {"level": "week", "period": "2026-10-05", "items": [item("甲", status="待核")]}
        self.assertTrue(any("status" in e for e in vp.validate(plan)))

    def test_duplicate_titles(self):
        plan = {"level": "day", "period": "2026-10-07", "items": [day("甲"), day("甲")]}
        self.assertIn("duplicate titles in this period", vp.validate(plan))


class FakeDida:
    """In-memory stand-in for the dida CLI; records every write."""

    def __init__(self):
        self.tasks, self.deleted, self.writes, self.next_id = {}, set(), [], 1
        self.unindexed = set()  # created in this run: real search lags behind writes

    def add(self, project, title, due_utc, status=0, completed=None):
        tid = f"t{self.next_id}"
        self.next_id += 1
        self.tasks[tid] = {"id": tid, "projectId": project, "title": title, "dueDate": due_utc,
                           "timeZone": "Asia/Shanghai", "priority": 0, "status": status, "completedTime": completed}
        return tid

    def opt(self, args, name):
        return args[args.index(name) + 1] if name in args else None

    def apply(self, task, args):
        if "--title" in args:
            task["title"] = self.opt(args, "--title")
        for flag, key in (("--due-date", "dueDate"), ("--start-date", "startDate")):
            if flag in args:
                local = ds.dt.datetime.strptime(self.opt(args, flag), "%Y-%m-%dT%H:%M:%S%z")
                task[key] = local.astimezone(ds.dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000+0000")
        if "--priority" in args:
            task["priority"] = int(self.opt(args, "--priority"))
        if "--items" in args:
            task["items"] = json.loads(self.opt(args, "--items"))

    def __call__(self, args):
        args = [a for a in args if a != "--json"]
        kind = args[1]
        if kind == "get":
            task = self.tasks.get(args[3])
            if not task or task["projectId"] != args[2]:
                raise ds.CliError("DIDA API 错误 404: task not found")
            return json.dumps(task)
        if kind == "search":
            hits = [t for i, t in self.tasks.items() if args[2] in t["title"]
                    and i not in self.deleted | self.unindexed]
            return json.dumps(hits)
        if args[0] == "project" and kind == "data":
            return json.dumps({"tasks": [t for i, t in self.tasks.items() if t["projectId"] == args[2] and i not in self.deleted]})
        if kind == "filter":
            low, high = (ds.dt.datetime.strptime(self.opt(args, n), "%Y-%m-%dT%H:%M:%S%z") for n in ("--start-date", "--end-date"))
            def due(t):
                return ds.dt.datetime.strptime(t["dueDate"], "%Y-%m-%dT%H:%M:%S.000%z") if t["dueDate"] else None
            hits = [t for i, t in self.tasks.items() if i not in self.deleted and t["projectId"] == self.opt(args, "--projects")
                    and due(t) and low <= due(t) <= high]
            return json.dumps(hits)
        self.writes.append(kind)
        if kind == "create":
            tid = self.add(self.opt(args, "--project"), "", None)
            self.unindexed.add(tid)
            self.apply(self.tasks[tid], args)
            parent = self.opt(args, "--parent-id")
            if parent:
                self.tasks[tid]["parentId"] = parent
                self.tasks[parent].setdefault("childIds", []).append(tid)
            return json.dumps(self.tasks[tid])
        if kind == "move":
            self.tasks[self.opt(args, "--task")]["projectId"] = self.opt(args, "--to")
            return "{}"
        if kind == "update":
            self.apply(self.tasks[args[2]], args)
            return "{}"
        raise AssertionError(f"unexpected write: {args}")


def sync(fake, mode, items):
    out = io.StringIO()
    payload = io.StringIO(json.dumps({"project_id": "inbox-x", "time_zone": "Asia/Shanghai", "items": items}))
    real_stdout, ds.sys.stdout = ds.sys.stdout, out
    try:
        code = ds.main(["dida_sync.py", mode], stdin=payload, runner=fake)
    finally:
        ds.sys.stdout = real_stdout
    return code, json.loads(out.getvalue())


def todo(**extra):
    base = {"record_id": "rec1", "title": "写完提纲", "date": "2026-10-06", "priority": 0, "content": "来源"}
    base.update(extra)
    return base


class DidaPush(unittest.TestCase):
    def test_new_todo_is_created_and_read_back(self):
        fake = FakeDida()
        code, res = sync(fake, "push", [todo(priority=5)])
        self.assertEqual((code, res[0]["result"]), (0, "created"))
        task = fake.tasks[res[0]["dida_task_id"]]
        self.assertEqual((task["dueDate"], task["priority"]), ("2026-10-05T16:00:00.000+0000", 5))

    def test_second_push_without_backfilled_id_does_not_duplicate(self):
        # Original failure (2026-10-06 live run): search lagged, the retry created a duplicate.
        fake = FakeDida()
        sync(fake, "push", [todo()])
        code, res = sync(fake, "push", [todo()])
        self.assertEqual((code, res[0]["result"], fake.writes), (0, "matched", ["create"]))

    def test_same_title_other_day_is_still_created(self):
        # Counter-example: a repeat of the same todo on a new day is a new task.
        fake = FakeDida()
        fake.add("inbox-x", "写完提纲", "2026-10-04T16:00:00.000+0000")
        self.assertEqual(sync(fake, "push", [todo()])[1][0]["result"], "created")

    def test_known_id_without_fields_never_overwrites_user_postpone(self):
        fake = FakeDida()
        tid = fake.add("inbox-x", "写完提纲", "2026-10-07T16:00:00.000+0000")
        code, res = sync(fake, "push", [todo(dida_task_id=tid)])
        self.assertEqual((res[0]["result"], fake.writes), ("exists", []))
        self.assertEqual(fake.tasks[tid]["dueDate"], "2026-10-07T16:00:00.000+0000")

    def test_date_change_moves_start_date_too(self):
        # 2026-10-07 original failure: a user-made task kept its old start date, so DIDA showed
        # 10/5–10/6 instead of 10/7 and a task moved to 10/12 still appeared under today.
        fake = FakeDida()
        tid = fake.add("inbox-x", "写完提纲", "2026-10-05T16:00:00.000+0000")
        fake.tasks[tid]["startDate"] = "2026-10-04T16:00:00.000+0000"
        code, res = sync(fake, "push", [todo(date="2026-10-07", dida_task_id=tid, fields=["date"])])
        task = fake.tasks[tid]
        self.assertEqual((code, res[0]["result"]), (0, "updated"))
        self.assertEqual(task["startDate"], task["dueDate"])

    def test_confirmed_title_change_updates_same_task(self):
        fake = FakeDida()
        tid = fake.add("inbox-x", "写完提纲", "2026-10-05T16:00:00.000+0000")
        code, res = sync(fake, "push", [todo(title="写完提纲第一章", dida_task_id=tid, fields=["title"])])
        self.assertEqual((code, res[0]["result"], fake.tasks[tid]["title"]), (0, "updated", "写完提纲第一章"))

    def test_deleted_task_is_reported_not_recreated(self):
        fake = FakeDida()
        tid = fake.add("inbox-x", "写完提纲", "2026-10-05T16:00:00.000+0000")
        fake.deleted.add(tid)
        res = sync(fake, "push", [todo(dida_task_id=tid, fields=["title"])])[1]
        self.assertEqual((res[0]["result"], fake.writes), ("deleted", []))


class DidaTargets(unittest.TestCase):
    """2026-10-06: push to each todo's own list, 🐸 in the title, subtasks at most 3 per level."""

    def test_inbox_task_is_moved_retitled_and_split(self):
        # Original failure: first batch went to the inbox with no subtasks and no 🐸.
        fake = FakeDida()
        tid = fake.add("inbox-x", "写完提纲", "2026-10-05T16:00:00.000+0000")
        fake.unindexed.clear()
        item = todo(title="🐸写完提纲", old_title="写完提纲", dida_task_id=tid, project_id="写作", priority=5,
                    subtasks=[{"title": "列章节"}, {"title": "写二级标题"}, {"title": "写核心论点"}],
                    fields=["project", "title", "priority", "subtasks"])
        code, res = sync(fake, "push", [item])
        task = fake.tasks[tid]
        self.assertEqual((code, res[0]["result"]), (0, "updated"))
        self.assertEqual((task["projectId"], task["title"], len(task["items"])), ("写作", "🐸写完提纲", 3))
        self.assertNotIn("create", fake.writes)

    def test_new_todo_goes_to_its_own_list(self):
        fake = FakeDida()
        res = sync(fake, "push", [todo(project_id="人脉管理")])[1]
        self.assertEqual(fake.tasks[res[0]["dida_task_id"]]["projectId"], "人脉管理")

    def test_nested_subtasks_become_child_tasks(self):
        fake = FakeDida()
        subs = [{"title": "甲", "subtasks": [{"title": "甲1"}, {"title": "甲2"}]}, {"title": "乙"}]
        code, res = sync(fake, "push", [todo(subtasks=subs)])
        parent = fake.tasks[res[0]["dida_task_id"]]
        kids = [fake.tasks[c] for c in parent["childIds"]]
        self.assertEqual((code, [k["title"] for k in kids], len(kids[0]["items"])), (0, ["甲", "乙"], 2))

    def test_fourth_subtask_is_rejected_before_any_write(self):
        fake = FakeDida()
        code, res = sync(fake, "push", [todo(subtasks=[{"title": t} for t in "甲乙丙丁"])])
        self.assertEqual((code, res[0]["result"], fake.writes), (1, "error", []))

    def test_existing_checklist_is_not_overwritten(self):
        # Counter-example: the user may already have ticked items in DIDA.
        fake = FakeDida()
        tid = fake.add("inbox-x", "写完提纲", "2026-10-05T16:00:00.000+0000")
        fake.tasks[tid]["items"] = [{"title": "已勾", "status": 1}]
        res = sync(fake, "push", [todo(dida_task_id=tid, subtasks=[{"title": "新"}], fields=["subtasks"])])[1]
        self.assertEqual((res[0]["result"], fake.tasks[tid]["items"][0]["title"]), ("updated", "已勾"))
        self.assertIn("notes", res[0])


class DidaUntracked(unittest.TestCase):
    def test_user_added_tasks_are_listed_and_plan_tasks_are_not(self):
        # 2026-10-07: tasks the user adds straight into DIDA (e.g. 学seo) must be surfaced for triage.
        fake = FakeDida()
        planned = fake.add("写作", "🐸写提纲", "2026-10-06T16:00:00.000+0000")
        mine = fake.add("写作", "学seo", "2026-10-05T16:00:00.000+0000")
        done = fake.add("写作", "已经做完的", "2026-10-05T16:00:00.000+0000", status=2)
        undated = fake.add("写作", "随手一记", None)
        fake.tasks[undated]["createdTime"] = "2026-10-06T02:00:00.000+0000"
        old = fake.add("写作", "很早以前的", None)
        fake.tasks[old]["createdTime"] = "2026-09-01T02:00:00.000+0000"
        payload = {"project_ids": ["写作"], "time_zone": "Asia/Shanghai", "from": "2026-10-05", "to": "2026-10-07",
                   "known_ids": [planned]}
        out = io.StringIO()
        real, ds.sys.stdout = ds.sys.stdout, out
        try:
            code = ds.main(["dida_sync.py", "untracked"], stdin=io.StringIO(json.dumps(payload)), runner=fake)
        finally:
            ds.sys.stdout = real
        titles = [t["title"] for t in json.loads(out.getvalue())]
        self.assertEqual((code, sorted(titles)), (0, ["学seo", "随手一记"]))
        self.assertEqual(fake.writes, [])


class DidaRead(unittest.TestCase):
    def test_completed_postponed_moved_and_missing(self):
        fake = FakeDida()
        done = fake.add("inbox-x", "甲", "2026-10-05T16:00:00.000+0000", status=2,
                        completed="2026-10-06T04:33:13.370+0000")
        later = fake.add("inbox-x", "乙", "2026-10-07T16:00:00.000+0000")
        moved = fake.add("other", "丙", "2026-10-05T16:00:00.000+0000")
        items = [todo(record_id="r1", title="甲", dida_task_id=done), todo(record_id="r2", title="乙", dida_task_id=later),
                 todo(record_id="r3", title="丙", dida_task_id=moved), todo(record_id="r4", title="丁", dida_task_id="gone")]
        code, res = sync(fake, "read", items)
        by_id = {r["record_id"]: r for r in res}
        self.assertEqual((by_id["r1"]["status_text"], by_id["r1"]["completed_date"]), ("已完成", "2026-10-06"))
        self.assertEqual((by_id["r2"]["date_changed"], by_id["r2"]["due_date"]), (True, "2026-10-08"))
        self.assertEqual((by_id["r3"]["moved"], by_id["r3"]["project_id"]), (True, "other"))
        self.assertFalse(by_id["r4"]["found"])
        self.assertEqual(fake.writes, [])


class PrivacyScan(unittest.TestCase):
    """Public files must not carry personal resource coordinates."""
    PATTERNS = [r"feishu\.cn/(base|docx|drive|wiki)/", r"\btbl[A-Za-z0-9]{12,}", r"\b[A-Za-z0-9]{27}\b", r"\bou_[a-z0-9]{20,}", r"\binbox\d{6,}"]

    def test_no_personal_tokens_outside_private_config(self):
        hits = []
        for path in ROOT.rglob("*"):
            if not path.is_file() or path.name == "personal-config.md" or "__pycache__" in path.parts:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in self.PATTERNS:
                hits += [f"{path.relative_to(ROOT)}: {m.group(0)}" for m in re.finditer(pattern, text)]
        self.assertEqual(hits, [])


class RuleConsistency(unittest.TestCase):
    """Public rule files must agree with the current 333 rule and the current visual entry."""
    FILES = ["SKILL.md", "references/planning.md", "references/review.md", "references/schema.md"]

    def text(self, name):
        return (ROOT / name).read_text(encoding="utf-8")

    def test_no_old_monthly_three_total_rule(self):
        # Original failure: review.md kept "下月最多 3 个成果" after the rule became per-dimension.
        hits = [n for n in self.FILES if re.search(r"(下月|本月|每月)最多\s*3\s*个(关键)?成果", self.text(n))]
        self.assertEqual(hits, [])

    def test_three_frogs_rule_stated_where_plans_are_written(self):
        # Adjacent case: files that lead to writing plans carry the three-frogs rule, not a total cap.
        for n in ["references/planning.md", "references/review.md", "SKILL.md"]:
            self.assertRegex(self.text(n), r"3\s*(只|个)\s*🐸|3只🐸", n)
            self.assertNotRegex(self.text(n), r"每个?维度最多\s*3\s*条|合计最多\s*3\s*项|各最多\s*3\s*项", n)

    def test_no_cancelled_visual_presented_as_current(self):
        # Original failure: SKILL.md still described the deleted BaseApp board as the live entry.
        skill = self.text("SKILL.md")
        self.assertNotRegex(skill, r"v1\.1\s*使用\s*BaseApp")
        self.assertNotIn("刷新九宫格", skill)

    def test_planning_does_not_revive_cancelled_board(self):
        # Original failure: planning.md still said the BaseApp board was "未被用户取消" after D11.
        self.assertNotIn("未被用户取消", self.text("references/planning.md"))

    def test_dida_is_no_longer_read_only_in_entry(self):
        # 2026-10-06: daily todos are pushed after confirmation; status stays read-only.
        skill = self.text("SKILL.md")
        self.assertNotIn("待办工具只读取证", skill)
        self.assertIn("references/dida-push.md", skill)

    def test_old_field_names_are_gone(self):
        # 2026-10-06: fields renamed to 月目标／周计划 at the user's request.
        hits = [n for n in self.FILES + ["references/dida-push.md"] if re.search("月成果|周结果|周目标", self.text(n))]
        self.assertEqual(hits, [])

    def test_insert_triage_is_the_entry_for_mid_period_additions(self):
        # 2026-10-06 original failure: a new idea was pushed to next week without judging it.
        self.assertIn("## 插入判断", self.text("references/planning.md"))
        self.assertIn("插入判断", self.text("SKILL.md"))
        self.assertIn("切一小块本期做", self.text("references/planning.md"))

    def test_status_sync_no_longer_waits_for_confirmation(self):
        # 2026-10-07: statuses the user already set in DIDA are synced, not asked again.
        for n in ["SKILL.md", "references/dida-push.md", "references/review.md"]:
            self.assertNotRegex(self.text(n), "用户确认后才改执行台|回读结果改执行台前经过用户确认", n)
        self.assertIn("回读与同步", self.text("references/dida-push.md"))

    def test_project_ideas_stay_out_of_someday_list(self):
        # 2026-10-07 original failure: project ideas were suggested for the personal 「将来也许」 list.
        text = self.text("references/planning.md")
        self.assertIn("个人生活类的想法才放「将来也许」", text)

    def test_history_mentions_still_allowed(self):
        # Counter-example: saying the old routes were cancelled is fine and must not trip the checks.
        self.assertIn("已取消", self.text("SKILL.md"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
