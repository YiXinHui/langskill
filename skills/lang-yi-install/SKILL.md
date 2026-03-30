---
name: lang-yi-install
description: |
  意心会内部 ASOP Skill 安装器。从飞书云空间下载并部署 skill/tool 到本地。
  触发方式：/lang-yi-install、「安装意心会skill」「部署内部skill」「同步飞书skill」
  YiXinHui internal ASOP skill installer. Downloads and deploys skills/tools from Feishu Drive.
  Trigger: /lang-yi-install, "install yi skills", "deploy internal skills", "sync feishu skills"
---

# lang-yi-install — 意心会内部 Skill 安装器

从飞书云空间下载并部署意心会内部 ASOP skill 到本地 `~/.claude/` 目录。

**原理**：文件清单硬编码在本 skill 中，只需 `drive:file:download` 权限即可下载，不需要列文件夹权限。

## 前置条件

- `lark-cli` 已安装：`npm install -g @larksuite/cli`
- `lark-cli config init --new` 已完成初始化
- `lark-cli auth login` 已完成认证（需要 `drive:file:download` scope）

## 执行流程

### Step 1：环境检查

```bash
echo "=== 意心会 Skill 安装器 ==="
echo ""

# 检查 lark-cli
if ! command -v lark-cli &>/dev/null; then
  echo "ERROR: lark-cli 未安装。请先执行以下三步："
  echo ""
  echo "  1. npm install -g @larksuite/cli"
  echo "  2. lark-cli config init --new"
  echo "  3. lark-cli auth login"
  echo ""
  echo "完成后重新运行 /lang-yi-install"
  exit 1
fi

# 检查认证状态
AUTH_RESULT=$(lark-cli auth status 2>&1)
if echo "$AUTH_RESULT" | grep -q '"ok": false'; then
  echo "ERROR: lark-cli 未认证。请先运行："
  echo ""
  echo "  lark-cli auth login"
  echo ""
  echo "完成后重新运行 /lang-yi-install"
  exit 1
fi

echo "OK: lark-cli 已安装且已认证"
```

如果检查失败，**停止执行**，不要继续。

### Step 2：下载文件

**直接运行以下 Python 脚本**，不做任何修改。脚本内含完整文件清单，逐个下载：

```bash
python3 << 'PYEOF'
import subprocess, os, sys, time

SKILLS_DIR = os.path.expanduser("~/.claude/skills")
TOOLS_DIR = os.path.expanduser("~/.claude/tools")
META_DIR = os.path.expanduser("~/.claude/skills/.yi-meta")

# === 文件清单（file_token -> 本地相对路径）===
# 路径前缀：skills/ -> ~/.claude/skills/，tools/ -> ~/.claude/tools/，其他 -> .yi-meta/
MANIFEST = [
    # --- yi（主路由）---
    ("GrV4b7OqLo4bWwx4Tggc86ZFnof", "skills/yi/SKILL.md"),

    # --- yi-illustration（极简抽象配图）---
    ("FI84bNqSkoqbD4x1SsIceDa4nZB", "skills/yi-illustration/SKILL.md"),
    ("AsNxbD4GMojKscxjO4wcyDN1nXb", "skills/yi-illustration/references/aesthetic-prompt.md"),
    ("Zf0TbIiFPod5uaxZGGQcbm0Vnbn", "skills/yi-illustration/scripts/brand_overlay.py"),

    # --- yi-poster（海报制作）---
    ("THLMbcJ5ZohsUmxTpGTcGCpZnoe", "skills/yi-poster/SKILL.md"),
    ("IiELb0vYUoerobxmQYccoeM0nTe", "skills/yi-poster/references/沙龙海报模板.md"),
    ("Cq4UbtpkLoM3tcxgrpRc8metnih", "skills/yi-poster/scripts/export_poster.sh"),

    # --- yi-recording（录音整理）---
    ("VnHUb8aovoYKDcxzM3UcHlGInNd", "skills/yi-recording/SKILL.md"),
    ("Zxwgb7oo5otL1hxBt0Rcu7KCnoe", "skills/yi-recording/references/萃取规范.md"),
    ("Pm29b9fqFoJWcdxpgmFcuc9An3z", "skills/yi-recording/references/知识单元模板.md"),
    ("M2FrbgyUUot8AmxMYXYcQO5gnzc", "skills/yi-recording/references/方法论路由规则.md"),
    ("Fbs0bZqJYo8cxYxZFXYctc7anq3", "skills/yi-recording/references/客户档案模板.md"),

    # --- yi-minutes（飞书妙记整理）---
    ("AwsUbZ3aboqB6sxjRF6cdq8NnHb", "skills/yi-minutes/SKILL.md"),

    # --- yiskill-upgrade（升级器）---
    ("RatgbywgOoAUmZxm5pqcClRnn8l", "skills/yiskill-upgrade/SKILL.md"),

    # --- tools ---
    ("G67Xb7CaMoZCjsx7I3cc2bK3nvg", "tools/feishu-sync/feishu_minutes_auto_export.py"),
    ("BlHLbj1zNos3fXx6jLvcR1KdnIc", "tools/feishu-sync/requirements.txt"),
    ("FpGpbvFkoo6YtRxnYNxce6K4nUW", "tools/feishu-sync/README.md"),

    # --- 元文件 ---
    ("OLb8bAHt3opOHWxohAjcwSIlnEf", "meta/README.md"),
    ("WQ6sbHh1WoF6uZxcL5OcK2mrnie", "meta/setup.md"),
    ("JIcXbDngtosTDpx8VHIcLGXVnyd", "meta/VERSION"),
]

def resolve_path(rel_path):
    """将清单中的相对路径映射到本地绝对路径"""
    if rel_path.startswith("skills/"):
        return os.path.join(SKILLS_DIR, rel_path[len("skills/"):])
    elif rel_path.startswith("tools/"):
        return os.path.join(TOOLS_DIR, rel_path[len("tools/"):])
    elif rel_path.startswith("meta/"):
        return os.path.join(META_DIR, rel_path[len("meta/"):])
    return os.path.join(META_DIR, rel_path)

def download_file(file_token, local_path):
    """用 lark-cli drive +download 下载单个文件"""
    output_dir = os.path.dirname(local_path)
    filename = os.path.basename(local_path)
    os.makedirs(output_dir, exist_ok=True)

    result = subprocess.run(
        ["lark-cli", "drive", "+download",
         "--file-token", file_token,
         "--output", filename,
         "--as", "user"],
        capture_output=True, text=True,
        cwd=output_dir
    )
    return result.returncode == 0

# --- Main ---
print(f"目标目录：")
print(f"  Skills: {SKILLS_DIR}")
print(f"  Tools:  {TOOLS_DIR}")
print(f"  Meta:   {META_DIR}")
print(f"")
print(f"共 {len(MANIFEST)} 个文件，开始下载...")
print("")

ok_count = 0
fail_count = 0
fail_list = []

for i, (token, rel_path) in enumerate(MANIFEST, 1):
    local_path = resolve_path(rel_path)
    short_path = rel_path
    print(f"  [{i:2d}/{len(MANIFEST)}] {short_path} ... ", end="", flush=True)

    if download_file(token, local_path):
        print("OK")
        ok_count += 1
    else:
        print("FAIL")
        fail_count += 1
        fail_list.append(rel_path)

    # 避免 API 限流
    if i % 5 == 0:
        time.sleep(0.5)

print("")
print(f"=== 完成：成功 {ok_count}，失败 {fail_count} ===")

if fail_list:
    print(f"")
    print(f"失败文件：")
    for f in fail_list:
        print(f"  - {f}")
    print(f"")
    print(f"可能原因：drive:file:download scope 未授权。")
    print(f"修复：lark-cli auth login --scope drive:file:download")

# 设置脚本可执行权限
export_sh = os.path.join(SKILLS_DIR, "yi-poster/scripts/export_poster.sh")
if os.path.exists(export_sh):
    os.chmod(export_sh, 0o755)

PYEOF
```

