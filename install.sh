#!/bin/sh
# Install or remove herdr-vibe reporting hooks for the Mistral Vibe CLI.
#
# Vibe 2.26.1 resolves plugin hooks (ai.mistral.vibe/hooks.toml) but does not
# execute them yet, so this installer also wires the same hooks as user-level
# entries in $VIBE_HOME/hooks.toml, which Vibe runs today. Remove the
# user-level entries once a Vibe release executes plugin hooks.
#
# Usage:
#   ./install.sh            install the reporting hooks
#   ./install.sh uninstall  remove them
set -eu

PLUGIN_ROOT=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
VIBE_HOME_DIR=${VIBE_HOME:-"$HOME/.vibe"}
HOOKS_FILE="$VIBE_HOME_DIR/hooks.toml"
ASSET_DIR="$VIBE_HOME_DIR/herdr-vibe"
REPORT="$ASSET_DIR/report-herdr.py"
SOURCE_REPORT="$PLUGIN_ROOT/scripts/report-herdr.py"

BEGIN_MARKER='# >>> herdr-vibe >>>'
END_MARKER='# <<< herdr-vibe <<<'

remove_block() {
  [ -f "$HOOKS_FILE" ] || return 0
  awk -v begin="$BEGIN_MARKER" -v end="$END_MARKER" '
    $0 == begin { skip = 1 }
    !skip { print }
    $0 == end { skip = 0 }
  ' "$HOOKS_FILE" > "$HOOKS_FILE.tmp" && mv "$HOOKS_FILE.tmp" "$HOOKS_FILE"
}

install() {
  command -v python3 >/dev/null 2>&1 || {
    echo "error: python3 is required on PATH" >&2
    exit 1
  }
  case "$PLUGIN_ROOT" in
    *\'*) echo "error: plugin path contains an apostrophe: $PLUGIN_ROOT" >&2; exit 1 ;;
  esac
  mkdir -p "$VIBE_HOME_DIR" "$ASSET_DIR"
  cp "$SOURCE_REPORT" "$REPORT"
  remove_block
  cat >> "$HOOKS_FILE" <<EOF

$BEGIN_MARKER
# Managed by herdr-vibe (https://github.com/herdrdev/herdr integration).
# Edit or remove with: ./install.sh uninstall

[[hooks]]
name = "herdr-vibe-report-blocked"
type = "pre_tool"
match = "ask_user_question"
command = "python3 '$REPORT' blocked"
timeout = 10.0

[[hooks]]
name = "herdr-vibe-report-working"
type = "pre_tool"
match = "re:^(?!ask_user_question\$).*$"
command = "python3 '$REPORT' working"
timeout = 10.0

[[hooks]]
name = "herdr-vibe-report-tool-done"
type = "post_tool"
command = "python3 '$REPORT' working"
timeout = 10.0

[[hooks]]
name = "herdr-vibe-report-idle"
type = "post_agent"
command = "python3 '$REPORT' idle"
timeout = 10.0
$END_MARKER
EOF
  echo "installed herdr-vibe hooks in $HOOKS_FILE"
  echo "report script: $REPORT"
}

uninstall() {
  remove_block
  rm -rf "$ASSET_DIR"
  echo "removed herdr-vibe hooks from $HOOKS_FILE"
  echo "removed $ASSET_DIR"
}

case "${1:-install}" in
  install) install ;;
  uninstall) uninstall ;;
  *) echo "usage: $0 [install|uninstall]" >&2; exit 2 ;;
esac
