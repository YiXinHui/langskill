# 2026-08-02 LangSkill 全量接入全局共享目录

## 给非技术读者的一句话

LangSkill 的 14 个公开能力现在由 Codex 和 Claude Code 读取同一份正文，后续安装与升级也会继续保持这套结构。

## 修改请求

用户发现全局 `~/.agents/skills/` 没有完整的 LangSkill 映射，要求全量映射，而不是只修补单个 Skill。

## 执行计划

1. 以 `skill-catalog.json` 盘点完整清单和同名冲突。
2. 建立共享入口与 Claude Code 入口，移除 Codex 和 Desktop 重复入口。
3. 修正公开安装说明与 `lang-upgrade`，避免后续升级恢复旧结构。
4. 增加跨平台真实安装回归和升级场景 eval。
5. 验证本机映射、双端发现、仓库结构和公开信息边界。

## 这次做了什么

- 将机器清单中的 14 个 LangSkill 全部映射到 `~/.agents/skills/`，入口直接指向本地公开仓正文。
- 为 Claude Code 建立 14 个指向共享层的全局软链接。
- 移除 6 个已经被共享层替代的旧软链接，避免同一 Skill 在 Codex 或 Desktop 工作区重复发现。
- 把 README 和 `lang-upgrade` 从 Claude 单端安装改成 Codex、Claude Code 双端统一安装。
- 增加真实临时目录安装测试和 3 个升级回归场景。

## 为什么要做

- 旧结构来自不同时间的手工映射：部分入口在 `~/.claude`，部分在 `~/.codex`，只有企业 AI 诊断进入了 `~/.agents`。
- 只补当前软链接无法解决长期问题；旧 `lang-upgrade` 会再次把内容复制回 Claude Code 目录，重新产生多份正文。
- 机器清单已有 14 个 Skill，安装与发现应该由清单驱动，不再靠人工逐个记名称。

## 具体改了什么

| 文件/模块 | 改动 | 你需要知道的意思 |
|---|---|---|
| `~/.agents/skills/<14 个 Skill>` | 全量软链接到本仓 `skills/<name>/` | 项目仓继续是唯一正文，Codex 直接读取共享入口 |
| `~/.claude/skills/<14 个 Skill>` | 全部指向 `../../.agents/skills/<name>` | Claude Code 与 Codex 使用同一份内容 |
| `~/.codex/skills/`、Desktop Skill 目录 | 移除 6 个同目标旧软链接 | 同一 Skill 在同一宿主不再重复显示 |
| `README.md` | 安装命令改为 `-g -a codex claude-code -s '*'` | 新用户默认获得双端全量安装 |
| `skills/lang-upgrade/SKILL.md` | 重写升级、迁移、冲突保护、验证和恢复边界 | 旧 Claude 单端安装会收敛到共享结构；有未提交改动的开发仓不会被覆盖 |
| `skills/lang-upgrade/evals/evals.json` | 增加旧安装迁移、脏开发仓保护、已是最新三个场景 | 防止升级逻辑重新退回单端或覆盖开发源码 |
| `scripts/test-cross-platform-install.mjs` | 在临时目录调用统一安装器并检查双端发现 | 发布前可以真实验证 14 个 Skill 的安装拓扑 |
| `scripts/validate-sharing-system.mjs` | 增加安装命令、升级边界和 eval 门禁 | 安装说明和升级 Skill 以后不能无声漂移 |
| `docs/DESIGN.md`、`docs/TODO.md` | 固化共享架构并关闭对应待办 | 当前设计与实际状态一致 |
| `VERSION` | `0.11.0` 升至 `0.11.1` | 本次属于分发与升级修复 |

## 对系统意味着什么

- 全局正文路径统一为 `~/.agents/skills/<name>`。
- Codex 直接扫描共享目录，不再额外创建 `~/.codex/skills/<name>`。
- Claude Code 只保留一个指向共享层的全局入口。
- 开发机入口继续指向 Git 项目仓；公开安装用户由统一安装器维护共享实体和锁文件。
- 已经启动的宿主任务可能继续使用启动时的 Skill 快照，新开任务后会读取完整清单。

## 怎么证明没搞坏

```bash
node scripts/validate-sharing-system.mjs
node scripts/test-cross-platform-install.mjs
python3 /Users/lang/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/lang-upgrade
./pre-check.sh
git diff --check
```

结果：

- 本机映射检查：`14 checked, 0 failures`。
- `npx skills list -g -a codex --json`：命中 `14/14`。
- `npx skills list -g -a claude-code --json`：命中 `14/14`。
- 仓库结构检查：`14 public skills` 全部有效。
- 临时目录真实安装：`14` 个 Skill 通过一个共享根安装，Codex 与 Claude Code 全部可发现。
- `lang-upgrade` 快速校验：通过。
- 敏感信息扫描：`0` 条残留。
- `git diff --check`：通过。

## 还没解决什么

- 本次没有提交、推送或发布公开版本。
- 仓库中原有的企业 AI 诊断未提交改动继续保留，本次没有回退或覆盖。
- 当前已打开的 Codex／Claude Code 任务不会动态刷新启动清单，需要新开任务查看完整菜单。

## 技术细节

- 移除的 6 个旧入口均为指向本仓的软链接：Desktop Claude Code 的 `lang`、`lang-think`、`lang-upgrade`，全局 Codex 的 `lang-skill-iteration`、`lang-enterprise-ai-diagnosis`，以及 Desktop Codex 的 `lang-skill-iteration`。
- 没有手工修改 `~/.agents/.skill-lock.json`；开发机映射保持 `source: local`，公开安装仍由统一安装器登记来源。
