# 企业 AI 诊断交接契约（HandoffV2）

## 定位与生成门槛

Handoff 是把用户审核过的诊断结论交给另一位咨询师、正式诊断流程或其他系统的**中立数据包**。它不是销售转化页，也不意味着已经建档、预约、发送、写入系统或启动项目。

只有用户明确要求生成或更新交接草稿时才生成。默认状态为 `draft_for_review`；用户必须先审核内容与敏感范围，再分别决定是否允许导出和是否允许外发。三个授权彼此独立。

## 稳定结构

```yaml
schema_version: enterprise_ai_diagnosis_handoff_v2
handoff_id: stable-handoff-id
created_at: 2026-08-02T10:00:00+08:00
status: draft_for_review | approved_for_export | imported | superseded
source_hash: sha256:...
source_session_ref: optional-private-session-ref
respondent_scope:
  role: 回答者角色；未知则为 unknown
  can_speak_for: 本轮可代表的范围
  cannot_confirm: 需要其他角色、材料或系统核验的范围
claims:
  - claim_id: claim-001
    text: 声明的可读摘要
    claim_kind: reported_fact | observed_fact | experience_judgment | inference | hypothesis
    source_visibility: respondent_reported | third_party_reported | ai_observed | source_unavailable
    verification_status: unverified | corroborated | corrected | invalidated
    scope_level: company | business_unit | team | role | work_system | event | sample | unknown
    scope_ref: optional-scope-reference
    object_refs: []
    sensitivity: public | internal | confidential | restricted
    audiences:
      - exportable
      - owner_visible
    source_ref: optional-source-reference
diagnosis_result:
  result_schema: enterprise_ai_diagnosis_result_v3
  ai_status: validation_candidate | foundation_first | non_ai_priority | insufficient_evidence
  primary_judgment:
    text: 当前判断
    source_result_paths:
      - priority_focus.statement
    supporting_claim_ids:
      - claim-001

  # 以下均为可选 ResultV3 扩展；保留 report-contract.md 的原始对象形状
  business_snapshot:
    summary: 对公司如何服务客户和形成价值的有来源摘要
    supporting_claim_ids: []
    object_refs: [business_map]
    audiences: [exportable, owner_visible]

  respondent_scope:
    role_label:
      text: unknown
      supporting_claim_ids: []
      object_refs: [respondent.role_label]
      audiences: [exportable, owner_visible]
    actual_responsibilities: []
    can_speak_for: []
    cannot_confirm: []
    supporting_claim_ids: []
    object_refs: [respondent]
    audiences: [exportable, owner_visible]

  agenda:
    user_wording: []
    desired_outcomes:
      - outcome_id: G-001
        statement: null
        observable_change: null
        priority: unresolved
        scope_ref: null
        supporting_claim_ids: []
        object_refs: [agenda.desired_outcomes.G-001]
        audiences: [exportable, owner_visible]
    unresolved_priorities: []
    supporting_claim_ids: []
    object_refs: [agenda]
    audiences: [exportable, owner_visible]

  opportunity_map:
    - opportunity_id: O-001
      label: null
      business_contribution: null
      outcome_refs: []
      known_signals: []
      current_status: candidate
      supporting_claim_ids: []
      object_refs: [opportunity_portfolio.O-001]
      audiences: [exportable, owner_visible]

  priority_focus:
    opportunity_id: null
    statement: null
    selection_status: unselected
    considered_opportunity_refs: []
    relevant_outcome_refs: []
    selection_basis: []
    unresolved_comparison:
      affects_focus: true
      dimensions: []
      related_opportunity_refs: []
      related_outcome_refs: []
      statement: null
      supporting_claim_ids: []
      object_refs: [selected_focus]
      audiences: [exportable, owner_visible]
    supporting_claim_ids: []
    object_refs: [selected_focus]
    audiences: [exportable, owner_visible]

  current_work_system:
    summary: null
    confirmed_elements: []
    open_elements: []
    supporting_claim_ids: []
    object_refs: [current_work_system]
    audiences: [exportable, owner_visible]

  ai_assessment:
    ai_status: insufficient_evidence
    mechanism: unknown
    candidate_change: null
    conditions: []
    supporting_claim_ids: []
    object_refs: [intervention_assessment]
    audiences: [exportable, owner_visible]

  change_signals: []
  limitations: []

  minimum_validation:
    validation_id: MV-001
    decision_question: null
    evidence_unit:
      kind: natural_event
      description: null
    user_action: null
    evaluation_rule: null
    update_scope:
      statement: null
      object_refs: []
    stop_conditions: []
    supporting_claim_ids: []
    object_refs: [intervention_assessment]
    audiences: [exportable, owner_visible]

  audiences: [exportable, owner_visible]
consent:
  user_reviewed: false
  export_authorized: false
  external_send_authorized: false
```

