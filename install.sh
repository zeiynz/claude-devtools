#!/usr/bin/env bash
# Install all skills for Claude Code.
#   ./install.sh              -> ~/.claude/skills   (all your projects)
#   ./install.sh --project    -> ./.claude/skills   (current project only)
#   ./install.sh /custom/dir  -> custom directory
set -euo pipefail

case "${1:-}" in
  --project) DEST="$PWD/.claude/skills" ;;
  "")        DEST="$HOME/.claude/skills" ;;
  *)         DEST="$1" ;;
esac

SRC="$(cd "$(dirname "$0")/skills" && pwd)"
mkdir -p "$DEST"
for dir in "$SRC"/*/; do
  name="$(basename "$dir")"
  rm -rf "${DEST:?}/$name"
  cp -R "$dir" "$DEST/$name"
  find "$DEST/$name" -name __pycache__ -type d -prune -exec rm -rf {} +
  echo "installed $name -> $DEST/$name"
done
echo "Done. Restart Claude Code, then try: \"audit this repo\" or \"build a dashboard from data.csv\"."
