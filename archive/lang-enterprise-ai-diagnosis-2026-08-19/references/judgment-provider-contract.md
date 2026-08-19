# JudgmentProviderV1 运行接口

## 定位

`JudgmentProviderV1` 是可选的只读经验判断接口。公开初诊不携带私人判断正文，也不要求宿主实现 Provider；零命中、降级或不可用时，必须继续使用公共诊断核心。

Provider 返回经验比较镜片。它不具备客户事实、用户授权、正式结论或方法注册的效力。所有返回项进入 `claim_kind: experience_judgment`、`source_visibility: source_unavailable`，默认只允许 `audiences: [consultant_only]` 或 `[internal_only]`。

## Request

```json
{
  "schema": "judgment_provider_v1",
  "query_id": "opaque-query-id",
  "allowed_surface": "public_hosted",
  "limit": 3,
  "business_context": {
    "business_scenes": ["企业服务"],
    "desired_change": "减少创始人对关键判断的重复介入",
    "current_hypothesis": "团队可能缺少可识别例外的判断边界",
    "key_variables": ["判断依据是否可表达", "结果好坏是否可见"],
    "exclusions": ["客户名称", "个人信息", "原始聊天", "凭证"]
  }
}
```

必填：

- `schema = judgment_provider_v1`
- `query_id`
- `allowed_surface`
- `limit`
- `business_context`

`allowed_surface`：

```text
public_hosted | internal
```

`limit` 只能是 `0—5`。`0` 表示当前调用显式禁用返回，不得由 Provider 自行扩大。

`business_context` 是 `EnterpriseDiagnosisCaseV2` 的脱敏兼容投影，必须包含：

- `business_scenes[]`
- `desired_change`
- `current_hypothesis`
- `key_variables[]`
- `exclusions[]`

只有最小生意图、议题组合和 selected focus 已经形成后才生成该投影：`business_scenes[]` 来自允许公开的生意与工作系统类别，`desired_change` 来自当前相关目标，`current_hypothesis` 来自选定工作系统的开放判断。查询只使用脱敏后的经营场景、决策问题和关键变量。不得发送客户名、联系人、聊天全文、订单原文、生产数据、Token、密钥或其他客户 PII。

## Response

```json
{
  "schema": "judgment_provider_v1",
  "query_id": "opaque-query-id",
  "provider_revision": "revision-or-hash",
  "status": "ok",
  "judgments": [
    {
      "judgment_id": "stable-id",
      "title": "一句话判断",
      "applies_when": "适用条件",
      "decision": "经验判断",
      "key_variables": ["变量 A"],
      "change_signals": ["出现什么应改判"],
      "suggested_actions": ["可选的比较动作"],
      "business_scenes": ["企业 AI 提效"],
      "confirmation_status": "confirmed",
      "lifecycle_status": "current",
      "version": "v1",
      "confirmed_at": "2026-01-01T00:00:00+08:00",
      "allowed_surfaces": ["public_hosted", "internal"],
      "content_hash": "sha256:..."
    }
  ]
}
```

Response 必填：

- `schema`
- `query_id`
- `provider_revision`
- `status`
- `judgments[]`

`status`：

```text
ok | degraded | unavailable
```

每条 judgment 必填：

- `judgment_id`
- `title`
- `applies_when`
- `decision`
- `key_variables[]`
- `change_signals[]`
- `suggested_actions[]`
- `business_scenes[]`
- `confirmation_status`
- `lifecycle_status`
- `version`
- `confirmed_at`
- `allowed_surfaces[]`
- `content_hash`

`source_ref` 只允许在 `allowed_surface: internal` 的响应中出现；公共 hosted 响应不得包含私人链接、Base token 或内部定位信息。

`confirmation_status` 当前只接受 `confirmed`。`lifecycle_status` 只能是：

```text
current | superseded | retired
```

确认状态和生命周期必须分开表达。不能用一个 `status` 同时表示“经人工确认”和“当前生效”，否则会误放行“已确认但已过期”或“当前但未确认”的记录。

## Provider 过滤门槛

返回记录必须同时满足：

- 人工确认，`confirmation_status: confirmed`；
- 当前生效，`lifecycle_status: current`；
- `allowed_surfaces[]` 包含本次 request 的 surface；
- 适用条件、关键变量和改判信号完整；
- 不包含客户 PII、凭证或私人原文；
- 可以用 `judgment_id + version + content_hash + provider_revision` 追踪。

接口只接收同时满足 `confirmed + current` 的记录。待校验、冲突、过期、已替代或已退役记录不得为了凑满 limit 返回。

## 诊断引擎使用规则

1. 先形成最小生意图、议题组合和 selected focus，再投影 desired change 与 current hypothesis；Provider 不负责冷启动、生成候选或选择焦点。
2. 同时检查 `applies_when`、`key_variables` 和 `change_signals`，不只按标题相似度采用。
3. 返回项进入 `experience_judgment`，不得改变 reported／observed fact 的来源状态。
4. `suggested_actions` 只是候选；仍须经过公开范围、`interaction.next_move` 和证据充分性检查。
5. 多条判断冲突时保留冲突，不按排名自动裁决。
6. 零命中时继续公共核心；不得强行套用“狼哥方法”。
7. `degraded` 或 `unavailable` 时只在内部状态记录，不向普通用户暴露索引、同步、错误或凭证信息。
8. Presenter 默认拒绝显示 Provider query、命中正文、revision 和 source_ref；用户可见结论必须由客户 claim 独立支撑。

## 失败与降级

| Provider 状态 | 运行行为 |
|---|---|
| `ok` + 有合格命中 | 作为经验镜片参与比较，保存版本追踪 |
| `ok` + 零命中 | 继续公共方法，不补造判断 |
| `degraded` | 只可使用仍明确 `confirmed + current` 的合格项；不描述为最新全量判断 |
| `unavailable` | 完全跳过 Provider，继续公共核心 |

Provider 失败不能改变 AI status，也不能成为向用户索取更多客户信息的理由。

## 与架构设计的关系

本文件是模型运行时 canonical 接口。权威编辑源、同步、只读索引、过期和运维架构见仓库 [docs/enterprise-diagnosis-judgment-provider.md](../../../docs/enterprise-diagnosis-judgment-provider.md)；架构文档不得重新定义一套不同的请求／响应字段。
