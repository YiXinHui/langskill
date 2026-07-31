#!/usr/bin/env python3
"""Deterministic structural checks for lang-enterprise-ai-diagnosis."""

from __future__ import annotations

import json
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
REFERENCES = SKILL_DIR / "references"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(f"FAIL: {message}")


require(SKILL.startswith("---\n"), "SKILL.md frontmatter is missing")
require("name: lang-enterprise-ai-diagnosis" in SKILL, "skill name is wrong")
require("description:" in SKILL, "skill description is missing")

required_references = {
    "conversation-guide.md",
    "report-contract.md",
    "handoff-contract.md",
}
actual_references = {path.name for path in REFERENCES.glob("*.md")}
require(actual_references == required_references, f"unexpected reference set: {sorted(actual_references)}")
for name in required_references:
    require(f"references/{name}" in SKILL, f"SKILL.md does not route to {name}")

for phrase in [
    "最多 3 次用户回答",
    "user_turn_count >= 4",
    "L0 自述初诊",
    "L1 样本增强初诊",
    "L2 正式诊断",
    "每回合最多要求用户完成一个动作",
    "允许“不做 AI”",
    "不超过 900 个字符",
    "不超过 500 个字符",
    "sample_reported",
    "sample_observed",
    "现成证据包",
    "单例不得直接触发全公司优先级反转",
    "l1_update_used",
    "工作画面",
    "证据动作总数为 0 或 1",
    "公开结果没有暴露 L0／L1",
    "除第一轮和终局交付外",
    "公司主要靠什么产品或服务赚钱",
    "终局事实闸门",
    "不得发明“超过六成”之类门槛",
]:
    require(phrase in SKILL, f"runtime contract missing: {phrase}")
require(
    "公司主要做什么生意，最近最想改变什么" not in SKILL,
    "cold start must not ask for business and goal in the same turn",
)

conversation = (REFERENCES / "conversation-guide.md").read_text(encoding="utf-8")
require("目标留到下一轮" in conversation, "cold-start goal must be deferred")

report = (REFERENCES / "report-contract.md").read_text(encoding="utf-8")
for phrase in [
    "一屏《企业 AI 初诊卡》",
    "当前不建议立项",
    "900 个字符",
    "500 个字符",
    "sample_reported",
    "sample_observed",
    "单一证据动作判定",
    "1 个有界更新",
    "最多一个，也可以为零",
    "谁 × 在什么时刻 × AI 改变什么动作 × 怎样看到反馈",
    "不得再邀请第二轮样本核验",
    "本轮未创建或转交任何材料",
    "下一问、要不要继续看 AI",
    "2—3 条同类已完结工单",
    "五项来源核对",
    "每个数字都要能逐字落回用户原话",
]:
    require(phrase in report, f"result contract missing: {phrase}")
require("由 AI 先" not in report, "AI work-scene template must not imply an execution chain")

handoff = (REFERENCES / "handoff-contract.md").read_text(encoding="utf-8")
require("status: draft_for_review" in handoff, "handoff review status is missing")
require("尚未发送" in handoff, "handoff must not imply external submission")
require("sample_reported | sample_observed" in handoff, "handoff sample source states are missing")
require("独立回复" in handoff, "handoff must be separate from the diagnosis card")
require("明确要求“生成正式诊断交接草稿”" in handoff, "handoff draft needs an explicit request")

evals = json.loads((SKILL_DIR / "evals" / "evals.json").read_text(encoding="utf-8"))
items = evals.get("evals", [])
require(len(items) == 35, f"expected 35 evals, got {len(items)}")
require([item["id"] for item in items] == list(range(1, 36)), "eval ids must be contiguous 1..35")
for item in items[15:]:
    require(len(item.get("expectations", [])) >= 4, f"eval {item['id']} needs at least four expectations")

by_id = {item["id"]: item for item in items}
require(
    "没有在同一轮继续要求客户类型、目标、流程或样本" in by_id[1]["expectations"],
    "eval 1 must keep the cold-start question to one business anchor",
)
for eval_id, ceiling in [(3, 500), (14, 500), (17, 900), (18, 500), (22, 900), (23, 900), (27, 500)]:
    expectations = "\n".join(by_id[eval_id]["expectations"]).replace(" ", "")
    require(
        f"不超过{ceiling}个字符" in expectations,
        f"eval {eval_id} must assert its output-length ceiling",
    )
require("未查看原始材料" in "\n".join(by_id[22]["expectations"]), "eval 22 must test reported samples")
require("没有新的用户取证动作" in "\n".join(by_id[23]["expectations"]), "eval 23 must allow zero user evidence actions")
require("没有输出负责人任务清单" in "\n".join(by_id[23]["expectations"]), "eval 23 must reject validation-loop task lists")
require("draft_for_review" in "\n".join(by_id[26]["expectations"]), "eval 26 must generate a review-only draft after an explicit request")
require("第二次样本更新" in "\n".join(by_id[28]["expectations"]), "eval 28 must stop repeated L1 updates")
require("内部术语" in "\n".join(by_id[29]["expectations"]), "eval 29 must enforce boss-facing language")
require("具体角色" in "\n".join(by_id[30]["expectations"]), "eval 30 must test the AI work scene")
require("用户取证动作数量为零" in "\n".join(by_id[31]["expectations"]), "eval 31 must allow zero evidence actions")
require("没有生成交接草稿" in "\n".join(by_id[32]["expectations"]), "eval 32 must prevent automatic handoff")
require("已有诊疗记录和医嘱" in "\n".join(by_id[33]["expectations"]), "eval 33 must preserve the production fact-boundary regression")
require("没有编造任何数字阈值" in "\n".join(by_id[34]["expectations"]), "eval 34 must generalize the numeric fact gate")
require("允许输出一个 AI 工作画面" in "\n".join(by_id[35]["expectations"]), "eval 35 must preserve evidence-supported AI scenes")

print(
    "OK: 3 staged references, 35 evals, L0/L1/L2 runtime, absolute turn stop, "
    "boss-facing output, fact gate, optional evidence action, one-shot L1 and review-only handoff are present"
)
