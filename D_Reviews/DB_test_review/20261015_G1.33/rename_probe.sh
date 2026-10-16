#!/bin/bash
# R2 checkpoint G1.33 probes (test-outcome-reviewer). Each case: a scratch repo with check_snapshots.py
# from 3994f43 (via git show, never the working tree), one enforced commit, the tool's exit and git's view.
# Usage: rename_probe.sh <repo-root> <scratch-dir>
set -u
ROOT="$1"; S="$2"; rm -rf "$S"; mkdir -p "$S"
export GIT_AUTHOR_DATE=2026-10-10T12:00:00 GIT_COMMITTER_DATE=2026-10-10T12:00:00 PYTHONUTF8=1
c() { git add -A; git -c user.name=t -c user.email=t@t commit -qm "$1"; }
body() { for i in $(seq 1 20); do echo "line_$i = $i"; done; }
setup() { W="$S/$1"; mkdir -p "$W/A_Codes/AZ_tools" "$W/A_Codes/AB_backend/app"; cd "$W"
  git -C "$ROOT" show 3994f43:A_Codes/AZ_tools/check_snapshots.py > A_Codes/AZ_tools/check_snapshots.py
  git init -q -b main; git config core.autocrlf false
  body > A_Codes/AB_backend/app/thing.py; c base; B=$(git rev-parse HEAD); }
report() { echo "-- git diff-tree -M:"; git diff-tree --no-commit-id -r -M --name-status HEAD
  python A_Codes/AZ_tools/check_snapshots.py "$B" HEAD | tail -3; echo "exit=${PIPESTATUS[0]}"; echo; }
OLD=A_Codes/_OLD/AB_backend/app

echo "== 1. Self-test case 'rename + rewrite with the source snapshotted' reproduced: what does git pair?"
setup t1; mkdir -p $OLD; cp A_Codes/AB_backend/app/thing.py $OLD/thing_v1_20261009.py
git mv A_Codes/AB_backend/app/thing.py A_Codes/AB_backend/app/renamed.py
body | sed 's/line_20 = 20/line_20 = 99/' > A_Codes/AB_backend/app/renamed.py; c "rename+rewrite, source snapshotted"; report

echo "== 2. Same, but the snapshot committed first (separate commit), so the rename pairs thing->renamed"
setup t2; mkdir -p $OLD; cp A_Codes/AB_backend/app/thing.py $OLD/thing_v1_20261009.py; c "snapshot"
git mv A_Codes/AB_backend/app/thing.py A_Codes/AB_backend/app/renamed.py
body | sed 's/line_20 = 20/line_20 = 99/' > A_Codes/AB_backend/app/renamed.py; c "rename+rewrite"; report

echo "== 3. Snapshot named for the destination, committed first (exercises the dst candidate branch; N1)"
setup t3; mkdir -p $OLD; cp A_Codes/AB_backend/app/thing.py $OLD/renamed_v1_20261009.py; c "snapshot under new name"
git mv A_Codes/AB_backend/app/thing.py A_Codes/AB_backend/app/renamed.py
body | sed 's/line_20 = 20/line_20 = 99/' > A_Codes/AB_backend/app/renamed.py; c "rename+rewrite"; report

echo "== 4. Rename + heavy rewrite (similarity below git's 50% default), no snapshot"
setup t4; git mv A_Codes/AB_backend/app/thing.py A_Codes/AB_backend/app/renamed.py
body | sed '1,12s/= [0-9]*/= 0/' > A_Codes/AB_backend/app/renamed.py; c "rename+heavy rewrite"; report

echo "== 5. Rename + rewrite with an exact decoy copy of the source added elsewhere under A_Codes, no snapshot"
setup t5; cp A_Codes/AB_backend/app/thing.py A_Codes/AB_backend/app/thing_backup.py
git rm -q --cached A_Codes/AB_backend/app/thing.py; mv A_Codes/AB_backend/app/thing.py A_Codes/AB_backend/app/renamed.py
body | sed 's/line_20 = 20/line_20 = 99/' > A_Codes/AB_backend/app/renamed.py; c "rename+rewrite plus decoy"; report

echo "== 6. Rename out of A_Codes/ and rewrite, no snapshot (N3: covered(src) only)"
setup t6; mkdir -p docs; git mv A_Codes/AB_backend/app/thing.py docs/thing.py
body | sed 's/line_20 = 20/line_20 = 99/' > docs/thing.py; c "move out and rewrite"; report

echo "== 7. Delete a covered file outright (out of PLT-02 scope by wording; shown for context)"
setup t7; git rm -q A_Codes/AB_backend/app/thing.py; c "delete"; report
