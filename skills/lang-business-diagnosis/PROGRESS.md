# PROGRESS — lang-business-diagnosis（开源商业初诊）

## 目标
开源「商业初诊」skill，给陌生老板用：一轮引导式对话，用他自己说的业务证据让他自己发现真正的问题在哪，同时留下结构化生意信息。咨询漏斗入口：体验→信任→正式项目。

## 顺序（依赖链）
任务0 基线核对（完成，2026-08-03）→ 1 SKILL.md 主文档 → 2 references/ 拆分 → 3 evals 静态检查+反向验证 → 4 三个剧本 → 5 交付证据+BLOCKED.md。主文档定原则 → references 承接细节 → 检查锁死前两者 → 剧本验体验。

## 最大风险
1. 用户可见文案混入内部字段名/广告词 → 靠检查项锁死，反向验证必须真实跑红。
2. 剧本自问自答、无真实改判时刻（最易作弊） → 用户台词带行业细节，改判轮贴原文。
3. 白名单外改动 → 只动新目录 + skill-catalog.json 一行，交付前 git status 核验。

## 进度（2026-08-03 全部完成）
- 任务0 基线核对 ✓（HEAD=825059c、pre-check exit 0、旧检查 596 全过、8 处无关改动未触碰）
- 任务1 SKILL.md ✓（65 行，8 条体验机制全部落地，无内部词无广告词）
- 任务2 references/ ✓（experience-contract / report-contract / lead-card-contract / handoff-compat 四份，自包含）
- 任务3 evals/run_static_checks.py ✓（122 项全绿；反向验证红→绿已贴证据）
- 任务4 三个剧本 ✓（transcript 1/2/3 存 evals/，每个含入口识别+≥2次回放+手段登记+改判时刻+合法结尾）
- skill-catalog.json ✓（只加一行 lang-business-diagnosis, role: public-product）
- BLOCKED.md ✓（无）

## 关键拍板（照此执行）
- 判断库只做接口不建库；线索卡只做草稿、自愿导出、不连飞书；输出与 HandoffV2 兼容但不迁移。
- 让步顺序：对话体验真实 ＞ 商业分析前置 ＞ 与旧契约兼容 ＞ 做得快。
