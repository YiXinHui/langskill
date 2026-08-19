#!/usr/bin/env node

import { execFile } from "node:child_process";
import { promisify } from "node:util";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

const execFileAsync = promisify(execFile);
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const checker = path.join(root, "skills", "lang", "scripts", "check-remote-update.mjs");

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function runCheck(server, version) {
  server.version = version;
  const { stdout } = await execFileAsync(process.execPath, [checker], {
    env: { ...process.env, LANGSKILL_VERSION_URL: `http://127.0.0.1:${server.address().port}/VERSION` },
    maxBuffer: 1024 * 1024,
  });
  return JSON.parse(stdout);
}

const server = http.createServer((request, response) => {
  response.writeHead(200, { "content-type": "text/plain" });
  response.end(server.version);
});

try {
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));

  const ahead = await runCheck(server, "99.0.0");
  assert(ahead.status === "update_available", `expected update_available, got ${ahead.status}`);

  const current = await runCheck(server, ahead.local_version);
  assert(current.status === "up_to_date", `expected up_to_date, got ${current.status}`);

  const invalid = await runCheck(server, "not-a-version");
  assert(invalid.status === "invalid_remote_version", `expected invalid_remote_version, got ${invalid.status}`);

  console.log("OK: lang update checker distinguishes remote ahead, current, and invalid versions");
} finally {
  await new Promise((resolve) => server.close(resolve));
}
