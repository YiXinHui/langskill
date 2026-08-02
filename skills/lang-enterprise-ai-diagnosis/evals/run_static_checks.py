#!/usr/bin/env python3
"""Deterministic contract checks for lang-enterprise-ai-diagnosis."""

from __future__ import annotations

import json
import re
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_DIR.parents[1]
SKILL = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
REFERENCES = SKILL_DIR / "references"
CORE = REFERENCES / "core"
CHECK_COUNT = 0


def require(condition: bool, message: str) -> None:
    global CHECK_COUNT
    CHECK_COUNT += 1
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def require_all(text: str, phrases: list[str], label: str) -> None:
    for phrase in phrases:
        require(phrase in text, f"{label} missing: {phrase}")


require(SKILL.startswith("---\n"), "SKILL.md frontmatter is missing")
require("name: lang-enterprise-ai-diagnosis" in SKILL, "skill name is wrong")
require("description:" in SKILL, "skill description is missing")

required_references = {
    "entry-experience.md",
    "conversation-guide.md",
    "report-contract.md",
    "handoff-contract.md",
    "presentation-contract.md",
    "judgment-provider-contract.md",
}
actual_references = {path.name for path in REFERENCES.glob("*.md")}
require(actual_references == required_references, f"unexpected top-level reference set: {sorted(actual_references)}")

required_core = {
    "diagnosis-core.md",
    "case-model.md",
    "evidence-and-interaction.md",
    "method-registry.md",
}
actual_core = {path.name for path in CORE.glob("*.md")}
require(actual_core == required_core, f"unexpected core reference set: {sorted(actual_core)}")

for name in required_references:
    require(f"references/{name}" in SKILL, f"SKILL.md does not route to {name}")
for name in required_core:
    require(f"references/core/{name}" in SKILL, f"SKILL.md does not route to core/{name}")

entry = (REFERENCES / "entry-experience.md").read_text(encoding="utf-8")
conversation = (REFERENCES / "conversation-guide.md").read_text(encoding="utf-8")
report = (REFERENCES / "report-contract.md").read_text(encoding="utf-8")
handoff = (REFERENCES / "handoff-contract.md").read_text(encoding="utf-8")
presentation = (REFERENCES / "presentation-contract.md").read_text(encoding="utf-8")
provider = (REFERENCES / "judgment-provider-contract.md").read_text(encoding="utf-8")
core = (CORE / "diagnosis-core.md").read_text(encoding="utf-8")
case_model = (CORE / "case-model.md").read_text(encoding="utf-8")
evidence = (CORE / "evidence-and-interaction.md").read_text(encoding="utf-8")
methods = (CORE / "method-registry.md").read_text(encoding="utf-8")
runtime = "\n".join(
    [SKILL, entry, conversation, report, handoff, presentation, provider, core, case_model, evidence, methods]
)

require(
    "最近最想改变的一项经营结果，或者最近一次本来不该你亲自介入" not in conversation,
    "blank-start event-first prompt survived",
)
for obsolete_blank_start in [
    "可以。先说说你和公司现在主要做什么，你平时负责哪些事情？",
    "像正常顾问初次见面，邀请用户介绍公司主要做什么、本人负责哪些事情",
]:
    require(obsolete_blank_start not in runtime, f"obsolete blank-start rule survived: {obsolete_blank_start}")

# Runtime decisions must not be driven by fixed counters, fixed evidence quotas or hard size budgets.
for forbidden in [
    "最多 3 次用户回答",
    "user_turn_count >= 4",
    "累计第4个用户回合",
    "l1_update_used",
    "不得再邀请第二轮样本核验",
    "唯一一次样本增强",
    "最多 500 个字符",
    "最多 900 个字符",
]:
    require(forbidden not in runtime, f"fixed-turn, one-shot or fixed-size boundary survived: {forbidden}")

