# langgeladi — 狼格拉底的ASOP

帮中小企业老板和AI咨询顾问做三件事：诊断客户、定产品、做AI化。

## 一句话安装（交给 AI）

把下面这句话发给你电脑上任何一个能执行命令的 AI 助手（Codex、Claude Code、WorkBuddy、豆包电脑版等）：

```text
帮我安装这套 Skill：https://github.com/YiXinHui/langskill
```

装一次，本机的 Codex、Claude Code、WorkBuddy / CodeBuddy、豆包电脑版和豆包工作模式都能用。装完新开一个对话，输入 `/lang` 或说「用 lang」开始。

### 给 AI 助手的安装步骤

如果你是收到上面这句话的 AI 助手，请在用户本机（不是你自己的沙箱或项目目录）按顺序执行。不管你是哪个助手，都按这套步骤装，不要只装给自己：

1. 运行 `node -v`。没有 Node.js 就停下，把下面「前置条件」告诉用户，不要擅自安装系统软件。
2. 运行 `npx skills add YiXinHui/langskill -g -a codex claude-code -s '*' -y`，把全部 Skill 装到 `~/.agents/skills/`，Codex 与 Claude Code 共用。
3. 再单独运行 `npx skills add YiXinHui/langskill -g -a codebuddy -s '*' -y`，给 WorkBuddy / CodeBuddy 装一份。不要和第 2 步合成一条。
4. 运行 `node ~/.agents/skills/lang-upgrade/scripts/link-extra-agents.mjs`（Windows PowerShell：`node "$HOME\.agents\skills\lang-upgrade\scripts\link-extra-agents.mjs"`），把 Skill 接入豆包电脑版和豆包工作模式。没装豆包时它只报告「没有找到」，属于正常。报告里有 `stale_copy`（旧副本）时加 `--refresh-copies` 重跑；有 `conflict` 时不要删除，原样告诉用户。
5. 检查 `~/.agents/skills/` 下有 `lang`、`lang-think`、`lang-business-diagnosis` 等文件夹，告诉用户装好了哪些助手，并提醒新开对话后用 `/lang` 开始。

## 前置条件

需要 Node.js 环境。Mac 终端安装：

```bash
# 如果没有 brew，先装 brew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装 Node.js
brew install node
```

安装完成后运行 `node -v` 确认有版本号输出。

## 安装

> 2026-10-08 起公开仓采用新的干净历史基线（上一次为 2026-07-25）。通过安装命令使用的用户正常升级即可；此前直接 `git clone` 的开发者请重新 clone，不要把旧本地提交继续合并回新主线。

```bash
# Codex + Claude Code：共用 ~/.agents/skills/ 正文
npx skills add YiXinHui/langskill -g -a codex claude-code -s '*' -y

# 腾讯 WorkBuddy / CodeBuddy：安装到 ~/.codebuddy/skills/
npx skills add YiXinHui/langskill -g -a codebuddy -s '*' -y

# 豆包电脑版 / 豆包工作模式：链接到豆包的技能目录（没装豆包可跳过）
node ~/.agents/skills/lang-upgrade/scripts/link-extra-agents.mjs
```

默认全局安装到共享目录 `~/.agents/skills/`。Codex 直接读取共享目录，Claude Code 通过 `~/.claude/skills/` 软链接读取同一份内容；腾讯 WorkBuddy / CodeBuddy 读取 `~/.codebuddy/skills/`；豆包读取各自 `agent_mode/workspace/.user_skills/` 下指向共享目录的链接（Windows 为目录联接），升级共享目录后豆包同步看到新版。不会在 `~/.codex/skills/` 再建重复入口。需要只给当前项目安装时，去掉 `-g`，对应目录为 `.agents/skills/`、`.claude/skills/` 和 `.codebuddy/skills/`。

安装后每次触发 `/lang` 都会只读检查公开仓的 `VERSION`。发现远端版本领先时，`lang` 会先询问是否升级；只有回复同意后才转入 `/lang-upgrade`，网络失败或版本无法判断不会阻断正常使用。

从 v0.21.0 及更早版本升级时请运行 `/lang-upgrade`。v0.22.0 退役了依赖私人框架的 `lang-wechat-pyq`；仅重新执行安装命令可能保留旧入口，升级流程会备份并核对来源后清理。

## 卸载

```bash
npx skills remove -g
```

在交互列表中选择 `lang` 与 `lang-*` 条目。

## 包含的工具

