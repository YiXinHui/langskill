#!/usr/bin/env python3
"""Regressions for the 333 validator and a privacy scan of the public skill files."""
import importlib.util
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("validate_plan", ROOT / "scripts/validate_plan.py")
vp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vp)


def item(title, **extra):
    base = {"title": title, "parent": "rec-synthetic-parent", "done_when": "可检查的结果", "dimension": "工作事业"}
    base.update(extra)
    return base


class PlanChecks(unittest.TestCase):
    def test_three_items_pass(self):
        plan = {"level": "month", "period": "2026-10", "items": [item("甲"), item("乙"), item("丙", due="2026-10-31")]}
        self.assertEqual(vp.validate(plan), [])

    def test_fourth_item_in_one_dimension_fails(self):
        plan = {"level": "month", "period": "2026-10", "items": [item(t) for t in "甲乙丙丁"]}
        self.assertTrue(any("per dimension" in e for e in vp.validate(plan)))

    def test_month_non_frogs_across_dimensions_pass(self):
        dims = ["工作事业", "工作事业", "体验突破", "财务理财", "学习成长", "人际社交"]
        titles = ["🐸甲", "🐸乙", "🐸丙", "丁", "戊", "己"]
        plan = {"level": "month", "period": "2026-10", "items": [item(t, dimension=d) for t, d in zip(titles, dims)]}
        self.assertEqual(vp.validate(plan), [])

    def test_fourth_frog_fails_even_across_dimensions(self):
        dims = ["工作事业", "体验突破", "财务理财", "学习成长"]
        plan = {"level": "month", "period": "2026-10", "items": [item("🐸" + t, dimension=d) for t, d in zip("甲乙丙丁", dims)]}
        self.assertTrue(any("frog" in e for e in vp.validate(plan)))

    def test_multi_dimension_item_counts_in_each(self):
        items = [item(t) for t in "甲乙丙"] + [item("丁", dimension=["学习成长", "工作事业"])]
        self.assertTrue(any("工作事业" in e for e in vp.validate({"level": "month", "period": "2026-10", "items": items})))

    def test_month_needs_dimension(self):
        plan = {"level": "month", "period": "2026-10", "items": [item("甲", dimension=None)]}
        self.assertTrue(any("dimension" in e for e in vp.validate(plan)))

    def test_week_still_total_three(self):
        items = [item(t, dimension=d) for t, d in zip("甲乙丙丁", ["工作事业", "体验突破", "财务理财", "学习成长"])]
        self.assertTrue(any("333" in e for e in vp.validate({"level": "week", "period": "2026-10-05", "items": items})))

    def test_completed_and_cancelled_still_count(self):
        items = [item("甲", status="已完成", actual_result="做成了"), item("乙", status="取消"), item("丙"), item("丁")]
        self.assertTrue(any("333" in e for e in vp.validate({"level": "week", "period": "2026-10-05", "items": items})))

    def test_week_must_start_monday(self):
        self.assertEqual(vp.validate({"level": "week", "period": "2026-10-06", "items": []}), ["week period must be a Monday"])

    def test_due_outside_month(self):
        plan = {"level": "month", "period": "2026-10", "items": [item("甲", due="2026-11-01")]}
        self.assertTrue(any("outside" in e for e in vp.validate(plan)))

    def test_completed_needs_actual_result(self):
        plan = {"level": "month", "period": "2026-10", "items": [item("甲", status="已完成")]}
        self.assertTrue(any("actual_result" in e for e in vp.validate(plan)))

    def test_day_needs_parent_not_done_when(self):
        ok = {"level": "day", "period": "2026-10-07", "items": [{"title": "写完提纲", "parent": "rec-week"}]}
        self.assertEqual(vp.validate(ok), [])
        orphan = {"level": "day", "period": "2026-10-07", "items": [{"title": "写完提纲"}]}
        self.assertTrue(any("parent" in e for e in vp.validate(orphan)))

    def test_old_status_rejected(self):
        plan = {"level": "week", "period": "2026-10-05", "items": [item("甲", status="待核")]}
        self.assertTrue(any("status" in e for e in vp.validate(plan)))

    def test_duplicate_titles(self):
        plan = {"level": "day", "period": "2026-10-07", "items": [{"title": "甲", "parent": "r"}, {"title": "甲", "parent": "r"}]}
        self.assertIn("duplicate titles in this period", vp.validate(plan))


class PrivacyScan(unittest.TestCase):
    """Public files must not carry personal resource coordinates."""
    PATTERNS = [r"feishu\.cn/(base|docx|drive|wiki)/", r"\btbl[A-Za-z0-9]{12,}", r"\b[A-Za-z0-9]{27}\b", r"\bou_[a-z0-9]{20,}"]

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

    def test_month_rule_stated_where_month_plans_are_written(self):
        # Adjacent case: both files that lead to writing a month plan carry the per-dimension rule.
        for n in ["references/planning.md", "references/review.md"]:
            self.assertRegex(self.text(n), r"每个维度最多\s*3\s*条", n)

    def test_no_cancelled_visual_presented_as_current(self):
        # Original failure: SKILL.md still described the deleted BaseApp board as the live entry.
        skill = self.text("SKILL.md")
        self.assertNotRegex(skill, r"v1\.1\s*使用\s*BaseApp")
        self.assertNotIn("刷新九宫格", skill)

    def test_history_mentions_still_allowed(self):
        # Counter-example: saying the old routes were cancelled is fine and must not trip the checks.
        self.assertIn("已取消", self.text("SKILL.md"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
