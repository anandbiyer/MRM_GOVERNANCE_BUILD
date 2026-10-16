"""PreToolUse hook: a merge or push to `main` needs a Ready gate review of that exact commit (R4).

This is the only enforced review point. Commits are never blocked, so ordinary development is never
slowed down by reviews — see CLAUDE.md Part 0, "When reviews run — and when they do not".

Usage:  python review_gate.py merge|push
Reads the tool call as JSON on stdin (Claude Code's PreToolUse payload) and prints a
`hookSpecificOutput` decision. Always exits 0: a non-zero exit would be a hook failure rather than a
decision, and a failure here must still deny (a broken gate that silently allows is worse than a
noisy one).

Standard library only, so it runs under whatever Python is on PATH.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

STATE = Path(__file__).resolve().parents[2] / "D_Reviews" / "review_state.json"


def decide(decision: str, reason: str) -> None:
    """Emit the decision and exit. 'allow' with no reason stays silent."""
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


def targets_main(action: str, command: str) -> bool:
    """Whether this git command would move `main`.

    Deliberately generous: anything that mentions main/master as the target counts, because a false
    "needs review" is a prompt, while a false "fine" is an unreviewed merge.
    """
    if action == "merge":
        # `git merge X` run while main is checked out merges X *into* main.
        return current_branch() in ("main", "master")
    # push: `git push origin main`, `git push origin HEAD:main`, `git push --all`.
    if re.search(r"\b(main|master)\b", command):
        return True
    if re.search(r"--all\b|--mirror\b", command):
        return True
    # `git push` with no refspec pushes the current branch.
    return bool(re.fullmatch(r"\s*git\s+push\s*(-{1,2}[\w-]+\s*)*", command)) and \
        current_branch() in ("main", "master")


def current_branch() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip()
    except Exception:
        return ""


def head() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10)
        return out.stdout.strip()
    except Exception:
        return ""


def latest_gate(state: dict) -> tuple[str, dict] | tuple[None, None]:
    """The most recently dated gate entry, which is the one that must be Ready."""
    gates = state.get("gates") or {}
    if not gates:
        return None, None
    name = max(gates, key=lambda k: str(gates[k].get("date", "")))
    return name, gates[name]


def main() -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else "merge"
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}
    command = ((payload.get("tool_input") or {}).get("command") or "")

    if not targets_main(action, command):
        decide("allow", "")

    if not STATE.exists():
        decide("deny", f"Merging to main needs a Ready gate review of this commit. "
                       f"No {STATE.name} yet — run /review-build gate <N>.")

    state = json.loads(STATE.read_text(encoding="utf-8"))
    gate, entry = latest_gate(state)
    if entry is None:
        decide("deny", "Merging to main needs a Ready gate review of this commit. "
                       "No gate has been reviewed yet — run /review-build gate <N>.")

    commit = head()
    if entry.get("verdict") != "Ready":
        decide("deny", f"Merging to main needs a Ready gate review of this commit. "
                       f"Gate {gate} is '{entry.get('verdict')}' — run /review-build gate {gate}.")
    if entry.get("head") != commit:
        decide("deny", f"Merging to main needs a Ready gate review of this commit. "
                       f"Gate {gate} was reviewed at {str(entry.get('head'))[:8]}, "
                       f"HEAD is {commit[:8]} — run /review-build gate {gate}.")

    decide("allow", f"Gate {gate} reviewed Ready at this commit ({commit[:8]}).")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # a broken gate must be noticed, not silently skipped
        decide("deny", f"The review gate hook failed ({type(exc).__name__}: {exc}). "
                       f"Fix .claude/hooks/review_gate.py rather than bypassing it.")
