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
  const sharedInstallCommand = "npx skills add YiXinHui/langskill -g -a codex claude-code -s '*' -y";
  const codeBuddyInstallCommand = "npx skills add YiXinHui/langskill -g -a codebuddy -s '*' -y";
  if (!readme.includes(sharedInstallCommand)) {
    fail("README does not use the shared Codex + Claude Code global install command");
  }
  if (!readme.includes(codeBuddyInstallCommand)) {
    fail("README does not provide the CodeBuddy global install command");
  }
  for (const boundary of ["~/.agents/skills/", "~/.codebuddy/skills/", "Codex", "Claude Code", "CodeBuddy"]) {
    if (!upgradeSkill.includes(boundary)) {
      fail(`lang-upgrade cross-platform boundary missing: ${boundary}`);
    }
  }
  if (!upgradeSkill.includes(sharedInstallCommand) || !upgradeSkill.includes(codeBuddyInstallCommand)) {
    fail("lang-upgrade does not converge Codex/Claude Code and CodeBuddy installs");
  }
  if (!upgradeSkill.includes("必须单独执行，不能和上面合并")) {
    fail("lang-upgrade does not protect the separate CodeBuddy install step");
  }
  if (upgradeSkill.includes("只支持通过 `~/.claude/skills/` 安装的版本")) {
    fail("lang-upgrade still declares Claude-only support");
  }
  const packageVersion = (await fs.readFile(path.join(root, "VERSION"), "utf8")).trim();
  const bundledLangVersion = (await fs.readFile(path.join(root, "skills", "lang", "VERSION"), "utf8"))
    .trim();
  if (!/^\d+\.\d+\.\d+$/.test(packageVersion) || bundledLangVersion !== packageVersion) {
    fail("skills/lang/VERSION must match the package VERSION for installed update checks");
  }
  const langSkill = await fs.readFile(path.join(root, "skills", "lang", "SKILL.md"), "utf8");
  if (!langSkill.includes("references/update-check.md")) {
    fail("lang entry does not route through the load-time update check");
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

  const businessDiagnosisDir = path.join(root, "skills", "lang-business-diagnosis");
  const businessDiagnosis = await fs.readFile(path.join(businessDiagnosisDir, "SKILL.md"), "utf8");
  for (const reference of [
    "experience-contract.md",
    "report-contract.md",
    "lead-card-contract.md",
    "handoff-compat.md",
  ]) {
    try {
      await fs.access(path.join(businessDiagnosisDir, "references", reference));
    } catch {
      fail(`business diagnosis reference missing: ${reference}`);
    }
    if (!businessDiagnosis.includes(`references/${reference}`)) {
      fail(`business diagnosis does not route to reference: ${reference}`);
    }
  }
  for (const boundary of [
    "先给结果预期，再识别入口",
    "一次只问一个问题",
    "回放确认",
    "商业分析前置",
    "破手段执念",
    "结尾交付三件套",
    "全程零广告",
    "基础先行",
    "自愿导出的线索卡草稿",
  ]) {
    if (!businessDiagnosis.includes(boundary)) {
      fail(`business diagnosis boundary missing: ${boundary}`);
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
