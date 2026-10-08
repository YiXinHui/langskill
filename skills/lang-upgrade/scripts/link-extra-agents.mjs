#!/usr/bin/env node
// 把 ~/.agents/skills 里的 LangSkill 接入 `skills` 安装器不支持的 Agent（目前是豆包电脑版与豆包工作模式）。
// 只建链接（Windows 用目录联接），不复制正文；已有同名内容一律保留并报告，除非显式 --refresh-copies。
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

const args = new Set(process.argv.slice(2));
if (args.has("--help") || args.has("-h")) {
  console.log(`用法：node link-extra-agents.mjs [--dry-run] [--refresh-copies]

  --dry-run         只报告将要做什么，不改文件
  --refresh-copies  同名位置是旧的 LangSkill 实体副本时，先备份到 ~/.agents/backups/ 再换成链接

环境变量 LANGSKILL_HOME 可替换用户目录（测试用）。`);
  process.exit(0);
}
const isDryRun = args.has("--dry-run");
const shouldRefreshCopies = args.has("--refresh-copies");
const home = process.env.LANGSKILL_HOME || os.homedir();
const isWindows = process.platform === "win32";
const sharedRoot = path.join(home, ".agents", "skills");

const DOUBAO_APP_DIRS = ["Doubao", "DoubaoWork"];
const MAX_SEARCH_DEPTH = 5;

async function exists(target) {
  try {
    await fs.lstat(target);
    return true;
  } catch {
    return false;
  }
}

function appDataBases() {
  if (isWindows) {
    return [
      process.env.APPDATA || path.join(home, "AppData", "Roaming"),
      process.env.LOCALAPPDATA || path.join(home, "AppData", "Local"),
    ];
  }
  return [path.join(home, "Library", "Application Support")];
}

async function findWorkspaces(dir, depth) {
  if (depth > MAX_SEARCH_DEPTH) return [];
  let entries;
  try {
    entries = await fs.readdir(dir, { withFileTypes: true });
  } catch {
    return [];
  }
  if (path.basename(dir) === "workspace" && path.basename(path.dirname(dir)) === "agent_mode") {
    return [dir];
  }
  const found = [];
  for (const entry of entries) {
    if (!entry.isDirectory() || entry.name === ".sessions" || entry.name === "Cache") continue;
    found.push(...(await findWorkspaces(path.join(dir, entry.name), depth + 1)));
  }
  return found;
}

async function discoverDoubaoRoots() {
  const roots = [];
  for (const base of appDataBases()) {
    for (const appDir of DOUBAO_APP_DIRS) {
      const appRoot = path.join(base, appDir);
      if (!(await exists(appRoot))) continue;
      for (const workspace of await findWorkspaces(appRoot, 0)) {
        roots.push({ agent: appDir === "DoubaoWork" ? "豆包工作" : "豆包", root: path.join(workspace, ".user_skills") });
      }
    }
  }
  return roots;
}

async function listLangSkills() {
  let entries;
  try {
    entries = await fs.readdir(sharedRoot, { withFileTypes: true });
  } catch {
    return [];
  }
  const skills = [];
  for (const entry of entries) {
    if (entry.name !== "lang" && !entry.name.startsWith("lang-")) continue;
    if (await exists(path.join(sharedRoot, entry.name, "SKILL.md"))) skills.push(entry.name);
  }
  return skills.sort();
}

async function readSkillName(dir) {
  try {
    const text = await fs.readFile(path.join(dir, "SKILL.md"), "utf8");
    return text.match(/^name:\s*["']?([^"'\n]+)["']?\s*$/m)?.[1].trim() ?? null;
  } catch {
    return null;
  }
}

async function linkOne(source, entry, backupDir) {
  const stat = await fs.lstat(entry).catch(() => null);
  if (stat?.isSymbolicLink()) {
    const current = path.resolve(path.dirname(entry), await fs.readlink(entry));
    if (current === path.resolve(source)) return "existing";
    return "conflict";
  }
  if (stat) {
    const isOldCopy = stat.isDirectory() && (await readSkillName(entry)) === path.basename(source);
    if (!isOldCopy) return "conflict";
    if (!shouldRefreshCopies) return "stale_copy";
    if (!isDryRun) {
      await fs.mkdir(backupDir, { recursive: true });
      await fs.rename(entry, path.join(backupDir, path.basename(entry)));
    }
  }
  if (!isDryRun) await fs.symlink(source, entry, isWindows ? "junction" : "dir");
  return stat ? "refreshed" : "created";
}

const skills = await listLangSkills();
if (skills.length === 0) {
  console.error(`没有在 ${sharedRoot} 找到 LangSkill。先运行 npx skills add YiXinHui/langskill -g -a codex claude-code -s '*' -y`);
  process.exit(1);
}

const stamp = new Date().toISOString().replace(/[-:]/g, "").replace("T", "-").slice(0, 15);
const backupRoot = path.join(home, ".agents", "backups", `langskill-doubao-${stamp}`);
const report = { dry_run: isDryRun, shared_root: sharedRoot, skills: skills.length, targets: [] };

for (const [index, { agent, root }] of (await discoverDoubaoRoots()).entries()) {
  const result = { agent, root, created: [], refreshed: [], existing: [], stale_copy: [], conflict: [] };
  const backupDir = path.join(backupRoot, `${index + 1}-${agent}`);
  if (!isDryRun) await fs.mkdir(root, { recursive: true });
  for (const name of skills) {
    const status = await linkOne(path.join(sharedRoot, name), path.join(root, name), backupDir);
    result[status].push(name);
  }
  report.targets.push(result);
}

if (report.targets.length === 0) {
  report.note = "本机没有找到豆包电脑版或豆包工作模式的技能目录；没装豆包可忽略。装了的话先打开一次豆包的「技能」页再重跑。";
}
if (report.targets.some((target) => target.stale_copy.length > 0)) {
  report.note = "豆包里有旧的 LangSkill 副本，不会跟着升级。加 --refresh-copies 重跑，会先备份再换成链接。";
}
if (report.targets.some((target) => target.conflict.length > 0)) {
  report.note = "conflict 里的同名位置不是 LangSkill 或指向别处，已保留未动；请人工确认后再处理。";
}
console.log(JSON.stringify(report, null, 2));
process.exit(report.targets.some((target) => target.conflict.length > 0) ? 2 : 0);