require_all(
    SKILL,
    [
        "先建立用户方向感",
        "入口之后形成最小生意图",
        "目标允许并行",
        "先保留候选，再选择焦点",
        "焦点选定后还原工作系统",
        "价值判断与 AI 判断分开",
        "认路阶段不强行洞察",
        "每轮只有一个明确去向",
        "只问会改变决定且容易回答的问题",
        "允许纠正、疲劳与暂停",
        "允许不做 AI",
        "默认拒绝内部逻辑和广告",
        "draft_for_review",
    ],
    "stable runtime principle",
)

require_all(
    entry,
    [
        "用户进入后先获得什么",
        "三种入口",
        "整体扫描",
        "具体业务问题",
        "已有 AI 想法",
        "直接上下文优先",
        "用户不知道怎样选择",
        "入口之后的前台体验",
        "入口完成条件",
        "首轮禁区",
        "最后形成一份初诊判断和下一步验证建议",
        "不使用没有承接对象的“可以”“好的”“没问题”",
        "不直接询问公司做什么和用户负责什么",
        "不能自行补出收衣检查、洗后质检、交付前复检等阶段",
        "不在进度提示中出现 Skill 标识符、文件名或“按某入口／路由处理”",
        "空激活时只需要读取本协议",
    ],
    "entry experience",
)

require_all(
    conversation,
    [
        "入口完成后的路由",
        "整体扫描中的生意图与回答者范围",
        "空激活、结果预期和三种入口选择",
        "先了解产品／服务和主要客户",
        "不重复说明产品、不再次展示三种方式",
        "生意图与回答者范围",
        "把宽泛目标整理成议题组合",
        "形成候选工作系统组合",
        "选定焦点后还原工作系统",
        "普通回合契约",
        "选择下一问",
        "非终局回复不能莫名结束",
        "`next_move = ask`",
        "`next_move = checkpoint`",
        "`next_move = result`",
        "`next_move = pause`",
        "`next_move = repair`",
        "用户主动提供具体时间、差异、动作和发现方式",
        "不能直接问“最近一次具体错了什么、怎样发现”",
        "新日期没有进入共同执行依据",
        "不得出现“这项工作是否适合 AI”",
        "具体工作先于目标取舍出现时",
        "必须显式说出这些目标仍然开放",
        "用户愿意继续",
        "纠偏、疲劳与暂停",
        "恢复时回放已确认的生意范围",
    ],
    "conversation contract",
)

require_all(
    core,
    [
        "入口方向",
        "整体扫描",
        "具体业务问题",
        "已有 AI 想法",
        "企业经营地图",
        "候选工作系统组合",
        "选定工作系统的证据",
        "价值维度",
        "AI 介入",
        "工作系统",
        "validation_candidate",
        "foundation_first",
        "non_ai_priority",
        "insufficient_evidence",
        "事件证据阶段不提前讨论 AI 适配",
        "某张表未更新",
        "任何非终局回复都必须有明确去向",
    ],
    "diagnosis core",
)

# EnterpriseDiagnosisCaseV2 is the canonical case model. StateV1 is read-only compatibility only.
require_all(
    case_model,
    [
        "schema: enterprise_ai_diagnosis_case_v2",
        "entry_context:",
        "diagnosis_intent: unspecified",
        "entry_form: blank_activation",
        "route_source: system_activation",
        "company_scan | specific_business_issue | evaluate_ai_idea | unspecified",
        "blank_activation | intent_only | contextualized | resumed",
        "explicit | inferred | system_activation | unknown",
        "第一条回复先说明结果预期并识别入口",
        "respondent:",
        "actual_responsibilities:",
        "business_map:",
        "agenda:",
        "desired_outcomes:",
        "diagnostic_boundary:",
        "opportunity_portfolio:",
        "selected_focus:",
        "current_work_system:",
        "value_map:",
        "intervention_assessment:",
        "readiness:",
        "role_fact_id:",
        "responsibility_id:",
        "focus_ref:",
        "candidate_intervention:",
        "intervention_id:",
        "每个事实项都有案例内稳定 ID",
        "组合中最多一个候选为 `selected`",
        "多个目标同时存在",
        "不为凑数量制造其他问题",
        "第一件具体事情可以成为候选",
        "最近一次真实工作",
        "不代表对话进度",
        "旧 `enterprise_ai_diagnosis_state_v1` 可以读取并映射",
        "新会话只写 `EnterpriseDiagnosisCaseV2`",
    ],
    "EnterpriseDiagnosisCaseV2",
)

