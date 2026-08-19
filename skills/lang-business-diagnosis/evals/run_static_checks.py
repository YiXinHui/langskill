#!/usr/bin/env python3
"""Deterministic contract checks for lang-business-diagnosis (开源商业初诊)."""

from __future__ import annotations

import re
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
SKILL = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
REFERENCES = SKILL_DIR / "references"
CHECK_COUNT = 0


def require(condition: bool, message: str) -> None:
    global CHECK_COUNT
    CHECK_COUNT += 1
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def require_all(text: str, phrases: list[str], label: str) -> None:
    for phrase in phrases:
        require(phrase in text, f"{label} missing: {phrase}")


# 面向用户的可见文案文件：主文档 + 三份用户体验规则。内部英文术语只允许
# 存在于 handoff-compat.md（内部兼容文档），其余文件一律不得出现。
USER_FACING_FILES = [
    "SKILL.md",
    "experience-contract.md",
    "report-contract.md",
    "lead-card-contract.md",
]
INTERNAL_TERMS = ["claim", "audiences", "Handoff", "DiagnosisState"]
AD_WORDS = ["作者", "微信", "@", "欢迎咨询", "商务合作"]

SKILL_LINES = SKILL.splitlines()
SKILL_FRONTMATTER = "\n".join(SKILL_LINES[:12])

# --- 1. frontmatter: name 与 description ---
require(SKILL.startswith("---\n"), "SKILL.md frontmatter is missing")
require("name: lang-business-diagnosis" in SKILL_FRONTMATTER, "frontmatter name is missing or wrong")
require("description:" in SKILL_FRONTMATTER, "frontmatter description is missing")
require_all(
    SKILL_FRONTMATTER,
    [
        "帮公司看看",
        "AI 化",
        "初诊",
    ],
    "description trigger scenes",
)
require("description:" in SKILL_FRONTMATTER and "ROI" in SKILL_FRONTMATTER,
        "description must state the public boundary (止于初诊，不承诺 ROI)")

# --- 2. 主文档 ≤150 行 ---
require(len(SKILL_LINES) <= 150, f"SKILL.md must be <=150 lines, got {len(SKILL_LINES)}")

# --- 3. 零广告黑名单（SKILL.md 全文，禁止语境出现也算失败） ---
for word in AD_WORDS:
    require(word not in SKILL, f"ad word survived in SKILL.md: {word}")

# --- 4. SKILL.md 引用的 references 路径都存在 ---
linked_refs = re.findall(r"\[[^\]]*\]\(references/([^)#]+)\)", SKILL)
require(len(linked_refs) > 0, "SKILL.md must route to at least one reference")
for ref in linked_refs:
    require((REFERENCES / ref).is_file(), f"SKILL.md routes to missing reference: {ref}")

# --- 5. 内部英文术语只允许在 handoff-compat.md，不出现在用户可见文案 ---
for fname in USER_FACING_FILES:
    text = SKILL if fname == "SKILL.md" else (REFERENCES / fname).read_text(encoding="utf-8")
    for term in INTERNAL_TERMS:
        require(
            not re.search(rf"\b{term}\b", text),
            f"internal term leaked into user-facing file {fname}: {term}",
        )

# --- 6. SKILL.md 落地八条体验机制（领导亲验核心） ---
require_all(
    SKILL,
    [
        "先给结果预期",
        "一次只问一个问题",
        "回放确认",
        "商业分析前置",
        "基础先行",
        "破手段执念",
        "最小验证动作",
        "全程零广告",
        "疲劳与暂停",
    ],
    "experience mechanism in SKILL.md",
)
require("合法结论" in SKILL, "SKILL.md must allow non-AI conclusions explicitly")

# --- 7. 入口体验（experience-contract.md） ---
entry = (REFERENCES / "experience-contract.md").read_text(encoding="utf-8")
require_all(
    entry,
    [
        "先给结果预期，再识别入口",
        "整体扫描",
        "具体业务问题",
        "已有 AI 想法",
        "直接上下文优先",
        "首轮禁区",
        "不直接询问公司做什么",
        "一次只问一个问题",
        "回放确认",
        "登记为候选",
        "商业分析前置",
        "用他自己说的业务证据做比较",
        "禁止说教、禁止兜售焦虑",
        "保住他的手段",
    ],
    "entry & conversation contract",
)

# --- 8. 报告契约（report-contract.md） ---
report = (REFERENCES / "report-contract.md").read_text(encoding="utf-8")
require_all(
    report,
    [
        "带证据边界",
        "最小验证动作",
        "值得进一步验证",
        "基础先行",
        "当前不该用 AI",
        "证据不足",
        "用户一个人就能完成",
        "不把新问题设为领取条件",
        "单例事件当成公司事实",
        "结构化声明的英文术语",
    ],
    "report contract",
)

# --- 9. 线索卡契约（lead-card-contract.md） ---
lead = (REFERENCES / "lead-card-contract.md").read_text(encoding="utf-8")
require_all(
    lead,
    [
        "自愿",
        "用户明确要求导出",
        "不自动外发",
        "不留联系方式",
        "不连接任何外部系统",
        "当前没有把它发送给任何人",
        "单例和样本不升级为公司事实",
    ],
    "lead card contract",
)

# --- 10. 交接兼容（handoff-compat.md） ---
handoff = (REFERENCES / "handoff-compat.md").read_text(encoding="utf-8")
require("兼容 lang-enterprise-ai-diagnosis HandoffV2" in handoff,
        "handoff compat must declare HandoffV2 compatibility")
require("本文件自包含，不引用仓外路径" in handoff, "handoff compat must be self-contained")
require_all(
    handoff,
    [
        "schema_version: enterprise_ai_diagnosis_handoff_v2",
        "draft_for_review | approved_for_export | imported | superseded",
        "source_hash",
        "respondent_scope",
        "claims:",
        "diagnosis_result:",
        "consent:",
        "exportable",
        "external_send_authorized",
        "允许导出永远不自动意味着允许发送",
        "supporting_claim_ids",
        "source_result_paths",
        "internal_only | consultant_only | owner_visible | client_visible | exportable",
    ],
    "handoff v2 compatibility envelope",
)

# 契约中必须存在三项独立授权，防止把“导出”误解为“外发”。
require("export_authorized: false" in handoff and "external_send_authorized: false" in handoff,
        "handoff consent defaults must be false")

# --- 11. 三个模拟剧本必须存在且覆盖全部体验要素 ---
TRANSCRIPTS = [
    "2026-08-03_transcript_1_manufacturing-ai-platform.md",
    "2026-08-03_transcript_2_ecommerce-support-bot.md",
    "2026-08-03_transcript_3_bakery-cost-reduction.md",
]
for tname in TRANSCRIPTS:
    tpath = SKILL_DIR / "evals" / tname
    require(tpath.is_file(), f"missing transcript: {tname}")
    text = tpath.read_text(encoding="utf-8")
    label = tname
    require("入口识别" in text, f"{label} missing 入口识别")
    require("回放确认 1" in text, f"{label} missing first 回放确认")
    require("回放确认 2" in text, f"{label} missing second 回放确认")
    require("改判时刻" in text, f"{label} missing 改判时刻")
    require("手段登记候选" in text, f"{label} missing 手段登记候选")
    require_all(text, ["证据边界", "最小验证", "线索卡"], f"{label} legal ending")
    require("当前没有把它发送给任何人" in text, f"{label} must state no send was executed")

print(
    f"OK: {CHECK_COUNT} checks passed across the entry experience, report, lead card, "
    "HandoffV2 compatibility contracts, and the three transcript scenarios"
)
