# 2026-08-01 企业诊断方法源与旧工作区收尾

## 给非技术读者的一句话

企业 AI 提效诊断现在只认 `langgeladi/main` 下的正式 Skill 为方法源，使用说明也不再让人误以为必须被连续追问三轮。

## 这次做了什么

- 核对正式仓库、旧 Worktree、合并历史和当前公开版本。
- 将用户入口和设计文档的“最多追问 3 轮”精确为“最多处理 3 次用户回答”。
- 保留旧 Worktree 复核现场，等用户看完清场清单后再删除。

## 为什么要做

- `langgeladi-enterprise-diagnosis-v2` 是同一 Git 仓库的历史开发 Worktree，不是第二份正式 Skill。
- “追问 3 轮”会把回合上限误解为必答问卷，与现役 Skill 允许跳阶段和提前交付的事实不符。

## 具体改了什么

| 文件/模块 | 改动 | 你需要知道的意思 |
|---|---|---|
| `README.md` | 把企业诊断的使用承诺改成“最多回答 3 次” | 与实际回合预算一致 |
| `docs/DESIGN.md` | 同步精确回合边界 | 设计文档不再传播旧口径 |

## 对系统意味着什么

- 正式方法源仍是 `skills/lang-enterprise-ai-diagnosis/`，没有修改 Skill 正文、版本号或公开运行行为。
- 旧分支提交已以 squash 方式进入 v0.10.1，v0.10.2 又继续增加了角色与自由回答入口。

## 怎么证明没搞坏

```bash
git diff --check
node scripts/validate-sharing-system.mjs
./pre-check.sh
```

结果：14 个公开 Skill 结构校验通过，敏感词预扫描无残留，文档差异无空白错误。`git cherry -v origin/main codex/enterprise-diagnosis-v0101` 将旧提交标为 `-`，且旧分支树与 v0.10.1 合并结果无内容差异。

## 清场结果

- 用户在完整清场报告后明确确认删除旧 Worktree 和过程评测目录。
- 已删除 `langgeladi-enterprise-diagnosis-v2`；其中 620 个被 Git 忽略的历史评测文件随 Worktree 删除，已提交、已合并的方法历史继续保留在 `main` 和 GitHub PR 中。
- 正式 Skill 仓只保留 `langgeladi/main`；本地和远端过程分支均已删除。
- `lang-wechat-writing-workspace/`、`lang-wutai-dialogue-workspace/`、`.DS_Store` 和未被 Git 使用的 `.git/index 2` 已移入系统废纸篓，可在清空废纸篓前恢复。

## 还没解决什么

- 无。
