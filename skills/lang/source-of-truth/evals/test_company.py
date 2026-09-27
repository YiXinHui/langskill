#!/usr/bin/env python3
"""Company module checks through its public CLI."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import re
from urllib.parse import unquote, urlsplit

SKILL = Path(__file__).resolve().parents[1]
SCRIPT = SKILL / "scripts/init_company.py"


class CompanyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="company-sot-test-")
        self.base = Path(self.temp.name)
        self.root = self.base / "company"

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
            content = path.read_text()
            for angle, bare in re.findall(r"\]\((?:<([^>]+)>|([^\s)]+))\)", content):
                target = angle or bare
                if target.startswith("https://"):
                    continue
                self.assertTrue((path.parent / unquote(urlsplit(target).path)).exists(),
                                f"Broken link: {path}: {target}")

    def test_preview_create_check_and_idempotence(self):
        self.assertEqual(self.cli("--dry-run")["status"], "preview_no_writes")
        self.assertFalse(self.root.exists())
        self.assertEqual(self.cli("--check", expected=1)["status"], "incomplete")
        self.assertFalse(self.root.exists())
        self.assertEqual(self.cli()["status"], "created")
        structure = json.loads((SKILL / "assets/company-structure.json").read_text())
        for top in structure:
            self.assertTrue((self.root / top / ".docs/README.md").is_file())
        self.assertTrue((self.root / ".docs/SOURCE_OF_TRUTH.md").is_file())
        self.assertTrue((self.root / "AGENTS.md").is_file())
        self.assertFalse((self.root / "01-知识体系").exists())
        self.check_links()
        self.assertEqual(self.cli("--check")["status"], "verified")
        before = self.snapshot()
        self.assertEqual(self.cli()["status"], "unchanged")
        self.assertEqual(before, self.snapshot())

    def test_custom_company_and_remote_authority(self):
        cfg = self.config({"company_name": "星河咨询", "extra_directories": {
            "01-产品/企业培训": "企业培训入口"}, "authorities": {
            "customers": "https://example.com/customers"}})
        self.cli("--config", cfg)
        self.assertTrue((self.root / "01-产品/企业培训").is_dir())
        sot = (self.root / ".docs/SOURCE_OF_TRUTH.md").read_text()
        self.assertIn("星河咨询", sot)
        self.assertIn("https://example.com/customers", sot)
        self.assertIn("初始化未联网验证", sot)
        self.assertNotIn("# 公司名称 — Source of Truth", sot)
        self.assertNotIn("狼格拉底", sot)
        self.assertIn("只作导航", (self.root / "02-客户/客户索引.md").read_text())
        self.check_links()
        self.assertEqual(self.cli("--check")["status"], "verified")

    def test_conflict_preserves_existing_files_and_zero_writes(self):
        self.root.mkdir()
        (self.root / "AGENTS.md").write_text("用户已有规则")
        before = self.snapshot()
        self.assertEqual(self.cli(expected=2)["status"], "conflict_no_writes")
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.root / "01-产品").exists())

    def test_invalid_extra_and_existing_personal_workspace_rejected(self):
        for relative in ("02-客户", "02-客户/.docs/new", "11-法务/资料", "01-产品/../坏"):
            with self.subTest(relative=relative):
                self.cli("--config", self.config({"extra_directories": {relative: "用途"}}), expected=2)
                self.assertFalse(self.root.exists())
        (self.root / ".docs").mkdir(parents=True)
        (self.root / ".docs/sot-config.json").write_text("{}")
        self.cli(expected=2)
        self.assertFalse((self.root / "01-产品").exists())


if __name__ == "__main__":
    unittest.main()
