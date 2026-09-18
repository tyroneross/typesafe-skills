#!/usr/bin/env bash
# Link this skill into Claude Code and Codex from one source directory.
# Usage: scripts/install.sh [--copy]   (--copy installs copies instead of symlinks)
set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME="$(basename "$SRC")"
MODE="${1:-}"

install_into() {
  local root="$1" host="$2"
  [ -d "$root" ] || { echo "skip $host: $root does not exist"; return; }
  local dest="$root/$NAME"
  if [ -e "$dest" ] || [ -L "$dest" ]; then rm -rf "$dest"; fi
  if [ "$MODE" = "--copy" ]; then cp -R "$SRC" "$dest"; else ln -s "$SRC" "$dest"; fi
  echo "installed $host: $dest -> $SRC"
}

install_into "$HOME/.claude/skills" "Claude Code"
install_into "$HOME/.codex/skills" "Codex"
echo "source: $SRC"