必填字段是：

- `schema_version`
- `handoff_id`
- `created_at`
- `status`
- `source_hash`
- `respondent_scope`
- `claims[]`
- `diagnosis_result`
- `consent`

`source_session_ref` 可选，且不得放入可公开导出的材料。`source_hash` 用于判断交接内容所依据的源状态是否发生变化，不能反推出原始敏感内容。

每条声明必填：`claim_id`、`text`、`claim_kind`、`source_visibility`、`verification_status`、`scope_level`、`sensitivity`、`audiences[]`。`scope_ref`、`object_refs[]`、`source_ref` 可选；`object_refs[]` 保留 ResultV3 子项与声明的对象关系，`source_ref` 只允许内部保存，不进入公开呈现或外部交接。

`diagnosis_result.primary_judgment.source_result_paths[]` 和 `supporting_claim_ids[]` 是新产物的必填字段；旧接收方可忽略前者。路径必须指向本包实际携带的 ResultV3 单元，声明 ID 必须链接本包 `claims[]` 中仍有效的声明。不能只传结论，不传能审查结论边界的证据关系。

## ResultV3 兼容投影

公开核心使用 `enterprise_ai_diagnosis_result_v3`。第一阶段继续输出 HandoffV2；`diagnosis_result.ai_status + primary_judgment` 保持兼容必填，旧接收方可只读这两项。新接收方可读取 `business_snapshot`、`respondent_scope`、`agenda`、`opportunity_map[]`、`priority_focus`、`current_work_system`、`ai_assessment`、`change_signals[]`、`limitations[]`、`minimum_validation` 和 `audiences[]`。

这些扩展是 ResultV3 对象的选择性深拷贝，不是同名摘要字段：

- 对象、列表项和 `EvidenceBoundValue` / `EvidenceBoundItem` 必须保留 `report-contract.md` 的原始键、类型与嵌套形状；不得把它们压成裸字符串；
- `ai_assessment.ai_status` → `diagnosis_result.ai_status`，两者同时存在时必须一致；
- 顶层 `respondent_scope` 是旧接收方的窄投影，分别来自 ResultV3 的 `role_label`、`can_speak_for[]` 和 `cannot_confirm[]`；不得补全未出现的职责；
- 内部候选评分、生成逻辑、淘汰理由、readiness、next move、Provider 命中和未列入 ResultV3 canonical schema 的键全部删除。

### 安全投影与裁剪

1. 先确定具体接收者与用途，例如指定咨询师、正式诊断项目或接收系统；接收者和用途未知时只保留不可外发草稿。
2. 从叶子单元开始检查。实际权限是 Result 顶层、父块、当前单元和其全部有效 supporting claims 的 `audiences[]` 交集。可导出单元必须在每一层保留 `exportable`；空引用单元、未知受众或交集不足时直接裁剪。接收者许可由 consent、sensitivity 和最小必要范围另行判断，不能用 `consultant_only`、`owner_visible` 或 `client_visible` 代替用户对本次接收者的授权。
3. 先过滤 claims，再按稳定列表项裁剪 ResultV3。某单元任一 supporting claim 未进包、已被 `corrected | invalidated`，或其 `object_refs[]` 无法定位有效案例对象时，删除整个单元；不得只删 claim ID 却保留原结论。
4. 数组可逐项过滤；摘要、焦点、AI 判断和验证动作在失去任一实质支撑后整块删除。父块的 claims、object refs 和 audiences 按保留子项重算；不得用父块宽权限“洗白”子项。
5. 裁剪后再检查引用完整性：`priority_focus.opportunity_id`、各类 opportunity / outcome / affected object refs 必须仍能回到包内对象；不可达则删除引用该对象的整个单元，不重编 ID、不改写为另一个判断。
6. 最终 `claims[]` 只保留受访者范围、`primary_judgment` 和已投影 ResultV3 单元真正引用的最小集合。`source_ref`、`source_session_ref`、原始对话和未评审附件永不进入可导出版本。

