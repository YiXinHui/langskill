#!/usr/bin/env python3
"""检查一篇知识单元成稿有没有踩过的几类格式错。

用法：
  lark-cli docs +fetch --doc <token> | python3 check_unit.py --owner-name 狼哥
  python3 check_unit.py page.xml --owner-name 狼哥

只查能机械判断的：模板栏目、第三人称写本人、理论全堆页尾、缺开头、缺档位和一句话、
正文里的时间戳和过程注记、禁用词。「读着像不像本人」查不了，仍要本人看。
ERROR 必改；WARN 看情况。有 ERROR 时退出码为 1。
"""
import argparse
import json
import re
import sys

TEMPLATE_HEADINGS = ["核心命题", "误区澄清", "推理链", "适用边界", "错误认知", "正确认知", "核心差异"]
DEFAULT_BANNED = ["说白了", "值得注意的是", "综上所述", "不难发现", "总而言之", "让我们来看看"]
PROCESS_NOTES = ["校准", "本轮", "候选编号", "水库第"]


def load_content(path):
    raw = open(path, encoding="utf-8").read() if path else sys.stdin.read()
    raw = raw.strip()
    if raw.startswith("{"):
        data = json.loads(raw)
        return data["data"]["document"]["content"]
    return raw


def text_of(fragment):
    return re.sub(r"<[^>]+>", "", fragment)


def top_blocks(content):
    body = re.sub(r"<title[^>]*>.*?</title>", "", content, flags=re.S)
    pattern = r"<(h\d|p|blockquote|callout|ol|ul|table|checkbox)\b[^>]*>.*?</\1>"
    return [(m.group(1), m.group(0)) for m in re.finditer(pattern, body, flags=re.S)]


def check(content, owner_name, banned):
    errors, warns = [], []
    blocks = top_blocks(content)
    headings = [text_of(b) for tag, b in blocks if tag.startswith("h")]
    for heading in headings:
        if any(word in heading for word in TEMPLATE_HEADINGS):
            errors.append(f"小标题用了模板栏目：「{heading}」，小标题要写这个观点自己的事")

    body_blocks = [(tag, b) for tag, b in blocks if not text_of(b).startswith(("档位", "来源", "相关观点"))]
    body_text = "".join(text_of(b) for _, b in body_blocks)
    if owner_name:
        count = body_text.count(owner_name)
        if count:
            errors.append(f"正文出现 {count} 次「{owner_name}」，本人的观点要用第一人称写")

    quotes = [i for i, (tag, _) in enumerate(blocks) if tag == "blockquote"]
    tail = blocks[-4:]
    if any(text_of(b).startswith("依据") for _, b in tail) and not quotes:
        errors.append("理论只放在页尾「依据」里，要放进它支撑的那一段旁边的引用块")

    first = next(((tag, b) for tag, b in blocks), None)
    if first is None or first[0].startswith("h"):
        errors.append("标题下面直接是小标题，没有开头：先用一两句给出判断")

    full_text = text_of(content)
    if "档位" not in full_text:
        errors.append("页尾缺「档位」")
    if "一句话" not in full_text:
        warns.append("没有「一句话」收尾")
    if re.search(r"\b\d{1,2}:\d{2}:\d{2}\b", body_text):
        errors.append("正文里有时间戳，追溯信息只放页尾来源")
    for word in PROCESS_NOTES:
        if word in body_text:
            warns.append(f"正文出现过程词「{word}」，确认不是过程注记")
    occasion = re.findall(r"\d{1,2}\s*月\s*\d{1,2}\s*日[^。]{0,12}(?:跟|和|与)[^。]{0,16}(?:讲|聊|说|备课|开会)", body_text)
    if occasion:
        warns.append(f"正文像是在讲哪天跟谁讲过（如「{occasion[0]}」），讲述经过只放页尾来源")
    for word in banned:
        if word in body_text:
            errors.append(f"出现禁用词「{word}」")
    long_paras = [text_of(b) for tag, b in body_blocks if tag == "p" and len(text_of(b)) > 160]
    if long_paras:
        warns.append(f"{len(long_paras)} 段超过 160 字，读起来会成一坨，考虑拆开")
    if not quotes:
        warns.append("没有引用块：如果正文用到了理论或别人的话，要就近放引用块")
    return errors, warns


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("path", nargs="?", help="XML 文件或 lark-cli fetch 的 JSON；省略则读 stdin")
    parser.add_argument("--owner-name", default="", help="本人在第三人称时的称呼，如「狼哥」")
    parser.add_argument("--banned", default=",".join(DEFAULT_BANNED), help="逗号分隔的禁用词")
    args = parser.parse_args()
    content = load_content(args.path)
    banned = [w for w in args.banned.split(",") if w]
    errors, warns = check(content, args.owner_name, banned)
    for message in errors:
        print(f"ERROR {message}")
    for message in warns:
        print(f"WARN  {message}")
    if not errors and not warns:
        print("OK")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
