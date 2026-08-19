# DiagnosisStateV2｜证据与交互状态

## 目的

`DiagnosisStateV2` 负责保存案例、证据、纠正、用户当前交互状态和下一动作。案例成熟度由 `EnterpriseDiagnosisCaseV2.readiness` 表达；交互状态只处理正常交流、修复、疲劳、暂停和安全边界。两者分开，避免系统为了推进一个对话阶段而提问。

状态属于后台。任何用户可见内容都必须经过 Presenter 的受众与泄漏检查。

## Canonical schema

```yaml
schema: enterprise_ai_diagnosis_state_v2
session_id: opaque-session-id

interaction:
  status: engaged
  entry:
    status: awaiting_intent
    contract_presented: false
    intent_ref: case.entry_context
  next_move:
    kind: ask
    decision_id: D-001
    expected_case_delta: null
    terminal_reason: null
  energy: engaged

case:
  schema: enterprise_ai_diagnosis_case_v2
  case_id: opaque-case-id
  # 完整结构见 case-model.md

unresolved_decisions:
  - decision_id: D-001
    question: null
    affects: []
    prerequisites: []
    premise_claim_ids: []
    expected_branches: []
    answerability: high
    burden: low
    priority: 1

claims:
  - claim_id: C-001
    text: null
    claim_kind: reported_fact
    source_visibility: respondent_reported
    verification_status: unverified
    scope_level: unknown
    scope_ref: null
    object_refs: []
    sensitivity: confidential
    audiences: [owner_visible]
    source_ref: current_conversation
    derived_from: []
    provider_provenance: null

corrections: []
ruled_out:
  - exclusion_id: X-001
    target_kind: claim
    target_ref: C-003
    reason: null
    supporting_claim_ids: []
    status: active
    status_claim_ids: []
    replacement_ref: null
last_checkpoint: null
result_status:
  status: none
  result_schema: null
  result_ref: null
  source_case_id: opaque-case-id
export_status:
  status: not_requested
  artifact_kind: null
  artifact_ref: null
  source_result_ref: null
  export_authorized: false
  external_send_authorized: false

analytics:
  user_messages: 0
  meaningful_case_updates: 0
  correction_events: 0
  fatigue_signals: []
```

## 交互状态与下一动作

`interaction.status` 使用：

```text
engaged | repair | fatigue | paused | safety
```

`interaction.energy` 使用：

```text
engaged | uncertain | fatigued | paused
```

`interaction.entry.status` 使用：

```text
awaiting_intent | routed | bypassed
```

- `awaiting_intent`：只有空激活或仍然模糊的请求使用。第一条回复先交付克制的产品结果预期，再用一个问题识别整体扫描、具体业务问题或已有 AI 想法；
- `routed`：用户已经明确选择入口。后续直接进入对应问题，不重复产品介绍和入口选项；
- `bypassed`：用户已经提供实际问题、AI 想法、业务上下文、恢复信息或结果请求。系统直接使用这些内容，不要求补做入口选择。

`contract_presented` 只记录是否已经向当前用户说明过能够带走什么。它不允许模型播报内部流程，也不能成为反复介绍产品的理由。空激活首轮呈现后设为 true；`routed | bypassed`、恢复会话和后续普通回合不得再次展示入口介绍。

空激活时，`next_move.kind = ask` 的 `expected_case_delta` 指向 `case.entry_context.diagnosis_intent`。用户选择入口后，下一问才开始更新生意、职责、具体问题或 AI 想法。用户已经带来实质上下文时直接把 entry 标为 `bypassed`，下一问更新实际案例对象。

`next_move.kind` 使用：

```text
ask | checkpoint | result | pause | repair
```

每次回复前先写 `next_move`：

- `ask`：用户可见回复必须有且只有一个凭现有经验可回答的动作；
- `checkpoint`：交付阶段理解，可以有一个明确的继续入口，不能在正文中暗藏多项作业；
- `result`：先交付结果，不再追加问题；
- `pause`：保存恢复胶囊并停止；
- `repair`：撤回具体误解并更新案例；仍需继续时最多一个新问题。

非终局回复不能没有去向。若 `kind = ask` 却没有一个可回答的问题，改为 checkpoint 或 result；若已经决定结束，必须明确交付阶段结果，不能静默停止。

