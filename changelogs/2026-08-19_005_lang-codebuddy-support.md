# LangSkill 支持腾讯 WorkBuddy / CodeBuddy

## 为什么

LangSkill 原先只通过 Codex 与 Claude Code 的共享安装结构发布，腾讯 WorkBuddy / CodeBuddy 无法从自己的 Skill 目录发现完整工具集。

## 改了什么

- 增加 `codebuddy` agent 的安装说明，目标目录为 `~/.codebuddy/skills/` 或项目级 `.codebuddy/skills/`。
- 将 CodeBuddy 安装拆成独立命令，避免与 Codex、Claude Code 合并时被 `skills` 安装器的 universal agent 收敛逻辑漏掉。
- 扩展 `lang-upgrade` 的入口检查、安装步骤、交付格式和回归评测。
- 扩展跨平台安装测试，验证 Codex、Claude Code 和 CodeBuddy 均能发现完整 Skill 清单。

## 验证

- `node scripts/validate-sharing-system.mjs`
- `node scripts/test-cross-platform-install.mjs`
- `./pre-check.sh`
