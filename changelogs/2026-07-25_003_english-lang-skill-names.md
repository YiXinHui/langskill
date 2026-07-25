# 2026-07-25 公开 Skill 统一使用英文 lang-* 名称

## 给非技术读者的一句话

langskill 的公开入口现在有一套稳定、可识别的英文命名，安装、调用和后续开源分享不再混用中文目录与旧名称。

## 这次做了什么

- 将 4 个旧公开标识改为英文 `lang-*` 名称。
- 把公开命名规则写入设计文档和自动检查，防止以后重新混入中文 Skill 标识。
- 增加旧名迁移表，升级时自动清理旧目录，避免新旧入口并存。

## 为什么要做

- 公开 Skill 的目录名、调用命令和机器标识混用中英文，会提高安装、分享和跨平台调用成本。
- `feedback` 只表达“反馈”，没有覆盖“把反馈变成下一版能力”的完整动作；`iteration` 更准确。
- 只改目录而不处理升级迁移，会让老用户机器上同时留下两个版本。

## 具体改了什么

| 文件/模块 | 改动 | 你需要知道的意思 |
|---|---|---|
| `skills/lang-skill-iteration/` | 原 `lang-skill-feedback` 改名 | 公开反馈迭代入口改为 `/lang-skill-iteration` |
| `skills/lang-wutai-dialogue/` | 原中文目录改名 | 产品中文名仍叫“五台山论道”，机器标识统一英文 |
| `skills/lang-evolution-structure/` | 原中文目录改名 | 演变—结构研究获得稳定英文调用名 |
| `skills/lang-wechat-moments/` | 原中文目录改名 | 狼格拉底朋友圈获得稳定英文调用名 |
| `skill-renames.json`、`lang-upgrade` | 新增旧名清理机制 | 老用户升级后不会残留 4 个旧目录 |
| `scripts/validate-sharing-system.mjs` | 强制目录、清单、frontmatter 同名且符合 `lang-*` | 命名规范从文档要求变成发布门禁 |
| `README.md`、`docs/DESIGN.md`、`skill-catalog.json` | 同步用户入口、设计与机器清单 | 人读文档和系统读配置保持一致 |
| `VERSION` | `0.5.1` 升至 `0.6.0` | 本次包含公开命名迁移，按 0.x 版本规则发布 minor 版本 |

## 对系统意味着什么

- `lang` 继续作为总路由的唯一保留名，其余公开 Skill 必须使用英文 `lang-*`。
- 中文产品名仍可用于标题、说明和自然语言触发，不再承担目录和机器标识职责。
- 下游内部增强层可继续依赖公开核心，但必须锁定新的 `lang-skill-iteration`。

## 怎么证明没搞坏

```bash
node scripts/validate-sharing-system.mjs
./pre-check.sh
git diff --check
node -e '/* 解析 4 份 JSON */'
node -e '/* 在临时目录模拟旧名清理与新版复制 */'
```

结果：

- `7` 个公开 Skill 全部通过清单、英文命名、frontmatter 和目录一致性检查。
- 敏感信息扫描为 `0` 条残留。
- `4` 份关键 JSON 均可解析。
- 临时升级验证确认 `4` 个旧目录被清理，最终只保留 `7` 个当前 Skill。
- `git diff --check` 通过。

## 还没解决什么

- 旧名称仍会保留在历史 changelog 和迁移表中，这是兼容与审计需要，不代表仍可作为当前入口使用。
- 完整模型行为 benchmark 未重跑；本次修改的是标识、路由和升级机制，原有方法正文未发生实质变化。

## 技术细节

- 当前映射：`lang-skill-feedback` → `lang-skill-iteration`、`五台山论道` → `lang-wutai-dialogue`、`演变-结构研究` → `lang-evolution-structure`、`狼哥朋友圈` → `lang-wechat-moments`。
