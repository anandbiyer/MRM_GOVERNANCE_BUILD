#!/bin/bash
# Runs the reset-related tests against each mutant (in memory) four at a time.
B=/c/Users/anand/OneDrive/Documents/AI_Projects/MRM_Governance_Build/A_Codes/AB_backend
R=/c/Users/anand/OneDrive/Documents/AI_Projects/MRM_Governance_Build/D_Reviews/DB_test_review/20261015_G1.32
SP="C:/Users/anand/AppData/Local/Temp/claude/C--Users-anand-OneDrive-Documents-AI-Projects-MRM-Governance-Build/7475a71c-ccaa-41be-b1e5-87e13ffed8ec/scratchpad/mut32"
K="reset or ft_0 or cr_5 or gen_01 or g1_32 or reg_17 or baseline or second_reset"
cd $B
run() { name=$1; if [ "$name" = control ]; then MUT=""; else MUT="$SP/$name.py"; fi
  MUTANT="$MUT" PYTHONPATH="$R" .venv/Scripts/python -m pytest -q -p no:cacheprovider -p mutation_plugin \
    tests/test_imports.py tests/test_documents.py tests/test_reports.py tests/test_reset_lock.py -k "$K" > "$R/mut_$name.txt" 2>&1; }
names="control $(ls $SP | sed 's/\.py$//')"
for n in $names; do run $n & while [ $(jobs -r | wc -l) -ge 4 ]; do sleep 2; done; done; wait
for n in $names; do echo "== $n"; grep -E "^FAILED|passed|failed" "$R/mut_$n.txt" | sed 's/ - .*//' ; done > "$R/mutation_results.txt"
