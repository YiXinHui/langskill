# DiagnosisResultV3｜企业 AI 初诊结果契约

## 定位

`DiagnosisResultV3` 是当前证据边界内形成的可审查初诊结果。它保存生意理解、议题组合、候选工作系统、优先焦点、AI 适配判断和最小验证。它不等同于咨询报告、实施方案、ROI 或销售线索。

结果由案例成熟度和用户当前决定触发，不使用固定轮数、固定时长、固定字数或固定材料次数。用户要求先看结论、继续提问已无增量、出现疲劳，或下一步需要正式项目权限时，可以输出 partial、final 或 paused 结果。

## Canonical schema

```yaml
schema: enterprise_ai_diagnosis_result_v3
result_id: stable-result-id
case_id: opaque-case-id
created_at: 2026-08-02T10:00:00+08:00
status: partial
audiences: [owner_visible]

business_snapshot:
  summary: 对公司如何服务客户和形成价值的有来源摘要
  supporting_claim_ids: []
  object_refs: [business_map]
  audiences: [owner_visible]

respondent_scope:
  role_label:
    text: unknown
    supporting_claim_ids: []
    object_refs: [respondent.role_label]
    audiences: [owner_visible]
  actual_responsibilities:
    - item_id: RS-001
      text: null
      supporting_claim_ids: []
      object_refs: [respondent.actual_responsibilities]
      audiences: [owner_visible]
  can_speak_for: []       # 每项使用 EvidenceBoundItem
  cannot_confirm: []      # 每项使用 EvidenceBoundItem
  supporting_claim_ids: []
  object_refs: [respondent]
  audiences: [owner_visible]

agenda:
  user_wording: []        # 每项使用 EvidenceBoundItem
  desired_outcomes:
    - outcome_id: G-001
      statement: null
      observable_change: null
      priority: unresolved
      scope_ref: null
      supporting_claim_ids: []
      object_refs: [agenda.desired_outcomes.G-001]
      audiences: [owner_visible]
  unresolved_priorities:
    - item_id: UP-001
      statement: null
      related_outcome_refs: []
      affects_focus: true
      supporting_claim_ids: []
      object_refs: [agenda]
      audiences: [owner_visible]
  supporting_claim_ids: []
  object_refs: [agenda]
  audiences: [owner_visible]

opportunity_map:
  - opportunity_id: O-001
    label: null
    business_contribution: null
    outcome_refs: []
    known_signals: []     # 每项使用 EvidenceBoundItem
    current_status: candidate
    supporting_claim_ids: []
    object_refs: [opportunity_portfolio.O-001]
    audiences: [owner_visible]

priority_focus:
  opportunity_id: null
  statement: null
  selection_status: unselected
  considered_opportunity_refs: []
  relevant_outcome_refs: []
  selection_basis:
    - basis_id: PB-001
      dimension: business_impact
      statement: null
      supporting_claim_ids: []
      object_refs: [selected_focus]
      audiences: [owner_visible]
  unresolved_comparison:
    affects_focus: true
    dimensions: [business_impact, urgency]
    related_opportunity_refs: []
    related_outcome_refs: []
    statement: null
    supporting_claim_ids: []
    object_refs: [selected_focus]
    audiences: [owner_visible]
  supporting_claim_ids: []
  object_refs: [selected_focus]
  audiences: [owner_visible]

current_work_system:
  summary: null
  confirmed_elements:
    - element_id: WS-001
      element_type: action
      statement: null
      supporting_claim_ids: []
      object_refs: [current_work_system.work_nodes]
      audiences: [owner_visible]
  open_elements: []       # 每项沿用 confirmed_elements 的证据与受众结构
  supporting_claim_ids: []
  object_refs: [current_work_system]
  audiences: [owner_visible]

ai_assessment:
  ai_status: insufficient_evidence
  mechanism: unknown
  candidate_change:
    change_id: AC-001
    actor:
      text: null
      supporting_claim_ids: []
      object_refs: [current_work_system.roles_and_handoffs]
      audiences: [owner_visible]
    trigger:
      text: null
      supporting_claim_ids: []
      object_refs: [current_work_system.trigger]
      audiences: [owner_visible]
    available_inputs: []              # 每项使用 EvidenceBoundItem
    current_action_or_judgment:
      text: null
      supporting_claim_ids: []
      object_refs: [current_work_system.work_nodes]
      audiences: [owner_visible]
    ai_change:
      text: null
      supporting_claim_ids: []
      object_refs: [intervention_assessment.candidate_intervention]
      audiences: [owner_visible]
    natural_feedback:
      text: null
      supporting_claim_ids: []
      object_refs: [current_work_system.feedback]
      audiences: [owner_visible]
    human_responsibility: []          # 每项使用 EvidenceBoundItem
    stop_conditions: []               # 每项使用 EvidenceBoundItem
    supporting_claim_ids: []
    object_refs: [intervention_assessment.candidate_intervention]
    audiences: [owner_visible]
  conditions: []                      # 每项使用 EvidenceBoundItem
  supporting_claim_ids: []
  object_refs: [intervention_assessment]
  audiences: [owner_visible]

change_signals:
  - signal_id: CS-001
    observable_condition: null
    judgment_update: null
    affected_object_refs: []
    supporting_claim_ids: []
    object_refs: [selected_focus]
    audiences: [owner_visible]

limitations:
  - limitation_id: LM-001
    kind: evidence
    statement: null
    affected_object_refs: []
    supporting_claim_ids: []
    object_refs: [diagnostic_boundary]
    audiences: [owner_visible]

minimum_validation:
  validation_id: MV-001
  decision_question:
    text: null
    supporting_claim_ids: []
    object_refs: [intervention_assessment]
    audiences: [owner_visible]
  evidence_unit:
    kind: natural_event
    description:
      text: null
      supporting_claim_ids: []
      object_refs: [current_work_system]
      audiences: [owner_visible]
  user_action:
    text: null                         # 只能有一个动作
    supporting_claim_ids: []
    object_refs: [current_work_system]
    audiences: [owner_visible]
  evaluation_rule:
    text: null
    supporting_claim_ids: []
    object_refs: [intervention_assessment]
    audiences: [owner_visible]
  update_scope:
    text: null
    supporting_claim_ids: []
    object_refs: []
    audiences: [owner_visible]
  stop_conditions: []                 # 每项使用 EvidenceBoundItem
  supporting_claim_ids: []
  object_refs: [intervention_assessment]
  audiences: [owner_visible]
```

