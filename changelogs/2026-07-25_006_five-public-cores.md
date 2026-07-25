# 2026-07-25 五个内部能力晋升为公开核心

## 给非技术读者的一句话

Lang Skill 不再只是几个零散入口，新增了从思考、录音、知识沉淀、咨询复盘到视觉表达的一条完整公共能力链。

## 这次做了什么

- 新增 `lang-logic-tracing`、`lang-recording-insight`、`lang-knowledge-system`、`lang-consulting-retro` 和 `lang-poster`。
- 从内部版本重新抽取跨组织成立的方法，没有复制客户、飞书、品牌和本机配置。
- 为每个 Skill 增加三条行为用例；海报增加跨平台导出脚本和公开配置模板。
- 更新公开清单、README、待办和版本号到 `0.7.0`。

## 为什么要做

- 公开仓应该承载真正可复用的方法，而不是内部仓的脱敏镜像。
- 这五个能力能组成“审计逻辑—提取洞察—建立系统—复盘咨询—视觉表达”的连续工作流。
- 内部版后续只叠加组织配置，通用修改统一回到公开上游。

## 具体改了什么

| 文件／模块 | 改动 | 你需要知道的意思 |
|---|---|---|
| `skills/lang-logic-tracing/` | 新增论证审计流程 | 能检查每个“所以”是否真的成立 |
| `skills/lang-recording-insight/` | 新增低噪声录音筛选与按需深挖 | 默认不再把所有录音内容自动灌入知识库 |
| `skills/lang-knowledge-system/` | 新增业务地图驱动的初诊／复诊 | 不给通用模板，结构从实际工作中长出来 |
| `skills/lang-consulting-retro/` | 新增证据化咨询复盘 | 不把点头当满意，不从单一案例直接总结真理 |
| `skills/lang-poster/` | 新增 HTML 海报、导出脚本和视觉规范 | 用户能拿到可编辑源稿和真实导出图 |
| `.gitignore` | 只允许公开 eval 定义、脱敏冒烟结果和固定夹具进入 Git | 调试工作区继续忽略，但回归证据不会被漏掉 |
| `skill-catalog.json`、`README.md`、`VERSION` | 登记能力并升级版本 | 安装和升级流程可以识别这一批新增 Skill |

## 对系统意味着什么

- 五个公共核心成为这些通用方法的唯一公开真身。
- 内部仓通过版本锁加载它们，只维护内部增量。
- 公开标识符继续统一使用英文 `lang-*`。

## 怎么证明没搞坏

收尾时运行：

```bash
node scripts/validate-sharing-system.mjs
./pre-check.sh
python3 -m json.tool skills/<skill>/evals/evals.json
```

实际结果：

- `12` 个公开 Skill 全部完成清单和 frontmatter 校验；
- 敏感扫描 `0` 项泄漏；
- 五个 `evals.json` 均通过 JSON 校验；
- 五个代表性提示均由 Codex CLI 真实加载对应 Skill 执行，退出码全部为 `0`；
- 海报导出脚本通过 Bash 语法检查，并使用最小夹具完成真实 JPG 导出和尺寸验证。

## 还没解决什么

- `docs-init`、PDF 转 Word、视频分析和踩坑记录仍在下一批候选中。
- 公开安装器的 Codex 双端回归仍在待办中。
