# 四类知识库契约

本文件拥有概念、判断、案例和金句的通用准入与最小字段。当前配置没有启用的库不运行。

## 共享字段

所有库至少保留：

- 稳定 ID／系统写入键；
- 核心文本；
- `status`：`pending_review | confirmed | discarded`；
- `access_scope`：`private | team | public_candidate | needs_review`；
- 来源标题、原始位置和可定位锚点；
- 作者／说话人及归属状态；
- 创建时间、更新时间和审核备注。

稳定写入键应由“库角色＋来源稳定身份＋证据位置＋候选语义身份”组成。标题和措辞变化不能导致重复新建。

## 概念库

概念回答“这个词在我的知识系统里稳定指什么”。满足以下条件才准入：

- 来源明确给出稳定名称或可核验的定义；
- 它能帮助多次理解、检索或连接判断，而不是一次性名词；
- 能说清它包含什么、不包含什么，或与近似词的区别；
- 通常由已准入判断使用，或来源本身正在明确界定该概念。

普通名词、项目名、内部黑话、漂亮命名和只出现一次的缩写不自动入库。

最小字段：

```text
concept_id, name, one_sentence_definition, boundary_or_distinction,
aliases, supporting_judgment_ids, source_ref, status, access_scope, review_note
```

初始化阶段不自动创建上位概念树。候选未确认前，不把它当作其他记录的正式分类依据。

## 判断库

判断回答“面对一类情境，应该怎样理解或选择，以及什么时候会改判”。准入需要：

- 存在真实选择、评价、因果解释或行动方向；
- 依据和结论之间有可检查的关系；
- 有适用条件、边界或可能改变结论的变量；
- 脱离本次材料后仍可能影响未来的判断或行动。

事实摘录、待办、流程步骤、数据口径、单纯感受、普通常识和 SOP 默认不属于判断。它们可以作为依据或进入其他系统。

最小字段：

```text
judgment_id, judgment, decision_question, basis, boundary_or_change_conditions,
linked_concept_ids, source_ref, status, access_scope, review_note
```

核心判断尽量是一句可独立理解的成品；依据与边界承接证据，不把所有背景塞进核心句。AI 只能生成候选，不能替用户写成 `confirmed`。

## 案例库

案例默认在 `growth` 以后启用。它回答“什么真实经历验证、修正或限制了哪条判断”。准入需要：

- 主体与情境；
- 关键问题或冲突；
- 采取的行动／干预；
- 可观察结果；
- 为什么出现这个结果的机制或解释；
- 至少关联一条已准入判断，并说清案例增加了什么证据。

流水账、故障片段、会议决定、只有结果没有机制或虚构例子不入正式案例库。

最小字段：

```text
case_id, title, context, key_problem, action, result, mechanism,
linked_judgment_ids, reuse_value, source_ref, status, access_scope, review_note
```

## 金句库

金句默认在 `advanced` 启用。它是忠实于来源命题、经过表达打磨且值得重复传播的一句话。

- 简短不等于金句；普通正确观点可以留在判断库。
- 可以修辞重构，但不能新增来源没有的立场、因果、敌我关系或绝对范围。
- 他人的话不能署成用户的话；多人共同形成的命题要保留真实形成过程。
- 未经用户明确采用的 AI 改写保持 `pending_review`。

最小字段：

```text
quote_id, quote, meaning_core, original_evidence, attribution,
linked_judgment_ids, source_ref, status, access_scope, review_note
```

每个语义内核只保留一个最佳候选；没有达标稿允许为零。

## 去重顺序

每个库分别执行：

1. 稳定写入键精确匹配；
2. 核心对象与语义匹配；
3. 判断新内容能否被已有记录的依据、边界、别名或案例吸收；
4. 只有出现新的独立知识对象或会改变未来调用的增量时才新建。

重复默认返回现有位置，不自动覆盖已确认正文。需要补充时先展示差异并让审核人决定更新还是保留。