# DiagnosisStateV2 keeps interaction state separate from case readiness and evidence.
require_all(
    evidence,
    [
        "schema: enterprise_ai_diagnosis_state_v2",
        "interaction:",
        "entry:",
        "awaiting_intent | routed | bypassed",
        "contract_presented",
        "case.entry_context.diagnosis_intent",
        "next_move:",
        "unresolved_decisions:",
        "expected_case_delta:",
        "object_refs:",
        "claims:",
        "corrections:",
        "ruled_out:",
        "provider_provenance:",
        "exclusion_id:",
        "result_status:",
        "export_status:",
        "active_exclusion_ids:",
        "ask | checkpoint | result | pause | repair",
        "有且只有一个凭现有经验可回答的动作",
        "非终局回复不能没有去向",
        "reported_fact | observed_fact | experience_judgment | inference | hypothesis",
        "respondent_reported | third_party_reported | ai_observed | source_unavailable",
        "unverified | corroborated | corrected | invalidated",
        "internal_only | consultant_only | owner_visible | client_visible | exportable",
        "缺失 `audiences[]` 时按 `[internal_only]`",
        "被纠正或 ruled out 的内容不得复活",
        "新会话只写 `enterprise_ai_diagnosis_state_v2`",
    ],
    "DiagnosisStateV2",
)

# No contract may reintroduce a singular visibility field. source_visibility is canonical.
require(not re.search(r"(?m)^\s*visibility\s*:", runtime), "singular visibility field is forbidden")

# DiagnosisResultV3 is canonical. ResultV2 remains read-only compatibility only.
require_all(
    report,
    [
        "schema: enterprise_ai_diagnosis_result_v3",
        "result_id:",
        "case_id:",
        "created_at:",
        "status: partial",
        "business_snapshot:",
        "respondent_scope:",
        "agenda:",
        "opportunity_map:",
        "priority_focus:",
        "current_work_system:",
        "ai_assessment:",
        "change_signals:",
        "limitations:",
        "minimum_validation:",
        "audiences:",
        "EvidenceBoundValue",
        "每个顶层结果块必须包含",
        "一个结果单元的有效受众",
        "candidate_change",
        "change_signals",
        "affected_object_refs",
        "validation_id",
        "不使用固定轮数、固定时长、固定字数或固定材料次数",
        "不得为凑数量补写",
        "旧 `enterprise_ai_diagnosis_result_v2` 可以读取并保留来源",
        "新结果只写 `enterprise_ai_diagnosis_result_v3`",
    ],
    "DiagnosisResultV3",
)

