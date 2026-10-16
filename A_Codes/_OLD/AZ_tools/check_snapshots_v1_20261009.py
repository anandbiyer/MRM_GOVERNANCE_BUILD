#!/usr/bin/env python3
"""Fail if a change set edited a file under A_Codes/ or B_Inputs/ without snapshotting it first.

    python A_Codes/AZ_tools/check_snapshots.py <base-ref> [<head-ref>]

Part 0's first convention says: before editing an existing hand-edited file under `A_Codes/` or
`B_Inputs/`, copy it into `_OLD/` with `snapshot.sh`. It has been broken and repaired at **five**
consecutive reviews — CR-22, CR-29, CR-40 (twice over) and CR-54 — always found by a reviewer reading
`git log`, never by the build. The pattern is consistent: a file edited across several commits in one
session, where the first snapshot is taken and the later edits are not. A reviewer's eye is the wrong
instrument for that, so this is plan row **G3.0**, pulled into Gate 1 to guard its own fixes.

**What it actually guarantees.** For every hand-edited file modified between the two refs, the
content it had *at the base ref* is recoverable from `_OLD/`. That is weaker than "one snapshot per
edit", which no post-hoc check can verify — a file edited three times in the range leaves only its
starting point to look for. It is the guarantee that matters in practice: whatever the file looked
like before this change set, you can still find it.

Matching is by **content**, not by filename. A `_OLD/` copy with a plausible name but different bytes
is what the hand checks kept having to rule out, and line endings are normalised because the working
tree is CRLF while `git show` yields LF.

Exclusions, all deliberate:
  * `_OLD/` itself — snapshots of snapshots.
  * `B_Inputs/AC_seed/` and `B_Inputs/AD_demo_files/` — generated from `generate_seed.py` and the
    bootstrap CSVs, both of which *are* covered. Part 0 excludes them explicitly: snapshotting them
    per regeneration would restore exactly the churn G0.15 removed.
  * Added and deleted files. The convention is about *editing* something that already existed.

Exit 0 when clean, 1 with a per-file report when not. Standard library only.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

ROOTS = ("A_Codes/", "B_Inputs/")
GENERATED = ("B_Inputs/AC_seed/", "B_Inputs/AD_demo_files/")
REPO = Path(__file__).resolve().parents[2]


def git(*args: str) -> str:
    out = subprocess.run(["git", *args], cwd=REPO, capture_output=True, timeout=120)
    if out.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed:\n{out.stderr.decode('utf-8', 'replace')}")
    return out.stdout.decode("utf-8", "replace")


def blob(ref: str, path: str) -> bytes | None:
    """Raw bytes of `path` at `ref`, or None when it is absent there."""
    out = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=REPO, capture_output=True, timeout=120)
    return out.stdout if out.returncode == 0 else None


def digest(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def covered(path: str) -> bool:
    if not path.startswith(ROOTS) or "/_OLD/" in f"/{path}":
        return False
    return not path.startswith(GENERATED)


def old_candidates(path: str) -> list[Path]:
    """`_OLD/` files that could be a snapshot of `path`, by position and stem."""
    p = Path(path)
    root, rest = p.parts[0], Path(*p.parts[1:])
    folder = REPO / root / "_OLD" / rest.parent
    if not folder.is_dir():
        return []
    return sorted(folder.glob(f"{rest.stem}_v*{rest.suffix}"))


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    base, head = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "HEAD")

    modified = [line for line in git("diff", "--name-only", "--diff-filter=M", base, head).splitlines()
                if line.strip() and covered(line.strip())]
    if not modified:
        print(f"No hand-edited files under {' or '.join(ROOTS)} modified between "
              f"{base[:12]} and {head[:12]}.")
        return 0

    missing: list[str] = []
    for path in modified:
        before = blob(base, path)
        if before is None:  # a rename can show as a modification of the new path
            continue
        want = digest(before)
        if any(digest(c.read_bytes()) == want for c in old_candidates(path)):
            continue
        found = ", ".join(c.name for c in old_candidates(path)) or "none"
        missing.append(f"  {path}\n      pre-change sha256 {want[:16]}…  _OLD/ copies present: {found}")

    print(f"Checked {len(modified)} modified file(s) between {base[:12]} and {head[:12]}.")
    if not missing:
        print("Every one has its pre-change content in _OLD/.")
        return 0

    print(f"\n{len(missing)} file(s) were edited without a recoverable snapshot:\n")
    print("\n".join(missing))
    print("\nPart 0: snapshot before editing —")
    print("  bash A_Codes/AZ_tools/snapshot.sh <A_Codes|B_Inputs> <path within it>")
    print("To recover one after the fact, as four reviews have had to:")
    print(f"  git show {base}:<path> > A_Codes/_OLD/<same relative path>/<name>_v<N>_<YYYYMMDD>.<ext>")
    return 1


if __name__ == "__main__":
    sys.exit(main())
