#!/bin/bash
name="$1"; MUTDIR="$2"
cd /c/Users/anand/OneDrive/Documents/AI_Projects/MRM_Governance_Build/A_Codes/AB_backend
case "$name" in
  R*) tests="tests/test_reports.py tests/test_api_timestamps.py";;
  G*) tests="tests/test_reset_lock.py tests/test_imports.py tests/test_reports.py";;
esac
MUT="$name" PYTHONPATH="$MUTDIR" PYTHONDONTWRITEBYTECODE=1 timeout 1500 .venv/Scripts/python -m pytest -q -p no:cacheprovider -p mut_g1x $tests > "$MUTDIR/out_$name.txt" 2>&1
echo "exit=$?" >> "$MUTDIR/out_$name.txt"
echo "$name $(grep -E '[0-9]+ (passed|failed)' "$MUTDIR/out_$name.txt" | tail -1)"
