"""PreToolUse hook: a merge or push to `main` needs a Ready gate review of that exact commit (R4).

This is the only enforced review point. Commits are never blocked, so ordinary development is never
slowed down by reviews — see CLAUDE.md Part 0, "When reviews run — and when they do not".

Usage:  python review_gate.py auto   (or merge|push to force one)
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

# What the gate actually protects. The reviewed commit no longer has to *be* HEAD — recording a Ready
# verdict necessarily creates a commit after the one reviewed, so `head == HEAD` was unsatisfiable:
# refuse, review, HEAD moves, refuse again. It never showed until Gate 0 first reached Ready.
#
# The guarantee kept instead: the reviewed commit is an ancestor of HEAD, and nothing under these
# paths changed between them. So a review can record itself, and the plan, the reports and the BRD
# can be written up afterwards, while any change to the product, the inputs, the review machinery or
# CI still demands a fresh review. `.claude/` and `.github/` are in the list because the agents, the
# commands, this hook and the CI workflows are the controls: changing a control unreviewed is the one
# thing worse than changing the code unreviewed.
#
# CLAUDE.md itself is deliberately *not* protected — it is the BRD, and a gate review's own findings
# are written into it (the §76A.14 coverage table is recalculated from the test reviewer's report).
# Protecting it would reintroduce the deadlock for documentation alone.
PROTECTED_PATHS = ("A_Codes", "B_Inputs", ".claude", ".github")

# The hook is registered on the Bash tool as a whole, so it sees every command, not only git ones:
# the `if` field in settings.json does not filter. It must therefore decide for itself whether the
# command is a push or a merge at all. Matching the bare word "main" anywhere was not enough --
# `uvicorn app.main:app` contains it, so starting the backend was refused as a merge to main.
GIT_PUSH = re.compile(r"(?:^|[;&|]\s*|&&\s*)git\s+(?:-\S+\s+)*push\b")
GIT_MERGE = re.compile(r"(?:^|[;&|]\s*|&&\s*)git\s+(?:-\S+\s+)*merge\b")
# What a `git merge` would bring in. For a push, HEAD already contains the commits under scrutiny; for
# a merge run on main it does not — main is behind by definition — so checking HEAD would report "not
# an ancestor" for every merge and the gate would be a blanket deny, useful to nobody. The commit to
# judge is the one being merged in.
GIT_MERGE_ARGS = re.compile(r"(?:^|[;&|]\s*|&&\s*)git\s+(?:-\S+\s+)*merge\b(?P<rest>[^;&|]*)")
# `--abort` and `--quit` undo a merge in progress; they introduce nothing, so the gate ignores them.
MERGE_UNDO = re.compile(r"--(?:abort|quit)\b")


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
    """Whether this command would move `main`.

    Two conditions, in order: it has to be a git push or merge at all, and it has to be aimed at
    main or master. The first check is what keeps every other command out of the gate.

    Within a real push or merge the matching stays generous, because a false "needs review" is a
    prompt while a false "fine" is an unreviewed merge.
    """
    is_push = bool(GIT_PUSH.search(command))
    is_merge = bool(GIT_MERGE.search(command))
    if action == "merge" and not is_merge:
        return False
    if action == "push" and not is_push:
        return False
    if action == "auto" and not (is_push or is_merge):
        return False

    if is_merge and not is_push:
        if MERGE_UNDO.search(command):
            return False  # --abort / --quit remove a merge in progress; nothing new arrives
        # `git merge X` run while main is checked out merges X *into* main.
        return current_branch() in ("main", "master")
    # push: `git push origin main`, `git push origin HEAD:main`, `git push --all`.
    if re.search(r"\b(main|master)\b", command):
        return True
    if re.search(r"--all\b|--mirror\b", command):
        return True
    # `git push` with no refspec pushes the current branch.
    return current_branch() in ("main", "master")


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


def merge_source(command: str) -> str | None:
    """The ref a `git merge` would bring in, or None if the command names none.

    Flags and their values are skipped, and the ref is the last bare token left. A merge with no ref
    (`git merge --continue`) returns None, and the caller then falls back to HEAD rather than
    guessing — a gate that cannot tell what is being merged must not allow it.
    """
    m = GIT_MERGE_ARGS.search(command)
    if not m:
        return None
    tokens = [tok for tok in m.group("rest").split() if not tok.startswith("-")]
    return tokens[-1].strip("'\"") if tokens else None


def resolve(rev: str) -> str:
    """Full sha for a possibly abbreviated rev, or "" if it is not a commit in this repository."""
    if not rev:
        return ""
    try:
        out = subprocess.run(["git", "rev-parse", "--verify", f"{rev}^{{commit}}"],
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def is_ancestor(earlier: str, later: str) -> bool:
    """True only on a clear yes. `merge-base --is-ancestor` exits 0 for yes, 1 for no, >1 on error,
    and an error must not read as a yes."""
    try:
        out = subprocess.run(["git", "merge-base", "--is-ancestor", earlier, later],
                             capture_output=True, text=True, timeout=10)
        return out.returncode == 0
    except Exception:
        return False


def protected_changes(earlier: str, later: str) -> list[str] | None:
    """Files under PROTECTED_PATHS that differ between the two commits. None if git could not say —
    which the caller must treat as a refusal, not as "nothing changed"."""
    try:
        out = subprocess.run(["git", "diff", "--name-only", earlier, later, "--", *PROTECTED_PATHS],
                             capture_output=True, text=True, timeout=30)
        if out.returncode != 0:
            return None
        return [line for line in out.stdout.splitlines() if line.strip()]
    except Exception:
        return None


def latest_gate(state: dict) -> tuple[str, dict] | tuple[None, None]:
    """The most recently dated gate entry, which is the one that must be Ready."""
    gates = state.get("gates") or {}
    if not gates:
        return None, None
    name = max(gates, key=lambda k: str(gates[k].get("date", "")))
    return name, gates[name]


def main() -> None:
    action = sys.argv[1] if len(sys.argv) > 1 else "auto"
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
    recorded = resolve(str(entry.get("head") or ""))
    if not recorded:
        decide("deny", f"Merging to main needs a Ready gate review. Gate {gate} records head "
                       f"{str(entry.get('head'))[:12]!r}, which is not a commit in this repository — "
                       f"re-run /review-build gate {gate}.")
    if not commit:
        decide("deny", "Merging to main needs a Ready gate review, and HEAD could not be read.")

    # For a merge, judge what is arriving; for a push, HEAD already holds it.
    incoming = merge_source(command) if (GIT_MERGE.search(command) and not GIT_PUSH.search(command)) else None
    target, target_name = commit, "HEAD"
    if incoming is not None:
        target = resolve(incoming)
        target_name = f"{incoming} ({target[:8]})" if target else incoming
        if not target:
            decide("deny", f"Merging to main needs a Ready gate review of what is being merged, and "
                           f"{incoming!r} is not a commit in this repository.")

    if recorded != target:
        if not is_ancestor(recorded, target):
            decide("deny", f"Merging to main needs a Ready gate review of this commit. Gate {gate} "
                           f"was reviewed at {recorded[:8]}, which is not an ancestor of "
                           f"{target_name} — the branch has diverged or been rewritten since. "
                           f"Run /review-build gate {gate}.")
        changed = protected_changes(recorded, target)
        if changed is None:
            decide("deny", f"Merging to main needs a Ready gate review of this commit, and the "
                           f"changes between {recorded[:8]} and {target_name} could not be compared. "
                           f"Run /review-build gate {gate}.")
        if changed:
            shown = ", ".join(changed[:5]) + (f" (+{len(changed) - 5} more)" if len(changed) > 5 else "")
            decide("deny", f"Merging to main needs a Ready gate review of this commit. Gate {gate} was "
                           f"reviewed at {recorded[:8]}, and {len(changed)} protected file(s) have "
                           f"changed since: {shown}. Run /review-build gate {gate}.")

    where = (f"at this commit ({target[:8]})" if recorded == target else
             f"at {recorded[:8]}; nothing under {'/, '.join(PROTECTED_PATHS)}/ has changed between "
             f"that and {target_name}")
    decide("allow", f"Gate {gate} reviewed Ready {where}.")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # a broken gate must be noticed, not silently skipped
        decide("deny", f"The review gate hook failed ({type(exc).__name__}: {exc}). "
                       f"Fix .claude/hooks/review_gate.py rather than bypassing it.")
