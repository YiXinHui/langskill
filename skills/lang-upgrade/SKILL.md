---
name: lang-upgrade
description: 升级或修复 LangSkill 的全局安装，并把旧 Claude 单端安装、分散软链接和重复 Codex 入口收敛到 ~/.agents/skills 共享结构。用户说“升级 langskill”“修复 langskill 安装”“让 Codex 和 Claude Code 都能调用”时使用。
---

# lang-upgrade

把 LangSkill 升级到最新公开版本，同时保持 Codex 与 Claude Code 使用同一份正文。

## 目标结构

```text
~/.agents/skills/<name>          共享入口，Codex 直接发现
        ↓
~/.claude/skills/<name>          指向共享入口的软链接
```

Codex 已直接扫描 `~/.agents/skills/`，不要再创建 `~/.codex/skills/<name>`。全局入口存在后，也不要在 Desktop 或当前项目中重复映射同一个 LangSkill。

公开仓 `skill-catalog.json` 是完整 Skill 清单。不要手写一份长期维护的名称数组。

## 升级流程

### 1. 恢复清单与远端版本

从公开仓读取：

- `skill-catalog.json`
- `skill-renames.json`
- `VERSION`

网络不可用或任一文件解析失败时停止，不改变本地安装。下载内容放在 `mktemp -d` 创建的临时目录，不放进 Skill 发现根。

### 2. 判断当前模式

检查 `~/.agents/skills/lang`、`~/.claude/skills/lang` 和 `~/.codex/skills/lang`，对已有入口执行 `realpath`。

分为三种状态：

1. **开发仓映射**：共享入口是软链接，目标位于含 `.git`、`skill-catalog.json` 和 `skills/lang/` 的仓库。
2. **统一安装**：共享入口存在，Claude Code 指向共享入口，Codex 没有重复入口。
3. **旧安装或未安装**：只有 Claude Code 入口、入口散落在多个目录，或尚未安装。

同名路径如果是独立实体且内容与目标不同，停止并报告冲突，不覆盖、不合并。

### 3. 保护开发仓

开发仓是当前机器的正文权威，不得用下载副本覆盖。

- 工作树有未提交修改时停止，列出状态，保留现有映射。
- 当前分支不是 `main` 时停止，不擅自切分支。
- 工作树干净且位于 `main` 时，才执行 `git pull --ff-only`。
- 拉取后运行仓内 `node scripts/validate-sharing-system.mjs`、`node scripts/test-cross-platform-install.mjs` 和 `./pre-check.sh`。
- 按最新 `skill-catalog.json` 补齐 `~/.agents/skills/` 与 `~/.claude/skills/` 入口；新增入口指向同一开发仓，不复制正文。

任一验证失败都保留工作树和现有映射，报告失败，不宣布升级完成。

### 4. 备份普通安装

普通安装或旧安装升级前，把清单内现有入口和旧名称保存到：

```text
~/.agents/backups/langskill-YYYYMMDD-HHMMSS/
```

备份清单、解析后的真实目标和 `~/.agents/.langskill-version`。只处理公开仓清单与改名表声明的名称，不使用 `lang*` 通配符删除其他内容。

### 5. 通过统一安装器收敛

旧安装、缺失映射或有新版本时执行：

```bash
npx skills add YiXinHui/langskill -g -a codex claude-code -s '*' -y
```

这条命令负责把全部正文安装到 `~/.agents/skills/`，并为 Claude Code 建立指向共享入口的软链接。不要把 Codex 安装成第二份实体。

安装成功后：

1. 按 `skill-renames.json` 处理旧名称；只删除清单声明的旧入口。
2. 如果 `~/.codex/skills/<name>` 是指向同一共享正文的软链接，移除这个重复入口。
3. 如果 `~/.codex/skills/<name>` 是独立目录或指向其他内容，保留并报告冲突。
4. 把远端版本写入 `~/.agents/.langskill-version`。

如果本地版本与远端一致，但清单不完整、双端不可见或存在重复入口，仍需执行收敛；只有“版本一致 + 结构正确 + 验证通过”才能直接结束。

### 6. 验证

必须同时通过：

1. `skill-catalog.json` 中每个 Skill 的 `~/.agents/skills/<name>/SKILL.md` 可读。
2. Claude Code 入口解析到同一共享正文。
3. Codex 没有同名 `~/.codex/skills/` 重复入口。
4. `npx skills list -g -a codex --json` 包含完整清单。
5. `npx skills list -g -a claude-code --json` 包含完整清单。
6. 同一平台、同一 `name` 只出现一次。

全局 Skill 较多时，列表 JSON 可能超过终端输出上限。先写入 `mktemp -d` 下的临时文件，再用 `jq` 按 `skill-catalog.json` 过滤；验证后删除临时目录，不把测试文件放进 `~/.agents/skills/`。

### 7. 失败恢复

安装或验证失败时，只恢复备份清单中属于 LangSkill 的入口。不要删除整个 `~/.agents/skills/`、`~/.claude/skills/` 或 `~/.codex/skills/`。

恢复后再次检查 `SKILL.md` 可读性，并报告：失败步骤、已恢复入口、仍需人工处理的冲突和备份位置。

## 交付格式

```text
LangSkill {旧版本或 unknown} → {新版本}
共享入口：{数量}/{清单数量}
Codex：{可见数量}/{清单数量}
Claude Code：{可见数量}/{清单数量}
重复入口：{0 或明细}
备份：{路径或未创建}
结果：已升级 / 已是最新 / 因冲突未改动 / 已恢复
```

没有完成双端清单验证时，不报告“升级完成”。