# DiagnosisPresenterV2 handles audience projection, next-move continuity and contrast-language admission.
require_all(
    presentation,
    [
        "schema: enterprise_ai_diagnosis_presenter_v2",
        "入口首轮",
        "interaction.entry.status = awaiting_intent",
        "初诊判断与下一步验证",
        "空激活首轮不得直接询问“公司主要做什么、你负责哪些事情”",
        "开头不能使用没有承接对象的“可以”“好的”“没问题”",
        "interaction.entry.status = bypassed",
        "Presenter 把 `DiagnosisResultV3`",
        "mode: turn",
        "state_ref: state-id",
        "result_ref: null",
        "`mode: turn` 必须提供一个 `state_ref`",
        "`mode: result` 必须提供一个 `result_ref`",
        "owner | client | neutral_export",
        "`target_audience: owner`",
        "`target_audience: client`",
        "`target_audience: neutral_export`",
        "缺失 `audiences[]` 时按 `[internal_only]`",
        "未知值、冲突值或无法确认接收对象时默认拒绝呈现",
        "`consultant_only` 与 `internal_only` 不由公共 Presenter 渲染",
        "external_send_authorized",
        "全部父块、该单元和所有 supporting claims",
        "对当前业务影响更大或更紧迫",
        "目标丢线",
        "中立摘要导出与交接路由",
        "不读取或生成 HandoffV2",
        "`neutral_export` 是既有结果的纯投影",
        "正文中每个有业务含义的句子都必须逐句回指一个或多个 `exportable` 单元",
        "不能补充新的判断、候选、因果、建议、风险、AI 状态、介入位置、验证目的或下一阶段安排",
        "以下内容供你自行复制／转发；当前没有执行发送",
        "Presenter 必须服从 `interaction.next_move`",
        "不能出现既没有问题、也没有阶段结果或暂停说明的非终局回复",
        "普通开场不主动加“暂时不用准备数据／不用整理／随便说”等预防性安抚",
        "用户可见禁词",
        "DiagnosisStateV2",
        "DiagnosisResultV3",
        "不是……而是……",
        "不只是……更／还……",
        "与其……不如……",
        "删除反差框架并直接正向陈述结论",
    ],
    "DiagnosisPresenterV2",
)

# HandoffV2 remains the compatibility envelope while carrying ResultV3-compatible fields.
require_all(
    handoff,
    [
        "schema_version: enterprise_ai_diagnosis_handoff_v2",
        "handoff_id:",
        "created_at:",
        "status: draft_for_review | approved_for_export | imported | superseded",
        "source_hash:",
        "respondent_scope:",
        "claims:",
        "diagnosis_result:",
        "result_schema: enterprise_ai_diagnosis_result_v3",
        "business_snapshot",
        "respondent_scope",
        "agenda",
        "opportunity_map[]",
        "priority_focus",
        "current_work_system",
        "ai_assessment",
        "change_signals[]",
        "limitations[]",
        "minimum_validation",
        "scope_level: company | business_unit | team | role | work_system | event | sample | unknown",
        "安全投影与裁剪",
        "选择性深拷贝",
        "source_result_paths",
        "consent:",
        "user_reviewed: false",
        "export_authorized: false",
        "external_send_authorized: false",
        "`source_ref` 只允许内部保存",
        "允许导出永远不自动意味着允许发送",
        "旧接收方可只读这两项",
        "不伪造兼容主判断",
    ],
    "HandoffV2 with ResultV3 compatibility",
)

# JudgmentProviderV1 stays optional, private and subordinate to CaseV2 focus selection.
require_all(
    provider,
    [
        '"schema": "judgment_provider_v1"',
        '"allowed_surface": "public_hosted"',
        '"limit": 3',
        '"business_context"',
        '"business_scenes"',
        '"desired_change"',
        '"current_hypothesis"',
        '"key_variables"',
        '"exclusions"',
        "public_hosted | internal",
        "`0—5`",
        "ok | degraded | unavailable",
        '"confirmation_status": "confirmed"',
        '"lifecycle_status": "current"',
        "current | superseded | retired",
        "同时满足 `confirmed + current`",
        "`source_ref` 只允许在 `allowed_surface: internal`",
        "先形成最小生意图、议题组合和 selected focus",
        "Provider 不负责冷启动、生成候选或选择焦点",
        "零命中时继续公共核心",
        "不得发送客户名",
    ],
    "JudgmentProviderV1",
)
require('"status": "confirmed"' not in provider, "Provider must not collapse confirmation and lifecycle into status")
response_required = provider.split("Response 必填：", 1)[1].split("`status`：", 1)[0]
for field in ["`schema`", "`query_id`", "`provider_revision`", "`status`", "`judgments[]`"]:
    require(field in response_required, f"Provider response required fields missing {field}")
