---
name: lang-yx-install
description: |
  意心会内部 ASOP Skill 安装器。从飞书云空间下载并部署 skill/tool 到本地。
  触发方式：/lang-yx-install、「安装意心会skill」「部署内部skill」「同步飞书skill」
  YiXinHui internal ASOP skill installer. Downloads and deploys skills/tools from Feishu Drive.
  Trigger: /lang-yx-install, "install yx skills", "deploy internal skills", "sync feishu skills"
---

# lang-yx-install — 意心会内部 Skill 安装器

从飞书云空间自动下载并部署意心会内部 ASOP skill 到本地 `~/.claude/` 目录。

## 前置条件

- `lark-cli` 已安装（`brew install lark-cli` 或 `npm i -g @anthropic/lark-cli`）
- `lark-cli auth login` 已完成认证
- 需要 `drive:drive` scope（读取云空间文件权限）
- `python3` 可用（用于解析飞书 API 返回的 JSON）

## 默认飞书文件夹

**YiXinSKILL**：`https://fcntz0gsnz8y.feishu.cn/drive/folder/B06yfyHVXl9SqWd4pk6cw29SnSc`

## 使用方式

用户调用 `/lang-yx-install` 后：

1. 如果用户提供了飞书文件夹 URL，使用该 URL
2. 如果没有提供，使用默认 URL（YiXinSKILL）
3. 执行下载部署流程

---

## 执行流程

### Step 1：环境检查

运行以下 bash 脚本检查前置条件：

```bash
# 检查 lark-cli
if ! command -v lark-cli &>/dev/null; then
  echo "ERROR: lark-cli 未安装。请先安装："
  echo "  brew install lark-cli"
  echo "  或 npm i -g @anthropic/lark-cli"
  exit 1
fi

# 检查认证状态
if ! lark-cli auth status &>/dev/null 2>&1; then
  echo "ERROR: lark-cli 未认证。请先运行："
  echo "  lark-cli auth login"
  exit 1
fi

# 检查 python3
if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 未安装。"
  exit 1
fi

echo "OK: 环境检查通过"
```

如果任何检查失败，**停止执行**，把错误信息告诉用户，不要继续。

### Step 2：提取 folder_token

从飞书文件夹 URL 中提取 `folder_token`：

```bash
FEISHU_URL="${1:-https://fcntz0gsnz8y.feishu.cn/drive/folder/B06yfyHVXl9SqWd4pk6cw29SnSc}"
FOLDER_TOKEN=$(echo "$FEISHU_URL" | python3 -c "import sys; url=sys.stdin.read().strip(); print(url.rstrip('/').split('/')[-1])")
echo "folder_token: $FOLDER_TOKEN"
```

### Step 3：递归下载文件夹内容

用以下 Python 脚本递归列出并下载所有文件：

