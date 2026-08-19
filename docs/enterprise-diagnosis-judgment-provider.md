# 旧版企业 AI 诊断判断库宿主架构

> 状态：随旧版 Skill 一并归档，仅供迁移参考。旧运行时契约见 [`judgment-provider-contract.md`](../archive/lang-enterprise-ai-diagnosis-2026-08-19/references/judgment-provider-contract.md)；当前公开入口是 `lang-business-diagnosis`，不以本文作为当前执行规范。

## 定位

判断库存的是“面对某类经营情况时，咨询师如何取舍”的可复用经验，不存客户事实，也不能代替现场证据。公共 Skill 不携带私人飞书记录、客户数据、内部链接、Token 或判断正文；实现方可通过 `JudgmentProviderV1` 注入经治理的判断。

Provider 是可选增强，不是公共诊断的运行依赖。零命中、同步降级或服务不可用时，诊断必须继续使用公共核心，且不能为了显示“用了独家方法”补造命中。

## 推荐分层

```text
权威编辑源（飞书 Base 或其他人工治理系统）
  → 单向同步、字段校验、版本记录、敏感过滤
运行时只读索引（现有应用数据库优先）
  → JudgmentProviderV1
  → 诊断引擎内部比较镜片
```

权威编辑源负责人工确认、修改、替代、退役和溯源。运行时索引是可重建的派生数据，不反向覆盖权威源，也不向公共浏览器提供编辑凭证。

不推荐：

- 每个对话回合直接查询飞书，让延迟、限流和授权过期影响主链；
- 把 SQLite、JSON 快照或私人判断正文提交进公开代码仓；
- 把整张判断库塞进提示词，无法证明实际采用了哪条；
- 为很小的数据量先引入复杂向量基础设施。先用结构化字段与关键词，需求增长后再增加混合检索。

## 权威记录治理

权威源至少要能生成运行契约要求的字段：判断 ID、标题、适用条件、决策、关键变量、改判信号、候选动作、业务场景、版本、确认时间、允许 surface 与内容 hash。

确认状态和生命周期分开维护：

```text
confirmation_status: confirmed
lifecycle_status: current | superseded | retired
```

运行索引只接收 `confirmation_status: confirmed` 且 `lifecycle_status: current` 的记录。这样不会把“曾经确认但已经被替代”或“标成当前但尚未确认”的记录放进诊断。

`source_ref` 是内部溯源键，只能在 `allowed_surface: internal` 的响应中出现。公共 hosted surface 不返回私人链接、Base token、内部主键或原始判断笔记。

## 同步与索引

推荐流程：

1. 依据权威源 revision、更新时间或事件流做增量同步；
2. 校验必填字段、枚举、允许 surface、内容 hash 与 `confirmed + current` 条件；
3. 对客户 PII、凭证、私人原文和内部链接执行拒绝或脱敏；
4. 写入运行时只读索引，保存 provider revision；
5. 定期全量对账，被替代或退役的记录在索引中软禁用；
6. 同步失败时保留上一份可用索引并标记降级，不把旧记录描述为最新全量判断。

已有 MySQL 或 PostgreSQL 的宿主优先复用现有数据库，不额外引入 SQLite。索引必须支持按 `allowed_surfaces[]`、业务场景、适用条件、关键变量和生命周期过滤，而不只是标题相似度排序。

## 运行调用

诊断引擎只在已经得到脱敏业务语境、期望变化和当前假设后发起请求。完整 Request/Response、必填字段、0—5 条限制与降级语义见运行时契约，不在本文复制第二套 schema。

Provider 返回内容进入内部：

```text
claim_kind: experience_judgment
source_visibility: source_unavailable
audiences: [consultant_only] 或 [internal_only]
```

它只帮助选择下一问、比较方向和寻找反例，不能成为客户事实，也不能单独支撑用户可见结论。Presenter 默认拒绝呈现查询、命中正文、revision 和 `source_ref`。

## 安全与审计

- 权威源凭证只放服务端同步任务，不进入浏览器、提示词、客户端日志或公开仓；
- 查询只发送脱敏业务场景、期望变化、当前假设、关键变量和排除项；
- 客户名称、个人信息、聊天全文、订单原文、生产数据、Token 与密钥不得发给 Provider；
- 客户会话数据与通用判断库分开存储；
- 诊断内部追踪 `judgment_id + version + content_hash + provider_revision`，便于重放和审计；
- Provider 失败只记录内部状态，不向普通用户暴露飞书、索引、同步或凭证术语；
- Provider 不得触发发送、建档、预约或任何外部动作。

## 降级原则

| 情况 | 行为 |
|---|---|
| 合格命中 | 作为内部经验镜片比较，仍由客户 claim 支撑外部结论 |
| 零命中 | 继续公共诊断核心，不补造判断 |
| `degraded` | 仅使用仍明确 `confirmed + current` 的合格项，并记录降级 |
| `unavailable` | 完全跳过 Provider，继续公共核心 |

Provider 状态不能直接改变 `ai_status`，也不能成为延长问答或索取更多客户信息的理由。