judgment_required = provider.split("每条 judgment 必填：", 1)[1].split("`source_ref`", 1)[0]
for field in ["`confirmation_status`", "`lifecycle_status`"]:
    require(field in judgment_required, f"Provider judgment required fields missing {field}")
require("- `status`\n" not in judgment_required, "judgment required fields must not include a singular status")
require("confirmation_status: confirmed" in methods, "method registry must require Provider confirmation")
require("lifecycle_status: current" in methods, "method registry must require current Provider records")

require_all(
    methods,
    [
        "enterprise_ai_diagnosis_method_v2",
        "公共诊断方法注册表",
        "公开可分发",
        "原始失败、相邻泛化和合法例外评测",
        "public.entry-orientation.v1",
        "public.business-map.v1",
        "public.agenda-map.v1",
        "public.opportunity-portfolio.v1",
        "public.focus-selection.v1",
        "public.work-system-map.v1",
        "public.event-evidence.v2",
        "public.value-loss-map.v1",
        "public.intervention-fit.v1",
        "public.source-contrast.v1",
        "public.next-decision.v1",
        "public.repair-and-resume.v2",
        "不能替用户生成候选或选择焦点",
        "用“是否适合 AI／AI 关键取决于”包装",
    ],
    "method registry",
)

evals = json.loads((SKILL_DIR / "evals" / "evals.json").read_text(encoding="utf-8"))
items = evals.get("evals", [])
require(len(items) == 85, f"expected 85 evals, got {len(items)}")
require([item["id"] for item in items] == list(range(1, 86)), "eval ids must be contiguous 1..85")
for item in items[15:]:
    require(len(item.get("expectations", [])) >= 4, f"eval {item['id']} needs at least four expectations")

by_id = {item["id"]: item for item in items}


def eval_text(eval_id: int) -> str:
    item = by_id[eval_id]
    return "\n".join([item["prompt"], item["expected_output"], *item["expectations"]])


all_eval_text = "\n".join(eval_text(item["id"]) for item in items)

# Evals must not continue rewarding the superseded fixed-turn, L0/L1, one-shot or fixed-size behavior.
obsolete_eval_markers = [
    "后台层级仍记为 L0",
    "后台按 L1",
    "后台完成本次唯一的 L1",
    "后台只做一次 L1",
    "第三个有效回答后直接",
    "累计第3个用户回合",
    "这是本轮第一次也是唯一一次样本增强",
    "不超过500个非空白字符",
    "不超过 500 个字符",
    "不超过900",
    "不超过 900",
    "最多三个语义区块",
    "最多四个语义区块",
]
for marker in obsolete_eval_markers:
    require(marker not in all_eval_text, f"obsolete eval boundary survived: {marker}")

# Original fact-gate failure, adjacent generalization, legal exception.
require("已有诊疗记录和医嘱" in eval_text(33), "eval 33 must preserve the original fact-boundary failure")
require("没有编造任何数字阈值" in eval_text(34), "eval 34 must generalize the numeric fact gate")
require("允许输出一个 AI 工作画面" in eval_text(35), "eval 35 must preserve the evidence-supported exception")

# Dynamic convergence replaces turn and update counters.
require("固定回合数、固定时长或固定题数" in eval_text(27), "eval 27 must reject counter-based stopping")
require("疲劳" in eval_text(27) and "重复" in eval_text(27), "eval 27 must test fatigue and repetition")
require("跨业务单元、跨角色和公司级优先级" in eval_text(28), "eval 28 must test decision-scope escalation")
require("固定材料次数" in eval_text(28), "eval 28 must reject one-shot evidence logic")

