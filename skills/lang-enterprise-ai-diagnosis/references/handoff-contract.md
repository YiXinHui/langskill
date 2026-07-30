# 正式诊断交接包

## 何时生成

只有用户明确表示愿意把初筛结果用于正式诊断衔接时才生成。生成前提醒用户审核并删除不希望传递的敏感信息。

同意生成交接包不等于同意：

- 自动写入客户系统；
- 向第三方发送联系方式；
- 公开案例或用于训练；
- 授权读取生产数据、账号和接口。

## 交接格式

```yaml
handoff_type: enterprise_ai_pre_diagnosis_v1
generated_at: YYYY-MM-DD
organization_label: 公司名或代号
respondent:
  role: 回答者角色
  decision_authority: 能决定什么；未知则待确认
engagement_intent:
  desired_outcome: 希望改变的经营结果
  unacceptable_loss: 最不能接受继续发生什么
  formal_diagnosis_requested: true
scope:
  included_business_chain: 本次讨论的业务链
  excluded_or_unknown: 未覆盖范围
recent_business_event:
  title: 可读事件名
  trigger: ...
  inputs: [...]
  actions: [...]
  judgments: [...]
  outputs: [...]
  exceptions: [...]
  feedback: ...
statements:
  - statement: ...
    status: sample_supported | user_statement | hypothesis | gap
    source: 用户提供的可读来源或“本次问答”
    scope: 适用角色、部门、时间或样本
single_point_dependencies:
  - location: 人／流程／数据／系统
    impact: ...
    current_basis: ...
candidate_starting_points:
  - candidate: ...
    business_action_changed: ...
    supporting_basis: ...
    blocking_gap: ...
    current_state: worth_validating | evidence_missing | not_recommended_now
recommended_next_probe:
  owner_or_role: ...
  real_event_or_record: ...
  question_answered: 这一步会改变哪个判断
evidence_request:
  - title: ...
    purpose: ...
    safe_access: 结构／脱敏样本／现场只读／其他
sensitivity:
  do_not_share: [...]
  user_approved_scope: 用户本轮明确同意传递的范围
```

## 接收方处理规则

正式诊断接收方应把这份材料视为“售前来源”，不是既定客户事实或已确认方案：

- `user_statement` 保留为对应角色的主张；
- `sample_supported` 仍需核对样本范围、口径和真实性；
- `hypothesis` 必须保留替代解释和证伪方式；
- `gap` 转成下一轮证据任务；
- 候选起点重新与真实业务事件、跨角色证据、数据条件、责任人和反馈比较。

如果当前环境具备正式诊断工具，也必须先完成用户授权和客户归属确认，再执行任何外部写入。
