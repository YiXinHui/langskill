# 2026-07-30 增加企业 AI 提效初诊

## 给非技术读者的一句话

企业老板现在可以免费用一轮结构化问答，先看清最值得核验的业务断点，再决定是否进入正式企业 AI 化诊断。

## 这次做了什么

- 新增公开产品 `lang-enterprise-ai-diagnosis`，中文产品名为“狼哥 AI 提效诊断分身”。
- 从近期真实业务事件出发，逐步还原工作链、单点依赖、经营影响和候选起点。
- 输出《企业 AI 提效初筛报告》，并在用户明确同意后生成正式诊断交接包。
- 将新产品加入 `/lang` 路由、README、机器清单和版本体系。

## 为什么要做

- “简单问答直接给完整解决方案”会越过真实操作、数据、责任人和反馈证据，容易把售前体验包装成正式结论。
- 一个好的免费产品应先让用户获得可独立使用的判断和资料清单，同时为正式诊断减少重复沟通。
- 公开方法与商业服务并不冲突：公开层负责发现和准备，正式服务负责取证、决策与落地。

## 具体改了什么

| 文件／模块 | 改动 | 你需要知道的意思 |
|---|---|---|
| `skills/lang-enterprise-ai-diagnosis/` | 新增主流程、对话规则、报告与交接契约 | 初筛和正式诊断的承诺分开 |
| `skills/lang/SKILL.md` | 新增企业 AI 初诊路由 | 用户不需要记新命令 |
| `README.md`、`skill-catalog.json` | 登记新公开产品 | 安装和机器清单保持一致 |
| `scripts/validate-sharing-system.mjs` | 增加公开初诊专属结构检查 | 报告、交接和同意门槛不会被后续误删 |
| `VERSION` | `0.8.1` 升级为 `0.9.0` | 新增产品按 minor 版本发布 |
| `docs/DESIGN.md`、`docs/TODO.md` | 记录公开初诊与正式服务的分层和后续验证 | 当前架构和待办有唯一入口 |

## 对系统意味着什么

- 公开 Skill 能独立创造价值，但不会把用户自述伪装成正式诊断。
- 售前信息可以通过稳定交接格式进入正式流程，不需要重复填写，也不会自动写入客户系统。
- 产品表达从“完整解决方案”校准为“初筛报告 + 正式诊断衔接”，长期信任边界更清楚。

## 怎么证明没搞坏

```bash
python3 skills/lang-enterprise-ai-diagnosis/evals/run_static_checks.py
python3 -m json.tool skills/lang-enterprise-ai-diagnosis/evals/evals.json
node scripts/validate-sharing-system.mjs
./pre-check.sh
git diff --check
```

结果：

- 公开 Skill 静态检查：`3 references, 6 evals`，通过；
- 公开仓分享系统：`14 public skills`，结构检查通过；
- 发布前敏感词扫描：无残留；
- JSON 语法和 `git diff --check`：通过；
- 1 个匿名高区分度场景完成启用／不启用行为对照，启用后守住角色主张、产品候选和正式诊断边界，详见 `skills/lang-enterprise-ai-diagnosis/evals/2026-07-30_behavior-comparison.md`。

## 还没解决什么

- 尚未验证用户在不同输入完整度下的完成率和正式诊断转化率。
- 当前只生成可审核的交接包，不自动收集联系方式或写入外部客户系统。