### Step 3：验证安装

```bash
echo "=== 验证安装结果 ==="
echo ""

# 检查 skills
echo "已安装的 Skills："
for skill_dir in ~/.claude/skills/yi ~/.claude/skills/yi-*; do
  if [ -f "$skill_dir/SKILL.md" ]; then
    skill_name=$(basename "$skill_dir")
    echo "  [OK] $skill_name"
  fi
done

if [ -f ~/.claude/skills/yiskill-upgrade/SKILL.md ]; then
  echo "  [OK] yiskill-upgrade"
fi

# 检查 tools
echo ""
echo "已安装的 Tools："
if [ -d ~/.claude/tools/feishu-sync ]; then
  echo "  [OK] feishu-sync"
else
  echo "  (无)"
fi

# 版本
echo ""
if [ -f ~/.claude/skills/.yi-meta/VERSION ]; then
  echo "版本：v$(cat ~/.claude/skills/.yi-meta/VERSION)"
fi

echo ""
echo "安装完成。新开会话即可使用 /yi 系列命令。"
```

### Step 4：告知用户结果

安装完成后，展示已安装的 skill 列表和简要说明：

| 命令 | 说明 |
|------|------|
| `/yi` | 意心会 ASOP 主路由，自动分发到对应 skill |
| `/yi-illustration` | 极简抽象风格配图（Seedream API） |
| `/yi-poster` | 大尺寸海报生成（HTML→Chrome headless→JPG） |
| `/yi-recording` | 录音转文字整理 |
| `/yi-minutes` | 飞书妙记导出整理 |
| `/yiskill-upgrade` | 升级到最新版本 |

---

## 错误处理

| 错误场景 | 处理方式 |
|---|---|
| `lark-cli` 未安装 | 提示三步安装流程，停止执行 |
| 未认证 | 提示 `lark-cli auth login`，停止执行 |
| 下载失败（scope 不足） | 提示 `lark-cli auth login --scope drive:file:download`，列出失败文件 |
| 单个文件下载失败 | 打印 FAIL，继续下载其他文件，最后汇总失败列表 |

## 注意事项

- 已有同名文件会被覆盖（等同于"同步最新版"）
- 文件清单更新时需要同步更新本 skill 的 MANIFEST（由 `/yiskill-upgrade` 处理）
- 不需要 `drive:drive:readonly` scope（不列文件夹，只下载已知文件）
