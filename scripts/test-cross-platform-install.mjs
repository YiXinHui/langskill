#!/usr/bin/env node
import { execFile } from "node:child_process";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";

const execFileAsync = promisify(execFile);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const catalog = JSON.parse(await fs.readFile(path.join(root, "skill-catalog.json"), "utf8"));
const expectedIds = catalog.skills.map((skill) => skill.id).sort();
const testRoot = await fs.mkdtemp(path.join(os.tmpdir(), "langskill-install-"));

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

try {
  await fs.mkdir(path.join(testRoot, ".codex"));
  await execFileAsync(
    "npx",
    ["skills", "add", root, "-s", "*", "-a", "codex", "claude-code", "-y"],
    {
      cwd: testRoot,
      env: { ...process.env, DISABLE_TELEMETRY: "1", NO_COLOR: "1" },
      maxBuffer: 10 * 1024 * 1024,
    },
  );

  const canonicalRoot = path.join(testRoot, ".agents", "skills");
  const actualIds = (await fs.readdir(canonicalRoot)).sort();
  assert(JSON.stringify(actualIds) === JSON.stringify(expectedIds), "canonical install set differs from skill-catalog.json");

  for (const id of expectedIds) {
    await fs.access(path.join(canonicalRoot, id, "SKILL.md"));
    const claudeEntry = path.join(testRoot, ".claude", "skills", id);
    assert((await fs.lstat(claudeEntry)).isSymbolicLink(), `Claude Code entry is not a symlink: ${id}`);
    assert((await fs.readlink(claudeEntry)) === `../../.agents/skills/${id}`, `Claude Code entry bypasses shared root: ${id}`);
    try {
      await fs.lstat(path.join(testRoot, ".codex", "skills", id));
      throw new Error(`duplicate Codex entry exists: ${id}`);
    } catch (error) {
      if (error?.code !== "ENOENT") throw error;
    }
  }

  const { stdout } = await execFileAsync("npx", ["skills", "list", "--json"], {
    cwd: testRoot,
    env: { ...process.env, DISABLE_TELEMETRY: "1", NO_COLOR: "1" },
    maxBuffer: 10 * 1024 * 1024,
  });
  const installed = JSON.parse(stdout).filter((skill) => expectedIds.includes(skill.name));
  assert(installed.length === expectedIds.length, `discovery count is ${installed.length}, expected ${expectedIds.length}`);
  for (const skill of installed) {
    assert(skill.agents.includes("Codex"), `Codex cannot discover ${skill.name}`);
    assert(skill.agents.includes("Claude Code"), `Claude Code cannot discover ${skill.name}`);
  }

  console.log(`OK: ${expectedIds.length} skills install through one shared root and are discoverable by Codex and Claude Code`);
} finally {
  await fs.rm(testRoot, { recursive: true, force: true });
}
