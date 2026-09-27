#!/usr/bin/env python3
"""Initialize one company's portable Source of Truth module. Python 3.9+ only."""
import argparse
from datetime import date
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlsplit

from init_sot import (SKILL, checked_root, encode_local_links, ensure_plain_path,
                      path_key, read_json)

ASSETS = SKILL / "assets"
STATE = ".docs/sot-company-config.json"
VERSION = "company-1.0"
AUTHORITIES = {
    "company_knowledge": ("公司可复用知识", "04-运营/"),
    "customers": ("客户列表与当前状态", "02-客户/客户索引.md"),
    "customer_events": ("客户沟通事件", "02-客户/沟通记录/"),
    "customer_materials": ("客户稳定档案与原始材料", "02-客户/档案与材料/"),
    "products": ("产品定义、方案与定价", "01-产品/"),
    "content": ("内容成品与发布记录", "03-内容/"),
    "finance": ("财务记录与凭证", "06-财务/"),
    "hr": ("员工、合作伙伴与招聘", "08-人力资源/"),
}


def normalized_config(given):
    defaults = read_json(ASSETS / "company-template.json")
    if not isinstance(given, dict) or set(given) - set(defaults):
        raise ValueError("公司配置必须为对象，且只能使用 company-template.json 中的字段")
    config = {**defaults, **given}
    name = config["company_name"]
    if (not isinstance(name, str) or not name.strip() or name != name.strip()
            or len(name) > 60 or re.search(r'[\\/<>:"|?*`\[\]{}#\x00-\x1f\x7f]', name)):
        raise ValueError("company_name 必须是合法的单层名称")
    projects = config["projects_root"]
    if (not isinstance(projects, str) or not projects.strip()
            or re.search(r'[\r\n`\x00|]', projects)
            or not (Path(projects).is_absolute() or projects.startswith("~/"))):
        raise ValueError("projects_root 必须是绝对路径或 ~/ 开头的路径")
    structure = read_json(ASSETS / "company-structure.json")
    extras = config["extra_directories"]
    if not isinstance(extras, dict):
        raise ValueError("extra_directories 必须是路径到用途的对象")
    reserved = {path_key(top) for top in structure}
    for top, spec in structure.items():
        reserved.update(path_key(top + "/" + child) for child in spec["children"])
    for relative, purpose in extras.items():
        if (not isinstance(relative, str) or len(relative) > 220
                or relative.startswith("/") or any(not part or part.startswith(".")
                or part.endswith(".") or part != part.strip() for part in relative.split("/"))
                or re.search(r'[\\<>:"|?*`\[\]{}#\x00-\x1f\x7f]', relative)):
            raise ValueError(f"非法补充目录路径：{relative}")
        if relative.split("/")[0] not in structure or "/" not in relative:
            raise ValueError(f"补充目录必须位于已有公司职能目录下：{relative}")
        if path_key(relative) in reserved or "/.docs/" in relative + "/":
            raise ValueError(f"补充目录不能重定义基础职责或治理目录：{relative}")
        if (not isinstance(purpose, str) or not purpose.strip() or len(purpose) > 300
                or re.search(r'[\x00-\x1f\x7f|{}]', purpose)):
            raise ValueError(f"补充目录必须有单行用途说明：{relative}")
    given_authorities = given.get("authorities", {})
    if not isinstance(given_authorities, dict) or set(given_authorities) - set(AUTHORITIES):
        raise ValueError("authorities 包含未知类别或不是对象")
    config["authorities"] = {**defaults["authorities"], **given_authorities}
    for key, url in config["authorities"].items():
        if url is None:
            continue
        if not isinstance(url, str) or re.search(r'[\s<>|`]', url):
            raise ValueError(f"{key} 必须是完整 HTTPS URL 或 null")
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError(f"{key} 必须是无登录凭据的 HTTPS URL")
    return config


