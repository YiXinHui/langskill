#!/usr/bin/env python3
import json
from pathlib import Path
from xml.etree import ElementTree
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
init = (ROOT / "references" / "initialization.md").read_text(encoding="utf-8")
source = (ROOT / "references" / "source-intake.md").read_text(encoding="utf-8")
storage = (ROOT / "references" / "storage-contract.md").read_text(encoding="utf-8")
libraries = (ROOT / "references" / "library-contracts.md").read_text(encoding="utf-8")
growth = (ROOT / "references" / "review-and-growth.md").read_text(encoding="utf-8")
config = (ROOT / "assets" / "starter-config.example.yaml").read_text(encoding="utf-8")
evals = json.loads((ROOT / "evals" / "evals.json").read_text(encoding="utf-8"))
workbook_path = ROOT / "assets" / "knowledge-extraction-starter.xlsx"

require(skill.startswith("---\nname: lang-knowledge-extraction\n"), "invalid public skill identity")
for reference in [
    "initialization.md",
    "source-intake.md",
    "library-contracts.md",
    "storage-contract.md",
    "review-and-growth.md",
]:
    require(f"references/{reference}" in skill, f"missing route to {reference}")

require("只启用 `concepts` 与 `judgments`" in skill, "starter must stay two-library")
require("preview_then_confirm" in skill and "默认私有" in skill, "safe first-run defaults missing")
require("配置不存在" in skill and "初始化" in skill, "missing first-run initialization route")
require("截图" in source and "OCR" in source and "partial" in source, "screenshot evidence contract missing")
require("录音" in source and "时间戳" in source and "说话人" in source, "audio evidence contract missing")
require("AI 提议" in source and "明确采用" in source, "AI conversation attribution boundary missing")
require("飞书" in init and "钉钉" in init and "企微" in init and "本地工作簿" in init, "carrier examples missing")
for mode in ["structured_table", "workbook", "document_table", "database"]:
    require(mode in storage and mode in config, f"storage mode missing: {mode}")
for library in ["concepts", "judgments", "cases", "quotes"]:
    require(library in config, f"config mapping missing: {library}")
require("事实摘录、待办、流程步骤、数据口径" in libraries, "judgment negative boundary missing")
require("情境" in libraries and "行动" in libraries and "结果" in libraries and "机制" in libraries, "case closure missing")
require("AI 只能生成候选" in libraries, "AI confirmation boundary missing")
require("两套当前知识" in skill and "一个当前权威源" in storage, "single authority rule missing")
require("增加案例库" in growth and "增加金句库" in growth and "启用自动批处理" in growth, "growth gates missing")
require(evals["skill_name"] == "lang-knowledge-extraction" and len(evals["evals"]) >= 6, "insufficient eval coverage")

require(workbook_path.exists(), "starter workbook missing")
with ZipFile(workbook_path) as archive:
    names = set(archive.namelist())
    require("xl/workbook.xml" in names, "starter workbook package is invalid")
    workbook_xml = ElementTree.fromstring(archive.read("xl/workbook.xml"))
    namespace = {"x": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    sheet_names = [item.attrib["name"] for item in workbook_xml.findall("x:sheets/x:sheet", namespace)]
    require(sheet_names == ["使用说明", "概念库", "判断库"], "starter workbook sheets are invalid")
    concept_xml = ElementTree.fromstring(archive.read("xl/worksheets/sheet2.xml"))
    judgment_xml = ElementTree.fromstring(archive.read("xl/worksheets/sheet3.xml"))
    concept_headers = [item.text for item in concept_xml.findall(".//x:row[@r='1']/x:c/x:is/x:t", namespace)]
    judgment_headers = [item.text for item in judgment_xml.findall(".//x:row[@r='1']/x:c/x:is/x:t", namespace)]
    require(concept_headers[1] == "概念名称", "concept workbook header missing")
    require(judgment_headers[1] == "判断", "judgment workbook header missing")
    formulas = [
        element.text
        for xml_name in ["xl/worksheets/sheet1.xml", "xl/worksheets/sheet2.xml", "xl/worksheets/sheet3.xml"]
        for element in ElementTree.fromstring(archive.read(xml_name)).findall(".//x:f", namespace)
    ]
    require(not formulas, f"starter workbook contains unexpected formulas: {formulas}")

print("OK: lang-knowledge-extraction static checks passed")