`unresolved_decisions[]` 保存问题依赖关系。下一问必须能够说明：

1. 它会改变 case 中哪个对象、关系或 AI 判断；
2. 问题中的事实前提来自哪些有效 claim；
3. 不同答案会导向什么不同动作；
4. 用户现在能否顺口回答；
5. 是否存在信息增益相近而负担更低的问法。

两种答案最终导向同一动作、前提无来源或需要新建资料时，该问题不能成为下一问。

## Evidence claim

`claim_kind`：

```text
reported_fact | observed_fact | experience_judgment | inference | hypothesis
```

`source_visibility`：

```text
respondent_reported | third_party_reported | ai_observed | source_unavailable
```

`verification_status`：

```text
unverified | corroborated | corrected | invalidated
```

`scope_level`：

```text
company | business_unit | team | role | work_system | event | sample | unknown
```

`sensitivity`：

```text
public | internal | confidential | restricted
```

`audiences[]`：

```text
internal_only | consultant_only | owner_visible | client_visible | exportable
```

`object_refs[]` 把声明挂到案例对象或关系，例如：

```text
respondent.actual_responsibilities.RSP-001
business_map.customer_outcomes.CO-001
agenda.desired_outcomes.G-001
opportunity_portfolio.O-002.known_signals.SG-003
current_work_system.work_nodes.N-003
intervention_assessment.candidate_intervention.AI-001
```

对象引用必须落到稳定对象 ID，例如 `respondent.actual_responsibilities.RSP-001`、`business_map.customer_outcomes.CO-001` 和 `opportunity_portfolio.O-002.known_signals.SG-003`。平铺 claims 负责来源记录，案例对象同时把该 claim 写入自身 `claim_ids[]`；两侧必须一致，避免系统知道很多零散事实，却不知道它们怎样组成生意、候选和工作系统。

### 合法来源组合

| 场景 | claim_kind | source_visibility | 默认 verification_status |
|---|---|---|---|
| 用户讲公司情况 | `reported_fact` | `respondent_reported` | `unverified` |
| 用户转述其他角色 | `reported_fact` | `third_party_reported` | `unverified` |
| AI 实际读取获准材料 | `observed_fact` | `ai_observed` | `unverified` |
| 公共方法或 Provider 判断 | `experience_judgment` | `source_unavailable` | `unverified` |
| 由有效声明推导 | `inference` | `source_unavailable` | `unverified` |
| 等待新信息支持或推翻 | `hypothesis` | `source_unavailable` | `unverified` |

以下组合非法：

- `reported_fact + ai_observed`；
- `observed_fact` 没有 AI 实际读取材料；
- `experience_judgment` 被写成客户事实；
- `corroborated` 没有第二来源与支持范围；
- company 范围只来自一个角色、事件或样本；
- audiences 缺失却进入用户输出。

缺失 `audiences[]` 时按 `[internal_only]`；`internal_only` 不得与其他值共存。

### Provider provenance

只有 `JudgmentProviderV1` 返回的 `experience_judgment` 才能写入 `provider_provenance`：

```yaml
provider_provenance:
  provider_schema: judgment_provider_v1
  query_id: opaque-query-id
  judgment_id: stable-judgment-id
  version: v1
  content_hash: sha256:...
  provider_revision: revision-or-hash
  confirmation_status: confirmed
  lifecycle_status: current
```

该对象用于重放、过期检查和回滚，只能保存在内部状态。带 `provider_provenance` 的 claim 必须是 `source_visibility: source_unavailable`，audiences 只能为 `[consultant_only]` 或 `[internal_only]`；Presenter、普通结果和公开导出一律删除该对象。公共方法产生的 `experience_judgment` 保持 `provider_provenance: null`。缺少 ID、version、hash 或 revision 的 Provider 返回项不得进入判断。

## 证据更新

每次收到新信息：

1. 保存原话、来源、范围、敏感度和 audiences；
2. 创建或更新 claim，不覆盖历史；
3. 用 `object_refs[]` 更新受影响的案例对象；
4. 标记新信息支持、削弱、纠正或推翻什么；
5. 重新计算受影响的 readiness、候选优先级和 AI 判断；
6. 选择下一项 unresolved decision 或进入交付。

