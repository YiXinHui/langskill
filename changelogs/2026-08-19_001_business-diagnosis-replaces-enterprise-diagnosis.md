# 企业咨询出诊入口切换

## 做了什么

- 将 `lang-business-diagnosis` 定为当前企业咨询式商业初诊入口，覆盖原企业 AI 诊断的公开路由。
- 将旧 `lang-enterprise-ai-diagnosis` 完整移入 `archive/lang-enterprise-ai-diagnosis-2026-08-19/`，并把旧 `SKILL.md` 改为 `SKILL.archived.md`，保留历史参考和评测但取消可发现入口。
- 更新 `/lang` 路由、README、Skill 清单、版本号和共享结构校验；旧名称通过 `skill-renames.json` 迁移到新入口。
- 本机共享 Skill 入口切换到 `lang-business-diagnosis`，Claude Code 继续通过共享软链发现同一实体。

## 版本与迁移

- `VERSION`：`0.15.0` → `0.16.0`
- 当前入口：`/lang-business-diagnosis`
- 旧入口：`/lang-enterprise-ai-diagnosis`，升级时迁移到 `lang-business-diagnosis`