## 可呈现单元的共同结构

任何可能单独进入正文的结果块、摘要、列表项、判断、限制、改判信号和验证动作，都是一个 evidence-bound unit。它不能只依赖父级或 Result 顶层的来源与权限。

短文本值使用：

```yaml
text: null
supporting_claim_ids: []
object_refs: []
audiences: [internal_only]
```

列表项在此基础上增加稳定 ID 和自身语义字段：

```yaml
item_id: ITEM-001
text: null
supporting_claim_ids: []
object_refs: []
audiences: [internal_only]
```

共同约束：

- `supporting_claim_ids[]` 指向仍有效的 claims；用户可见事实、推断、范围判断或“当前未知”都必须有相应声明，空引用的单元只能按 `[internal_only]` 处理；
- `object_refs[]` 指向该单元正在描述、限制、比较或准备更新的 CaseV2 对象；只有 claim 没有对象关系时不能进入结果；
- `audiences[]` 是该单元请求的可见范围，不是独立授权；实际权限还要与所有 supporting claims 的允许范围求交集；
- 父块的 `supporting_claim_ids[]` 与 `object_refs[]` 至少覆盖本次渲染所包含子项的并集，父块权限不得用一条宽权限声明替受限子项“洗白”；
- 子项即使允许更宽受众，也不能突破父块和 Result 顶层的权限上限；父块可过滤不适合当前受众的子项，并按剩余内容重新计算摘要与权限，不能保留由被过滤项推导出的句子。

`EvidenceBoundValue` 表示上面的短文本结构；`EvidenceBoundItem` 表示上面的列表项结构。Canonical schema 中标注这两个类型的字段必须保存完整结构，不能在实际结果中写成裸字符串。

## 必填字段

- `schema`
- `result_id`
- `case_id`
- `created_at`
- `status`
- `business_snapshot`
- `respondent_scope`
- `agenda`
- `opportunity_map[]`
- `priority_focus`
- `current_work_system`
- `ai_assessment`
- `change_signals[]`
- `limitations[]`
- `audiences[]`

`minimum_validation` 可以为 null。

每个顶层结果块必须包含 `supporting_claim_ids[]`、`object_refs[]` 和 `audiences[]`；块内每个可单独呈现的列表项也必须包含这三项。`candidate_change` 不成立时可以为 null；一旦存在，内部每个角色、触发、输入、当前动作、AI 改变、反馈、责任和停止条件都必须是独立的 EvidenceBoundValue／Item。

`status`：

```text
partial | final | paused
```

- `partial`：已经形成可带走的阶段理解，仍有一个会改变焦点或 AI 判断的缺口；
- `final`：本次公开授权范围内已经足以支持当前决定；
- `paused`：用户暂停或能量不足，保存可恢复结果。

## 结果各部分的门槛

### `business_snapshot`

