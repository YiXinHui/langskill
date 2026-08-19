#!/usr/bin/env bash

set -u

live_check=0
if [[ "${1:-}" == "--live" ]]; then
  live_check=1
elif [[ $# -gt 0 ]]; then
  echo "USAGE_ERROR=1"
  echo "NEXT_ACTION=Run without arguments or with --live"
  exit 2
fi

if command -v node >/dev/null 2>&1; then
  echo "NODE_INSTALLED=1"
else
  echo "NODE_INSTALLED=0"
fi

if command -v npm >/dev/null 2>&1; then
  echo "NPM_INSTALLED=1"
else
  echo "NPM_INSTALLED=0"
fi

if ! command -v lark-cli >/dev/null 2>&1; then
  echo "LARK_CLI_INSTALLED=0"
  echo "LARK_SHARED_BUNDLED=0"
  echo "LARK_MINUTES_BUNDLED=0"
  echo "LARK_CONFIG_READY=0"
  echo "USER_AUTH_READY=0"
  echo "MINUTES_SCOPES_READY=0"
  echo "LIVE_MINUTES_READ=SKIPPED"
  echo "NEXT_ACTION=Install @larksuite/cli after user confirmation"
  exit 1
fi

echo "LARK_CLI_INSTALLED=1"

if lark-cli skills list lark-shared >/dev/null 2>&1; then
  echo "LARK_SHARED_BUNDLED=1"
else
  echo "LARK_SHARED_BUNDLED=0"
fi

if lark-cli skills list lark-minutes >/dev/null 2>&1; then
  echo "LARK_MINUTES_BUNDLED=1"
else
  echo "LARK_MINUTES_BUNDLED=0"
fi

if ! command -v node >/dev/null 2>&1; then
  echo "LARK_CONFIG_READY=0"
  echo "USER_AUTH_READY=0"
  echo "MINUTES_SCOPES_READY=0"
  echo "LIVE_MINUTES_READ=SKIPPED"
  echo "NEXT_ACTION=Install Node.js before continuing"
  exit 1
fi

auth_json="$(LARKSUITE_CLI_NO_UPDATE_NOTIFIER=1 LARKSUITE_CLI_NO_SKILLS_NOTIFIER=1 lark-cli auth status --json --verify 2>/dev/null)"
auth_exit=$?

if [[ $auth_exit -ne 0 || -z "$auth_json" ]]; then
  echo "LARK_CONFIG_READY=0"
  echo "USER_AUTH_READY=0"
  echo "MINUTES_SCOPES_READY=0"
  echo "LIVE_MINUTES_READ=SKIPPED"
  echo "NEXT_ACTION=Initialize or bind a Feishu app"
  exit 1
fi

assessment="$(printf '%s' "$auth_json" | node -e '
let input = "";
process.stdin.setEncoding("utf8");
process.stdin.on("data", chunk => input += chunk);
process.stdin.on("end", () => {
  try {
    const data = JSON.parse(input);
    const user = data.identities && data.identities.user ? data.identities.user : {};
    const scopes = new Set(String(user.scope || "").split(/\s+/).filter(Boolean));
    const required = [
      "minutes:minutes:readonly",
      "minutes:minutes.transcript:export",
      "minutes:minutes.search:read"
    ];
    const missing = required.filter(scope => !scopes.has(scope));
    const configReady = Boolean(data.appId);
    const userReady = Boolean(user.available && user.verified && user.tokenStatus === "valid");
    console.log(`LARK_CONFIG_READY=${configReady ? 1 : 0}`);
    console.log(`USER_AUTH_READY=${userReady ? 1 : 0}`);
    console.log(`MINUTES_SCOPES_READY=${missing.length === 0 ? 1 : 0}`);
    if (missing.length > 0) console.log(`MISSING_MINUTES_SCOPES=${missing.join(",")}`);
  } catch (_) {
    console.log("LARK_CONFIG_READY=0");
    console.log("USER_AUTH_READY=0");
    console.log("MINUTES_SCOPES_READY=0");
  }
});
')"

printf '%s\n' "$assessment"

if [[ $live_check -eq 0 ]]; then
  echo "LIVE_MINUTES_READ=SKIPPED"
  echo "NEXT_ACTION=Run with --live after configuration is ready"
  exit 0
fi

if ! printf '%s\n' "$assessment" | grep -q '^USER_AUTH_READY=1$' || \
   ! printf '%s\n' "$assessment" | grep -q '^MINUTES_SCOPES_READY=1$'; then
  echo "LIVE_MINUTES_READ=SKIPPED"
  echo "NEXT_ACTION=Complete user authorization and grant missing read-only scopes"
  exit 1
fi

today="$(date +%F)"
if LARKSUITE_CLI_NO_UPDATE_NOTIFIER=1 LARKSUITE_CLI_NO_SKILLS_NOTIFIER=1 \
  lark-cli minutes +search \
    --as user \
    --owner-ids me \
    --start "$today" \
    --end "$today" \
    --page-size 1 \
    --format json >/dev/null 2>&1; then
  echo "LIVE_MINUTES_READ=1"
  echo "NEXT_ACTION=Feishu Minutes is ready"
  exit 0
fi

echo "LIVE_MINUTES_READ=0"
echo "NEXT_ACTION=Inspect authorization, scopes, or Feishu app configuration"
exit 1
