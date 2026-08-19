# lang 加载时更新检查

## 为什么

LangSkill 用户通常只触发 `/lang`，容易错过已经发布的新版本。需要在不静默修改本地文件的前提下，让入口发现远端更新并把决定权交给用户。

## 改了什么

- `lang` 每次加载先执行只读版本检查，比较本地版本与公开仓 `main/VERSION`。
- 只有远端版本领先时才询问；网络失败、本地未知或本地领先都不阻断使用。
- 用户明确同意后交给现有 `lang-upgrade`，不复制升级实现、不绕过开发仓保护。
- 增加可测试的版本检查脚本、三条行为评测和脚本级回归检查。

## 兼容与边界

- 只在 `lang` 主入口自动检查；直接触发子 Skill 不会重复复制这套启动规则。
- 升级完成后需要重新触发 `lang`，当前已经加载的旧正文不会在同一轮热替换。

## 验证

- `node scripts/test-lang-update-check.mjs`
- `node scripts/validate-sharing-system.mjs`
- `node scripts/test-cross-platform-install.mjs`
- `./pre-check.sh`
