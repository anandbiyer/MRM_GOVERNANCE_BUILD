#!/bin/bash
# Gate 1 exit re-run: one mutant of mut_g1y.py, applied in-process (no repository file is edited).
name="$1"; MUTDIR="$2"; OUTDIR="$3"
cd /c/Users/anand/OneDrive/Documents/AI_Projects/MRM_Governance_Build/A_Codes/AB_backend
case "$name" in
  R*) tests="tests/test_reports.py tests/test_api_timestamps.py";;
  C*|D*) tests="tests/test_reports.py tests/test_reset_lock.py";;
  G*) tests="tests/test_reset_lock.py tests/test_imports.py tests/test_reports.py";;
esac
MUT="$name" PYTHONPATH="$MUTDIR" PYTHONDONTWRITEBYTECODE=1 MRM_DATABASE_URL="sqlite://" timeout 1800 .venv/Scripts/python -m pytest -q -p no:cacheprovider -p mut_g1y -rf $tests > "$OUTDIR/out_$name.txt" 2>&1
echo "exit=$?" >> "$OUTDIR/out_$name.txt"
echo "$name | $(grep -E '[0-9]+ (passed|failed)' "$OUTDIR/out_$name.txt" | tail -1) | $(grep '^FAILED' "$OUTDIR/out_$name.txt" | head -3 | sed 's/FAILED tests\///; s/ - .*//' | tr '\n' ' ')"
