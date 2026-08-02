# EnterpriseDiagnosisCaseV2｜企业 AI 初诊案例模型

## 目的

`EnterpriseDiagnosisCaseV2` 说明一次企业 AI 初诊究竟在理解哪些业务对象，以及这些对象怎样相互关联。它是后台案例模型，不是问卷、对话步骤或用户报告。

案例模型遵循一条主线：

```text
本次进入方式
→ 回答者与生意图
→ 本次议题组合
→ 候选工作系统组合
→ 选定焦点
→ 当前工作系统
→ AI 介入判断与最小验证
```

用户可以乱序提供信息，也可以从一件具体事情开始。系统把信息放回对应对象，仅补会改变当前判断的缺口。字段未知不构成失败，也不能驱动逐项盘问。

## Canonical schema

```yaml
schema: enterprise_ai_diagnosis_case_v2
case_id: opaque-case-id

entry_context:
  diagnosis_intent: unspecified
  entry_form: blank_activation
  route_source: system_activation
  user_wording:
    statement: null
    claim_ids: []
  claim_ids: []

respondent:
  role_fact_id: ROLE-001
  role_label: unknown
  role_label_claim_ids: []
  actual_responsibilities:
    - responsibility_id: RSP-001
      statement: null
      claim_ids: []
  decision_authority:
    - authority_id: AUT-001
      statement: null
      claim_ids: []
  can_speak_for:
    - scope_id: RSC-001
      statement: null
      claim_ids: []
  cannot_confirm:
    - scope_id: RSC-002
      statement: null
      claim_ids: []

business_map:
  domain_labels:
    - domain_id: DOM-001
      label: null
      claim_ids: []
  offerings:
    - offering_id: OFF-001
      statement: null
      claim_ids: []
  customers:
    - customer_id: CUS-001
      statement: null
      claim_ids: []
  customer_outcomes:
    - customer_outcome_id: CO-001
      statement: null
      claim_ids: []
  revenue_logic:
    - revenue_item_id: REV-001
      statement: null
      claim_ids: []
  current_business_scope:
    scope_id: BS-001
    statement: null
    claim_ids: []

agenda:
  user_wording:
    - wording_id: UW-001
      text: null
      claim_ids: []
  desired_outcomes:
    - outcome_id: G-001
      category: unknown
      observable_change: null
      scope_ref: null
      priority: unresolved
      claim_ids: []
  unacceptable_losses:
    - agenda_loss_id: AL-001
      statement: null
      claim_ids: []
  tensions:
    - tension_id: T-001
      statement: null
      claim_ids: []

diagnostic_boundary:
  boundary_id: BND-001
  level: unknown
  object_ref: null
  in_scope:
    - scope_item_id: BI-001
      statement: null
      claim_ids: []
  out_of_scope:
    - scope_item_id: BO-001
      statement: null
      claim_ids: []
  baseline_status: unknown
  baseline_observations:
    - observation_id: BL-001
      statement: null
      claim_ids: []
  claim_ids: []

opportunity_portfolio:
  - opportunity_id: O-001
    label: null
    system_level: unknown
    business_contribution:
      statement: null
      claim_ids: []
    outcome_refs: []
    known_signals:
      - signal_id: SG-001
        statement: null
        claim_ids: []
    possible_loss_locations:
      - loss_location_id: LL-001
        relationship_ref: null
        statement: null
        claim_ids: []
    evidence_availability: unknown
    result_verifiability: unknown
    method_maturity: unknown
    assessment_claim_ids: []
    current_priority: unresolved
    claim_ids: []

selected_focus:
  opportunity_id: null
  selection_status: unselected
  selection_basis:
    - basis_id: FB-001
      statement: null
      claim_ids: []
  claim_ids: []

current_work_system:
  focus_ref: null
  purpose:
    element_id: WSP-001
    statement: null
    claim_ids: []
  trigger:
    element_id: WST-001
    statement: null
    claim_ids: []
  inputs:
    - element_id: WSI-001
      statement: null
      claim_ids: []
  work_nodes:
    - node_id: N-001
      statement: null
      claim_ids: []
  decisions:
    - decision_id: WD-001
      statement: null
      claim_ids: []
  outputs:
    - element_id: WSO-001
      statement: null
      claim_ids: []
  feedback:
    - element_id: WSF-001
      statement: null
      claim_ids: []
  roles_and_handoffs:
    - relation_id: RH-001
      statement: null
      claim_ids: []
  exceptions_and_responsibility:
    - relation_id: ER-001
      statement: null
      claim_ids: []
  coverage: empty
  coverage_claim_ids: []

value_map:
  focus_ref: null
  relevant_dimensions:
    - dimension_id: VD-001
      dimension: business_result
      claim_ids: []
  loss_points:
    - loss_id: VL-001
      relationship_ref: null
      dimension_refs: []
      statement: null
      claim_ids: []
  expected_gains:
    - gain_id: VG-001
      outcome_refs: []
      statement: null
      claim_ids: []

intervention_assessment:
  focus_ref: null
  ai_status: insufficient_evidence
  mechanism: unknown
  method_maturity: unknown
  input_readiness: unknown
  feedback_readiness: unknown
  responsibility_readiness: unknown
  candidate_intervention: null
  claim_ids: []

readiness:
  business_map: empty
  agenda: empty
  opportunity_portfolio: empty
  selected_focus: empty
  current_work_system: empty
  intervention_assessment: empty
```

