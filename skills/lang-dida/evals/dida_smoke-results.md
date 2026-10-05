# lang-dida 核验记录 — 2026-10-05

- `changed-and-verified`：入口静态校验、公开目录与分享结构校验、Codex／Claude Code／CodeBuddy安装回归、发布前敏感词扫描均通过。
- `changed-and-verified`：7项确定性回归通过，覆盖父子状态、检查事项独立日期、ID去重、时区月底边界、敏感标题与正文过滤、分段失败和边界重叠。
- `changed-and-verified`：官方CLI实际只读查询成功；按账号偏好时区运行整月三段查询，完成任务数量与先前整月查询一致；未保存原始任务正文或认证数据。
- `changed-and-verified`：共享根指向本仓本体，skill-tongbu补齐本机Agent入口；再次预览无新增或冲突。旧私人入口移出发现目录，未进入公开仓。
- `pending`：写入命令核对了官方CLI帮助，未在个人账号创建、移动或删除测试任务。evals.json是行为验收用例，未执行模型基准评测。
- 此记录对应提交前核验；提交、合并与远端状态以对应GitHub PR为准。
