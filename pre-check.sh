#!/bin/bash
# 发布前敏感信息扫描：通用规则（本机路径、飞书资源链接、各类 ID、手机号、密钥）
# 加上私人主库 internal/sensitive-words.txt 里的敏感词。实现见 scripts/pre-check.mjs。
#   ./pre-check.sh [仓库目录]
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec node "$SCRIPT_DIR/scripts/pre-check.mjs" "${1:-$SCRIPT_DIR}"
