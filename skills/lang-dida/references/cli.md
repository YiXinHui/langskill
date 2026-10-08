# 连接与命令

## 连接分支：首次安装或认证异常时读取

官方文档：[DIDA CLI](https://help.dida365.com/articles/7464976698707017728)、[滴答 MCP](https://help.dida365.com/articles/7438132116019216384)。本 Skill 采用官方 CLI，不调用旧版私人 API 客户端。
2026-10-05 核对官方包0.1.14：需要 Node.js 20或以上，提供任务、清单、习惯、专注和纪念日基础操作；后续命令以本机 `--help` 和官方文档为准。

```bash
node --version
npm install -g @suibiji/dida-cli
dida --version
dida --help
dida auth login
dida project list --json
```

浏览器登录平时使用的国内滴答账号，OAuth由用户完成。等待超时则说明原因，重新启动登录；不能把浏览器已登录当成本地授权已保存。
CLI原生凭据位置是 `~/.config/dida-cli/config.json`，由CLI管理。检查目录权限700、配置文件权限600，不读取或打印值，不改为另一套token管理。
认证失效时重新OAuth登录，不承诺CLI自动刷新token。遇网络错误先区分网络和授权，禁止关闭TLS验证；CLI错误体可能含敏感内容，不能原样回显。
清单列表与预期不一致时先核对账号，不合并账号或复制其他连接器的数据。

## 查询分支

各命令的 `--json` 输出捕获在本地；筛选所需字段、遮蔽凭据后再展示。正文和附件仅在任务所需时读取，不默认下载。

```bash
dida project list --json
dida project group list --json
dida project data <projectId> --json
dida task search "TODO" --json
dida task get <projectId> <taskId> --json
dida preference get --json
dida habit list --json
dida habit checkins --habits <habitId> --from 20260901 --to 20260930 --json
dida focus list --from "2026-09-01T00:00:00+0800" --to "2026-09-30T23:59:59+0800" --type pomodoro --json
dida focus list --from "2026-09-01T00:00:00+0800" --to "2026-09-30T23:59:59+0800" --type timing --json
```

数据流：`project list`取得现网清单ID → `project data`取得任务ID及所属`projectId` → `task get`取得详细内容和检查事项。搜索结果也可提供任务坐标，不能只按标题直接写入。
收件箱ID从实际任务的`projectId`或CLI现网返回值取得，不写死私人ID，也不把旧客户端的`inbox0`规则套入官方CLI。
习惯先列清单获得`habitId`，然后查询指定窗口打卡。专注一次最多30天；更长范围按本地时区拆段后去重。空列表只表示当前查询未返回记录。

### 完成任务和日期筛选

```bash
dida task completed --projects <projectId> --start-date "2026-09-01T00:00:00+0800" --end-date "2026-09-30T23:59:59+0800" --json
dida task filter --projects <projectId> --start-date "2026-09-01T00:00:00+0800" --end-date "2026-09-14T23:59:59+0800" --status 0 --json
```

`task completed`按完成时间查询；省略`--projects`读取当前账号可访问的清单。
`task filter`的日期按`dueDate`过滤，不能作为实际完成时间；未完成日期查询每段最多14天。
优先使用入口的复盘脚本读取完成窗口；大输出不能用终端截断片段统计。检查API是否提供分页／截断信号，有信号则继续取全；无信号也不声称覆盖全部历史数据。

## 写入分支

用户明确提出添加、修改、完成、移动或删除即授权相应动作。建议整理、提出计划或读取复盘不自动授权修改。
先列出现网唯一目标、现状和变更范围；用户已指定则继续执行。只有存在重名、目标不明或范围超出授权时才提问。
官方CLI未提供通用`--dry-run`；可先给拟执行字段。删除清单前读取其中任务及数量，核对用户是否授权连带影响。

```bash
dida task create --title "任务名称" --project <projectId>
dida task update <taskId> --id <taskId> --project <projectId> --title "修改后的名称"
dida task complete <projectId> <taskId>
dida task move --from <sourceProjectId> --to <targetProjectId> --task <taskId>
dida task delete <projectId> <taskId>
dida project create --name "清单名称"
```

使用原生`task move`，不能沿用旧版“先复制再删除”的移动方法；它可能制造重复、丢失原任务身份。
同名任务可能是合法重复实例，不能仅因标题相同就删除。循环、提醒、习惯写入和清单删除等低频命令先读取对应`--help`，核对字段再执行。
创建或修改后`task get`回读；移动核对目标清单及原任务ID；完成用`task get`／`task completed`核对；删除核对原对象查询结果，不能把其他错误当删除成功。
原生检查事项完成状态可能为1或2；父任务通常为2。判断见[取证规则](evidence.md)，保留返回原值。

官方网页入口：[滴答清单](https://dida365.com/webapp/)。没有现网返回的单任务链接时给网页入口、清单名称与任务标识，不编造链接。
