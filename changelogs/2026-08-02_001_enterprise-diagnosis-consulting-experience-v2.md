# 2026-08-02 企业 AI 初诊改成动态咨询体验

## 给非技术读者的一句话

企业 AI 初诊现在会根据用户真实信息动态推进和停止，先形成经营判断，再决定 AI 是否值得进入；它不再靠固定三轮、固定字数和反复引流制造完成感。

## 这次做了什么

- 将 `lang-enterprise-ai-diagnosis` 从固定回合初诊卡重构为“公共诊断核心 + 动态咨询对话 + 结果／呈现／交接契约”。
- 建立业务优先的经营六镜、证据与纠正状态、方法注册表，以及允许“不做 AI”的四类结果。
- 增加受众默认拒绝、敏感信息、交接授权分离和可选私人判断 Provider 契约。
- 新增 18 个咨询体验场景，使评测从 36 个增至 54 个；保留事实闸门的原始失败、相邻泛化和合法例外。
- 增加真实老板三人试诊模板和首轮汇总门槛，明确真实结果不得用模型模拟填充。

## 为什么要做

- 旧版把“最多三次回答、第四个用户回合截止、一次样本更新、固定字符数”当成产品边界，容易让对话为了计数收敛，而不是为了帮助用户做决定。
- 旧结构偏向 IT 和 AI 场景识别，对企业如何创造价值、内部怎样做决定、非 AI 选项是否更优的分析不足。
- 主 Skill 重复罗列大量变化快的方法与模板，路由、方法、状态和对外呈现没有稳定分层。
- 对外结果缺少统一的受众投影和反差句式准入，内部逻辑、私人判断和服务转化有泄露风险。

## 具体改了什么

| 文件／模块 | 改动 | 你需要知道的意思 |
|---|---|---|
| `skills/lang-enterprise-ai-diagnosis/SKILL.md` | 缩成稳定职责、读取路由、权威优先级和运行边界 | 主 Skill 只保留不常变的产品内核，不再重复展开全部方法 |
| `references/core/` | 新增诊断核心、状态与证据、方法注册表 | 经营问题、事实来源、纠正和方法许可有独立权威层 |
| `conversation-guide.md` | 改为镜映—判断—一问、动态收敛、疲劳、暂停／恢复和材料范围协议 | 用户不再被固定题数或问卷拖着走，每个问题都必须能改变判断 |
| `report-contract.md` | 升级为 `DiagnosisResultV2` | 结果用声明 ID 追溯判断，AI 可以进入、后置、让位给非 AI 或暂不判断 |
| `presentation-contract.md` | 新增 `DiagnosisPresenterV1`、受众默认拒绝、用户可见禁词和反差句式准入 | 老板与客户只看到有权限且能帮助决策的内容，内部状态和假专业修辞默认删除 |
| `handoff-contract.md` | 升级为 `enterprise_ai_diagnosis_handoff_v2` | 审核、导出和外发分别授权，允许导出不等于允许发送 |
| `judgment-provider-contract.md` 与宿主架构文档 | 定义公共／内部 surface、零命中降级及 `confirmed + current` 双重过滤 | 私人判断可以增强内部宿主，但不进入公开仓，也不能冒充客户事实 |
| `evals/evals.json` 与静态检查 | 新增 18 个 UX 场景并把契约检查扩展到 300 项 | 模糊入口、长输入、纠正、冲突、疲劳、暂停、导出、敏感信息和 Provider 降级均有回归入口 |
| `docs/enterprise-ai-diagnosis-pilot-template.md` | 增加单人记录和三人汇总页 | 首轮真实验收有明确样本、六项硬门槛和量化计算口径 |
| `README.md`、`docs/DESIGN.md`、`docs/TODO.md`、`VERSION` | 同步产品口径、公开／内部组合架构、外部验收门槛和 `0.11.0` 版本 | 使用说明、当前设计、待办与发布版本保持一致 |

## 对系统意味着什么

- 公开版和内部版不再建议各复制一套 Skill；公共仓维护通用核心和契约，内部宿主通过 Provider、正式诊断流程与客户系统适配扩展。
- 对话是否继续由决策增量和用户状态决定，回合数只能用于分析体验，不能强制终止或继续。
- 所有用户可见角色、数字、因果、范围和 AI 工作画面都必须可追溯；用户纠正的内容没有新证据不得复活。
- `audiences[]` 缺失时默认 `internal_only`，未知受众默认拒绝；`source_ref`、Provider 命中和内部推理不进入公共呈现。
- 判断 Provider 只接收同时 `confirmation_status: confirmed` 与 `lifecycle_status: current` 的记录；零命中、降级或不可用不阻断公共诊断。

## 怎么证明没搞坏

```bash
python3 skills/lang-enterprise-ai-diagnosis/evals/run_static_checks.py
```

结果：`300 checks passed`，覆盖 8 份运行时 reference、54 个连续评测场景和三人真实试诊门槛。

```bash
node scripts/validate-sharing-system.mjs
```

结果：`14 public skills are catalogued and structurally valid`。

```bash
python3 /Users/lang/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/lang-enterprise-ai-diagnosis
```

结果：`Skill is valid!`。

```bash
./pre-check.sh
```

结果：公开发布敏感词扫描无残留。

```bash
python3 -m json.tool skills/lang-enterprise-ai-diagnosis/evals/evals.json
git diff --check
```

结果：评测 JSON 合法，补丁没有空白错误。

只读模型烟测结果见 `skills/lang-enterprise-ai-diagnosis/evals/2026-08-02_dynamic-consulting-ux_smoke-results.md`：3 个高区分场景、16 条断言，结果 `16/16`。

## 还没解决什么

- 真实咨询体验尚未通过外部验收。必须由恰好 3 位、且来自 3 种不同业务类型的真实老板／管理者填写试诊模板；当前所有结果栏保持空白。
- 只完成 3／54 个场景的一次性模型烟测，其余场景目前是契约与回归定义，不能声称全量行为 benchmark 已通过。
- Provider 只定义运行契约和宿主架构，公开仓没有实现飞书同步、运行索引或内部判断正文。
- 正式诊断、客户建档、发送、预约、实施和成交规则继续留在内部增强层，不属于本次公开仓改动。

## 技术细节

- 新 schema：`enterprise_ai_diagnosis_state_v1`、`enterprise_ai_diagnosis_result_v2`、`enterprise_ai_diagnosis_presenter_v1`、`enterprise_ai_diagnosis_handoff_v2`、`judgment_provider_v1`。
- canonical AI 状态：`validation_candidate | foundation_first | non_ai_priority | insufficient_evidence`。
- canonical 受众：`internal_only | consultant_only | owner_visible | client_visible | exportable`；不再使用单一 `visibility` 字段。
- 旧 `sample_supported` 只读迁移为 `source_unavailable + unverified`，绝不升级为 AI 已观察事实。
