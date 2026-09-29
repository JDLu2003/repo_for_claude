#!/usr/bin/env bash
# 用法: scripts/new-session.sh <slug>
set -euo pipefail
cd "$(dirname "$0")/.."
slug="${1:?用法: $0 <slug>}"
date="$(date +%F)"
file="sessions/${date}-${slug}.md"
[ -e "$file" ] && { echo "已存在: $file"; exit 0; }
branch="$(git branch --show-current 2>/dev/null || true)"
sed -e "s/{{TITLE}}/${slug}/" -e "s/{{DATE}}/${date}/" -e "s#{{BRANCH}}#${branch}#" \
  sessions/_template.md > "$file"
echo "$file"
