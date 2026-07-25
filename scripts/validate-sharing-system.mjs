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

  const wutaiSkill = await fs.readFile(path.join(root, "skills", "lang-wutai-dialogue", "SKILL.md"), "utf8");
  for (const stage of ["第一关：定题", "第二关：排席", "第三关：各自立论", "第四关：对席追问", "第五关：山主收束"]) {
    if (!wutaiSkill.includes(stage)) fail(`wutai independent dialogue stage missing: ${stage}`);
  }

  if (!process.exitCode) {
    console.log(`OK: ${actual.length} public skills are catalogued and structurally valid`);
  }
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
