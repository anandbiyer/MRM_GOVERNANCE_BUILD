"""Scratch-branch tests for review_gate.py. Run them after any change to the hook.

    python .claude/hooks/test_review_gate.py

They were ad hoc before, which is how the 2026-10-06 repair shipped failing open: a heredoc turned
`\b` into a literal backspace in six places, `GIT_PUSH` matched nothing, and a real push to main was
ALLOWED. The deny path has to be tested, not only the allow path, and testing it by hand is how it
gets skipped.

Everything happens in a throwaway clone under the system temp directory, never in the repository: the
tests need commits that change protected paths, and making those here would pollute the history the
hook is meant to protect. The clone gets a copy of this hook, so it is the real code under test.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# The hook under test, NOT this file. Getting this wrong once cost about a thousand temp clones:
# `Path(__file__)` here copied the *test* into the clone as `review_gate.py`, so every simulated hook
# invocation ran the whole suite again inside its own clone, recursively. Hence the assertion below.
HOOK = Path(__file__).resolve().parent / "review_gate.py"
REPO = Path(__file__).resolve().parents[2]
assert "PreToolUse hook" in HOOK.read_text(encoding="utf-8"), f"{HOOK} is not the review gate hook"


def git(cwd, *args, check=True):
    out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=60)
    if check and out.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed in {cwd}:\n{out.stderr}")
    return out.stdout.strip()


def run_hook(cwd, command, action="auto"):
    """Invoke the clone's own hook exactly as Claude Code does, and return (decision, reason)."""
    payload = json.dumps({"tool_input": {"command": command}})
    out = subprocess.run([sys.executable, str(Path(cwd) / ".claude" / "hooks" / "review_gate.py"), action],
                         cwd=cwd, input=payload, capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise SystemExit(f"the hook exited {out.returncode}, which is itself a failure:\n{out.stderr}")
    body = json.loads(out.stdout)["hookSpecificOutput"]
    return body["permissionDecision"], body["permissionDecisionReason"]


def write_state(cwd, head, verdict="Ready"):
    state = {"checkpoints": {}, "gates": {"0": {
        "date": "2026-10-07", "verdict": verdict, "summary": "D_Reviews/x.md", "head": head}}}
    p = Path(cwd) / "D_Reviews" / "review_state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, indent=2), encoding="utf-8")


def commit_all(cwd, message):
    """Commit whatever is staged, tolerating nothing-to-commit: several scenarios rewrite
    review_state.json to a value it already holds, and git exits non-zero on an empty commit."""
    git(cwd, "add", "-A")
    git(cwd, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", message)
    return git(cwd, "rev-parse", "HEAD")


def commit_file(cwd, relpath, text, message):
    p = Path(cwd) / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    git(cwd, "add", "-A")
    git(cwd, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", message)
    return git(cwd, "rev-parse", "HEAD")


FAILURES = []


def check(name, got, want):
    ok = got == want
    print(f"  {'PASS' if ok else 'FAIL'}  {name}: {got}" + ("" if ok else f"  (expected {want})"))
    if not ok:
        FAILURES.append(name)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="review_gate_test_"))
    try:
        cwd = tmp / "repo"
        cwd.mkdir()
        git(cwd, "init", "-q", "-b", "main")
        for d in (".claude/hooks", "A_Codes", "B_Inputs", ".github/workflows", "D_Reviews", "E_ProjectPlan"):
            (cwd / d).mkdir(parents=True, exist_ok=True)
        shutil.copy(HOOK, cwd / ".claude" / "hooks" / "review_gate.py")
        base = commit_file(cwd, "A_Codes/app.py", "x = 1\n", "base")
        write_state(cwd, base)
        base = commit_all(cwd, "state")
        write_state(cwd, base)

        print("\nNot a push or merge at all — the command must pass straight through:")
        for cmd in ("uvicorn app.main:app", "echo 'git push origin main'", "git status", "npm run build"):
            check(f"{cmd!r}", run_hook(cwd, cmd)[0], "allow")
        print("  (the second is the one that matters: the matcher reads command text, and a false")
        print("   'needs review' is a prompt where a false 'fine' is an unreviewed merge)")

        print("\nReviewed commit IS HEAD:")
        git(cwd, "branch", "-f", "feature", "HEAD")  # the ref must exist: a merge is judged by
        check("git merge feature", run_hook(cwd, "git merge feature")[0], "allow")  # what it brings in
        check("git push origin main", run_hook(cwd, "git push origin main")[0], "allow")

        print("\nVerdict is not Ready:")
        write_state(cwd, base, verdict="Not ready")
        check("git push origin main", run_hook(cwd, "git push origin main")[0], "deny")
        write_state(cwd, base)

        print("\nOnly D_Reviews/ changed since the review — the deadlock this fix removes:")
        commit_file(cwd, "D_Reviews/20261007_summary.md", "Ready\n", "record the verdict")
        decision, reason = run_hook(cwd, "git push origin main")
        check("git push origin main", decision, "allow")
        assert "has changed between" in reason, reason

        print("\nE_ProjectPlan/ and CLAUDE.md too — a review writes its findings into both:")
        commit_file(cwd, "E_ProjectPlan/project_plan.md", "Done\n", "plan")
        commit_file(cwd, "claude.md", "BRD\n", "coverage table")
        check("git push origin main", run_hook(cwd, "git push origin main")[0], "allow")

        print("\nA protected path changed since the review — each must deny on its own:")
        after_docs = git(cwd, "rev-parse", "HEAD")
        for path, content in ((".claude/agents/x.md", "agent\n"),
                              ("A_Codes/app.py", "x = 2\n"),
                              ("B_Inputs/AA_bootstrap/T12.csv", "k,v\n"),
                              (".github/workflows/ci.yml", "on: push\n")):
            git(cwd, "reset", "-q", "--hard", after_docs)
            commit_file(cwd, path, content, f"change {path}")
            decision, reason = run_hook(cwd, "git push origin main")
            check(path, decision, "deny")
            assert path in reason, f"the refusal must name the file: {reason}"
        git(cwd, "reset", "-q", "--hard", after_docs)

        print("\nThe reviewed commit is not an ancestor of HEAD (branch rewritten):")
        git(cwd, "checkout", "-q", "--orphan", "rewritten")
        commit_file(cwd, "A_Codes/app.py", "x = 3\n", "rewritten history")
        write_state(cwd, base)
        commit_all(cwd, "state")
        decision, reason = run_hook(cwd, "git push origin main")
        check("orphan branch", decision, "deny")
        assert "ancestor" in reason, reason

        print("\nRecorded head is not a commit in this repository:")
        write_state(cwd, "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef")
        commit_all(cwd, "bad state")
        decision, reason = run_hook(cwd, "git push origin main")
        check("unknown head", decision, "deny")
        assert "not a commit" in reason, reason

        print("\nMerging INTO main: the gate judges the incoming commit, not main's tip.")
        print("  (main is behind by definition, so checking HEAD would deny every merge)")
        git(cwd, "checkout", "-q", "-B", "main", base)
        git(cwd, "checkout", "-q", "-B", "feature")
        commit_file(cwd, "D_Reviews/notes.md", "docs only\n", "docs on the branch")
        git(cwd, "checkout", "-q", "main")
        write_state(cwd, base)
        commit_all(cwd, "state on main")
        check("docs-only branch", run_hook(cwd, "git merge feature")[0], "allow")

        git(cwd, "checkout", "-q", "feature")
        commit_file(cwd, "A_Codes/app.py", "x = 9\n", "product change on the branch")
        git(cwd, "checkout", "-q", "main")
        decision, reason = run_hook(cwd, "git merge feature")
        check("branch with a product change", decision, "deny")
        assert "A_Codes/app.py" in reason, reason
        check("git merge --no-ff feature", run_hook(cwd, "git merge --no-ff feature")[0], "deny")
        check("git merge --abort", run_hook(cwd, "git merge --abort")[0], "allow")
        decision, reason = run_hook(cwd, "git merge no-such-branch")
        check("unknown ref", decision, "deny")
        assert "not a commit" in reason, reason

        # Shell operators and flag values are not refs. An early version took `2>` for a branch name
        # and refused an ordinary merge, which is the reason this block exists.
        git(cwd, "checkout", "-q", "feature")
        git(cwd, "reset", "-q", "--hard", "HEAD~1")  # drop the product change: docs-only again
        git(cwd, "checkout", "-q", "main")
        for cmd in ('git merge feature 2>&1 | tail -20',
                    'git merge feature -m "merge main into feature"',
                    'git merge --no-ff -m "x" feature > out.log',
                    "git merge -s ort -X theirs feature"):
            decision, reason = run_hook(cwd, cmd)
            check(cmd, decision, "allow")
            assert "feature" in reason, reason
        decision, reason = run_hook(cwd, "git merge feature no-such-branch")
        check("octopus with one bad ref", decision, "deny")
        assert "not a commit" in reason, reason

        print("\nNo review_state.json at all:")
        (cwd / "D_Reviews" / "review_state.json").unlink()
        check("git push origin main", run_hook(cwd, "git push origin main")[0], "deny")

        print()
        if FAILURES:
            print(f"{len(FAILURES)} FAILED: {', '.join(FAILURES)}")
            return 1
        print("All checks passed.")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