只总结已经有来源的产品／服务、客户结果、价值或收入方式和本轮范围。行业名称、渠道、价格和单个商品不能自动生成公司定位。信息不足时缩小摘要，并把未知内容写入 limitations。

### `respondent_scope`

实际职责与可代表范围必须分开。宽泛岗位只进入 `role_label`；没有具体职责时 `actual_responsibilities[]` 保持空，不用岗位常识补齐。

### `agenda`

保留用户原话和多个 desired outcomes。总括目标没有被具体化时，可以留在 `user_wording[]` 并写入 `unresolved_priorities[]`，不能自动选降本、增收或效率方向。

只要一项目标仍可能影响候选价值、焦点选择或验证方向，就必须保留为独立 outcome；不能在摘要里只留下更容易描述的一项，也不能把“提高收入”和“减少等待”等并列目标合并成“因为等待所以收入低”的无证据因果链。每个 outcome 自带 claims、object refs 与 audiences。

### `opportunity_map`

候选必须来自案例中的 `opportunity_portfolio[]` 和有效 claims。公司级扫描或职责较宽时，呈现当前有证据、对取舍有帮助的候选；用户明确只判断一个局部工作时允许只有一个候选。

每个候选用 `outcome_refs[]` 回链它承接的全部相关目标。多个候选分别对应不同目标时，两条目标线都留在结果中；候选自己的 `known_signals[]` 不能替换或吞掉目标。没有证据时不得声称一个候选会推动另一候选的结果。

不得为凑数量补写行业常见流程、部门和问题。`current_status` 使用：

```text
candidate | shortlisted | selected | deferred | ruled_out
```

用户可见结果默认不呈现 ruled out 项的内部淘汰理由；用户询问取舍时，只说明有来源、允许公开的依据。

### `priority_focus`

`selection_status` 使用：

```text
unselected | provisional | confirmed
```

只有候选之间已有比较依据或用户明确限定局部问题时，才写 statement。provisional 必须说明改选信号；unselected 时清楚写出目前还缺哪项比较信息，不能假装已经找到“最值得做”的场景。

`considered_opportunity_refs[]` 覆盖本次比较过的候选，`relevant_outcome_refs[]` 覆盖所有仍会影响焦点的目标。`selection_basis[].dimension` 只能使用当前有证据的可比维度：

```text
business_impact | urgency | frequency | unacceptable_loss |
evidence_availability | result_verifiability | authority | risk | other
```

若现有信息不足以排序、而排序会改变下一步，保留 `unresolved_comparison`，其首选比较维度是业务影响或紧迫度。用户个人偏好可以成为已明确授权的局部边界，但“更想聊哪个／更喜欢哪个”本身不能替代业务优先级证据。

### `current_work_system`

只总结已经确认的目的、输入、动作／判断、输出、反馈、交接和责任。模式与事件分开；一件事件只覆盖事件范围。`open_elements[]` 保存会改变当前判断的缺口，不列完整字段清单。

### `ai_assessment`

`ai_status`：

```text
validation_candidate | foundation_first | non_ai_priority | insufficient_evidence
```

`mechanism`：

```text
automation | augmentation | hybrid | none | unknown
```

只有焦点和工作系统已有足够证据时才写 candidate change。它至少需要：

```text
明确角色
× 真实触发
× 当前可用输入
× 当前动作或判断
× AI 可能改变的具体关系
× 现有反馈
× 人的责任与停止条件
```

上述每个元素分别保存 supporting claims、object refs 和 audiences；candidate wrapper 保存本次呈现所用子项的并集。不能用 candidate wrapper 的一组宽泛 claim 代替元素级来源核对。任何一项只能靠行业常识补齐、缺少当前可用输入或没有自然反馈时，`candidate_change` 置为 null，并缩小判断或使用 foundation_first／insufficient_evidence。

### `change_signals`

每项改判信号必须拆成“可观察条件”和“它会怎样改变当前焦点或 AI 判断”，并在 `affected_object_refs[]` 指明受影响对象。不能只写抽象的“数据更充分时再判断”，也不能发明阈值。两部分共同使用该项自己的 supporting claims、object refs 与 audiences。

### `limitations`

每项限制是一个可审查对象，`kind` 使用：

```text
evidence | scope | representativeness | authority | permission | formal_project_boundary
```

限制要说明当前结论不能覆盖什么，并用 `affected_object_refs[]` 指向被限制的结果对象。限制不是通用免责声明；没有来源或对象关系的固定话术不进入 Result。涉及私密或正式项目边界的限制也必须经过受众交集检查。

### `minimum_validation`

只有同时满足以下条件才保留：

