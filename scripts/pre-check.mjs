#!/usr/bin/env node
// 发布前敏感信息扫描。用法：node scripts/pre-check.mjs [仓库目录]
// 公开仓只跑通用规则；私人主库额外读取 internal/sensitive-words.txt（或 LANGSKILL_SENSITIVE_WORDS 指定的文件），
// 并跳过 internal/、internal/public.gitignore 与 internal/public-exclude.txt 排除的私人文件——它们不会导出到公开仓。
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(process.argv[2] || path.join(path.dirname(fileURLToPath(import.meta.url)), ".."));
const internalDir = path.join(root, "internal");

const GENERIC_RULES = [
  ["本机用户目录", /\/(?:Users|home)\/(?!<|user\b|USER\b|name\b|you\b|me\b)[A-Za-z0-9._-]+\//],
  ["Windows 用户目录", /[A-Za-z]:\\Users\\(?!<|Public\\)[A-Za-z0-9._-]+\\/],
  ["飞书资源链接", /feishu\.cn\/(?:docx|docs|base|wiki|drive|sheets|file|minutes|record)\/[A-Za-z0-9]{10,}/],
  ["飞书用户/群 ID", /\b(?:ou|oc|on)_[0-9a-f]{16,}\b/],
  ["微信 ID", /\bwxid_[a-z0-9]{6,}|\b\d{8,}@chatroom/],
  ["手机号", /(?<!\d)1[3-9]\d{9}(?!\d)/],
  ["密钥", /\bsk-[A-Za-z0-9_-]{20,}|\bghp_[A-Za-z0-9]{20,}|\bAKIA[A-Z0-9]{12,}|-----BEGIN [A-Z ]*PRIVATE KEY-----/],
];

function git(args) {
  return execFileSync("git", ["-C", root, ...args], { encoding: "utf8", maxBuffer: 64 * 1024 * 1024 });
}

function listFiles() {
  if (fs.existsSync(path.join(root, ".git"))) {
    return git(["ls-files", "-co", "--exclude-standard", "-z"]).split("\0").filter(Boolean);
  }
  const files = [];
  const walk = (dir) => {
    for (const entry of fs.readdirSync(path.join(root, dir), { withFileTypes: true })) {
      const relative = path.posix.join(dir, entry.name);
      if (entry.isDirectory()) {
        if (entry.name !== ".git" && entry.name !== "node_modules") walk(relative);
      } else {
        files.push(relative);
      }
    }
  };
  walk("");
  return files;
}

function privateFiles() {
  const excluded = new Set();
  for (const name of ["public.gitignore", "public-exclude.txt"]) {
    const file = path.join(internalDir, name);
    if (!fs.existsSync(file) || !fs.existsSync(path.join(root, ".git"))) continue;
    for (const relative of git(["ls-files", "-co", "-i", `--exclude-from=${file}`, "-z"]).split("\0")) {
      if (relative) excluded.add(relative);
    }
  }
  return excluded;
}

function loadWords() {
  const file = process.env.LANGSKILL_SENSITIVE_WORDS || path.join(internalDir, "sensitive-words.txt");
  if (!fs.existsSync(file)) return [];
  return fs.readFileSync(file, "utf8").split("\n")
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith("#"))
    .map((line) => {
      const [word, allow = ""] = line.split("|").map((part) => part.trim());
      return { word, allowed: new Set(allow.split(",").map((item) => item.trim()).filter(Boolean)) };
    });
}

const words = loadWords();
const skipped = privateFiles();
const findings = [];
for (const relative of listFiles()) {
  if (relative.startsWith("internal/") || skipped.has(relative)) continue;
  const absolute = path.join(root, relative);
  let text;
  try {
    text = fs.readFileSync(absolute, "utf8");
  } catch {
    continue;
  }
  if (text.includes("\0")) continue;
  text.split("\n").forEach((line, index) => {
    for (const [label, pattern] of GENERIC_RULES) {
      if (pattern.test(line)) findings.push(`${relative}:${index + 1} [${label}] ${line.trim().slice(0, 80)}`);
    }
    for (const { word, allowed } of words) {
      if (line.includes(word) && !allowed.has(relative)) {
        findings.push(`${relative}:${index + 1} [敏感词] ${line.trim().slice(0, 80)}`);
      }
    }
  });
}

console.log(`🔍 发布前敏感信息扫描：${root}（敏感词 ${words.length} 条${words.length ? "" : "，公开仓只跑通用规则"}）`);
if (findings.length > 0) {
  for (const finding of findings.slice(0, 80)) console.log(`  ❌ ${finding}`);
  if (findings.length > 80) console.log(`  … 共 ${findings.length} 处`);
  console.log("⛔ 有内容不能进公开仓：私人值放 personal-* / private-* 文件，或在私人主库的排除清单里排除。");
  process.exit(1);
}
console.log("  ✅ 无残留");
