#!/bin/bash
# langgeladi 发布前敏感词预扫描
# 仿 Yiching-skill-internal/publish.sh 的 check_sensitive 函数
#
# 这个仓是狼格拉底 IP 公开仓（GitHub: YiXinHui/langskill）
# 「狼格拉底/狼哥」是 IP 自身，可以出现
# 但「意心会/昭阳/yi 业务路径/具体客户名」不该出现 — 它们属于另一家公司
#
# 用法：
#   ./pre-check.sh
# 0 残留 → exit 0；有残留 → exit 1 + 列出位置

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

check_sensitive() {
  echo "🔍 langgeladi 发布前敏感词预扫描..."
  # yi 公司/业务名（不该在 lang IP 仓出现）
  local company_patterns=("意心会" "昭阳")
  # yi 业务路径
  local path_patterns=("01-内容生产" "02-业务资料" "03-意心会" "04-归档" "05-知识体系")
  # 具体客户名（已在 yi 仓出现过的，泄漏到 lang 仓即跨业务）
  local customer_patterns=("高飞" "张涛" "欣欣" "廖慧" "马子平" "赵晓箐" "王鹏程" "白依天使" "金磊")
  local all_patterns=("${company_patterns[@]}" "${path_patterns[@]}" "${customer_patterns[@]}")
  local found=0
  for pattern in "${all_patterns[@]}"; do
    local results
    results=$(grep -rn "$pattern" "$SCRIPT_DIR/skills/" \
      --include="*.md" --include="*.py" --include="*.sh" --include="*.json" \
      --exclude-dir=".docs" --exclude-dir=".git" --exclude-dir="evals" \
      --exclude-dir="*-workspace" --exclude-dir="__pycache__" \
      2>/dev/null | grep -v "personal-config.md" | head -5)
    if [ -n "$results" ]; then
      if [ $found -eq 0 ]; then echo ""; fi
      echo "  ❌ 残留 [$pattern]:"
      echo "$results" | sed "s|$SCRIPT_DIR/|     |"
      found=1
    fi
  done
  if [ $found -eq 1 ]; then
    echo ""
    echo "⛔ 仓内有 yi 业务/客户信息泄漏（langgeladi 是公开仓）"
    echo "   规则：跨业务具体值下沉到 references/personal-config.md（已 .gitignore）"
    echo "        SKILL.md / public-config-example.md 只能用 <占位符>"
    echo "   注：'狼格拉底' '狼哥' 是 IP 自身，可以出现，不在扫描范围"
    exit 1
  else
    echo "  ✅ 无残留"
    exit 0
  fi
}

check_sensitive
