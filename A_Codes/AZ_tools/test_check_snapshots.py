#!/usr/bin/env python3
"""Tests for check_snapshots.py — criteria PLT-02 and PLT-03 (§76E). Run after any change to it.

    python A_Codes/AZ_tools/test_check_snapshots.py

`check_snapshots.py` is a build control, so a defect in it fails **open**: the job goes green and the
convention stops being enforced without anyone noticing. Its R2 checkpoint raised exactly that
(TR-51), and `.claude/hooks/test_review_gate.py` already makes the argument from experience — the
2026-10-06 merge-hook repair shipped failing open because its checks were done by hand.

Stdlib only and no pytest, like the hook's tests, so the CI job that runs the control can run these
in the same step without installing anything.

Everything happens in throwaway repositories under the system temp directory. Several cases need
commits that *violate* the convention, and making those here would pollute the history the control
exists to protect.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TOOL = Path(__file__).resolve().parent / "check_snapshots.py"
ENFORCED = "2026-10-09"           # must match ENFORCED_FROM in the tool
BEFORE_ENFORCED = "2026-10-01"
FAILURES: list[str] = []


def git(cwd: Path, *args: str, when: str | None = None, authored: str | None = None) -> str:
    env = dict(os.environ)
    if when:
        stamp = f"{when}T12:00:00"
        env |= {"GIT_AUTHOR_DATE": stamp, "GIT_COMMITTER_DATE": stamp}
    if authored:  # an author date that differs from the committer date, as a rebase preserves
        env |= {"GIT_AUTHOR_DATE": f"{authored}T12:00:00"}
    env |= {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t",
            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
    out = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, env=env, timeout=120)
    if out.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} in {cwd}:\n{out.stderr}")
    return out.stdout


def write(cwd: Path, rel: str, data: str | bytes) -> None:
    p = cwd / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data if isinstance(data, bytes) else data.encode("utf-8"))


def commit(cwd: Path, message: str, when: str = ENFORCED, authored: str | None = None) -> str:
    git(cwd, "add", "-A")
    git(cwd, "commit", "-q", "--allow-empty", "-m", message, when=when, authored=authored)
    return git(cwd, "rev-parse", "HEAD").strip()


def new_repo(tmp: Path, name: str) -> Path:
    cwd = tmp / name
    cwd.mkdir(parents=True)
    git(cwd, "init", "-q", "-b", "main")
    # TR-89: with the machine's `core.autocrlf=true`, git would convert the CRLF case's bytes on the
    # way in, so the case proved nothing here while still meaning something under CI's settings. Pin
    # the repository to store bytes exactly as written, so the case means the same on every machine.
    git(cwd, "config", "core.autocrlf", "false")
    git(cwd, "config", "core.safecrlf", "false")
    # The tool resolves the repo as parents[2] of its own path, so it must live in the same layout.
    shutil.copy(TOOL, cwd / "A_Codes" / "AZ_tools" / "check_snapshots.py") if (
        (cwd / "A_Codes" / "AZ_tools").mkdir(parents=True, exist_ok=True) or True) else None
    write(cwd, "README.md", "repo\n")
    commit(cwd, "base", when=BEFORE_ENFORCED)
    return cwd


def run(cwd: Path, base: str, head: str = "HEAD") -> tuple[int, str]:
    out = subprocess.run([sys.executable, str(cwd / "A_Codes" / "AZ_tools" / "check_snapshots.py"),
                          base, head], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                         timeout=300)
    return out.returncode, out.stdout + out.stderr


def run_ci(cwd: Path, **env: str) -> tuple[int, str]:
    """The CI entry point: base and head resolved from the event, as the workflow passes them."""
    full = dict(os.environ) | {"PYTHONIOENCODING": "utf-8"} | env
    out = subprocess.run([sys.executable, str(cwd / "A_Codes" / "AZ_tools" / "check_snapshots.py"), "--ci"],
                         cwd=cwd, capture_output=True, text=True, encoding="utf-8", env=full, timeout=300)
    return out.returncode, out.stdout + out.stderr


def check(name: str, got, want) -> None:
    ok = got == want
    print(f"  {'PASS' if ok else 'FAIL'}  {name}: {got!r}" + ("" if ok else f"  (expected {want!r})"))
    if not ok:
        FAILURES.append(name)


def snapshot_of(cwd: Path, rel: str, version: int, content: str | bytes) -> None:
    """Place a `_OLD/` copy the way snapshot.sh would."""
    p = Path(rel)
    root, rest = p.parts[0], Path(*p.parts[1:])
    dest = f"{root}/_OLD/{rest.parent.as_posix()}/{rest.stem}_v{version}_20261009{rest.suffix}"
    write(cwd, dest.replace("/./", "/"), content)


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="check_snapshots_test_"))
    try:
        SRC = "A_Codes/AB_backend/app/thing.py"

        print("\nA commit that snapshots what it edits passes:")
        r = new_repo(tmp, "clean")
        write(r, SRC, "x = 1\n")
        base = commit(r, "add thing")
        snapshot_of(r, SRC, 1, "x = 1\n")
        write(r, SRC, "x = 2\n")
        commit(r, "edit thing, snapshotted")
        code, out = run(r, base)
        check("clean", code, 0)

        print("\nA commit that edits without snapshotting fails, and names the file:")
        r = new_repo(tmp, "missing")
        write(r, SRC, "x = 1\n")
        base = commit(r, "add thing")
        write(r, SRC, "x = 2\n")
        commit(r, "edit thing, no snapshot")
        code, out = run(r, base)
        check("missing snapshot", code, 1)
        check("names the file", SRC in out, True)

        print("\nThe near misses the hand checks kept having to rule out:")
        r = new_repo(tmp, "wrongbytes")
        write(r, SRC, "x = 1\n")
        base = commit(r, "add thing")
        snapshot_of(r, SRC, 1, "x = 999\n")  # right name, wrong bytes
        write(r, SRC, "x = 2\n")
        commit(r, "edit thing")
        check("right name, wrong bytes", run(r, base)[0], 1)

        r = new_repo(tmp, "wrongdir")
        write(r, SRC, "x = 1\n")
        base = commit(r, "add thing")
        write(r, "A_Codes/_OLD/AB_backend/thing_v1_20261009.py", "x = 1\n")  # right bytes, wrong folder
        write(r, SRC, "x = 2\n")
        commit(r, "edit thing")
        check("right bytes, wrong directory", run(r, base)[0], 1)

        print("\nLine endings are normalised, so CRLF in _OLD/ still matches:")
        r = new_repo(tmp, "crlf")
        write(r, SRC, "x = 1\n")
        base = commit(r, "add thing")
        snapshot_of(r, SRC, 1, b"x = 1\r\n")
        write(r, SRC, "x = 2\n")
        commit(r, "edit thing")
        check("CRLF snapshot of an LF file", run(r, base)[0], 0)

        print("\nPart 0's exclusions:")
        r = new_repo(tmp, "generated")
        write(r, "B_Inputs/AC_seed/T12.xlsx", "a\n")
        write(r, "B_Inputs/AA_bootstrap/T12.csv", "k,v\n")
        base = commit(r, "add inputs")
        write(r, "B_Inputs/AC_seed/T12.xlsx", "b\n")          # generated: excluded
        snapshot_of(r, "B_Inputs/AA_bootstrap/T12.csv", 1, "k,v\n")
        write(r, "B_Inputs/AA_bootstrap/T12.csv", "k,v2\n")   # hand-edited: covered, snapshotted
        commit(r, "regenerate seed, edit bootstrap")
        check("AC_seed excluded, bootstrap covered", run(r, base)[0], 0)

        r = new_repo(tmp, "bootstrap")
        write(r, "B_Inputs/AA_bootstrap/T12.csv", "k,v\n")
        base = commit(r, "add bootstrap")
        write(r, "B_Inputs/AA_bootstrap/T12.csv", "k,v2\n")   # no snapshot
        commit(r, "edit bootstrap")
        check("bootstrap CSV is covered", run(r, base)[0], 1)

        print("\nAdded and deleted files are not edits:")
        r = new_repo(tmp, "added")
        base = commit(r, "nothing", when=BEFORE_ENFORCED)
        write(r, SRC, "x = 1\n")
        commit(r, "add thing")
        check("an added file needs no snapshot", run(r, base)[0], 0)

        print("\nMerge commits are skipped — a merge-brought change was never a hand edit:")
        r = new_repo(tmp, "merge")
        write(r, SRC, "x = 1\n")
        base = commit(r, "add thing")
        git(r, "checkout", "-q", "-b", "side")
        write(r, SRC, "x = 2\n")          # edited on the branch, unsnapshotted
        commit(r, "edit on side")
        git(r, "checkout", "-q", "main")
        write(r, "README.md", "main moves\n")
        commit(r, "main moves")
        git(r, "merge", "-q", "--no-ff", "-m", "merge side", "side")
        # The side commit is still checked (it is in the range and not a merge), so this must fail
        # for that reason — but the merge commit itself must contribute nothing.
        code, out = run(r, base)
        check("the side edit is still caught", code, 1)
        check("the merge commit is not charged", out.count("FAIL"), 1)

        print("\nA mode-only change is not an edit:")
        r = new_repo(tmp, "mode")
        write(r, SRC, "x = 1\n")
        base = commit(r, "add thing")
        git(r, "update-index", "--chmod=+x", SRC)
        commit(r, "chmod only")
        check("mode-only change", run(r, base)[0], 0)

        print("\nA file edited twice needs the second edit snapshotted too:")
        r = new_repo(tmp, "twice")
        write(r, SRC, "x = 1\n")
        base = commit(r, "add thing")
        snapshot_of(r, SRC, 1, "x = 1\n")
        write(r, SRC, "x = 2\n")
        commit(r, "first edit, snapshotted")
        write(r, SRC, "x = 3\n")          # second edit, no snapshot of "x = 2"
        commit(r, "second edit, not snapshotted")
        code, out = run(r, base)
        check("the second edit is caught", code, 1)
        check("only the second commit fails", out.count("FAIL"), 1)

        print("\nRecovering a snapshot afterwards satisfies the earlier commit:")
        r = new_repo(tmp, "recovered")
        write(r, SRC, "x = 1\n")
        base = commit(r, "add thing")
        write(r, SRC, "x = 2\n")
        commit(r, "edit thing, no snapshot")
        check("before recovery", run(r, base)[0], 1)
        snapshot_of(r, SRC, 1, "x = 1\n")   # the accepted remedy
        commit(r, "recover the snapshot")
        check("after recovery", run(r, base)[0], 0)

        print("\nCommits before the enforcement date are reported, not failed:")
        r = new_repo(tmp, "grandfathered")
        write(r, SRC, "x = 1\n")
        base = commit(r, "add thing", when=BEFORE_ENFORCED)
        write(r, SRC, "x = 2\n")
        commit(r, "old edit, no snapshot", when=BEFORE_ENFORCED)
        code, out = run(r, base)
        check("grandfathered exit", code, 0)
        check("but it is reported", "reported, not failed" in out, True)

        print("\nPLT-02: a file renamed and rewritten in one commit is an edit (TR-87):")
        r = new_repo(tmp, "rename_rewrite")
        write(r, SRC, "x = 1\n" * 20)
        base = commit(r, "add thing")
        git(r, "mv", SRC, "A_Codes/AB_backend/app/renamed.py")
        write(r, "A_Codes/AB_backend/app/renamed.py", "x = 1\n" * 19 + "x = 2\n")  # similar enough for -M
        commit(r, "rename and rewrite, no snapshot")
        code, out = run(r, base)
        check("PLT-02 rename + rewrite without a snapshot fails", code, 1)
        check("PLT-02 names the new path", "A_Codes/AB_backend/app/renamed.py" in out, True)

        r = new_repo(tmp, "rename_rewrite_ok")
        write(r, SRC, "x = 1\n" * 20)
        base = commit(r, "add thing")
        snapshot_of(r, SRC, 1, "x = 1\n" * 20)            # the source, snapshotted before the rename
        git(r, "add", "-A")
        git(r, "mv", SRC, "A_Codes/AB_backend/app/renamed.py")
        write(r, "A_Codes/AB_backend/app/renamed.py", "x = 1\n" * 19 + "x = 2\n")
        commit(r, "rename and rewrite, source snapshotted")
        check("PLT-02 rename + rewrite with the source snapshotted passes", run(r, base)[0], 0)

        r = new_repo(tmp, "rename_only")
        write(r, SRC, "x = 1\n" * 20)
        base = commit(r, "add thing")
        git(r, "mv", SRC, "A_Codes/AB_backend/app/renamed.py")
        commit(r, "pure rename")
        check("PLT-02 a pure rename is not an edit", run(r, base)[0], 0)

        print("\nPLT-03: a non-ASCII path is checked, not silently dropped:")
        r = new_repo(tmp, "nonascii")
        uni = "A_Codes/AB_backend/app/café_règle.py"
        write(r, uni, "x = 1\n")
        base = commit(r, "add accented file")
        write(r, uni, "x = 2\n")
        commit(r, "edit accented file, no snapshot")
        code, out = run(r, base)
        check("PLT-03 non-ASCII edit without a snapshot fails", code, 1)
        check("PLT-03 names the non-ASCII path", uni in out, True)

        print("\nPLT-03: the number of file edits checked is reported, so a skip cannot be silent:")
        r = new_repo(tmp, "count")
        write(r, SRC, "x = 1\n")
        write(r, "A_Codes/AB_backend/app/other.py", "y = 1\n")
        base = commit(r, "add two")
        snapshot_of(r, SRC, 1, "x = 1\n")
        snapshot_of(r, "A_Codes/AB_backend/app/other.py", 1, "y = 1\n")
        write(r, SRC, "x = 2\n")
        write(r, "A_Codes/AB_backend/app/other.py", "y = 2\n")
        commit(r, "edit two, both snapshotted")
        code, out = run(r, base)
        check("PLT-03 count line", "2 file edit(s) checked" in out, True)

        print("\nPLT-03: the enforcement cut-off reads the committer date, which a rebase resets (CR-69):")
        r = new_repo(tmp, "rebased")
        write(r, SRC, "x = 1\n")
        base = commit(r, "add thing")
        write(r, SRC, "x = 2\n")
        commit(r, "edit, no snapshot, old author date", authored=BEFORE_ENFORCED)  # committed after
        check("PLT-03 an old author date does not grandfather a new commit", run(r, base)[0], 1)

        print("\nPLT-03: CI resolves a non-empty base on every trigger, and fails closed (TR-88):")
        r = new_repo(tmp, "ci")
        write(r, SRC, "x = 1\n")
        first = commit(r, "add thing")
        git(r, "checkout", "-q", "-b", "feature")
        write(r, SRC, "x = 2\n")                  # unsnapshotted, so a correct range fails
        head = commit(r, "edit on feature")
        zeros = "0" * 40
        common = {"SNAP_HEAD": head, "SNAP_DEFAULT_BRANCH": "main"}
        code, out = run_ci(r, **common, SNAP_EVENT="push", SNAP_BEFORE=first)
        check("PLT-03 push uses `before`", (code, f"Range: {first}..{head}" in out), (1, True))
        code, out = run_ci(r, **common, SNAP_EVENT="push", SNAP_BEFORE=zeros)
        check("PLT-03 first push falls back to the merge base", (code, f"Range: {first}..{head}" in out),
              (1, True))
        code, out = run_ci(r, **common, SNAP_EVENT="workflow_dispatch", SNAP_BEFORE="")
        check("PLT-03 manual run uses the merge base, not a vacuous pass", (code, "Range: " in out), (1, True))
        git(r, "checkout", "-q", "main")
        write(r, "README.md", "main moves on\n")
        moved = commit(r, "main moves after the branch")
        code, out = run_ci(r, SNAP_EVENT="pull_request", SNAP_PR_BASE=moved, SNAP_PR_HEAD=head,
                           SNAP_HEAD="ignored-for-pr", SNAP_DEFAULT_BRANCH="main")
        check("PLT-03 pull request uses the merge base, not base.sha", f"Range: {first}..{head}" in out, True)
        code, out = run_ci(r, SNAP_EVENT="push", SNAP_BEFORE=zeros, SNAP_HEAD=head,
                           SNAP_DEFAULT_BRANCH="no-such-branch")
        check("PLT-03 an unresolvable base fails closed", code != 0 and "Range: " not in out, True)
        check("PLT-03 an empty base on the command line fails closed", run(r, "")[0] != 0, True)

        print("\nAn empty range, and failing closed on nonsense:")
        r = new_repo(tmp, "empty")
        base = commit(r, "second", when=BEFORE_ENFORCED)
        check("no commits in range", run(r, base)[0], 0)
        check("unknown ref fails closed", run(r, "no-such-ref")[0] != 0, True)

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