更晚、更具体不自动拥有更高权威。实际材料通常更能说明该材料范围内发生了什么，老板认可不能替代一线证据，局部样本也不能替代公司级判断。

## 纠正与排除

`corrections[]` 使用：

```yaml
- correction_id: R-001
  correction_type: wording
  target_claim_ids: [C-003]
  user_correction: null
  effect: null
  replacement_claim_ids: []
```

`correction_type`：

```text
wording | fact | frame | goal | boundary
```

`ruled_out[]` 保存明确排除，不能只删除原文本：

```text
target_kind: claim | case_object | opportunity | hypothesis | question
status: active | lifted | superseded
```

`active` 排除项不得支撑候选、焦点、问题和结果。只有新的同层证据或用户明确重新确认，才能把它改为 `lifted`，并写入 `status_claim_ids[]`；被新排除记录替代时使用 `superseded + replacement_ref`。稳定 `exclusion_id` 不因状态变化而重用。

处理顺序：

1. 明确撤回哪项原表达；
2. 将目标 claim 标为 `corrected` 或 `invalidated`；
3. 更新关联案例对象、候选和判断；
4. 写入替代 claim 或新的目标／边界；
5. 说明当前理解发生了什么变化；
6. 仍有改判问题时最多问一个。

没有新同层证据时，被纠正或 ruled out 的内容不得复活。连续两次纠正同一框架时进入 `repair`，清除未确认推断，只用有效 claim 重建案例。

## 结果与导出状态

`result_status.status` 使用：

```text
none | partial | final | paused | superseded
```

`none` 时 `result_schema` 与 `result_ref` 必须为 null；其余状态必须引用真实存在的结果。新信息或纠正使结果失效时先标为 `superseded`，不能继续把旧结果描述为当前结论。

`export_status.status` 使用：

```text
not_requested | draft_for_review | approved_for_export | exported | superseded
```

`artifact_kind` 使用 `neutral_result | handoff | null`。生成草稿不等于获准导出，获准导出也不等于获准外发；只有执行环境真实完成导出后才可写 `exported`。源结果被替代时，相关导出状态同步变为 `superseded`。`external_send_authorized` 只记录独立授权，不扩大内容受众。

## 疲劳、暂停与恢复

以下信号触发 fatigue：用户明确说问题太多、重复、先给结论；回答持续缩短且拒绝继续；同一问题换词重复；修复后用户仍明确不愿继续。

触发后停止追加问题，选择 checkpoint、result 或 pause。不能说“最后再问一个”，也不能把疲劳解释成企业能力问题。

用户说“太细了”首先属于 boundary correction，作用是提高问题粒度；只有同时表达停止、暂停或先看结论时才结束。

暂停时 `last_checkpoint` 至少保存：

```yaml
case_summary: null
confirmed_claim_ids: []
active_exclusion_ids: []
selected_focus: null
open_decision_id: null
```

恢复时使用胶囊继续，不重问公司背景和已确认职责。

## 终局事实闸门

结果前逐项检查：

- 用户可见的角色、客户、产品、数字、事件、动作和因果词都能回到有效 claim；
- claim 的 scope 覆盖当前措辞；
- opportunity、selected focus 和 AI 候选的每项事实都有 claim_id；
- 共现没有升级成因果；
- experience judgment 没有写成客户事实；
- corrected／invalidated claim 没有继续支撑结果；
- sensitivity 与 audiences 允许当前受众查看。

检查失败时缩小范围、降低判断强度或输出 partial 结果。不能靠补字段让报告显得完整。

## V1 兼容

旧 `DiagnosisStateV1` 只读映射见 [case-model.md](case-model.md)。旧 `dialogue_state` 不映射成新的案例阶段；只根据用户当前意愿映射 interaction status。旧 `open_decision_question` 可以成为 unresolved decision 候选，但必须重新检查前提、分支、可回答性与负担。旧排除项迁移为带稳定 ID 的 `ruled_out[]`；没有真实 Provider 版本信息时保持 `provider_provenance: null`，不得补造。旧状态没有结果或导出记录时分别写 `none` 与 `not_requested`。

新会话只写 `enterprise_ai_diagnosis_state_v2`。
