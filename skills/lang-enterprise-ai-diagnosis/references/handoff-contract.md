# 正式企业 AI 诊断交接契约

## 生成门槛

只有用户看完初诊结果，并明确要求“生成正式诊断交接草稿”时才生成。仅表示想进入正式诊断，或要求直接建档、发送、预约，不等于草稿请求；这种情况下先用一句话重申初诊对“是否值得进入正式诊断”的建议，再陈述未执行与授权边界，不要求用户回复固定口令，也不承诺当前环境之后能够执行外部动作。默认状态必须是 `draft_for_review`：用户先审核、删减敏感信息，再决定是否转交。

Handoff 草稿必须作为初诊结果之后的独立回复生成，不能与初诊卡同条输出。初诊卡的 900／500 字、四／三区块和至多一个证据动作限制，只适用于 `L0 RESULT`、`L1 RESULT` 与 `UPDATED L1 RESULT`；handoff 草稿不受该字数和区块限制，但不得借此改写初诊结论、增加当前用户作业或暗示已经授权。

同意生成交接草稿不等于同意：

- 自动写入客户系统；
- 自动发送联系人或材料；
- 公开案例、训练模型或长期保存；
- 查看生产数据、账号、接口或跨角色材料。

## 稳定格式

```yaml
handoff_type: enterprise_ai_pre_diagnosis_v1
status: draft_for_review
generated_at: YYYY-MM-DD
diagnosis_level: L0 | L1 | unknown
organization_label: 公司名或代号
respondent_scope:
  role: 回答者角色；未知则待确认
  can_speak_for: 本轮可代表的业务范围
  cannot_confirm: 需要其他角色或系统核验的事项
business_focus:
  value_creation: 公司靠什么产品或服务创造价值
  desired_outcome: 这次想改变的结果
  unacceptable_loss: 最不能接受继续发生什么；未知则留空
statements:
  - statement: 用户原意的可读摘要
    status: user_statement | sample_reported | sample_observed | hypothesis | ruled_out | gap
    source: 本次问答或脱敏样本代号
    scope: 角色、时间与样本范围
diagnostic_fork:
  primary_hypothesis: 当前主判断
  alternative_explanation: 替代解释
  change_signal: 什么证据会改判
  current_confidence: low | medium
sample_review:
  provided: true | false | unknown
  source_mode: none | sample_reported | sample_observed | mixed | unknown
  sample_label: 脱敏代号；未提供则留空
  supports_or_weakens: 样本支持或削弱了什么
  cannot_generalize: 不能外推什么
recommended_start:
  decision: validate_ai | foundation_not_ready | do_not_start_now
  business_action_changed: validate_ai 时填写“改变谁在什么触发下的什么动作”；其余状态为 null
  next_evidence_action: 原样引用最终初诊卡中的可选补充；若没有则为 null
  continue_signal: 继续条件
  adjust_or_stop_signal: 调整或停止条件
formal_diagnosis_scope:
  roles_or_owners: 下一阶段应核验的角色
  records_or_systems: 需要的脱敏材料或只读记录
  questions_to_resolve: 只有正式诊断才能回答的问题
sensitivity:
  excluded: 不进入交接的客户名、凭证、个人信息或其他内容
  user_approved_scope: 用户本轮明确批准进入草稿的范围
```

## 接收方规则

正式诊断接收方把该包视为售前来源，而不是客户事实或已确认方案：

- `user_statement` 保留为对应角色主张；
- `sample_reported` 只表示用户转述了有界样本汇总，不得写成接收方已查看或已核验；
- `sample_observed` 只表示实际查看的样本中出现了该现象，不表示材料已验真、具有代表性或识别了因果；
- `hypothesis` 必须继续保留替代解释和改判信号；
- `ruled_out` 不得在没有新证据时复活；
- `gap` 保留为正式诊断待核验问题，不自动转成当前用户任务；
- 需要跨角色、数据、权限、ROI、架构和实施承诺的内容重新进入正式诊断流程。

`formal_diagnosis_scope` 可以列多个待核验范围，因为它描述后续项目边界，不是要求用户当前执行的动作；不得附带负责人、期限、访问授权或已承诺实施的措辞。缺失信息直接保留 `unknown`／`gap`，不通过新一轮提问补齐。

当前环境没有真实转交或写入能力时，只输出可复制草稿并明确“尚未发送”。如果用户粘贴 Token、密钥或客户个人信息，输出时删去原值，提醒其撤销／轮换已暴露凭证；不得在交接包中复述。
