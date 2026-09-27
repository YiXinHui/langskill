#!/usr/bin/env python3
"""Create an additive, portable Source of Truth workspace. Python 3.9+, stdlib only."""
import argparse
from datetime import date
import json
import os
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import quote, urlsplit

SKILL = Path(__file__).resolve().parents[1]
ASSETS = SKILL / "assets"
STATE = ".docs/sot-config.json"
VERSION = "1.1.2"


def path_key(value):
    """Conservative portable comparison, including on case-sensitive volumes."""
    return unicodedata.normalize("NFC", value.casefold())


def reject_existing_alias(path):
    if path.parent.is_dir():
        for existing in path.parent.iterdir():
            if path_key(existing.name) == path_key(path.name) and existing.name != path.name:
                raise ValueError(f"路径与已有名称存在大小写或 Unicode 别名冲突：{path}")


def checked_root(value):
    raw = Path(os.path.expanduser(value))
    if ".." in raw.parts:
        raise ValueError("目标路径不能包含 ..；请提供明确的完整路径")
    absolute = raw if raw.is_absolute() else Path.cwd() / raw
    current = Path(absolute.anchor)
    # Root-owned macOS aliases are the only exceptions; user-created links stay forbidden.
    aliases = {"/var": "/private/var", "/tmp": "/private/tmp", "/etc": "/private/etc"}
    for index, part in enumerate(absolute.parts[1:]):
        current = current / part
        reject_existing_alias(current)
        if current.is_symlink():
            trusted = aliases.get(str(current)) if sys.platform == "darwin" else None
            if (trusted and index < len(absolute.parts) - 2 and current.lstat().st_uid == 0
                    and current.resolve() == Path(trusted)):
                current = Path(trusted)
            else:
                raise ValueError(f"拒绝目标或祖先路径中的软链接：{current}")
        if current.exists() and not current.is_dir():
            raise ValueError(f"目标或父路径不是目录：{current}")
    return current


def encode_local_links(content):
    def replace(match):
        target = match.group(1) or match.group(2)
        if target.startswith("https://"):
            return match.group(0)
        return "](<" + quote(target, safe="/") + ">)"
    return re.sub(r"\]\((?:<([^>]+)>|([^\s)]+))\)", replace, content)


def read_json(path):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"重复配置字段：{key}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)


def config_normalized(given):
    defaults = read_json(ASSETS / "config.example.json")
    if not isinstance(given, dict) or set(given) - set(defaults):
        raise ValueError("配置必须为对象，且只能使用配置示例中的字段")
    config = {**defaults, **given}
    for field in ("main_company", "secondary_company", "personal_brand", "public_account"):
        value = config[field]
        if field == "secondary_company" and value is None:
            continue
        if (not isinstance(value, str) or not value.strip() or value != value.strip()
                or value.startswith(".") or value.endswith(".") or len(value) > 60
                or re.search(r'[\\/<>:"|?*`\[\]{}#\x00-\x1f\x7f]', value)):
            raise ValueError(f"{field} 必须是合法的单层目录名")
    if path_key(config["personal_brand"]) == path_key(config["public_account"]):
        raise ValueError("personal_brand 与 public_account 必须使用不同目录名")
    extras = config["extra_directories"]
    groups = {"knowledge", "personal", "main", "secondary", "archive"}
    if not isinstance(extras, dict) or set(extras) - groups:
        raise ValueError("extra_directories 只能使用 knowledge/personal/main/secondary/archive 分组")
    for group, entries in extras.items():
        if not isinstance(entries, dict):
            raise ValueError(f"extra_directories.{group} 必须是目录路径到用途的对象")
        if group == "secondary" and entries and config["secondary_company"] is None:
            raise ValueError("关闭第二业务后不能给 secondary 添加目录")
        for relative, purpose in entries.items():
            if (not isinstance(relative, str) or len(relative) > 220
                    or any(not p or p.startswith('.') or p.endswith('.') or p != p.strip()
                           for p in relative.split('/'))
                    or re.search(r'[\\<>:"|?*`\[\]{}#\x00-\x1f\x7f]', relative)):
                raise ValueError(f"非法补充目录路径：{relative}")
            if (not isinstance(purpose, str) or not purpose.strip()
                    or len(purpose) > 300 or re.search(r'[\x00-\x1f\x7f|{}]', purpose)):
                raise ValueError(f"补充目录必须有单行用途说明：{relative}")
    projects = config["projects_root"]
    if (not isinstance(projects, str) or not projects.strip()
            or re.search(r'[\r\n`\x00|]', projects)
            or not (Path(projects).is_absolute() or projects.startswith("~/"))):
        raise ValueError("projects_root 必须是绝对路径或 ~/ 开头的路径")
    provided = given.get("authorities", {})
    if not isinstance(provided, dict) or set(provided) - set(defaults["authorities"]):
        raise ValueError("authorities 包含未知类别或不是对象")
    config["authorities"] = {**defaults["authorities"], **provided}
    for key, url in config["authorities"].items():
        if url is None:
            continue
        if not isinstance(url, str) or re.search(r'[\s<>|`]', url):
            raise ValueError(f"{key} 必须是完整 HTTPS URL 或 null")
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError(f"{key} 必须是无登录凭据的 HTTPS URL")
    return config


