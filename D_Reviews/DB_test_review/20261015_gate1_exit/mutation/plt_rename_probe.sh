#!/bin/bash
# Reviewer probe for PLT-02 / PLT-03 (test-outcome-reviewer, Gate 1 exit, 2026-10-15).
# Builds a throwaway repo outside the repository, makes one enforced commit that renames AND rewrites
# a hand-edited file with no snapshot, and runs the real check_snapshots.py over it, once as shipped
# and once with `-M` added to diff-tree. Usage: plt_rename_probe.sh <scratch-dir>
set -u
REPO_TOOL="$(cd "$(dirname "$0")/../../../.." && pwd)/A_Codes/AZ_tools/check_snapshots.py"
W="$1/plt_rename_probe"; rm -rf "$W"; mkdir -p "$W/A_Codes/AZ_tools" "$W/A_Codes/AB_backend/app"; cd "$W"
cp "$REPO_TOOL" A_Codes/AZ_tools/
git init -q -b main; git config core.autocrlf false
export GIT_AUTHOR_DATE=2026-10-10T12:00:00 GIT_COMMITTER_DATE=2026-10-10T12:00:00
c() { git add -A; git -c user.name=t -c user.email=t@t commit -qm "$1"; }
printf 'a = 1\nb = 2\nc = 3\nd = 4\ne = 5\n' > A_Codes/AB_backend/app/old.py; c base; B=$(git rev-parse HEAD)
git mv A_Codes/AB_backend/app/old.py A_Codes/AB_backend/app/new.py
printf 'a = 1\nb = 2\nc = 3\nd = 4\ne = 6\n' > A_Codes/AB_backend/app/new.py; c "rename and rewrite, no snapshot"
echo "== git sees:"; git diff-tree --no-commit-id -r -M --name-status HEAD
echo "== as shipped (PLT-02 expects exit 1):"; python A_Codes/AZ_tools/check_snapshots.py "$B" HEAD; echo "exit=$?"
sed -i 's/"-r", "-z", "--diff-filter=MR"/"-r", "-z", "-M", "--diff-filter=MR"/' A_Codes/AZ_tools/check_snapshots.py
echo "== with -M added (still the destination path as the base path):"; python A_Codes/AZ_tools/check_snapshots.py "$B" HEAD; echo "exit=$?"
echo "== empty base (the script alone; CI guards with test -n):"; python A_Codes/AZ_tools/check_snapshots.py "" HEAD; echo "exit=$?"