# Existing consulting-experience regressions remain required, with the entry workflow replacing direct background collection.
require_all(eval_text(1), ["初诊判断和下一步验证", "整体扫描、具体业务问题和已有 AI 想法", "没有直接询问公司主要做什么"], "eval 1")
require_all(eval_text(2), ["入口选择负担", "默认进入整体扫描", "没有在同一轮继续追问本人职责"], "eval 2")
required_eval_markers = {
    37: ["初诊判断和下一步验证", "整体扫描、具体业务问题和已有 AI 想法", "销售 CTA"],
    38: ["产品名", "候选手段", "业务结果"],
    39: ["杂乱输入", "一个当前最有信息增益的问题", "成熟度评分"],
    40: ["撤回", "纠正", "复活", "不得把交付初诊卡绑定到继续回答"],
    41: ["不同来源", "没有直接判定", "一件事件"],
    42: ["validation_candidate", "角色、触发、现成输入、被改变动作和现有反馈"],
    43: ["non_ai_priority", "当前优先不做", "销售机会"],
    44: ["疲劳", "停止追问", "固定回合数"],
    45: ["暂停", "恢复胶囊", "不输出销售话术"],
    46: ["恢复", "没有重新冷启动", "没有复活"],
    47: ["运营负责人", "可代表范围", "撤回或降级"],
    48: ["单例", "公司级 ROI", "新的授权"],
    49: ["enterprise_ai_diagnosis_handoff_v2", "exportable", "external_send_authorized"],
    50: ["撤销或轮换", "没有自动发送", "没有创建客户档案"],
    51: ["缺失 audiences", "internal_only", "没有输出状态机"],
    52: ["用户明确说出的误解", "两侧", "改变"],
    53: ["删除所有没有来源的反差修辞", "不只是", "表面／本质", "很多人以为／其实"],
    54: ["零命中", "继续公共诊断", "source_ref", "没有补造"],
    55: ["第一条用户可见回复", "没有以‘可以／好的／没问题’", "没有直接询问公司主营业务", "没有预设用户是老板"],
    56: ["利润低，不赚钱", "没有假设项目制", "没有询问哪一单白干"],
    57: ["9.9 元垃圾袋", "整体收入或利润逻辑", "没有直接追问货品、快递、佣金"],
    58: ["不知道，没算过，太细了", "更高层", "没有说‘先停下’"],
    59: ["先别问了", "直接停止追问", "没有继续询问"],
    60: ["不同分类轴", "互斥单选", "允许组合"],
    61: ["工业配件经销", "供应链负责人", "没有重新询问行业"],
    62: ["用户选择了整体扫描", "低价日用品为主", "9.9 元或抖音", "主要客户及购买结果"],
    63: ["经营设计", "利润链路已经清楚", "只核验客户是否继续购买"],
    64: ["负责运营", "实际负责哪些运营工作", "没有直接询问‘运营结果"],
    65: ["商品上架、活动投放和每周数据复盘", "没有重复询问", "日常语言"],
    66: ["降本增效", "具体变化", "没有询问哪件工作太费人"],
    67: ["销售和利润", "客户、商品、成交或后续价值", "没有询问哪里太费人"],
    68: ["每周汇总 30 家店数据", "人力和时间", "没有重新要求"],
    69: ["员工传表格", "数据提交前是否可靠", "没有要求用户回忆最近一次出错"],
    70: ["中性工作事实", "没有判断表格数据不可靠", "没有询问最近一次出错"],
    71: ["库存表少算 100 件", "没有重复询问具体错了什么", "没有把一次库存表事件外推", "没有在工作系统仍待澄清时讨论"],
    72: ["需要提前准备", "允许并明确说明", "没有列出"],
}
for eval_id, markers in required_eval_markers.items():
    require_all(eval_text(eval_id), markers, f"eval {eval_id}")

