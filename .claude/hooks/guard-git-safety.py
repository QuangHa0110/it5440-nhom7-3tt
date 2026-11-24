#!/usr/bin/env python3
"""PreToolUse/Bash guard: block the destructive git operations this repo forbids.

Enforces mechanically what CLAUDE.md states as policy (ADR 0016), because preserving
reproducible history is a hard requirement and prose is only guidance:

  * --no-verify / --no-gpg-sign            (unconditional)
  * force-push / delete / rebase / reset --hard / commit --amend / branch -D
    touching a protected branch            (main, dev, trinq/release)
  * history rewrites                       (filter-branch, filter-repo)
  * tag destruction                        (tag -d, tag -f, push --delete of a tag)

There is deliberately NO bypass environment variable: a switch the agent can set
itself is not a guard. The escape hatch is a human running the command in a plain
terminal.

Exit codes: 2 blocks the tool call and feeds stderr back to the model; 0 allows.
Every unexpected condition — unparseable input, a missing git, an internal error —
FAILS OPEN (exit 0), so this hook can never wedge a session on its own bug.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys

PROTECTED = ("main", "dev")

# Split on shell chaining so `make x && git push --force origin main` is inspected
# segment by segment rather than as one blob.
_CHAIN = re.compile(r"&&|\|\||;|\|")

_FORCE = re.compile(r"(?:^|\s)(?:--force\b|--force-with-lease\b|-f\b)")
_HELP = re.compile(r"(?:^|\s)(?:--help\b|-h\b)")

# Text that is *data*, not command: a heredoc body, or a commit/tag message value.
# Without stripping these first, documenting a forbidden flag inside a commit message
# would block the commit — a false positive found the first time this guard ran live.
_HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1.*?^\2$", re.DOTALL | re.MULTILINE)
_MSG_VALUE = re.compile(r"(?:-m|-F|--message|--file)(?:=|\s+)(?:'[^']*'|\"(?:[^\"\\]|\\.)*\"|\S+)")


def strip_payloads(command: str) -> str:
    """Remove heredoc bodies and -m/-F message values so their text is not parsed as flags."""
    out = _HEREDOC.sub(" <<heredoc>> ", command)
    return _MSG_VALUE.sub(" -m <msg> ", out)


def _run(args: list[str]) -> str | None:
    try:
        out = subprocess.run(args, capture_output=True, text=True, timeout=2)
    except Exception:
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def current_branch() -> str | None:
    return _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])


def _names_protected(seg: str) -> bool:
    """True if the segment explicitly names a protected branch (as a ref word)."""
    for b in PROTECTED:
        if re.search(rf"(?:^|[\s:/]){re.escape(b)}(?:$|[\s:])", seg):
            return True
    return False


def _on_protected(branch: str | None) -> bool:
    return branch in PROTECTED


def check(command: str, branch: str | None) -> str | None:
    """Return a human-readable block reason, or None to allow."""
    command = strip_payloads(command)
    for raw in _CHAIN.split(command):
        seg = raw.strip()
        if not seg or not re.search(r"(?:^|\s|/)git(?:\s|$)", seg):
            continue
        if _HELP.search(seg):
            continue  # `git push --help` is not a push

        if re.search(r"--no-verify\b|--no-gpg-sign\b", seg):
            return (
                "`--no-verify` / `--no-gpg-sign` is never allowed in this repo. "
                "If a hook fails, fix the underlying issue and make a new commit."
            )

        # --- tag destruction: release tags (vX.Y.Z) and eval-freeze tags are irreplaceable -------------------
        if re.search(r"\bgit\s+tag\b", seg) and re.search(r"(?:^|\s)-(?:d|D)\b|--delete\b", seg):
            return (
                "deleting a git tag is never allowed — release and eval-freeze tags are how a result gets reproduced; "
                "add a new tag instead."
            )
        if re.search(r"\bgit\s+tag\b", seg) and _FORCE.search(seg):
            return (
                "force-moving a git tag is never allowed (tags are immutable in this repo). "
                "Add a new tag instead."
            )
        if (
            re.search(r"\bpush\b", seg)
            and re.search(r"--delete\b|(?:^|\s):refs/tags/|(?:^|\s):tags?/", seg)
            and re.search(r"refs/tags/|\btag\b|eval-|(?:^|\s)v\d", seg)
        ):
            return "deleting a remote tag is never allowed — tags are the reproducibility backbone."

        # --- history rewrites ---------------------------------------------------
        if re.search(r"\bfilter-branch\b|\bfilter-repo\b", seg):
            return "history-rewriting commands are never allowed in this repo."

        # --- protected-branch operations ---------------------------------------
        hits_protected = _names_protected(seg) or _on_protected(branch)

        if re.search(r"\bpush\b", seg):
            if _FORCE.search(seg) and hits_protected:
                return (
                    f"force-push touching a protected branch ({', '.join(PROTECTED)}) is never "
                    "allowed. Force-pushing a personal branch ({dev}/{slug}/{topic}) is fine."
                )
            if re.search(r"--delete\b|--mirror\b", seg) and _names_protected(seg):
                return f"deleting a protected branch ({', '.join(PROTECTED)}) via push is never allowed."
            if re.search(r"(?:^|\s):(?:main|dev)\b", seg):
                return "the `push origin :<branch>` delete form is never allowed for a protected branch."

        if re.search(r"\brebase\b", seg) and hits_protected:
            return (
                f"rebasing onto/within a protected branch ({', '.join(PROTECTED)}) rewrites shared "
                "history. Rebase your feature branch instead."
            )

        if re.search(r"\breset\b", seg) and re.search(r"--hard\b", seg) and _on_protected(branch):
            return f"`git reset --hard` while on `{branch}` discards shared history."

        if re.search(r"\bcommit\b", seg) and re.search(r"--amend\b", seg) and _on_protected(branch):
            return f"`git commit --amend` while on `{branch}` rewrites a published commit."

        if (
            re.search(r"\bbranch\b", seg)
            and re.search(r"(?:^|\s)-(?:d|D)\b|--delete\b", seg)
            and _names_protected(seg)
        ):
            return f"deleting a protected branch ({', '.join(PROTECTED)}) is never allowed."

    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # unparseable input is not our call to block

    if payload.get("tool_name") != "Bash":
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    if not command or "git" not in command:
        return 0

    try:
        reason = check(command, current_branch())
    except Exception as exc:  # never let a bug in this guard wedge the session
        print(f"guard-git-safety: internal error, failing open: {exc}", file=sys.stderr)
        return 0

    if reason:
        print(f"BLOCKED by .claude/hooks/guard-git-safety.py: {reason}", file=sys.stderr)
        print(
            "This guard has no bypass flag. If a human genuinely intends this, run it "
            "in a plain terminal outside Claude Code.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
