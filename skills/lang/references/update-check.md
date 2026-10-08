# LangSkill 加载时更新检查

这份 reference 只负责 `lang` 主入口的启动检查和确认交接。升级施工仍由 `lang-upgrade` 唯一负责。

## 启动顺序

在解释用户问题、展示菜单或路由前，每次执行一次以下检查：

1. 从当前已加载的 `lang` Skill 目录执行 `scripts/check-remote-update.mjs`。
2. 优先使用宿主能解析到的当前 Skill 实际路径；全局共享安装通常是 `~/.agents/skills/lang/scripts/check-remote-update.mjs`。
3. 读取脚本输出的 JSON，不执行 `git pull`、`git fetch`、安装器或任何写操作。

脚本比较本地版本与公开仓 `YiXinHui/langskill` 的 `main/VERSION`。仓库发布规则要求任何 Skill 改动都更新 `VERSION`，因此不需要逐文件下载来判断是否有更新。

## 状态处理

| 脚本状态 | 处理 |
|---|---|
| `update_available` | 暂停当前路由，询问用户是否现在升级 |
| `up_to_date` | 静默继续当前工作 |
| `local_ahead` | 静默继续；这通常表示本地开发仓领先于公开仓 |
| `local_version_unknown` | 静默继续，不把未知版本当成可升级 |
| `check_unavailable` / `invalid_remote_version` | 静默继续，不让网络或远端格式问题阻断使用 |

发现更新时只发出一条确认：

```text
发现 LangSkill 有新版本：v{remote_version}（当前 v{local_version}）。要现在升级吗？回复“更新”开始，或“稍后”继续当前问题。
```

在用户回复确认的下一轮：

- “更新”“现在更新”“好，更新”等明确肯定表示同意，直接执行 `/lang-upgrade`，不要再次询问同一个确认；
- “稍后”“暂不更新”“不用”等表示暂缓，继续处理用户原本的问题，本轮不再次检查；
- 其他回答先按对更新确认的最小澄清处理，仍只允许补问一次。

## 安全边界

- 远端版本检查是只读动作，超时或网络不可用不影响 `lang` 的正常路由。
- 只有用户明确同意后，才启动 `lang-upgrade` 的本地写入、备份、安装和验证流程。
- 不在 `lang` 中复制 `lang-upgrade` 的升级实现，也不直接覆盖 `~/.agents/skills/`、`~/.claude/skills/`、`~/.codebuddy/skills/` 或开发仓。
- 更新成功后，当前已加载的旧正文不会在同一轮自动替换；升级流程完成后重新触发 `lang`，再继续原问题，确保使用新正文。
