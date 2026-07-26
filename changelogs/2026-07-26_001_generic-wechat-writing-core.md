# 2026-07-26 新增通用朋友圈写作核心

## 给非技术读者的一句话

新增 `lang-wechat-writing`：它只依据用户选中的 1—3 份真实资料写一条朋友圈，并把关键事实对应回来源；狼格拉底每日 4—5 条朋友圈规划仍由原来的专用 Skill 负责。

## 这次做了什么

- 新增通用朋友圈写作流程和 `wechat-draft-v1` 产品输出协议。
- 建立事实边界、来源引用、写作画像与用户确认后学习的约束。
- 明确不自动发布、不扫描私人目录、不默认套用狼格拉底人设。
- 增加单素材生成、事实不编造、专用规划分流、非连续引用、动作推断和合法反例六类回归场景。
- 第三轮修复要求每个 `excerpt` 都是 `source.content` 的连续逐字子串，禁止拼接不连续片段；事实性 claim 不能借来源标题补入正文没有的动作、范围或限定词。
- 同步 README、机器清单，并将修复版本从 `0.8.0` 更新为 `0.8.1`。

## 为什么要做

会员需要的是“用自己的资料、按自己的表达写一条可用朋友圈”，而不是复制狼格拉底的专属日更系统。把通用核心与专用上层分开，才能既保持事实可靠，又允许每个人拥有独立写作画像。

## 边界

- 本次没有修改 `lang-wechat-pyq` 的专用流程。
- 本次没有接入任何私人目录、客户资料或发布凭证。
- 产品是否激活该 Skill，由下游应用完成契约测试和版本发布后决定。

## 验证

- `node scripts/validate-sharing-system.mjs`
- `./pre-check.sh`
- iteration-1 paired eval：形式断言 with-skill 11/11、baseline 8/11；但 claim 审计发现无来源的“今天”和阶段成果拔高，因此不视为质量通过。
- 已据此补充无来源时间锚点、阶段升级、逐句事实审计和逐字 excerpt 约束，并增强 eval 2/3 的区分断言；iteration-2 结果在本地评测工作区留证。
- iteration-3 current-skill：6 个 fresh run 的形式断言 `34/34`；结构化用例共 `11/11` 条引用通过确定性 `source.content.includes(excerpt)` 检查，标题事实越界回归在修复后的 eval 5 run-2 为 `0` 次。
- iteration-3 baseline：五个 fresh 旧快照用例 `26/30`，另复用 iteration-2 的专属分流基线；明确捕获无依据动作扩写、未拆分 citation 和仅凭标题补事实三类差异。人工审阅仍是发布前门禁，自动通过不等于已经发布。
- `node scripts/validate-sharing-system.mjs`、`./pre-check.sh`、Skill Creator `quick_validate.py` 和 `git diff --check` 通过。
- `skills/lang-wechat-writing-workspace/` 仅保存本地评测证据并被 Git 忽略，不进入发布包。