Schema 中的对象是形状示例。真实字段未知时使用 `null` 或空数组，不创建占位事实。每个事实项使用案例内稳定 ID；创建后不复用、不因改写文本而更换。`claim_ids[]` 必须指向 `DiagnosisStateV2.claims[]` 中仍有效的声明。枚举、成熟度和优先级等派生判断使用所在对象的 `claim_ids[]` 或 `assessment_claim_ids[]` 回链依据。

## 本次进入方式

`entry_context` 记录用户准备从哪里进入本次初诊。它服务于首轮体验和后续分流，不代替业务事实，也不能驱动逐项补字段。

`diagnosis_intent` 使用：

```text
company_scan | specific_business_issue | evaluate_ai_idea | unspecified
```

`entry_form` 使用：

```text
blank_activation | intent_only | contextualized | resumed
```

`route_source` 使用：

```text
explicit | inferred | system_activation | unknown
```

约束：

- 用户只激活 Skill 时写 `blank_activation + unspecified + system_activation`；第一条回复先说明结果预期并识别入口，不能直接采集公司与职责；
- 用户明确选择整体扫描、具体业务问题或已有 AI 想法时，保存原话 claim，并使用 `route_source: explicit`；
- 用户首句已经带来实际问题、AI 方案或足够业务背景时，使用 `entry_form: contextualized`，根据原话选择入口并写 `route_source: inferred`，不要求用户重新选择；
- 推断只决定从哪里继续交流，不能把行业经验、工具名称或单个现象补成业务事实；
- 用户纠正进入方式时更新 `entry_context`，旧入口不得继续支撑后续问题；
- 入口枚举、推断来源和路由状态属于内部信息，不进入用户报告和普通对话。

## 回答者与生意图

### `respondent`

- `role_label` 保存用户原话中的岗位或身份，使用 `role_fact_id` 稳定定位，来源写入 `role_label_claim_ids[]`。
- `actual_responsibilities[]` 保存其经常负责的工作、决定或产出，每项有 `responsibility_id + claim_ids[]`。
- `decision_authority[]` 保存其能够批准、改变或承担结果的范围，每项有独立 ID 和证据。
- `can_speak_for[]` 与 `cannot_confirm[]` 限制结论能覆盖的层级；每个范围项单独追溯。

“老板、运营、销售、管理、负责人”等标签只提供入口。岗位覆盖多类工作且会导向不同判断时，继续了解实际职责；用户已经给出具体职责时直接使用。

### `business_map`

生意图只补到足以解释本次问题：

- 公司提供什么产品或服务；
- 谁付费或直接受益；
- 客户购买后希望获得什么结果；
- 收入、利润或后续价值怎样形成；
- 本轮讨论哪条业务线、产品、客群或经营范围。

`domain_labels[]` 用于行业语言、监管、周期和价值链导航。行业名称不能替代产品、客户、客户结果和收入逻辑，也不要求每次初诊先取得完整行业分类。生意图中的标签、产品、客户、客户结果、收入逻辑和当前范围均保存稳定 ID 与 `claim_ids[]`；摘要不能成为无来源的新事实。

## 议题组合

