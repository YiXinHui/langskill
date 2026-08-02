# 企业 AI 初诊 CaseV2 结构重构

## 变更背景

两次真实手测暴露出同一组结构问题：

- 开场没有先形成回答者实际职责与企业生意图；
- 第一处具体痛点被自动选成诊断焦点；
- “降本增效”被默认路由到节省人力和时间；
- 长期模式被强行改写成一件近期事件；
- 旧评测仍奖励固定回合停止和一次性样本更新；
- 非终局回复存在没有问题、没有阶段交付的静默结束风险。

本轮参考《提效知识统一结构_深化稿》中的价值链、工作流、岗位动作和价值维度，重建公开初诊的案例对象、交互决策与用户结果。五本账、线性／结构／跃迁三级改变和六步推进只作为内部研究来源，不进入公开问卷或用户报告。

## 根因判断

旧结构以 `business_context + desired_change + focal_event + primary_read + work_scene` 为主，能够处理单点问题，难以承载宽职责、复合目标、多个候选工作系统及其取舍。对话层因此容易沿最早出现的具体信息一路下钻，并把“凑齐阶段字段”误当成咨询进展。

## 结构变更

### EnterpriseDiagnosisCaseV2

新增独立案例模型，主线为：

```text
回答者与生意图
→ 议题组合
→ 候选工作系统组合
→ 选定焦点
→ 当前工作系统
→ AI 介入判断与最小验证
```

案例成熟度单独记录。字段未知不会触发逐项盘问；第一处具体痛点只进入候选；用户已经明确限定局部工作时允许直接聚焦。

### DiagnosisStateV2

交互状态与案例成熟度分离。每轮只有一个 `next_move`：

```text
ask | checkpoint | result | pause | repair
```

`ask` 必须包含一个可回答、会改判的问题；其他动作必须交付阶段理解、结果、暂停或纠正。非终局回复不能静默结束。

claims 增加 `object_refs[]`，证据可以明确挂到回答者、生意图、目标、候选工作系统、焦点、工作节点或介入判断。

### DiagnosisResultV3 与 PresenterV2

结果增加企业与回答者范围、议题组合、候选工作系统、焦点取舍、当前工作系统、AI 判断、改判信号、限制和最小验证。每个可呈现区块和分项都保存 supporting claims、对象引用与 audiences；实际权限取结果、父块、当前单元和全部 supporting claims 的交集。

Presenter 增加互斥的 `mode: turn | result`，普通回合与结果呈现不再共用一个模糊输入。普通可读摘要使用 `neutral_export`；只有明确交给咨询师、正式项目或接收系统时才生成 HandoffV2。

### 兼容层

- `EnterpriseDiagnosisCaseV1`、`DiagnosisStateV1`、`DiagnosisResultV2` 保留只读迁移。
- `enterprise_ai_diagnosis_handoff_v2` 继续作为公开与内部的兼容交接包，并可携带 ResultV3 投影。
- `JudgmentProviderV1` 保持现有接口，只允许在生意图、议题和焦点具备后查询，不能替用户生成候选或选择焦点。

CaseV2 的职责、生意、候选、工作节点、损耗和介入对象都增加稳定 ID 与 claim 回链；焦点、工作系统、价值损耗与介入判断通过 `focus_ref` 同步。StateV2 增加排除项生命周期、结果／导出状态和 Provider 版本 provenance。

## 评测变更

- 清理固定 500／900 字、固定三／四区块、第三次回答自动结束、L0／L1 和“唯一一次样本增强”等旧奖励信号。
- 保留两次手测反馈对应的逐点回归。
- 新增五类结构评测：
  1. 宽职责、复合目标与具体痛点并存；
  2. 两个经营目标与两个候选工作系统比较；
  3. 用户主动给出完整局部事件的直接准入；
  4. 多轮后仍存在高信息增益问题时继续；
  5. 完整 ResultV3 用户结果。
- 新增两条导出分流评测：普通中性摘要、用户自行转发给合伙人的摘要；既有外部顾问交接评测作为合法 Handoff 例外。
- 中立导出增加逐句纯投影约束：只能重排、删减和忠实改写既有 `exportable` 单元，不能自行补充 AI 判断、建议、风险或下一阶段安排；用户自行转发时明确确认当前没有执行发送。

## 变更范围

- `skills/lang-enterprise-ai-diagnosis/SKILL.md`
- `skills/lang-enterprise-ai-diagnosis/references/`
- `skills/lang-enterprise-ai-diagnosis/evals/`
- `README.md`
- `docs/DESIGN.md`
- `docs/TODO.md`
- `scripts/validate-sharing-system.mjs`
- `VERSION`

内部 Skill 和托管应用未纳入本轮修改。

## 验证

- 14 个 YAML／JSON 契约示例解析通过；
- 517 项静态契约检查通过；
- 79 个评测场景结构有效且 ID 连续；
- 14 个公开 Skill 目录与清单校验通过；
- 14 个 Skill 的 Codex／Claude Code 共享安装回归通过；
- 官方 Skill 结构校验通过；
- 敏感信息预扫描与 `git diff --check` 通过。

模型行为烟测覆盖 eval 73—75、77—79：宽职责与复合目标、候选比较、完整局部事件、完整结果、老板自存摘要和合伙人可读副本均通过。合伙人摘要首次运行发现了未授权补充 AI 判断和漏报发送状态的问题；收紧 Presenter 后隔离复测 6/6 通过。详细记录见 `skills/lang-enterprise-ai-diagnosis/evals/2026-08-02_case-v2_structural_smoke-results.md`。

## 发布状态

本轮只完成本地迭代与验证，没有提交、推送、发布、部署或同步内部 Skill。