def ensure_plain_path(root, relative):
    current = root
    if root.is_symlink():
        raise ValueError(f"拒绝软链接目标：{root}")
    parts = Path(relative).parts
    for part in parts:
        current = current / part
        reject_existing_alias(current)
        if current.is_symlink():
            raise ValueError(f"拒绝目标中的软链接：{current}")
    if not current.is_relative_to(root):
        raise ValueError(f"路径越界：{relative}")
    return current


def render(text, context):
    def replace(match):
        key = match.group(1)
        if key not in context:
            raise ValueError(f"模板变量未定义：{key}")
        return context[key]
    return re.sub(r"\{\{([A-Z_]+)\}\}", replace, text)


def build(config, initialized_on):
    main = "03-" + config["main_company"]
    second = "04-" + config["secondary_company"] if config["secondary_company"] else None
    groups = {"knowledge": "01-知识体系", "personal": "02-个人资料", "main": main,
              "secondary": second, "archive": "05-归档"}
    purposes = {"knowledge": "知：个人认知与可复用方法", "personal": "方向：目标与个人资料",
                "main": "行：主营业务", "secondary": "行：另一项业务", "archive": "历史与追溯"}
    context = {"MAIN": main, "SECOND": second or "", "BRAND": config["personal_brand"],
               "PUBLIC_ACCOUNT": config["public_account"],
               "PROJECTS": config["projects_root"], "DATE": initialized_on}
    directories, files = set(), {}

    def add(path, content):
        path = render(path, context)
        if path in files:
            raise ValueError(f"重复生成路径：{path}")
        files[path] = encode_local_links(render(content, context))

    layout = read_json(ASSETS / "structure.json")
    for group, entries in config["extra_directories"].items():
        reserved = set()
        for existing in layout[group]:
            path = Path(render(existing, context))
            reserved.update(path_key(p.as_posix()) for p in [path, *path.parents] if str(p) != ".")
        for relative, purpose in entries.items():
            if path_key(relative) in reserved:
                raise ValueError(f"补充目录与基础结构重复：{relative}；专项职责应在初始化后维护")
            layout[group][relative] = purpose
    top_rows = []
    for key, base in groups.items():
        if base is None:
            continue
        directories.add(base)
        directories.add(base + "/.docs/changelogs")
        rows = []
        for relative, purpose in layout[key].items():
            relative = render(relative, context)
            directories.add(base + "/" + relative)
            rows.append(f"| `{relative}/` | {purpose} |")
        context[key.upper() + "_DIRS"] = "| 子目录 | 职责 |\n|---|---|\n" + "\n".join(rows)
        top_rows.append(f"| `{base}/` | {purposes[key]} | [管理说明](<../{base}/.docs/README.md>) |")
    context["TOP_TABLE"] = "| 模块 | 职责 | 规则入口 |\n|---|---|---|\n" + "\n".join(top_rows)
    authorities = {
        "knowledge": ("个人成熟知识", "01-知识体系/"),
        "goals": ("年度目标、复盘与愿景", "02-个人资料/年度目标/"),
        "company_knowledge": ("公司执行、销售、培训等复用知识", f"{main}/04-运营/"),
        "customers": ("客户列表与当前状态", f"{main}/02-客户/客户索引.md"),
        "customer_events": ("客户沟通事件流水", f"{main}/02-客户/沟通记录/"),
        "customer_materials": ("客户稳定档案与原始材料", f"{main}/02-客户/档案与材料/"),
        "products": ("产品定义、方案与定价", f"{main}/01-产品/"),
        "hr": ("员工、合作伙伴与招聘", f"{main}/08-人力资源/")}
    authority_rows = []
    for key, (label, local) in authorities.items():
        remote = config["authorities"][key]
        source = f"[云端入口](<{remote}>)" if remote else f"`{local}`"
        role = "本地仅作入口、草稿、按需缓存或历史资料" if remote else "本地维护（新工作区默认）"
        authority_rows.append(f"| {label} | {source} | {role} |")
    for label, local in [("录音清单", "05-归档/02-录音/录音全景索引.md"),
                         ("内容选题", f"{main}/03-内容/{config['personal_brand']}/选题/选题看板.md"),
                         ("已验证内容规律", f"{main}/03-内容/{config['personal_brand']}/复盘/内容规律.md")]:
        authority_rows.append(f"| {label} | `{local}` | 本地维护 |")
    if second:
        authority_rows.append(f"| 第二业务资料 | `{second}/` | 本地维护 |")
    context["AUTHORITY_TABLE"] = "| 数据类别 | 唯一正式来源 | 本地角色 |\n|---|---|---|\n" + "\n".join(authority_rows)
    templates = {".docs/SOURCE_OF_TRUTH.md": "source-of-truth.md",
                 "01-知识体系/.docs/README.md": "knowledge.md",
                 "01-知识体系/10-原料-flomo-慎用/.docs/README.md": "raw.md",
                 "02-个人资料/.docs/README.md": "personal.md",
                 main + "/.docs/README.md": "main.md",
                 "05-归档/.docs/README.md": "archive.md"}
    if second:
        templates[second + "/.docs/README.md"] = "secondary.md"
    for path, template in templates.items():
        add(path, (ASSETS / "templates" / template).read_text(encoding="utf-8"))
    add(".docs/README.md", "# 工作区治理入口\n\n先读 [Source of Truth](SOURCE_OF_TRUTH.md)，再进入对应模块的管理说明。\n\n总规则只在该索引维护；模块规则放对应 `.docs/README.md`。`changelogs/` 记录治理变更，`sot-config.json` 仅记录首次初始化配置。\n")
    pointer = "# 工作区 AI 入口\n\n查找、创建、整理业务资料前，读取 [.docs/SOURCE_OF_TRUTH.md](.docs/SOURCE_OF_TRUTH.md)，再读目标模块最近的 `.docs/README.md`。遵循其中的权威源、归属与管理规则。\n"
    add("AGENTS.md", pointer)
    add("CLAUDE.md", pointer)
    for platform in (".claude", ".Codex"):
        add(platform + "/SOURCE_OF_TRUTH.md", "# Source of Truth 兼容入口\n\n唯一维护入口：[工作区 Source of Truth](../.docs/SOURCE_OF_TRUTH.md)。请读取该文件，不在这里维护第二份规则。\n")
    add("{{MAIN}}/.docs/cache/README.md", "# 按需处理缓存\n\n仅存手动拉取后临时处理的材料，不是备份或正文镜像。每批材料记录来源链接、获取时间、用途、清理条件；处理完核对成果落点后再清理。正式来源见 [总索引](../../../.docs/SOURCE_OF_TRUTH.md)。\n")
    add("01-知识体系/02-知识单元/索引.md", "# 知识单元索引\n\n状态：尚未收录。只登记已确认的成品；若知识权威源在云端，本表只导航、不另存正式正文。\n\n| 类型 | 标题与链接 | 原始证据 | 确认日期 |\n|---|---|---|---|\n")
    customer_note = "客户当前状态的权威源在云端，见 [总索引](../../.docs/SOURCE_OF_TRUTH.md)；此文件仅为入口，不维护本地客户状态。" if config["authorities"]["customers"] else "状态：尚未登记客户。这里维护当前状态，沟通流水与稳定材料按总索引分别登记。"
    add("{{MAIN}}/02-客户/客户索引.md", "# 客户索引\n\n" + customer_note + "\n" + ("" if config["authorities"]["customers"] else "\n| 客户 | 当前状态 | 稳定档案链接 | 最近沟通链接 | 更新日期与来源 |\n|---|---|---|---|---|\n"))
    add("{{MAIN}}/03-内容/{{BRAND}}/选题/选题看板.md", "# 选题看板\n\n状态：尚未登记选题。写作前按知识体系规则检索已有证据。\n\n| 选题 | 目标受众与用途 | 证据链接 | 状态 | 成品链接 |\n|---|---|---|---|---|\n")
    add("{{MAIN}}/03-内容/{{BRAND}}/复盘/内容规律.md", "# 已验证的内容规律\n\n状态：暂无已验证规律。单篇表现或假设不能直接写成规律。\n\n| 规律 | 样本与原始数据 | 适用条件 | 反例或限制 | 验证日期 |\n|---|---|---|---|---|\n")
    add("{{MAIN}}/04-运营/工作手册/00-工具索引.md", "# 工具、提示词与模板索引\n\n状态：尚未收录。通用模板归知识体系工具箱，业务化实例归本模块；公司知识配置为云端时这里只维护导航。\n\n| 名称 | 用途 | 唯一正文或工具入口 | 版本/核验日期 |\n|---|---|---|---|\n")
    add("05-归档/02-录音/录音全景索引.md", "# 录音全景索引\n\n状态：尚未收录录音。原文件、转写和分析互相回链，分清说话人和来源。\n\n| 日期 | 类型/主题 | 原始文件 | 转写 | 分析 | 说话人与证据 |\n|---|---|---|---|---|---|\n")
    add("05-归档/01-会话日志/.模板.md", "# YYMMDD 会话日志\n\n同一天只维护一个日志文件；后续会话追加以下段落。日期使用工作区使用者的本地日期。\n\n## HH:MM — 本次主题\n\n- 用户目标与范围：\n- 已明确授权/限制：\n- 关键结论与原始证据：\n- 产物、链接与权威落点：\n- 实际验证与未验证项：\n- 未完成事项与下一步：\n")
    add(".docs/changelogs/" + initialized_on.replace("-", "")[2:] + "_初始化.md", "# 文件系统初始化\n\n日期：{{DATE}}。模板版本：" + VERSION + "。\n\n创建目录、数据权威索引、模块治理规则、AI 指针与空白索引；未导入历史数据、未创建云端资源、未迁移资料、未启用同步。初始化参数见 `../sot-config.json`。\n")
    state = {"template_version": VERSION, "initialized_on": initialized_on, "config": config}
    files[STATE] = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    # Include every ancestor for deterministic preflight and checks.
    for path in list(directories) + list(files):
        for parent in Path(path).parents:
            if str(parent) != ".":
                directories.add(parent.as_posix())
    planned = {}
    for kind, paths in (("directory", directories), ("file", files)):
        for path in paths:
            key = path_key(path)
            if key in planned:
                raise ValueError(f"计划路径存在文件/目录、大小写或 Unicode 别名冲突：{planned[key][1]} 与 {path}")
            planned[key] = (kind, path)
    return sorted(directories, key=lambda p: (len(Path(p).parts), p)), files


