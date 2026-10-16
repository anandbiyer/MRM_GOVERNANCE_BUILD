#!/usr/bin/env python3
"""Fail if a commit edited a file under A_Codes/ or B_Inputs/ without snapshotting it first.

    python A_Codes/AZ_tools/check_snapshots.py <base-ref> [<head-ref>]
    python A_Codes/AZ_tools/check_snapshots.py --ci        # base and head from the CI event (below)

Criteria **PLT-02** and **PLT-03** (§76E, D15); tests in `test_check_snapshots.py`.

Part 0's first convention: before editing an existing hand-edited file under `A_Codes/` or
`B_Inputs/`, copy it into `_OLD/` with `snapshot.sh`. It has been broken and repaired at **five**
consecutive reviews — CR-22, CR-29, CR-40 (twice) and CR-54 — always found by a reviewer reading
`git log`, never by the build, and twice in the very commits that were fixing the previous instance.
Plan row **G3.0**.

**Per commit, not per range, and that is the whole point.** The first version of this script diffed
`base..head` as one change set, and its R2 checkpoint showed that could not work: all three files
CR-54 named are *created* on this branch, so against `main` they are additions and were excluded by
design — the control could not detect the finding it was written for (TR-50). Worse, a range diff
charges merge-brought changes to whoever merged, so the job could never go green on a branch that
Part 0 *requires* merging `main` into (TR-49). A control nobody can get green gets overridden, which
is the mirror of failing open.

So: walk the commits, skip merges, and ask of each one whether *that* commit snapshotted what it
edited. A file added in one commit and edited in the next is caught at the second, which is exactly
the pattern every one of the five instances took.

**What it guarantees.** For each non-merge commit, every hand-edited file it modified has the content
it had *in that commit's parent* somewhere in `_OLD/`. Matching is by **content**, not filename —
line endings normalised, because the working tree is CRLF while `git show` yields LF, and a
plausibly-named copy with different bytes is what the hand checks kept having to rule out.

**Renames.** A file renamed and rewritten in one commit is an edit. `diff-tree` runs with `-M`, and
the pre-change content is looked up at the rename's **source** path in the parent — the destination
does not exist there. Without both, a rename-and-rewrite passed with nothing snapshotted (TR-87). A
pure rename, content unchanged, is not an edit.

**Grandfathered.** Commits *committed* before `ENFORCED_FROM` are reported but not failed. The
committer date, not the author date: a rebase or cherry-pick preserves the author date, so a new
commit could otherwise borrow an old one's exemption (CR-69). The history
before this control contains gaps that are already repaired (the five reviews) and some that cannot
be repaired even in principle: `_OLD/` holds copies taken at *uncommitted* intermediate states, which
match no committed parent and so can never be found by any post-hoc check. Enforcing retroactively
would make the job permanently red, and a permanently red control is one that gets switched off.

Exclusions, all deliberate:
  * `_OLD/` itself — snapshots of snapshots.
  * `B_Inputs/AC_seed/` and `B_Inputs/AD_demo_files/` — generated from `generate_seed.py` and the
    bootstrap CSVs, both of which *are* covered. Part 0 excludes them: snapshotting them per
    regeneration would restore exactly the churn G0.15 removed.
  * Merge commits — a merge-brought change was never a hand edit.
  * Mode-only changes, where the content is identical on both sides.

Exit 0 when clean, 1 with a per-commit report when not. Standard library only, so CI installs nothing.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import os
from datetime import date
from pathlib import Path

ROOTS = ("A_Codes/", "B_Inputs/")
GENERATED = ("B_Inputs/AC_seed/", "B_Inputs/AD_demo_files/")
REPO = Path(__file__).resolve().parents[2]

#: Commits authored on or after this date are enforced; earlier ones are reported only. The date
#: G3.0 landed. See the module docstring for why the history before it cannot be made green.
ENFORCED_FROM = date(2026, 10, 9)


def git(*args: str) -> str:
    out = subprocess.run(["git", "-c", "core.quotePath=false", *args],
                         cwd=REPO, capture_output=True, timeout=180)
    if out.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{out.stderr.decode('utf-8', 'replace')}")
    return out.stdout.decode("utf-8", "replace")


def blob(ref: str, path: str) -> bytes | None:
    """Raw bytes of `path` at `ref`, or None when it is absent there."""
    out = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=REPO, capture_output=True, timeout=180)
    return out.stdout if out.returncode == 0 else None


def digest(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def covered(path: str) -> bool:
    if not path.startswith(ROOTS) or "/_OLD/" in f"/{path}":
        return False
    return not path.startswith(GENERATED)


def old_candidates(ref: str, path: str) -> list[tuple[str, bytes]]:
    """`(name, bytes)` of every `_OLD/` file at `ref` that could be a snapshot of `path`.

    `ref` is the **head** of the range, not the commit being checked, and that is deliberate. The
    convention exists so history stays recoverable, and recovering a missed snapshot afterwards with
    `git show <commit>^:<path>` is an accepted remedy — the owner has approved it three times. Read
    at the commit instead, a recovery could never satisfy the check that demanded it, so every past
    omission would stay red for ever and the job would be permanently unpassable. Read from the ref
    rather than the working tree so the answer does not depend on how the tree is checked out.
    """
    p = Path(path)
    root, rest = p.parts[0], Path(*p.parts[1:])
    prefix = f"{root}/_OLD/{rest.parent.as_posix()}/".replace("/./", "/")
    stem, suffix = rest.stem, rest.suffix
    out = []
    for listed in git("ls-tree", "-r", "--name-only", ref, "--", prefix).splitlines():
        name = Path(listed).name
        if name.startswith(f"{stem}_v") and name.endswith(suffix):
            data = blob(ref, listed)
            if data is not None:
                out.append((name, data))
    return out


def modified_in(sha: str) -> list[tuple[str, str]]:
    """`(path before, path after)` of each hand-edited file this commit modified or renamed.

    `-M` so a rename is reported as one (TR-87: without it, a rename-and-rewrite showed as an add plus
    a delete and was never checked). `-z` so odd filenames are neither quoted nor split, and
    `core.quotePath=false` (in `git`) for the same reason. A rename is covered if either end is.
    """
    raw = git("diff-tree", "--no-commit-id", "-r", "-z", "-M", "--diff-filter=MR", sha)
    fields = [f for f in raw.split("\0") if f]
    pairs: list[tuple[str, str]] = []
    i = 0
    while i < len(fields):
        meta = fields[i]
        # ":<srcmode> <dstmode> <srcsha> <dstsha> <status>" then one path, or two when status is R.
        status = meta.rsplit(" ", 1)[-1] if meta.startswith(":") else ""
        if status.startswith("R"):
            pairs.append((fields[i + 1], fields[i + 2]))
            i += 3
        else:
            pairs.append((fields[i + 1], fields[i + 1]))
            i += 2
    return [(src, dst) for src, dst in pairs if covered(src) or covered(dst)]


def check_commit(sha: str, head: str) -> tuple[int, list[str]]:
    """`(edits checked, report lines)` for this commit's edits whose pre-change content is not
    recoverable from `_OLD/` at `head`."""
    missing = []
    checked = 0
    for src, dst in modified_in(sha):
        before = blob(f"{sha}^", src)  # the source path: for a rename, the destination is new here
        if before is None:
            continue  # nothing earlier to recover
        after = blob(sha, dst)
        if after is not None and digest(before) == digest(after):
            continue  # mode-only, line-ending-only or pure rename: nothing was edited
        checked += 1
        want = digest(before)
        # A snapshot taken before a rename is named for the source; one taken after, for the
        # destination. Matching is by content, so either is accepted.
        candidates = old_candidates(head, src) + (old_candidates(head, dst) if dst != src else [])
        if any(digest(data) == want for _, data in candidates):
            continue
        names = ", ".join(n for n, _ in candidates) or "none"
        shown = dst if src == dst else f"{dst} (renamed from {src})"
        missing.append(f"      {shown}\n          pre-change sha256 {want[:16]}…  _OLD/ present: {names}")
    return checked, missing


ZERO_SHA = "0" * 40


def resolve_range(event: str, before: str, head: str, pr_base: str, pr_head: str,
                  default_branch: str) -> tuple[str, str]:
    """`(base, head)` for a CI run, or SystemExit when no base can be found. Never an empty base.

    Moved here from the workflow's shell so it can be tested (TR-88), and so every way it can go
    wrong fails closed rather than printing "nothing to diff" and exiting 0 (TR-52):
      * pull_request — the merge base of the PR's base and head, not `base.sha`: a base branch that
        has moved since the PR opened would otherwise charge the PR with other people's commits (TR-54).
      * push — `before`, unless it is the all-zero sha of a branch's first push, when the merge base
        with the default branch is used.
      * anything else (workflow_dispatch, a re-run) — the merge base with the default branch.
    """
    if event == "pull_request":
        head = pr_head
        base = git("merge-base", pr_base, pr_head).strip()
    elif event == "push" and before and before != ZERO_SHA:
        base = before
    else:
        base = git("merge-base", default_branch, head).strip()
    if not base or not head:
        raise SystemExit(f"Could not resolve a base for event {event!r}; refusing to pass vacuously.")
    return base, head


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    if sys.argv[1] == "--ci":
        e = os.environ.get
        base, head = resolve_range(e("SNAP_EVENT", ""), e("SNAP_BEFORE", ""), e("SNAP_HEAD", ""),
                                   e("SNAP_PR_BASE", ""), e("SNAP_PR_HEAD", ""),
                                   e("SNAP_DEFAULT_BRANCH", "origin/main"))
        print(f"Range: {base}..{head}  (event {e('SNAP_EVENT', '')})")
    else:
        base, head = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "HEAD")
    if not base.strip():
        # `git rev-list ..HEAD` is an empty range, so an empty base would pass vacuously (TR-88).
        print("An empty base ref was given; refusing to pass vacuously.")
        return 2

    listed = git("rev-list", "--no-merges", "--reverse", f"{base}..{head}").split()
    if not listed:
        print(f"No non-merge commits between {base[:12]} and {head[:12]}.")
        return 0

    enforced_failures = 0
    grandfathered = 0
    checked = 0
    edits = 0
    for sha in listed:
        # Committer date (CR-69): a rebase keeps the author date, which would let a new commit
        # borrow an old one's exemption.
        committed = date.fromisoformat(git("show", "-s", "--format=%cd", "--date=format:%Y-%m-%d", sha).strip())
        n, missing = check_commit(sha, head)
        edits += n
        checked += 1
        if not missing:
            continue
        subject = git("show", "-s", "--format=%s", sha).strip()
        if committed < ENFORCED_FROM:
            grandfathered += len(missing)
            print(f"  (before {ENFORCED_FROM}, reported only) {sha[:8]} {subject[:60]}")
            print("\n".join(missing))
            continue
        enforced_failures += len(missing)
        print(f"  FAIL {sha[:8]} {subject[:60]}")
        print("\n".join(missing))

    print(f"\nChecked {checked} non-merge commit(s) between {base[:12]} and {head[:12]}: "
          f"{edits} file edit(s) checked.")
    if grandfathered:
        print(f"{grandfathered} gap(s) in commits committed before {ENFORCED_FROM}: reported, not failed.")
    if not enforced_failures:
        print("Every enforced commit snapshotted what it edited.")
        return 0

    print(f"\n{enforced_failures} file edit(s) without a recoverable snapshot. Part 0:")
    print("  bash A_Codes/AZ_tools/snapshot.sh <A_Codes|B_Inputs> <path within it>")
    print("To recover one after the fact, as five reviews have had to:")
    print("  git show <commit>^:<path> > A_Codes/_OLD/<same relative path>/<name>_v<N>_<YYYYMMDD>.<ext>")
    return 1


if __name__ == "__main__":
    sys.exit(main())
