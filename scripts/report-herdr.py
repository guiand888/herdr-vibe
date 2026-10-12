#!/usr/bin/env python3
"""Report Mistral Vibe state to Herdr.

Reads a Vibe hook payload from stdin and calls
`herdr pane report-agent` through $HERDR_BIN_PATH (or `herdr`
on PATH on herdr versions that do not inject it, e.g. 0.7.5). Runs only inside
Herdr panes ($HERDR_ENV=1) and stays silent everywhere else. Vibe has
no session-exit hook, so release is left to Herdr's idle-shell cleanup.

Protocol: https://herdr.dev/docs/add-herdr-support/
Verified against herdr 0.7.5 (state and --agent-session-id) and
herdr 0.9.2 (trailing resume argv after `--`).
"""

import json
import os
import shutil
import subprocess
import sys
import time

SOURCE = "herdr-vibe"
AGENT = "mistral-vibe"
STATES = {"working", "blocked", "idle"}
CALL_TIMEOUT_S = 8.0


def _clean_session_id(value):
    """Herdr rejects resume argv containing apostrophes or control characters."""
    if not isinstance(value, str) or not value:
        return None
    if any(ord(char) < 32 or char == "'" for char in value):
        return None
    return value


def _resolve_herdr():
    """Prefer the injected binary; fall back to PATH.

    Verified on the running machine: herdr 0.7.5 panes inject
    HERDR_ENV, HERDR_PANE_ID, and HERDR_SOCKET_PATH but not
    HERDR_BIN_PATH, so the PATH fallback is required there.
    """
    injected = os.environ.get("HERDR_BIN_PATH", "")
    if injected:
        return injected
    return shutil.which("herdr") or ""


def _build_argv(herdr, pane, state, seq, session_id, resume_ok):
    argv = [
        herdr,
        "pane",
        "report-agent",
        pane,
        "--source",
        SOURCE,
        "--agent",
        AGENT,
        "--state",
        state,
        "--seq",
        str(seq),
    ]
    if state == "blocked":
        argv += ["--message", "Waiting for an answer"]
    if session_id:
        argv += ["--agent-session-id", session_id]
    if resume_ok and session_id:
        argv += ["--", "vibe", "--resume", session_id]
    return argv


def _report(herdr, pane, state, seq, session_id, resume_ok):
    argv = _build_argv(herdr, pane, state, seq, session_id, resume_ok)
    completed = subprocess.run(
        argv,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=CALL_TIMEOUT_S,
        check=False,
    )
    return completed.returncode


def main():
    state = sys.argv[1] if len(sys.argv) > 1 else ""
    if state not in STATES:
        return
    if os.environ.get("HERDR_ENV") != "1":
        return
    pane = os.environ.get("HERDR_PANE_ID", "")
    herdr = _resolve_herdr()
    if not pane or not herdr:
        return

    try:
        payload = json.load(sys.stdin)
    except (ValueError, UnicodeDecodeError):
        return
    if not isinstance(payload, dict):
        return
    if payload.get("parent_session_id"):
        # Subagent turns run in the same pane process; they must not
        # disturb the top-level agent's reported state.
        return

    session_id = payload.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        session_id = None
    resume_ok = session_id is not None and _clean_session_id(session_id) is not None
    seq = time.time_ns()
    try:
        code = _report(herdr, pane, state, seq, session_id, resume_ok=resume_ok)
        if code != 0 and resume_ok:
            # Herdr before 0.9.2 rejects the trailing resume argv.
            _report(herdr, pane, state, seq, session_id, resume_ok=False)
    except (OSError, subprocess.SubprocessError):
        return


if __name__ == "__main__":
    main()
    sys.exit(0)
