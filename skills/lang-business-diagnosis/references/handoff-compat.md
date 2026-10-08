# 交接兼容说明（HandoffV2）

本文件把既有交接契约的核心要点复制进本 Skill，保证本 Skill 生成的交接草稿与既有接收方兼容。标注：**兼容 lang-enterprise-ai-diagnosis HandoffV2**。本文件自包含，不引用仓外路径；本 Skill 不迁移内部交付流程，只保证输出格式兼容。

## 定位与生成门槛

交接是把用户审核过的初诊结论交给另一位咨询师、正式诊断流程或其他系统的**中立数据包**。它不是销售转化页，也不意味着已建档、预约、发送、写入系统或启动项目。

只有用户明确要求生成或更新交接草稿时才生成。默认状态为 `draft_for_review`；用户必须先审核内容与敏感范围，再分别决定是否允许导出和是否允许外发。三个授权彼此独立。

## 稳定结构

```yaml
schema_version: enterprise_ai_diagnosis_handoff_v2
handoff_id: stable-handoff-id
created_at: 2026-08-03T10:00:00+08:00
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
  business_snapshot: {}
  respondent_scope: {}
  agenda: {}
  opportunity_map: []
  priority_focus: {}
  current_work_system: {}
  ai_assessment: {}
  change_signals: []
  limitations: []
  minimum_validation: {}
  audiences: [exportable, owner_visible]
consent:
  user_reviewed: false
  export_authorized: false
  external_send_authorized: false
```

必填字段：

- `schema_version`
- `handoff_id`
- `created_at`
- `status`
- `source_hash`
- `respondent_scope`
- `claims[]`
- `diagnosis_result`
- `consent`

`source_session_ref` 可选且不得放入可公开导出的材料。`source_hash` 用于判断交接内容所依据的源状态是否变化，不能反推原始敏感内容。

每条声明必填：`claim_id`、`text`、`claim_kind`、`source_visibility`、`verification_status`、`scope_level`、`sensitivity`、`audiences[]`。`scope_ref`、`object_refs[]`、`source_ref` 可选；`source_ref` 只允许内部保存，不进入公开呈现或外部交接。

`diagnosis_result.primary_judgment.source_result_paths[]` 和 `supporting_claim_ids[]` 是新产物的必填字段；旧接收方可忽略前者。不能只传结论，不传能审查结论边界的证据关系。

## 兼容投影与裁剪

1. 先确定具体接收者与用途；接收者和用途未知时只保留不可外发草稿。
2. 从叶子单元开始检查。可导出单元必须在每一层保留 `exportable`；空引用单元、未知受众或交集不足时直接裁剪。
3. 先过滤 `claims[]`，再按稳定列表项裁剪诊断结果。某单元任一支撑声明未进包、已被 `corrected | invalidated`，或其对象引用无法定位有效对象时，删除整个单元。
4. 数组可逐项过滤；摘要、焦点、AI 判断和验证动作在失去任一实质支撑后整块删除。
5. 裁剪后再检查引用完整性：焦点、机会、结果和受影响对象的引用必须仍能回到包内对象；不可达则删除引用该对象的整个单元。
6. 最终 `claims[]` 只保留受访者范围、主判断和已投影单元真正引用的最小集合。

投影或裁剪不得提升证据强度、扩大范围、新选焦点或新写咨询判断。若裁剪后无法同时产生有来源的 `ai_status` 和 `primary_judgment`，不得输出不完整的已批准交接；保留为不可导出草稿并说明缺口。

### 主判断的来源

- 焦点 `provisional | confirmed` 且焦点单元通过投影时：`text` 来自焦点陈述，`source_result_paths[]` 至少包含焦点陈述路径，`supporting_claim_ids[]` 是焦点块与已使用选择依据的有效支撑并集。
- 焦点未选择时：`text` 只能陈述仍保留的候选和尚不能排序的范围；不得从一个候选的信号推导其相对优先级。

## 受众与敏感信息

`audiences[]` 只能使用 `internal_only | consultant_only | owner_visible | client_visible | exportable`。缺失时默认 `[internal_only]`；`internal_only` 不得与其他值共存。未知受众默认拒绝呈现。`exportable` 是内容传输资格；具体接收者仍由本次同意与敏感范围授权决定。

`exportable` 只是内容级资格，不能替代同意字段中的导出授权。外发还必须额外满足 `external_send_authorized = true`；允许导出永远不自动意味着允许发送。

`confidential | restricted` 的内容即使带有 `exportable`，也必须再次核对用户批准的接收对象和最小必要范围。Token、密钥、身份证件、客户个人信息和原始生产数据不得进入交接包；已暴露凭证只提示撤销或轮换，不复述原值。

## 状态与授权

- `draft_for_review`：默认草稿，三个同意字段默认均为 `false`；
- `approved_for_export`：用户已审核且明确允许生成可复制／可下载版本，但不代表允许发送；
- `imported`：经授权的接收系统已确认导入；不得由生成方预先声称；
- `superseded`：源诊断或用户校正发生变化，本包不再是当前版本。

当前环境没有外部写入能力时，只能给出草稿或经授权的可复制导出，并明确“尚未发送”。

## 接收方规则

接收方把交接视为有来源边界的输入，不是客户已确认方案：

- `reported_fact` 保留回答者或第三方转述身份；
- `observed_fact` 只表示 AI 实际看到材料中的现象，不表示材料已验真、具有代表性或建立因果；
- `experience_judgment` 是咨询经验，不是客户事实；
- `inference` 与 `hypothesis` 必须保留改判空间；
- `corrected`、`invalidated` 的声明不得继续支撑主判断；
- 公司、业务单元等范围不能由单个事件或样本自动获得；
- 跨角色、数据、权限、ROI、架构和实施承诺必须重新取得正式授权。

## 旧版只读兼容

旧版数据包可以读取，但不得继续作为新输出格式。迁移时逐项保留来源和范围：

- 用户原话 → `reported_fact`；
- 转述样本 → `reported_fact`，来源为回答者转述或第三方转述；
- 观察样本 → 仅在 AI 实际读取材料时映射为 `observed_fact`；
- 假设 → `hypothesis`；
- 已排除 → `invalidated`；
- 缺口 → 不伪造为事实，保留为限制或待核验问题；
- 样本支撑 → 只能映射为来源不可用与未核验，绝不能映射为观察事实。

迁移后所有缺失的受众标记按 `[internal_only]`，所有同意字段按 `false`。新产物一律写 `enterprise_ai_diagnosis_handoff_v2`。