```bash
python3 << 'PYEOF'
import subprocess
import json
import os
import sys

SKILLS_DIR = os.path.expanduser("~/.claude/skills")
TOOLS_DIR = os.path.expanduser("~/.claude/tools")
META_DIR = os.path.expanduser("~/.claude/skills/.yx-meta")

# 根目录文件（放到 .yx-meta/）
ROOT_META_FILES = {"README.md", "VERSION", "setup.md", "publish.sh"}

def lark_list_folder(folder_token, page_token=None):
    """调用飞书 API 列出文件夹内容"""
    cmd = ["lark-cli", "drive", "+list",
           "--folder-token", folder_token,
           "--page-size", "50"]
    if page_token:
        cmd += ["--page-token", page_token]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # 如果 +list 不可用，尝试原生 API
        cmd_alt = ["lark-cli", "api", "--method", "GET",
                   "--uri", f"/open-apis/drive/v1/files?folder_token={folder_token}&page_size=50"]
        if page_token:
            cmd_alt[-1] += f"&page_token={page_token}"
        result = subprocess.run(cmd_alt, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"ERROR: 无法列出文件夹 {folder_token}: {result.stderr}", file=sys.stderr)
            return None

    try:
        data = json.loads(result.stdout)
        # 飞书 API 返回格式：data.files[] 或直接是 files[]
        if "data" in data:
            return data["data"]
        return data
    except json.JSONDecodeError:
        print(f"ERROR: JSON 解析失败: {result.stdout[:200]}", file=sys.stderr)
        return None

def lark_download(file_token, output_path):
    """下载单个文件"""
    output_dir = os.path.dirname(output_path)
    filename = os.path.basename(output_path)
    os.makedirs(output_dir, exist_ok=True)

    # lark-cli drive +download 需要 cd 到目标目录执行
    result = subprocess.run(
        ["lark-cli", "drive", "+download",
         "--file-token", file_token,
         "--output", filename],
        capture_output=True, text=True,
        cwd=output_dir
    )
    if result.returncode != 0:
        print(f"  WARN: 下载失败 {file_token} -> {output_path}: {result.stderr}", file=sys.stderr)
        return False
    return True

def determine_target_dir(relative_path):
    """根据顶层目录决定本地映射路径"""
    parts = relative_path.strip("/").split("/")
    if len(parts) == 1 and parts[0] in ROOT_META_FILES:
        # 根目录元文件 -> .yx-meta/
        return os.path.join(META_DIR, parts[0])

    top_dir = parts[0] if len(parts) > 1 else ""

    if top_dir == "skills":
        # skills/ 下的内容 -> ~/.claude/skills/
        return os.path.join(SKILLS_DIR, "/".join(parts[1:]))
    elif top_dir == "tools":
        # tools/ 下的内容 -> ~/.claude/tools/
        return os.path.join(TOOLS_DIR, "/".join(parts[1:]))
    else:
        # 其他文件也放到 .yx-meta/
        return os.path.join(META_DIR, relative_path)

def crawl_and_download(folder_token, relative_path=""):
    """递归遍历文件夹并下载"""
    page_token = None
    total_files = 0

    while True:
        data = lark_list_folder(folder_token, page_token)
        if data is None:
            break

        files = data.get("files", [])
        for f in files:
            name = f.get("name", "unknown")
            token = f.get("token", "")
            file_type = f.get("type", "")

            item_path = f"{relative_path}/{name}" if relative_path else name

            if file_type == "folder":
                print(f"  [DIR]  {item_path}/")
                total_files += crawl_and_download(token, item_path)
            else:
                target = determine_target_dir(item_path)
                print(f"  [FILE] {item_path} -> {target}")
                if lark_download(token, target):
                    total_files += 1

        # 分页处理
        if data.get("has_more", False) and data.get("page_token"):
            page_token = data["page_token"]
        else:
            break

    return total_files

# --- Main ---
folder_token = os.environ.get("FOLDER_TOKEN", "B06yfyHVXl9SqWd4pk6cw29SnSc")

print(f"=== 意心会 Skill 安装器 ===")
print(f"源文件夹 token: {folder_token}")
print(f"Skills 目标: {SKILLS_DIR}")
print(f"Tools 目标:  {TOOLS_DIR}")
print(f"Meta 目标:   {META_DIR}")
print()

# 确保目标目录存在
for d in [SKILLS_DIR, TOOLS_DIR, META_DIR]:
    os.makedirs(d, exist_ok=True)

print("正在扫描飞书文件夹...")
count = crawl_and_download(folder_token)

print()
print(f"=== 完成：共下载 {count} 个文件 ===")
PYEOF
```

### Step 4：验证安装

```bash
echo "=== 验证安装结果 ==="

# 检查 skills 目录
echo ""
echo "Skills 目录 (~/.claude/skills/):"
if [ -d ~/.claude/skills ]; then
  find ~/.claude/skills -name "SKILL.md" -type f | while read f; do
    skill_dir=$(dirname "$f")
    skill_name=$(basename "$skill_dir")
    echo "  [OK] $skill_name"
  done
else
  echo "  (目录不存在)"
fi

# 检查 tools 目录
echo ""
echo "Tools 目录 (~/.claude/tools/):"
if [ -d ~/.claude/tools ]; then
  ls -1 ~/.claude/tools/ 2>/dev/null | head -20
else
  echo "  (目录不存在)"
fi

# 检查 meta 目录
echo ""
echo "Meta 目录 (~/.claude/skills/.yx-meta/):"
if [ -d ~/.claude/skills/.yx-meta ]; then
  ls -1 ~/.claude/skills/.yx-meta/ 2>/dev/null
else
  echo "  (目录不存在)"
fi

echo ""
echo "安装完成。重启 Claude Code 或新开会话即可使用新 skill。"
```

---

## 目录映射规则

| 飞书文件夹中的路径 | 本地目标路径 |
|---|---|
| `skills/*` | `~/.claude/skills/*` |
| `tools/*` | `~/.claude/tools/*` |
| `README.md` / `VERSION` / `setup.md` / `publish.sh` | `~/.claude/skills/.yx-meta/` |
| 其他文件 | `~/.claude/skills/.yx-meta/` |

---

## 错误处理

| 错误场景 | 处理方式 |
|---|---|
| `lark-cli` 未安装 | 提示安装命令，停止执行 |
| 未认证 | 提示 `lark-cli auth login`，停止执行 |
| scope 不足 / Permission denied | 提示用户执行 `lark-cli auth login --scope drive:drive`，停止执行 |
| 单个文件下载失败 | 打印 WARN，跳过该文件，继续下载其他文件 |
| 文件夹 token 无效 | 打印 ERROR，停止执行 |
| 网络超时 | 提示用户检查网络后重试 |

---

## 注意事项

- 已有同名文件会被覆盖（安装器行为等同于"同步最新版"）
- 不会删除本地已有但飞书上不存在的文件（只做增量覆盖）
- 如果飞书 API 返回分页数据，脚本会自动翻页直到读完
- 下载完成后建议重启 Claude Code 或新开会话，让新 skill 生效