| 命令 | 工具 | 说明 |
|------|------|------|
| `/lang` | **ASOP 入口** | 路由诊断工具；直接执行个人或公司 Source of Truth 文件体系初始化 |
| `/lang-think` | 狼哥盘认知 | 推理（想法→底层→系统）和推倒（错误认知→翻转→真相） |
| `/lang-upgrade` | 升级 | 升级 langskill 到最新版本 |
| `/lang-skill-iteration` | Skill 反馈迭代 | 从用户真实修改中提取规律并准确迭代 Skill、配置和测试 |
| `/lang-logic-tracing` | 逻辑卡点梳理 | 逐步审计论证，修补跳跃、隐含假设和结论过强 |
| `/lang-recording-insight` | 录音洞察 | 从转写中筛选高价值候选，用户选择后再深挖 |
| `/lang-knowledge-system` | 数字大脑 | 从业务地图、信息流和协作边界设计知识系统 |
| `/lang-knowledge-extraction` | **归纳式经验萃取师** | 首次初始化概念库与判断库，再把聊天截图、录音和文档持续沉淀；按需扩展案例与金句 |
| `/lang-consulting-retro` | 咨询复盘 | 用证据还原咨询转折并沉淀可验证的经验 |
| `/lang-business-diagnosis` | **企业咨询式商业初诊** | 先识别整体扫描、具体业务问题或已有 AI 想法，再还原生意与业务证据，形成有边界的初诊结论和最小验证动作 |
| `/lang-sales-master` | **销售大宗师** | 面向大客户、复杂销售和长周期跟进，基于客户原话与行动判断阶段、成交窗口、风险和下一步 |
| `/lang-poster` | 可编辑海报 | 生成 HTML 海报并导出、检查高清 JPG |
| `/lang-wutai-dialogue` | 五台山论道 | 根据话题推荐跨时代、跨流派思想家，模拟多角色对话与交锋 |
| `/lang-research` | 溯源研究 | 自动编排理论根脉、历史演变、当前结构与交汇判断 |
| `/lang-wechat-writing` | 通用朋友圈写作 | 基于 1—3 份真实来源生成一条可追溯草稿 |
| `/lang-dida` | 滴答清单 | 使用官方 DIDA CLI 查询和管理国内滴答任务、清单、习惯、专注及复盘证据 |
| `/lang-goals` | 个人目标管理 | 在飞书多维表格里管理年、月、周、日目标和日／周／月复盘，按 333 控制每期重点；每日待办确认后推到滴答对应清单 |

只安装“企业咨询式商业初诊”：

```bash
# Codex + Claude Code
npx skills add YiXinHui/langskill -g -a codex claude-code -s lang-business-diagnosis -y

# WorkBuddy / CodeBuddy
npx skills add YiXinHui/langskill -g -a codebuddy -s lang-business-diagnosis -y
```

## 核心理念

- **人只会为自己得出的结论买单** — 诊断通过问对问题，帮助人形成自己的结论
- **私有方法论 > 公开AI智能** — AI是放大器，放大你的强项也放大你的弱项
- **AI系统一定是长出来的** — 先打穿一个点，别想一步到位

## 关于狼格拉底

AI提效大师。意心会创始人，专注为中小企业提供AI智能体咨询、培训和交付。

- 公众号：狼格拉底
- 定位：帮中小企业老板用AI把脑子的价格打下来

## 发布规则

每次推送到 main 之前必须：

1. **改了就 bump VERSION** — 任何 skill 的增删改都必须更新 `VERSION` 文件，否则用户 `/lang-upgrade` 检测不到更新
2. **更新 README 工具表** — 新增/删除 skill 时同步更新上面的表格
3. **版本号规则** — `major.minor.patch`：新增 skill = minor+1，修 bug/微调 = patch+1
4. **更新机器清单** — 新增/删除 skill 时同步更新 `skill-catalog.json`
5. **运行发布检查** — `node scripts/validate-sharing-system.mjs && node scripts/test-cross-platform-install.mjs && ./pre-check.sh`；`pre-check.sh` 扫全仓的本机路径、飞书资源链接、各类 ID、手机号和密钥
7. **私人内容不进公开仓** — 个人配置与个人案例放 `personal-*` / `private-*` 文件（已被 `.gitignore` 排除），公开正文只用虚构案例
6. **统一英文命名** — 主入口保留 `lang`；其他 Skill 的目录名、frontmatter `name` 和调用命令必须使用英文 `lang-*`

设计与内部增强的联动规则见 [docs/DESIGN.md](docs/DESIGN.md)。

## License

MIT
