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

```bash
npx skills add YiXinHui/langskill --skill '*' --agent claude -y
```

只安装到 `.claude/skills/` 目录，不会生成其他 AI 编辑器的垃圾目录。安装时会提示选择安装目录（全局 `~/.claude/` 或当前项目），按需选择即可。

## 卸载

```bash
npx skills remove YiXinHui/langskill
```

## 包含的工具

| 命令 | 工具 | 说明 |
|------|------|------|
| `/lang` | **路由入口** | 自动分发到最合适的诊断工具 |
| `/lang-think` | 狼哥盘认知 | 推理（想法→底层→系统）和推倒（错误认知→翻转→真相） |
| `/lang-upgrade` | 升级 | 升级 langskill 到最新版本 |
| `/五台山论道` | 东方论道 | 根据话题推荐东方思想家，模拟多角色对话与交锋 |

## 核心理念

- **人只会为自己得出的结论买单** — 诊断不是给答案，是帮人问对问题
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

## License

MIT