# CaseV2 structural regressions: broad discovery, portfolio comparison, direct-event exception,
# non-counter continuation, and a complete user-visible ResultV3.
structural_eval_markers = {
    73: ["30多个网店", "实际负责的运营工作", "候选工作系统", "没有宣布数据提交可靠性更值得优先", "没有提前输出 AI 方案"],
    74: ["社区宠物医院", "两个目标", "两个有事实依据的候选工作系统", "焦点选择问题", "没有要求讲近期事件"],
    75: ["收入来自配件销售和履约服务", "有结果的本地事件", "没有为了凑候选数量", "直接整理现有事实", "没有把采购表未更新扩大", "AI 关键取决于"],
    76: ["对话已经进行6轮", "没有因为6轮对话", "固定规则与字段核对", "没有提前推荐"],
    77: ["enterprise_ai_diagnosis_result_v3", "并行目标", "两个候选", "最小验证", "会改变当前判断的信号", "没有承诺 ROI"],
}
for eval_id, markers in structural_eval_markers.items():
    require_all(eval_text(eval_id), markers, f"eval {eval_id}")

# Ordinary readable exports stay in Presenter; explicit consultant/system transfer is the Handoff exception.
require_all(
    eval_text(78),
    ["中性摘要", "neutral_export", "没有生成 enterprise_ai_diagnosis_handoff_v2", "claims、source_hash"],
    "eval 78",
)
require_all(
    eval_text(79),
    ["复制给合伙人", "neutral_export", "HandoffV2、claims", "当前没有执行发送"],
    "eval 79",
)

# Entry workflow regressions: route selection, three branches, direct-context bypass and user-visible journey.
entry_eval_markers = {
    80: ["整体扫描入口", "产品／服务和主要客户", "没有同时询问本人身份"],
    81: ["具体业务问题", "三家餐饮门店", "没有再次展示三种入口"],
    82: ["已有 AI 想法", "老板经营驾驶舱", "没有再次展示整体扫描"],
    83: ["旁路入口介绍", "连锁洗衣店", "收衣检查、洗后质检、交付前复检", "lang-enterprise-ai-diagnosis、文件名或内部入口路由", "没有展示整体扫描"],
    84: ["最后能给我什么", "初诊结果内容", "最多只有一个入口选择动作"],
    85: ["接下来大概会怎么聊", "用户可见的交流过程", "没有公开案例对象"],
}
for eval_id, markers in entry_eval_markers.items():
    require_all(eval_text(eval_id), markers, f"eval {eval_id}")

for obsolete_eval_phrase in [
    "首个用户动作是简单介绍公司业务与本人负责范围",
    "首轮自然询问公司主营业务与回答者负责范围",
    "只提出一个低负担的自我与公司介绍动作",
]:
    require(obsolete_eval_phrase not in all_eval_text, f"obsolete blank-start eval survived: {obsolete_eval_phrase}")
require_all(
    eval_text(49),
    ["给外部顾问审核", "enterprise_ai_diagnosis_handoff_v2", "draft_for_review"],
    "eval 49 handoff exception",
)

pilot = (REPO_ROOT / "docs" / "enterprise-ai-diagnosis-pilot-template.md").read_text(encoding="utf-8")
require_all(
    pilot,
    [
        "只填写真实试诊结果",
        "不得用模型模拟",
        "恰好 3 位",
        "三人的业务类型必须不同",
        "六项逐例硬门槛",
        "3 人 × 6 项全部通过",
        "追问改判率 **≥ 90%**",
        "重复问题率 **< 10%**",
        "三人平均 **≥ 4.0/5**",
        "三人平均 **≤ 2.5/5**",
        "至少 **2/3** 可以独立复述",
        "结果：____",
    ],
    "three-owner pilot acceptance gate",
)

readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
require("狼格拉底企业 AI 提效诊断" in readme, "public product name must use 狼格拉底")
require("狼哥企业 AI 提效诊断" not in readme, "public product name must not use the internal nickname")
require("诊断不是给答案" not in readme, "README must not retain an unsupported contrast slogan")

print(
    f"OK: {CHECK_COUNT} checks passed across 10 runtime references, "
    "85 eval scenarios, and the three-owner pilot gate"
)
