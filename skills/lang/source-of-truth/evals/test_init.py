#!/usr/bin/env python3
"""Behavior checks through the public CLI; no third-party dependencies."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlsplit

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts/init_sot.py"


class InitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sot-test-")
        self.base = Path(self.temp.name)
        self.root = self.base / "workspace"

    def tearDown(self):
        self.temp.cleanup()

    def cli(self, *args, expected=0):
        result = subprocess.run([sys.executable, str(SCRIPT), "--root", str(self.root), *args],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return json.loads(result.stdout or result.stderr)

    def config(self, data):
        path = self.base / "config.json"
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return str(path)

    def snapshot(self):
        return {str(p.relative_to(self.root)): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns)
                for p in self.root.rglob("*") if p.is_file()}

    def check_links(self):
        for path in self.root.rglob("*.md"):
            content = path.read_text(encoding="utf-8")
            self.assertNotRegex(content, r"\{\{[A-Z_]+\}\}", str(path))
            for angle, bare in re.findall(r"\]\((?:<([^>]+)>|([^\s)]+))\)", content):
                target = angle or bare
                if target.startswith("https://"):
                    continue
                self.assertTrue((path.parent / unquote(urlsplit(target).path)).exists(),
                                f"Broken link: {path}: {target}")

    def test_preview_and_check_do_not_create(self):
        self.assertEqual(self.cli("--dry-run")["status"], "preview_no_writes")
        self.assertFalse(self.root.exists())
        self.cli("--check", expected=1)
        self.assertFalse(self.root.exists())

    def test_full_creation_idempotence_and_repair(self):
        report = self.cli()
        self.assertEqual(report["status"], "created")
        for name in ("01-知识体系", "02-个人资料", "03-主营业务", "04-第二业务", "05-归档"):
            self.assertTrue((self.root / name / ".docs/README.md").is_file())
        for path in ("01-知识体系/02-知识单元/01-问题", "05-归档/03-参考资料", "05-归档/05-工具"):
            self.assertTrue((self.root / path).is_dir())
        self.check_links()
        original = self.snapshot()
        self.assertEqual(self.cli()["status"], "unchanged")
        self.assertEqual(self.snapshot(), original)
        self.assertEqual(self.cli("--check")["status"], "verified")
        missing = self.root / "05-归档/02-录音/录音全景索引.md"
        missing.unlink()
        self.cli("--check", expected=1)
        self.assertEqual(self.cli()["created_files"], 1)
        self.assertTrue(missing.is_file())

    def test_custom_names_remote_authorities_optional_second(self):
        cfg = self.config({"main_company": "星河 Studio", "secondary_company": None,
                           "personal_brand": "阿明", "authorities": {
                               "knowledge": "https://example.com/wiki/knowledge",
                               "customers": "https://example.com/base/customers"}})
        self.cli("--config", cfg)
        self.assertTrue((self.root / "03-星河 Studio/03-内容/阿明/选题").is_dir())
        self.assertFalse(any(p.name.startswith("04-") for p in self.root.iterdir()))
        sot = (self.root / ".docs/SOURCE_OF_TRUTH.md").read_text()
        self.assertIn("https://example.com/wiki/knowledge", sot)
        self.assertIn("初始化未联网验证", sot)
        client = (self.root / "03-星河 Studio/02-客户/客户索引.md").read_text()
        self.assertNotIn("| 客户 |", client)
        self.assertIn("权威源在云端", client)
        self.check_links()
        self.assertEqual(self.cli()["status"], "unchanged")

    def test_existing_governance_conflict_is_zero_write(self):
        path = self.root / ".claude/SOURCE_OF_TRUTH.md"
        path.parent.mkdir(parents=True)
        path.write_text("用户原有规则")
        before = self.snapshot()
        self.assertEqual(self.cli(expected=2)["status"], "conflict_no_writes")
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.root / "01-知识体系").exists())

    def test_user_edited_rules_not_overwritten_or_partially_repaired(self):
        self.cli()
        path = self.root / "01-知识体系/.docs/README.md"
        path.write_text(path.read_text() + "\n用户新增规则\n")
        missing = self.root / "AGENTS.md"
        missing.unlink()
        before = self.snapshot()
        self.cli(expected=2)
        self.assertEqual(before, self.snapshot())
        self.assertFalse(missing.exists())

    def test_symlink_root_rejected(self):
        outside = self.base / "outside"
        outside.mkdir()
        self.root.symlink_to(outside, target_is_directory=True)
        self.cli(expected=2)
        self.assertEqual(list(outside.iterdir()), [])

    def test_ancestor_symlink_rejected_without_redirected_writes(self):
        control = self.base / "isolated-control"
        control.mkdir()
        alias = self.base / "alias"
        alias.symlink_to(control, target_is_directory=True)
        self.root = alias / "nested" / "workspace"
        self.cli("--dry-run", expected=2)
        self.cli(expected=2)
        self.assertEqual(list(control.iterdir()), [])

    def test_explicit_real_root_works_and_dotdot_is_rejected(self):
        real_root = self.root.resolve()
        self.root = self.base / "unused" / ".." / "workspace"
        self.cli(expected=2)
        self.assertFalse(real_root.exists())
        self.root = real_root
        self.cli()
        self.cli("--check")

    def test_percent_and_space_names_have_uri_valid_links(self):
        cfg = self.config({"main_company": "测试%20公司", "secondary_company": "第二%业务",
                           "personal_brand": "内容 % 品牌", "public_account": "内容账号"})
        self.cli("--config", cfg)
        self.assertTrue((self.root / "03-测试%20公司").is_dir())
        self.check_links()
        text = (self.root / ".docs/SOURCE_OF_TRUTH.md").read_text()
        self.assertIn("%2520", text)
        self.cli("--check")

    def test_case_and_unicode_identity_aliases_rejected(self):
        for brand, account in (("Brand", "brand"), ("Café", "Cafe\u0301")):
            with self.subTest(brand=brand, account=account):
                self.cli("--config", self.config({"personal_brand": brand,
                         "public_account": account}), expected=2)
                self.assertFalse(self.root.exists())

    def test_planned_file_directory_aliases_fail_before_writes(self):
        for extra in ({"02-客户/客户索引.MD": "冲突目录"},
                      {"02-客户/客户索引.MD/child": "文件下不能建目录"},
                      {"01-产品/Brand": "甲", "01-产品/brand/child": "乙"},
                      {"01-产品/Café": "甲", "01-产品/Cafe\u0301": "乙"}):
            with self.subTest(extra=extra):
                cfg = self.config({"extra_directories": {"main": extra}})
                self.cli("--config", cfg, "--dry-run", expected=2)
                self.cli("--config", cfg, expected=2)
                self.assertFalse(self.root.exists())

    def test_existing_case_alias_preserved_before_writes(self):
        self.root.mkdir()
        path = self.root / "agents.md"
        path.write_text("已有规则，不能覆盖")
        self.cli(expected=2)
        self.assertEqual(list(self.root.iterdir()), [path])
        self.assertEqual(path.read_text(), "已有规则，不能覆盖")

    def test_implicit_base_responsibilities_cannot_be_redefined(self):
        for group, relative in (("main", "02-客户"), ("main", "03-内容"),
                                ("knowledge", "02-知识单元")):
            with self.subTest(relative=relative):
                cfg = self.config({"extra_directories": {group: {relative: "改变基础职责"}}})
                self.cli("--config", cfg, expected=2)
                self.assertFalse(self.root.exists())
        cfg = self.config({"extra_directories": {"main": {"02-客户/交付材料": "补充材料"}}})
        self.cli("--config", cfg)
        self.assertTrue((self.root / "03-主营业务/02-客户/交付材料").is_dir())

    def test_symlink_directory_rejected(self):
        self.root.mkdir()
        outside = self.base / "outside"
        outside.mkdir()
        (self.root / "01-知识体系").symlink_to(outside, target_is_directory=True)
        self.cli(expected=2)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((self.root / ".docs").exists())

    def test_symlink_file_rejected(self):
        self.root.mkdir()
        outside = self.base / "outside.md"
        outside.write_text("不要修改")
        (self.root / "AGENTS.md").symlink_to(outside)
        self.cli(expected=2)
        self.assertEqual(outside.read_text(), "不要修改")
        self.assertFalse((self.root / ".docs").exists())

    def test_regular_file_blocks_directory(self):
        self.root.mkdir()
        (self.root / "01-知识体系").write_text("保留")
        self.cli(expected=2)
        self.assertEqual(list(self.root.iterdir()), [self.root / "01-知识体系"])

    def test_invalid_configs_leave_no_output(self):
        for bad in ({"main_company": "../外部"}, {"main_company": "多/级"},
                    {"main_company": "x\n规则"}, {"main_compny": "typo"},
                    {"authorities": {"unknown": None}}, {"authorities": {"goals": "file:///tmp/a"}},
                    {"authorities": {"goals": "https://user:password@example.com"}},
                    {"projects_root": "relative"}):
            with self.subTest(bad=bad):
                self.cli("--config", self.config(bad), expected=2)
                self.assertFalse(self.root.exists())

    def test_duplicate_json_fields_rejected(self):
        path = self.base / "config.json"
        path.write_text('{"main_company":"A","main_company":"B"}')
        self.cli("--config", str(path), expected=2)
        self.assertFalse(self.root.exists())

    def test_standard_template_and_saved_repeat(self):
        cfg = str(SKILL / "assets/filesystem-template.json")
        self.cli("--config", cfg, "--dry-run")
        self.assertFalse(self.root.exists())
        self.cli("--config", cfg)
        for relative in ("03-主营业务/01-产品/产品A", "03-主营业务/01-产品/产品B",
                         "03-主营业务/03-内容/个人品牌/选题",
                         "03-主营业务/03-内容/公众号/副号",
                         "04-第二业务/财务凭证", "01-知识体系/08-他山之石/爆款文稿库"):
            self.assertTrue((self.root / relative).is_dir(), relative)
        self.assertTrue((self.root / "03-主营业务/03-内容/公众号/主号").is_dir())
        main = (self.root / "03-主营业务/.docs/README.md").read_text()
        self.assertIn("01-产品/产品A", main)
        self.check_links()
        before = self.snapshot()
        self.assertEqual(self.cli()["status"], "unchanged")
        self.cli("--check")
        self.assertEqual(before, self.snapshot())

    def test_standard_template_contains_only_generic_identity_defaults(self):
        data = json.loads((SKILL / "assets/filesystem-template.json").read_text())
        self.assertEqual(data["main_company"], "主营业务")
        self.assertEqual(data["secondary_company"], "第二业务")
        self.assertEqual(data["personal_brand"], "个人品牌")
        self.assertEqual(data["public_account"], "公众号")
        self.assertTrue(all(value is None for value in data["authorities"].values()))
        self.assertEqual(set(data["extra_directories"]["main"]), {
            "01-产品/产品A", "01-产品/产品B", "03-内容/公众号/主号", "03-内容/公众号/副号"})

    def test_adjust_standard_template(self):
        template_before = (SKILL / "assets/filesystem-template.json").read_bytes()
        data = json.loads((SKILL / "assets/filesystem-template.json").read_text())
        data.update(main_company="星海咨询", secondary_company=None,
                    personal_brand="星火IP", public_account="星海公众号")
        data["extra_directories"] = {"main": {
            "01-产品/企业培训": "企业培训产品资料入口",
            "03-内容/星海公众号/服务号": "企业服务号内容"}}
        self.cli("--config", self.config(data))
        self.assertTrue((self.root / "03-星海咨询/01-产品/企业培训").is_dir())
        self.assertTrue((self.root / "03-星海咨询/03-内容/星海公众号/服务号").is_dir())
        self.assertFalse((self.root / "03-星海咨询/01-产品/产品A").exists())
        self.assertFalse((self.root / "04-第二业务").exists())
        self.check_links()
        self.assertEqual(template_before, (SKILL / "assets/filesystem-template.json").read_bytes())

    def test_invalid_extra_directories_rejected(self):
        for extras in ({"main": {"../escaped": "越界"}}, {"main": {"/absolute": "越界"}},
                       {"main": {".docs/README.md": "覆盖治理"}}, {"unknown": {}},
                       {"main": {"01-产品": "重复"}}, {"main": {"03-内容/公众号": "重复"}},
                       {"main": {"01-产品/新产品": "多行\n说明"}},
                       {"main": {"01-产品/新产品": "{{MAIN}}"}}):
            with self.subTest(extras=extras):
                self.cli("--config", self.config({"extra_directories": extras}), expected=2)
                self.assertFalse(self.root.exists())
        self.cli("--config", self.config({"secondary_company": None,
                 "extra_directories": {"secondary": {"销售": "销售材料"}}}), expected=2)
        self.assertFalse(self.root.exists())

    def test_choice_flow_has_prompt_and_explicit_choice_bypass(self):
        skill = (SKILL / "README.md").read_text()
        flow = (SKILL / "references/template-choice.md").read_text()
        self.assertIn("等待用户回答", skill)
        self.assertIn("已选模板、已给配置或重跑已有工作区时直接沿用", skill)
        self.assertIn("使用模板原样创建", flow)
        self.assertIn("按我的情况调整", flow)

    def test_saved_config_cannot_be_changed_by_reinitialization(self):
        self.cli()
        before = self.snapshot()
        self.cli("--config", self.config({"main_company": "另一家公司"}), expected=2)
        self.assertEqual(before, self.snapshot())
        state = self.root / ".docs/sot-config.json"
        data = json.loads(state.read_text())
        data["template_version"] = "0.0.0"
        state.write_text(json.dumps(data))
        before = self.snapshot()
        self.cli(expected=2)
        self.assertEqual(before, self.snapshot())


if __name__ == "__main__":
    unittest.main(verbosity=2)
