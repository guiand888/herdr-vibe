# herdr-vibe

[![standard-readme compliant](https://img.shields.io/badge/standard--readme-OK-green.svg)](https://github.com/RichardLitt/standard-readme)

> Mistral Vibe plugin that reports agent state and resume commands to Herdr.

Herdr has no built-in detection for Mistral Vibe. This plugin implements Herdr's agent self-reporting protocol from Vibe's hook system, so Vibe sessions get a sidebar entry, finish and decision notifications, `herdr agent wait` support, and same-pane session restore after a Herdr server restart — without patching either project.

Mapping of Vibe events to Herdr states:

| Vibe hook | Herdr report |
| --- | --- |
| `pre_tool` on `ask_user_question` | `blocked` |
| `pre_tool` on any other tool | `working` |
| `post_tool` | `working` |
| `post_agent` | `idle`, plus the session id and `vibe --resume <id>` as the resume command |

Reports go through `$HERDR_BIN_PATH pane report-agent` and are gated on `HERDR_ENV=1`, so the plugin is silent outside Herdr panes.

## Install

Requires `python3` on `PATH` and Herdr 0.7 or newer (0.9.2 or newer for session restore).

Vibe 2.26.1 resolves plugin hooks (`ai.mistral.vibe/hooks.toml`) but does not execute them yet. The installer therefore also registers the hooks as user-level entries in `$VIBE_HOME/hooks.toml`, which Vibe runs today:

```bash
git clone <this repository> ~/.vibe/plugins/herdr-vibe
~/.vibe/plugins/herdr-vibe/install.sh
```

The installer is idempotent, preserves unrelated hooks, and copies `scripts/report-herdr.py` to `$VIBE_HOME/herdr-vibe/` so reports keep working if the checkout moves. New sessions pick the hooks up at startup.

Uninstall:

```bash
~/.vibe/plugins/herdr-vibe/install.sh uninstall
```

## Usage

Run `vibe` inside a Herdr pane. Herdr then shows the `mistral-vibe` agent with its state:

```bash
herdr agent list
herdr pane get "$HERDR_PANE_ID"
```

Known limitations:

- Tool-approval prompts are not reported as `blocked`; Vibe has no permission-prompt hook, so only questions (`ask_user_question`) do.
- Vibe has no session-exit hook, so pane release is left to Herdr's idle-shell cleanup.
- Windows is not supported; the hooks invoke `python3` through the system shell.
- Once a Vibe release executes plugin hooks, run `./install.sh uninstall` and rely on the plugin copy alone.

## Maintainers

Guillaume Andre \<mail@guillaumea.fr\>

## Contributing

Issues and pull requests welcome.

## License

AGPL-3.0-only © 2026 Guillaume Andre