1. 它只验证一个会改变当前决定的问题；
2. 使用一次自然发生的工作或一个现成、脱敏、有界的证据包；
3. 不要求新建系统、连续采样、组织多人实验或整理完整数据；
4. 结果只更新当前声明范围；
5. 它不承担延长对话和服务转化功能。

非 null 的 minimum validation 必须明确保存：一个 `decision_question`、一种 `evidence_unit.kind`（`natural_event | existing_bounded_package`）、一个 `user_action`、一条 `evaluation_rule`、一个有界 `update_scope` 以及必要的 `stop_conditions[]`。这些可呈现单元分别带 supporting claims、object refs 与 audiences；顶层 metadata 覆盖本次呈现子项的并集。任一子项没有来源或会要求第二个用户动作时，将 `minimum_validation` 置为 null。

需要跨角色、代表性样本、生产权限、ROI、架构或实施承诺时，写入 limitations，并停止扩张公开初诊。

## 证据门槛

所有 `supporting_claim_ids[]` 必须引用 `DiagnosisStateV2.claims[]` 中仍有效的声明。每个数字、时间、金额、频率、专名和因果连接都必须回到相应 claim；每个引用对象必须存在于本次 CaseV2，且没有被纠正、排除或移出边界。

声明类型保持：

```text
reported_fact | observed_fact | experience_judgment | inference | hypothesis
```

被 corrected、invalidated 或 ruled out 的声明不能支撑结果。只有未核验假设时，缩小措辞并使用 `insufficient_evidence`；不能用经验判断代替客户事实。

## 用户需要带走什么

公共结果帮助用户抓住：

1. 系统怎样理解他的生意和职责；
2. 这次同时想改善什么；
3. 当前有哪些值得分开看的工作系统；
4. 现在为什么先看某一项；
5. 该工作目前卡在哪里；
6. AI 当前是否值得进入、可能改变什么；
7. 下一项最小验证和改判信号。

Presenter 根据内容成熟度选择必要部分，不机械凑齐七段，也不使用固定字符预算。

## 受众与权限

`audiences[]` 只能使用：

```text
internal_only | consultant_only | owner_visible | client_visible | exportable
```

字段缺少 audiences 时按 `[internal_only]`；`internal_only` 不得与其他值共存。Result 具备 `exportable` 资格也不表示用户已经授权导出或外发。

计算权限时先把标签展开为可达受众：

```text
internal_only   → internal
consultant_only → consultant
owner_visible   → owner
client_visible  → owner + client
exportable      → owner + client + neutral_export
```

一个结果单元的有效受众是以下集合的交集：

```text
Result 顶层允许受众
∩ 所有父块允许受众
∩ 该单元声明受众
∩ 每一条 supporting claim 的允许受众
```

然后再叠加 sensitivity、目标接收者与 consent。任何 supporting claim 比结果单元更窄时，结果单元必须随之收窄；交集为空、claim 缺失、claim audiences 缺失或标签冲突时默认拒绝呈现。不能取并集、不能以“多数 claim 可见”放行，也不能通过重新措辞、块级摘要或另加一条宽权限 inference 提升原始支持声明的权限。

面向某个目标受众生成投影时，可以删除无权呈现的分项并重新形成只由剩余 claims 支撑的摘要；不能先生成包含受限信息的摘要再只删除来源。`neutral_export` 只接收有效受众包含 `neutral_export` 的单元，且还需要明确的 export authorization；这不等于 external send authorization。

## V2 只读兼容

旧 `enterprise_ai_diagnosis_result_v2` 可以读取并保留来源：

- `user_anchor` → `agenda.user_wording[]`；
- `current_judgment` → provisional `priority_focus.statement` 或 `ai_assessment`，按原语义选择；
- `alternative_judgment` → 带稳定 ID、supporting claims、object refs 与 audiences 的 change signal 或 limitation，不能自动生成第二候选；
- `work_scene` 只有角色、触发、输入、当前动作、AI 改变、反馈、责任和停止条件都能分别回链时才映射为 `ai_assessment.candidate_change`，否则置为 null；
- `next_validation` 只有能拆成 V3 的 decision question、evidence unit、单一 user action、evaluation rule、update scope 和 stop conditions 时才映射为 `minimum_validation`，否则置为 null；
- 旧 `limitations[]` 逐项生成稳定 `limitation_id`、kind、supporting claims、object refs 与 audiences，不能把裸字符串原样塞入 V3；
- 旧顶层 `supporting_claim_ids[]` 与 `audiences[]` 只作为迁移上限，不能替新分项补齐缺失的来源和权限。

缺失的生意图、候选组合和工作系统字段保持未知。新结果只写 `enterprise_ai_diagnosis_result_v3`。
