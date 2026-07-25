# 2026-07-25 langskill 建立干净公开历史基线

## 给非技术读者的一句话

公开仓从当前已验证版本重新建立主线，早期不再代表现有产品的实现历史不再通过 GitHub 分支和版本标签对外可达。

## 这次做了什么

- 在本地生成并验证完整 Git bundle，保留必要的内部恢复能力。
- 用当前 `v0.6.2` 文件树建立无父提交的新 `main` 根提交。
- 强制替换 GitHub `main`，删除旧版本标签，只发布新的 `v0.6.2` 标签。
- 删除本地遗留 feature 分支和旧标签，避免后续误把旧历史重新推回公开仓。
- 要求旧 clone 重新拉取仓库，不再把两条不相干的历史强行合并。

## 为什么要做

- 早期提交包含已经废弃的命名、流程和试验实现，继续公开会让外部读者把历史草稿误当成当前产品来源与设计依据。
- 只改最新文件不能改变 GitHub 的 commit 与 tag 可达历史；要建立清晰边界，必须同时处理主分支和所有公开标签。
- 历史重写风险较高，因此先留离线可恢复备份，再改变远程引用。

## 具体改了什么

| 文件/模块 | 改动 | 你需要知道的意思 |
|---|---|---|
| GitHub `main` | 改为新的根提交 | GitHub 正常浏览不再沿父提交进入旧实现 |
| GitHub tags | 删除 `v0.5.0`、`v0.6.0`、`v0.6.1`，新增 `v0.6.2` | 旧 tag 不再继续暴露旧提交链 |
| `VERSION` | 升至 `0.6.2` | 安装器和下游依赖能识别新的公开基线 |
| `README.md` | 增加旧 clone 处理说明 | 已 clone 的开发者需要重新 clone，避免旧历史回流 |
| 离线 bundle | 保存重写前完整 refs | 只用于内部事故恢复，不再作为公开上游 |

## 对系统意味着什么

- langskill 的公开 Git 历史从 `v0.6.2` 开始。
- 正常安装用户可以继续升级；直接 clone 的开发者需要重新 clone。
- 旧 commit SHA 可能仍存在于第三方 clone、fork 或 GitHub 临时缓存中，这些副本不受本仓分支与 tag 控制。
- 后续任何公开发布只允许从新的 `main` 继续，不得合并离线备份中的旧分支。

## 怎么证明没搞坏

执行并记录：

```bash
git bundle verify <离线备份>
node scripts/validate-sharing-system.mjs
./pre-check.sh
git diff --check
git ls-remote --heads --tags git@github.com:YiXinHui/langskill.git
git clone --depth 10 git@github.com:YiXinHui/langskill.git <临时目录>
```

验收口径：

- 离线 bundle 包含重写前完整 refs 且验证通过。
- 公开远程只有新的 `main` 与 `v0.6.2`。
- 从 GitHub 全新 clone 后，`main` 只有一个根提交。
- 新 clone 中 7 个 Skill 结构有效，敏感扫描与来源痕迹检查通过。
- 公开文件不包含已移除的外部来源标识。
- 发布门禁只检查五台山自身的正向产品结构，不把外部项目词汇重新写入公开仓。

## 还没解决什么

- 无法删除第三方已经保存的 clone、fork、截图或缓存副本。
- GitHub 对失去引用的对象何时物理回收由平台控制；如果需要让已知旧 SHA 立即失效，需要再联系 GitHub Support 处理缓存对象。

## 技术细节

- 本次采用“当前树生成新根提交”，不在旧提交链上逐个改写文件。
- 强制推送使用带旧主线 SHA 的 `--force-with-lease`，避免覆盖重写期间出现的未知远程提交。