def run(args):
    root = checked_root(args.root)
    if root == SKILL or root.is_relative_to(SKILL):
        raise ValueError("不要把业务工作区创建在 Skill 内")
    for ancestor in root.parents:
        if ancestor.exists() and not ancestor.is_dir():
            raise ValueError(f"父路径不是目录：{ancestor}")
    state_path = ensure_plain_path(root, STATE)
    saved = read_json(state_path) if state_path.exists() else None
    if saved is not None:
        if not isinstance(saved, dict) or set(saved) != {"template_version", "initialized_on", "config"}:
            raise ValueError("已有初始化记录格式无效；请人工核对，未写入")
        if saved["template_version"] != VERSION:
            raise ValueError("模板版本不同，初始化脚本不执行升级或迁移")
        initialized_on = date.fromisoformat(saved["initialized_on"]).isoformat()
        config = config_normalized(saved["config"])
        if args.config and config_normalized(read_json(Path(args.config).expanduser())) != config:
            raise ValueError("目标已采用不同配置，不能通过初始化重命名目录或切换权威源")
    else:
        initialized_on = date.today().isoformat()
        config = config_normalized(read_json(Path(args.config).expanduser()) if args.config else {})
    directories, files = build(config, initialized_on)
    missing_dirs, missing_files, preserved, conflicts = [], [], [], []
    for relative in directories:
        path = ensure_plain_path(root, relative)
        if not path.exists():
            missing_dirs.append(relative)
        elif not path.is_dir():
            conflicts.append({"path": relative, "reason": "应为目录，但已有其他类型"})
    for relative, content in files.items():
        path = ensure_plain_path(root, relative)
        if not path.exists():
            missing_files.append(relative)
        elif not path.is_file() or path.read_bytes() != content.encode("utf-8"):
            conflicts.append({"path": relative, "reason": "已有内容或类型与模板不同；保留原状"})
        else:
            preserved.append(relative)
    report = {"mode": "check" if args.check else "preview" if args.dry_run else "create",
              "root": str(root), "directories_total": len(directories), "files_total": len(files),
              "missing_directories": missing_dirs, "missing_files": missing_files,
              "preserved_files": len(preserved), "conflicts": conflicts,
              "external_sources_verified": False}
    if conflicts:
        report["status"] = "conflict_no_writes"
        code = 2
    elif args.check:
        report["status"] = "incomplete" if missing_dirs or missing_files else "verified"
        code = 1 if missing_dirs or missing_files else 0
    elif args.dry_run:
        report["status"], code = "preview_no_writes", 0
    else:
        root.mkdir(parents=True, exist_ok=True)
        for relative in missing_dirs:
            ensure_plain_path(root, relative).mkdir(exist_ok=True)
        for relative in missing_files:
            # Exclusive creation: never truncate even if a file appears after preflight.
            with ensure_plain_path(root, relative).open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(files[relative])
        report["status"], code = "created" if missing_dirs or missing_files else "unchanged", 0
        report["created_directories"], report["created_files"] = len(missing_dirs), len(missing_files)
        report.pop("missing_directories")
        report.pop("missing_files")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="目标工作区；不迁移、不覆盖已有内容")
    parser.add_argument("--config", help="可选 JSON 配置文件")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="只读预览，无写入")
    mode.add_argument("--check", action="store_true", help="只读检查目录和模板内容")
    args = parser.parse_args()
    try:
        return run(args)
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({"status": "error", "error": str(error),
                          "note": "未覆盖已有文件；若执行中遇到 I/O 错误，可能已创建部分新项目，可核查后重跑"},
                         ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