def build(config, initialized_on):
    structure = read_json(ASSETS / "company-structure.json")
    directories, files = set(), {}

    def add(relative, content):
        if relative in files:
            raise ValueError(f"重复生成路径：{relative}")
        files[relative] = encode_local_links(content)

    top_rows = []
    for top, spec in structure.items():
        directories.add(top)
        rows = [(child, purpose) for child, purpose in spec["children"].items()]
        rows.extend((relative[len(top) + 1:], purpose)
                    for relative, purpose in config["extra_directories"].items()
                    if relative.startswith(top + "/"))
        for child, _ in rows:
            directories.add(top + "/" + child)
        child_table = ("| 子目录 | 职责 |\n|---|---|\n" +
                       "\n".join(f"| `{child}/` | {purpose} |" for child, purpose in rows)) if rows else "本模板不预建业务实体子目录；按实际业务补充。"
        add(top + "/.docs/README.md", f"# {top}\n\n定位：{spec['purpose']}。\n\n{child_table}\n\n"
            f"## 使用边界\n\n- {spec['rule']}\n- 正式数据的唯一来源见 [公司 Source of Truth](../../.docs/SOURCE_OF_TRUTH.md)；云端配置须在实际读写时核验。\n- 改变本目录职责或权威源时，同步维护本页和公司总索引。\n")
        top_rows.append(f"| `{top}/` | {spec['purpose']} | [管理说明](../{top}/.docs/README.md) |")
    authority_rows = []
    for key, (label, local) in AUTHORITIES.items():
        remote = config["authorities"][key]
        source = f"[云端入口](<{remote}>)" if remote else f"`{local}`"
        role = "本地只作入口、草稿、缓存或历史资料" if remote else "本地维护（新公司工作区默认）"
        authority_rows.append(f"| {label} | {source} | {role} |")
    add(".docs/SOURCE_OF_TRUTH.md", f"# {config['company_name']} — Source of Truth\n\n"
        f"初始化日期：{initialized_on}。本文件是此公司工作区唯一维护的文件地图与数据权威索引。\n\n"
        "## 职能目录\n\n| 目录 | 职责 | 最近规则 |\n|---|---|---|\n" + "\n".join(top_rows) + "\n\n"
        "## 数据权威\n\n| 数据类别 | 唯一正式来源 | 本地角色 |\n|---|---|---|\n" + "\n".join(authority_rows) + "\n\n"
        "- 云端 URL 来自使用者配置，初始化未联网验证；读写前核对现网资源、权限和当前版本。\n"
        "- 未配置云端时，本地是新公司工作区的初始权威源；后续切换须更新本索引和受影响的模块入口。\n"
        "- 客户当前状态、沟通流水和稳定材料分别核对；业务数字、价格、客户结果和引语回到原始证据。\n"
        "- `.docs/sot-company-config.json` 仅记录初始化参数，不是另一份业务权威索引。\n\n"
        "## 维护规则\n\n"
        "1. 新资料先看内容和主体，再按职能放置；公司、客户和合作伙伴分别识别。\n"
        "2. 正式产物进入唯一权威源；草稿与历史资料标明状态，不把缓存冒充现行版本。\n"
        f"3. 新代码工程放 `{config['projects_root']}/<project>/`；`05-开发/` 只放治理与历史说明。\n"
        "4. 移动、归档或修改权威源前核对内容与引用；变更后更新本索引及最近 `.docs/README.md`。\n"
        "5. 本模板只初始化目录与空白入口，不迁移旧资料、不创建云端资源、不启用同步。\n")
    add(".docs/README.md", "# 公司治理入口\n\n先读 [Source of Truth](SOURCE_OF_TRUTH.md)，再读目标职能目录最近的 `.docs/README.md`。\n")
    pointer = "# 公司 AI 入口\n\n查找、创建或整理资料前，读取 [.docs/SOURCE_OF_TRUTH.md](.docs/SOURCE_OF_TRUTH.md)，再读目标职能目录的 `.docs/README.md`。\n"
    add("AGENTS.md", pointer)
    add("CLAUDE.md", pointer)
    add("02-客户/客户索引.md", "# 客户索引\n\n" + (
        "客户当前状态以云端权威源为准，见 [总索引](../.docs/SOURCE_OF_TRUTH.md)；此处只作导航。\n"
        if config["authorities"]["customers"] else
        "状态：尚未登记客户。当前状态在此维护；沟通流水与稳定材料分别进入对应权威源。\n\n| 客户 | 当前状态 | 稳定档案 | 最近沟通 | 更新日期与来源 |\n|---|---|---|---|---|\n"))
    state = {"template_version": VERSION, "initialized_on": initialized_on, "config": config}
    files[STATE] = json.dumps(state, ensure_ascii=False, indent=2) + "\n"
    for relative in list(directories) + list(files):
        for parent in Path(relative).parents:
            if str(parent) != ".":
                directories.add(parent.as_posix())
    planned = {}
    for kind, paths in (("directory", directories), ("file", files)):
        for relative in paths:
            key = path_key(relative)
            if key in planned:
                raise ValueError(f"计划路径存在文件/目录或名称别名冲突：{planned[key]} 与 {relative}")
            planned[key] = relative
    return sorted(directories, key=lambda p: (len(Path(p).parts), p)), files


def run(args):
    root = checked_root(args.root)
    if root == SKILL or root.is_relative_to(SKILL):
        raise ValueError("不要把公司工作区创建在 Skill 内")
    if ensure_plain_path(root, ".docs/sot-config.json").exists():
        raise ValueError("目标已有个人与业务综合工作区；公司模块须使用独立目标目录")
    state_path = ensure_plain_path(root, STATE)
    saved = read_json(state_path) if state_path.exists() else None
    if saved is not None:
        if not isinstance(saved, dict) or set(saved) != {"template_version", "initialized_on", "config"}:
            raise ValueError("已有公司初始化记录格式无效；请人工核对，未写入")
        if saved["template_version"] != VERSION:
            raise ValueError("公司模板版本不同，初始化脚本不执行升级或迁移")
        initialized_on = date.fromisoformat(saved["initialized_on"]).isoformat()
        config = normalized_config(saved["config"])
        if args.config and normalized_config(read_json(Path(args.config).expanduser())) != config:
            raise ValueError("目标已采用不同配置，不能通过初始化切换名称或权威源")
    else:
        initialized_on = date.today().isoformat()
        config = normalized_config(read_json(Path(args.config).expanduser()) if args.config else {})
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
        report["status"], code = "conflict_no_writes", 2
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
            with ensure_plain_path(root, relative).open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(files[relative])
        report["status"], code = ("created" if missing_dirs or missing_files else "unchanged"), 0
        report["created_directories"], report["created_files"] = len(missing_dirs), len(missing_files)
        del report["missing_directories"], report["missing_files"]
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, help="公司工作区目标；不迁移、不覆盖已有内容")
    parser.add_argument("--config", help="可选公司 JSON 配置")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="只读预览，无写入")
    mode.add_argument("--check", action="store_true", help="只读验收")
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