投影或裁剪不得提升证据强度、扩大范围、新选焦点或新写咨询判断。若裁剪后无法同时产生有来源的 `ai_status` 和 `primary_judgment`，不得输出不完整的 approved Handoff；保留为不可导出草稿并说明缺口。

### `primary_judgment` 的来源

- `selection_status = provisional | confirmed` 且焦点单元通过投影时：`text` 来自 `priority_focus.statement`，`source_result_paths[]` 至少包含 `priority_focus.statement`，`supporting_claim_ids[]` 是焦点块与已使用 selection basis 的有效支撑并集。
- `selection_status = unselected` 时：`text` 只能陈述本包仍保留的候选和尚不能排序的范围；`source_result_paths[]` 必须包含 `priority_focus.unresolved_comparison` 及实际使用的 `opportunity_map[opportunity_id]`，`supporting_claim_ids[]` 取 unresolved comparison 与这些候选的有效支撑并集。不得从一个候选的信号推导其相对优先级。
- 以上来源单元或支撑为空、被裁剪或不允许导出时，不伪造兼容主判断，本包不得进入 `approved_for_export`。

## 受众与敏感信息

`audiences[]` 只能使用 `internal_only | consultant_only | owner_visible | client_visible | exportable`。缺失时默认 `[internal_only]`；`internal_only` 不得与其他值共存。未知受众默认拒绝呈现。`exportable` 是内容传输资格；具体接收者仍由本次 consent 与敏感范围授权决定。

`exportable` 只是内容级资格，不能替代 `consent.export_authorized`。外发还必须额外满足 `consent.external_send_authorized = true`；允许导出永远不自动意味着允许发送。

`sensitivity = confidential | restricted` 的内容即使带有 `exportable`，也必须再次核对用户批准的接收对象和最小必要范围。Token、密钥、身份证件、客户个人信息和原始生产数据不得进入交接包；已暴露凭证只提示撤销或轮换，不复述原值。

## 状态与授权

- `draft_for_review`：默认草稿，三个 consent 字段默认均为 `false`；
- `approved_for_export`：用户已审核且明确允许生成可复制／可下载版本，但不代表允许发送；
- `imported`：经授权的接收系统已确认导入；不得由生成方预先声称；
- `superseded`：源诊断或用户校正发生变化，本包不再是当前版本。

只有真实完成对应动作的执行环境才能更新为 `imported`。当前环境没有外部写入能力时，只能给出草稿或经授权的可复制导出，并明确“尚未发送”。

## 接收方规则

接收方把 Handoff 视为有来源边界的输入，不是客户已确认方案：

- `reported_fact` 保留回答者或第三方转述身份；
- `observed_fact` 只表示 AI 实际看到材料中的现象，不表示材料已验真、具有代表性或建立因果；
- `experience_judgment` 是咨询经验，不是客户事实；
- `inference` 与 `hypothesis` 必须保留改判空间；
- `corrected`、`invalidated` 的声明不得继续支撑主判断；
- `company`、`business_unit` 等范围不能由单个事件或样本自动获得；
- 跨角色、数据、权限、ROI、架构和实施承诺必须重新取得正式授权。

## V1 只读兼容

旧 `enterprise_ai_pre_diagnosis_v1` 可以读取，但不得继续作为新输出格式。迁移时逐项保留来源和范围：

- `user_statement` → `claim_kind: reported_fact`；
- `sample_reported` → `reported_fact`，来源为 `respondent_reported` 或 `third_party_reported`；
- `sample_observed` → 仅在 AI 实际读取材料时映射为 `observed_fact` 与 `ai_observed`；
- `hypothesis` → `claim_kind: hypothesis`；
- `ruled_out` → `verification_status: invalidated`；
- `gap` → 不伪造为事实，保留为限制或待核验问题；
- `sample_supported` → 只能映射为 `source_visibility: source_unavailable` 与 `verification_status: unverified`，绝不能映射为 `observed_fact`。

迁移后所有缺失的 `audiences[]` 按 `[internal_only]`，所有 consent 字段按 `false`。新产物一律写 `enterprise_ai_diagnosis_handoff_v2`。