`agenda.desired_outcomes[]` 允许多个目标同时存在。`category` 使用：

```text
revenue | profit | cost | time | capacity | cycle | quality | risk |
customer | decision | organization_asset | new_opportunity | other | unknown
```

每项目标同时保留用户原话、可观察变化、作用范围和优先关系。`priority` 使用：

```text
selected | coequal | secondary | unresolved
```

“降本增效、提升运营、想 AI 化”等总括表达先进入 `user_wording[]`。只有用户说明希望发生的可观察变化，或现有上下文已经清楚指向某类变化时，才填入具体 category。多个方向可以并存；当前决定确实需要排序时再分先后。

## 诊断边界与基线

`diagnostic_boundary.level` 使用：

```text
company | product_business | multi_work_system | work_system | task | unknown
```

边界说明这次正在判断多大的对象以及哪些成本、结果、角色和证据可以计入。用户明确要求判断一个局部动作时，可以直接使用 `task` 或 `work_system`；公司级扫描需要先形成候选工作系统组合。

`baseline_status` 使用：

```text
unknown | qualitative | quantitative
```

公开初诊允许定性基线，例如“每周都要人工汇总”“错误会推迟补货判断”。没有数字时保持定性或未知，不要求用户临时整理数据，也不计算装饰性 ROI。

## 候选工作系统组合

`opportunity_portfolio[]` 保存当前范围内值得分开比较的工作系统。候选来自用户职责、价值链和已报告现象，不来自行业常识补全。

每个候选至少回答：

- 它对哪项经营结果有贡献；
- 用户已经报告了什么现象；
- 损耗可能位于哪类关系；
- 是否有现成材料和自然反馈；
- 当前人类方法是否稳定；
- 目前为什么保留、优先、后置或排除。

候选数量由当前决策决定。公司级或职责范围较宽时保留足够比较的组合；用户已经明确限定一个局部问题时允许只有一个候选，不为凑数量制造其他问题。

`current_priority` 使用：

```text
unresolved | shortlisted | selected | deferred | ruled_out
```

`selected_focus.selection_status` 使用：

```text
unselected | provisional | confirmed
```

用户随口提到的第一件具体事情可以成为候选。只有用户明确选择、现有证据显示其更影响当前目标，或其他候选已经有依据地后置时，才进入 `selected_focus`。

焦点与候选同步规则：

- `selection_status = unselected` 时，`selected_focus.opportunity_id = null`，组合中不能有 `current_priority = selected`；
- `selection_status = provisional | confirmed` 时，`opportunity_id` 必须引用当前组合中唯一一个非 `ruled_out` 候选，该候选的 `current_priority` 必须为 `selected`；
- 组合中最多一个候选为 `selected`；改选时先更新旧候选状态，再更新 `selected_focus` 和三个 `focus_ref`；
- 选择依据中的每一项使用 `basis_id + claim_ids[]`，不能只保存无法审查的总结句。

## 当前工作系统

焦点选定后，用下列结构理解真实工作：

```text
目的
→ 触发
→ 输入
→ 动作与判断
→ 输出
→ 反馈
→ 角色与交接
→ 异常与责任
```

`coverage` 使用：

```text
empty | partial | sufficient
```

`current_work_system.focus_ref` 必须引用 `opportunity_portfolio[].opportunity_id`。焦点尚未选定时，只有明确属于某个候选的有界信息才可暂存到该候选对应的工作系统；它不能提前支撑优先级或 AI 结论。焦点改变后，当前工作系统按新 `focus_ref` 重建，旧事实继续保留在 claims 与原候选信号中，不能改挂到新焦点。

目的、触发、输入、节点、判断、输出、反馈、交接、异常与责任均使用稳定元素 ID 和 `claim_ids[]`。“最近一次真实工作”只是补充工作系统的一种证据。用户给出长期模式时先记录模式；用户主动提供可定位事件，或确认可以轻松回忆一件代表性事件且它会改变判断时，再使用事件走查。

## 价值与 AI 介入

`value_map.relevant_dimensions[]` 使用：

```text
business_result | full_cost | cycle_speed | quality_risk | organization_asset
```

只启用与当前目标和候选有关的维度。五个维度用于组织证据和验收，不对用户逐项提问。

`intervention_assessment.mechanism` 使用：

