# langgeladi — 狼格拉底的ASOP

帮中小企业老板和AI咨询顾问做三件事：诊断客户、定产品、做AI化。

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

> 2026-07-25 起公开仓采用新的干净历史基线。通过安装命令使用的用户正常升级即可；此前直接 `git clone` 的开发者请重新 clone，不要把旧本地提交继续合并回新主线。

```bash
npx skills add YiXinHui/langskill -g -a codex claude-code -s '*' -y
```

默认全局安装到共享目录 `~/.agents/skills/`。Codex 直接读取共享目录，Claude Code 通过 `~/.claude/skills/` 软链接读取同一份内容；不会在 `~/.codex/skills/` 再建重复入口，也不会生成其他 AI 编辑器目录。需要只给当前项目安装时，去掉 `-g`。

## 卸载

```bash
npx skills remove -g
```

在交互列表中选择 `lang` 与 `lang-*` 条目。

## 包含的工具

| 命令 | 工具 | 说明 |
|------|------|------|
| `/lang` | **路由入口** | 自动分发到最合适的诊断工具 |
| `/lang-think` | 狼哥盘认知 | 推理（想法→底层→系统）和推倒（错误认知→翻转→真相） |
| `/lang-upgrade` | 升级 | 升级 langskill 到最新版本 |
| `/lang-skill-iteration` | Skill 反馈迭代 | 从用户真实修改中提取规律并准确迭代 Skill、配置和测试 |
| `/lang-logic-tracing` | 逻辑卡点梳理 | 逐步审计论证，修补跳跃、隐含假设和结论过强 |
| `/lang-recording-insight` | 录音洞察 | 从转写中筛选高价值候选，用户选择后再深挖 |
| `/lang-knowledge-system` | 数字大脑 | 从业务地图、信息流和协作边界设计知识系统 |
| `/lang-consulting-retro` | 咨询复盘 | 用证据还原咨询转折并沉淀可验证的经验 |
| `/lang-enterprise-ai-diagnosis` | **狼格拉底企业 AI 提效诊断** | 先选择整体扫描、具体业务问题或已有 AI 想法，再理清生意、职责和复合目标，比较值得先看的工作系统并形成最小验证 |
| `/lang-poster` | 可编辑海报 | 生成 HTML 海报并导出、检查高清 JPG |
| `/lang-wutai-dialogue` | 五台山论道 | 根据话题推荐跨时代、跨流派思想家，模拟多角色对话与交锋 |
| `/lang-research` | 溯源研究 | 自动编排理论根脉、历史演变、当前结构与交汇判断 |
| `/lang-wechat-pyq` | 狼格拉底朋友圈 | 规划每日朋友圈内容、文案与配图 |
| `/lang-wechat-writing` | 通用朋友圈写作 | 基于 1—3 份真实来源生成一条可追溯草稿 |

只安装“狼哥 AI 提效诊断分身”：

```bash
npx skills add YiXinHui/langskill -g -a codex claude-code -s lang-enterprise-ai-diagnosis -y
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
5. **运行发布检查** — `node scripts/validate-sharing-system.mjs && node scripts/test-cross-platform-install.mjs && ./pre-check.sh`
6. **统一英文命名** — 主入口保留 `lang`；其他 Skill 的目录名、frontmatter `name` 和调用命令必须使用英文 `lang-*`

设计与内部增强的联动规则见 [docs/DESIGN.md](docs/DESIGN.md)。

## License

MIT
