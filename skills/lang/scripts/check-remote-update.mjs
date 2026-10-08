#!/usr/bin/env node

import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const DEFAULT_VERSION_URL = "https://raw.githubusercontent.com/YiXinHui/langskill/main/VERSION";
const REQUEST_TIMEOUT_MS = 3000;

function parseVersion(value) {
  const match = String(value ?? "").trim().match(/^v?(\d+)\.(\d+)\.(\d+)$/);
  if (!match) return null;
  return { major: Number(match[1]), minor: Number(match[2]), patch: Number(match[3]) };
}

function compareVersions(left, right) {
  for (const key of ["major", "minor", "patch"]) {
    if (left[key] !== right[key]) return left[key] > right[key] ? 1 : -1;
  }
  return 0;
}

async function exists(target) {
  try {
    await fs.access(target);
    return true;
  } catch {
    return false;
  }
}

async function findRepositoryRoot(start) {
  let current = start;
  while (true) {
    const isRoot = await Promise.all([
      exists(path.join(current, "VERSION")),
      exists(path.join(current, "skill-catalog.json")),
      exists(path.join(current, "skills", "lang", "SKILL.md")),
    ]);
    if (isRoot.every(Boolean)) return current;
    const parent = path.dirname(current);
    if (parent === current) return null;
    current = parent;
  }
}

async function readFirstLine(target) {
  try {
    const value = await fs.readFile(target, "utf8");
    return value.trim().split(/\r?\n/, 1)[0].trim();
  } catch {
    return "";
  }
}

async function resolveLocalVersion(scriptDirectory) {
  const repositoryRoot = await findRepositoryRoot(scriptDirectory);
  if (repositoryRoot) {
    const value = await readFirstLine(path.join(repositoryRoot, "VERSION"));
    if (parseVersion(value)) {
      return { value, source: "repository", path: path.join(repositoryRoot, "VERSION") };
    }
  }

  const bundledVersionFile = path.join(scriptDirectory, "..", "VERSION");
  const bundledValue = await readFirstLine(bundledVersionFile);
  if (parseVersion(bundledValue)) return { value: bundledValue, source: "bundled_skill", path: bundledVersionFile };

  const versionFile = process.env.LANGSKILL_VERSION_FILE || path.join(os.homedir(), ".agents", ".langskill-version");
  const value = await readFirstLine(versionFile);
  if (parseVersion(value)) return { value, source: "installation", path: versionFile };
  return { value: "", source: "unknown", path: versionFile };
}

async function fetchRemoteVersion(url) {
  if (typeof fetch !== "function") throw new Error("fetch unavailable");
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(url, {
      signal: controller.signal,
      headers: { accept: "text/plain" },
      redirect: "error",
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return (await response.text()).trim().split(/\r?\n/, 1)[0].trim();
  } finally {
    clearTimeout(timeout);
  }
}

function output(payload) {
  process.stdout.write(`${JSON.stringify({ checked_at: new Date().toISOString(), ...payload })}\n`);
}

async function main() {
  const local = await resolveLocalVersion(path.dirname(path.resolve(fileURLToPath(import.meta.url))));
  const remoteUrl = process.env.LANGSKILL_VERSION_URL || DEFAULT_VERSION_URL;

  let remoteValue;
  try {
    remoteValue = await fetchRemoteVersion(remoteUrl);
  } catch (error) {
    output({ status: "check_unavailable", local_version: local.value || null, local_source: local.source, error: error.name === "AbortError" ? "timeout" : "request_failed" });
    return;
  }

  const remote = parseVersion(remoteValue);
  if (!remote) {
    output({ status: "invalid_remote_version", local_version: local.value || null, local_source: local.source, remote_version: remoteValue || null });
    return;
  }

  const localParsed = parseVersion(local.value);
  if (!localParsed) {
    output({ status: "local_version_unknown", local_version: null, local_source: local.source, remote_version: remoteValue });
    return;
  }

  const comparison = compareVersions(remote, localParsed);
  output({
    status: comparison > 0 ? "update_available" : comparison < 0 ? "local_ahead" : "up_to_date",
    local_version: local.value,
    local_source: local.source,
    remote_version: remoteValue,
    remote_url: remoteUrl,
  });
}

main().catch(() => {
  output({ status: "check_unavailable", local_version: null, local_source: "unknown", error: "unexpected_error" });
});