```text
automation | augmentation | hybrid | none | unknown
```

`method_maturity` 使用：

```text
stable | partly_stable | exploratory | unknown
```

`ai_status` 保留四个公开判断：

```text
validation_candidate | foundation_first | non_ai_priority | insufficient_evidence
```

`candidate_intervention` 非空时使用：

```yaml
candidate_intervention:
  intervention_id: AI-001
  focus_ref: O-001
  target_relation_refs: [current_work_system.work_nodes.N-001]
  responsible_role_refs: []
  trigger_refs: []
  input_refs: []
  current_action_refs: []
  proposed_change:
    statement: null
    claim_ids: []
  feedback_refs: []
  human_responsibility_refs: []
  stop_conditions:
    - condition_id: SC-001
      statement: null
      claim_ids: []
  claim_ids: []
```

AI 候选必须指向工作系统中的一个动作、判断、接口或反馈关系。`ai_status = validation_candidate` 时，角色、真实触发、现成输入、当前动作、拟改变关系、自然反馈、人的责任和停止条件都必须有对象引用或有效 claim；缺项时保持 `foundation_first` 或 `insufficient_evidence`。自动化适合稳定、重复、可校验的工作；增强适合需要人承担责任的分析、判断和创造。人类方法仍在探索时，只能提出共创验证，不能承诺稳定生产系统。

线性、结构性和价值创造深度属于真实验证后的派生判断，不进入公开初诊的早期焦点选择。

## Readiness 只做闸门

每项 readiness 使用：

```text
empty | partial | sufficient
```

readiness 描述当前案例成熟度，不代表对话进度，也不要求按顺序补齐。系统可以先收到具体事件，再补一个会改变解释的生意坐标；也可以先形成生意图，再比较候选工作系统。

`insufficient_evidence` 只表示当前 AI 判断强度，不能单独触发结束。是否继续由当前是否还有一个可回答、会改变决定且仍在公开范围内的问题决定。

## 对象关系不变量

1. 回答者范围限制所有公司、业务线、团队和角色级结论。
2. 每个事实项都有案例内稳定 ID，并通过 `claim_ids[]` 回链证据；不存在有效 claim 的项保持未知。
3. 议题选择诊断边界；边界包含候选工作系统；焦点只能引用当前候选。
4. `selected_focus` 与候选 `current_priority` 必须一致；焦点形成后，三个非空 `focus_ref` 都必须等于它。焦点形成前只有 `current_work_system` 可为有界证据暂挂候选，`value_map` 与 `intervention_assessment` 不能提前形成。
5. 损耗必须引用某个工作系统关系和至少一个价值维度，不能只写抽象“效率低”。
6. AI 介入必须引用当前工作系统中的具体改变；`candidate_intervention.focus_ref` 必须与 assessment 和 selected focus 一致。
7. 事件、样本和单个角色不能自动升级为公司级事实。
8. 被纠正、失效或处于 active ruled-out 记录中的 claim／对象不能继续支撑案例和结果。

## V1 只读兼容

旧 `enterprise_ai_diagnosis_state_v1` 可以读取并映射，不能作为新会话写入格式：

- 旧状态没有入口信息时使用 `entry_form: resumed`，`diagnosis_intent` 保持 `unspecified`；只有旧内容明确限定整体扫描、具体问题或 AI 想法时才可推断，不能补造用户选择；
- `speaker_scope` → `respondent`；宽泛岗位只进入 `role_label`；
- `business_context` → `business_map` 与 `diagnostic_boundary`；
- `desired_change` → `agenda.user_wording[]`，不能自动生成具体目标；
- `focal_event` → 带来源的事件 claim；已能确认所属候选时才进入该 `focus_ref` 的工作系统，不能自动成为 selected focus；
- `primary_read / alternative_read` → 带来源的开放假设；
- `work_scene` → `intervention_assessment.candidate_intervention`，并重新检查角色、触发、输入、反馈、责任和停止条件；
- `ai_status` 保留原值并重新检查当前对象关系。

兼容迁移中的每个事实都创建稳定对象 ID，并链接由旧字段生成的迁移 claim；缺少来源时保持 `unverified`，不能伪装为 observed fact。新会话只写 `EnterpriseDiagnosisCaseV2`。兼容映射不得补造候选、职责、客户、基线或工作系统节点。
