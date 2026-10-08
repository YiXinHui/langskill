# LangSkill v0.27.0：一句话安装，豆包也能用

把 `帮我安装这套 Skill：https://github.com/YiXinHui/langskill` 发给任何能在本机执行命令的 AI 助手，就能装好，本机各助手共用一份正文。起因：学员把课上的安装提示词发给豆包，豆包回复“不是一个环境”，建议改装 Codex；原有安装命令只覆盖 Codex、Claude Code、WorkBuddy / CodeBuddy。

- README 顶部新增「一句话安装（交给 AI）」和「给 AI 助手的安装步骤」，收到仓库链接的助手按同一套步骤装到用户本机，不只装给自己。
- 新增 `lang-upgrade/scripts/link-extra-agents.mjs`：自动发现豆包电脑版、豆包工作模式的 `agent_mode/workspace/.user_skills/`，为共享根下的 `lang`、`lang-*` 建指向 `~/.agents/skills/` 的链接（Windows 用目录联接），升级共享目录后豆包同步看到新版。已有指向别处或非 LangSkill 的同名内容保留并报告冲突；旧的 LangSkill 实体副本只在 `--refresh-copies` 时先备份再换链接；支持 `--dry-run`。
- `lang-upgrade` 安装后补跑链接脚本，验证项和交付格式加入豆包。
- 回归：安装测试在模拟的豆包、豆包工作目录上验证全部 Skill 链接到共享入口且复跑幂等；共享校验新增 README 一句话入口与链接命令检查；`lang-upgrade` 用例新增 1 条（豆包安装）。
