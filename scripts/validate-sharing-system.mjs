#!/usr/bin/env node
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const catalogPath = path.join(root, "skill-catalog.json");
const renamesPath = path.join(root, "skill-renames.json");

function fail(message) {
  console.error(`ERROR: ${message}`);
  process.exitCode = 1;
}

async function main() {
  const catalog = JSON.parse(await fs.readFile(catalogPath, "utf8"));
  const renames = JSON.parse(await fs.readFile(renamesPath, "utf8"));
  if (catalog.schema_version !== 1 || catalog.visibility !== "public") {
    fail("skill-catalog.json schema or visibility is invalid");
    return;
  }

  const entries = new Map(catalog.skills.map((skill) => [skill.id, skill]));
  if (entries.size !== catalog.skills.length) fail("duplicate skill id in catalog");

  const actual = (await fs.readdir(path.join(root, "skills"), { withFileTypes: true }))
    .filter((entry) => entry.isDirectory() && !entry.name.endsWith("-workspace"))
    .map((entry) => entry.name)
    .sort();

  for (const dir of actual) {
    if (dir !== "lang" && !/^lang-[a-z0-9]+(?:-[a-z0-9]+)*$/.test(dir)) {
      fail(`public skill id must be English and use lang-* format: ${dir}`);
    }
    const skillPath = path.join(root, "skills", dir, "SKILL.md");
    try {
      await fs.access(skillPath);
    } catch {
      fail(`missing SKILL.md: skills/${dir}`);
      continue;
    }
    if (![...entries.values()].some((entry) => entry.path === `skills/${dir}`)) {
      fail(`uncatalogued public skill: ${dir}`);
    }
  }

  for (const entry of entries.values()) {
    if (!new Set(["public-product", "public-core", "distribution"]).has(entry.role)) {
      fail(`invalid role for ${entry.id}: ${entry.role}`);
    }
    const skillMd = path.join(root, entry.path, "SKILL.md");
    const content = await fs.readFile(skillMd, "utf8").catch(() => "");
    if (!content.startsWith("---\n") || !/^name:\s*.+$/m.test(content) || !/^description:\s*(?:.+|\|)$/m.test(content)) {
      fail(`invalid frontmatter: ${entry.path}/SKILL.md`);
    }
    const frontmatterName = content.match(/^name:\s*(.+)$/m)?.[1]?.trim();
    if (frontmatterName !== entry.id || entry.path !== `skills/${entry.id}`) {
      fail(`skill id, directory and frontmatter name must match: ${entry.id}`);
    }
  }

  if (renames.schema_version !== 1 || typeof renames.renames !== "object") {
    fail("skill-renames.json schema is invalid");
  } else {
    for (const [oldName, newName] of Object.entries(renames.renames)) {
      if (actual.includes(oldName)) fail(`legacy skill directory still exists: ${oldName}`);
      if (!entries.has(newName)) fail(`rename target is not a current skill: ${oldName} -> ${newName}`);
    }
  }

  const readme = await fs.readFile(path.join(root, "README.md"), "utf8");
  const upgradeSkill = await fs.readFile(path.join(root, "skills", "lang-upgrade", "SKILL.md"), "utf8");
  const installCommand = "npx skills add YiXinHui/langskill -g -a codex claude-code -s '*' -y";
  if (!readme.includes(installCommand)) {
    fail("README does not use the shared Codex + Claude Code global install command");
  }
  for (const boundary of ["~/.agents/skills/", "Codex", "Claude Code"]) {
    if (!upgradeSkill.includes(boundary)) {
      fail(`lang-upgrade cross-platform boundary missing: ${boundary}`);
    }
  }
  if (!upgradeSkill.includes(installCommand)) {
    fail("lang-upgrade does not converge installs through the shared global command");
  }
  if (upgradeSkill.includes("只支持通过 `~/.claude/skills/` 安装的版本")) {
    fail("lang-upgrade still declares Claude-only support");
  }
  const upgradeEvals = JSON.parse(
    await fs.readFile(path.join(root, "skills", "lang-upgrade", "evals", "evals.json"), "utf8"),
  );
  if (upgradeEvals.skill_name !== "lang-upgrade" || upgradeEvals.evals?.length < 3) {
    fail("lang-upgrade needs at least three cross-platform regression evals");
  }

  const wutaiSkill = await fs.readFile(path.join(root, "skills", "lang-wutai-dialogue", "SKILL.md"), "utf8");
  for (const stage of ["第一关：定题", "第二关：排席", "第三关：各自立论", "第四关：对席追问", "第五关：山主收束"]) {
    if (!wutaiSkill.includes(stage)) fail(`wutai independent dialogue stage missing: ${stage}`);
  }

  const enterpriseDiagnosisDir = path.join(root, "skills", "lang-enterprise-ai-diagnosis");
  const enterpriseDiagnosis = await fs.readFile(path.join(enterpriseDiagnosisDir, "SKILL.md"), "utf8");
  for (const reference of [
    "entry-experience.md",
    "conversation-guide.md",
    "report-contract.md",
    "presentation-contract.md",
    "handoff-contract.md",
    "judgment-provider-contract.md",
  ]) {
    try {
      await fs.access(path.join(enterpriseDiagnosisDir, "references", reference));
    } catch {
      fail(`enterprise AI diagnosis reference missing: ${reference}`);
    }
    if (!enterpriseDiagnosis.includes(`references/${reference}`)) {
      fail(`enterprise AI diagnosis does not route to reference: ${reference}`);
    }
  }
  for (const reference of [
    "diagnosis-core.md",
    "case-model.md",
    "evidence-and-interaction.md",
    "method-registry.md",
  ]) {
    try {
      await fs.access(path.join(enterpriseDiagnosisDir, "references", "core", reference));
    } catch {
      fail(`enterprise AI diagnosis core reference missing: ${reference}`);
    }
    if (!enterpriseDiagnosis.includes(`references/core/${reference}`)) {
      fail(`enterprise AI diagnosis does not route to core reference: ${reference}`);
    }
  }
  for (const boundary of [
    "入口之后形成最小生意图",
    "整体扫描、具体业务问题或已有 AI 想法",
    "空激活首轮不预读完整诊断核心",
    "目标允许并行",
    "先保留候选，再选择焦点",
    "焦点选定后还原工作系统",
    "价值判断与 AI 判断分开",
    "每轮只有一个明确去向",
    "允许不做 AI",
    "默认拒绝内部逻辑和广告",
    "DiagnosisPresenterV2",
    "DiagnosisResultV3",
    "中立初诊摘要时，仍走 `DiagnosisPresenterV2",
    "明确要求把内容交给另一位咨询师、正式诊断项目或接收系统时",
    "结果块、分项、candidate change、最小验证、改判信号和限制都有 supporting claims",
    "非终局 ask 有且只有一个可回答动作",
  ]) {
    if (!enterpriseDiagnosis.includes(boundary)) {
      fail(`enterprise AI diagnosis boundary missing: ${boundary}`);
    }
  }
  for (const removedBoundary of ["最多 3 次用户回答", "user_turn_count >= 4", "l1_update_used"]) {
    if (enterpriseDiagnosis.includes(removedBoundary)) {
      fail(`enterprise AI diagnosis still contains a fixed runtime boundary: ${removedBoundary}`);
    }
  }

  if (!process.exitCode) {
    console.log(`OK: ${actual.length} public skills are catalogued and structurally valid`);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
