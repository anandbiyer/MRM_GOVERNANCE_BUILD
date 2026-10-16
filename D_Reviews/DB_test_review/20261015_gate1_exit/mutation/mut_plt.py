import shutil, subprocess, sys, pathlib
SRC = pathlib.Path(r"C:/Users/anand/OneDrive/Documents/AI_Projects/MRM_Governance_Build/A_Codes/AZ_tools")
here = pathlib.Path(__file__).parent
orig = (SRC/"check_snapshots.py").read_text(encoding="utf-8")
M = {
 "P1_no_z_and_quotepath": [('"git", "-c", "core.quotePath=false", *args', '"git", *args'), ('"-r", "-z", "--diff-filter=MR"', '"-r", "--diff-filter=MR"'), (r'raw.split("\0")', r'raw.replace("\t","\n").split("\n")')],
 "P2_modified_only_no_renames": [('--diff-filter=MR', '--diff-filter=M')],
 "P3_rename_uses_source_path": [('paths.append(fields[i + 2])', 'paths.append(fields[i + 1])')],
 "P4_merges_charged": [('"rev-list", "--no-merges", "--reverse"', '"rev-list", "--reverse"')],
 "P5_mode_only_charged": [('if after is not None and digest(before) == digest(after):', 'if False:')],
 "P6_name_match_only": [('if any(digest(data) == want for _, data in candidates):', 'if candidates:')],
 "P7_count_not_reported": [(r'print(f"\nChecked {checked} non-merge commit(s) between {base[:12]} and {head[:12]}.")', 'pass')],
 "P8_count_wrong": [('checked += 1', 'checked += 0')],
 "P9_all_B_Inputs_generated": [('GENERATED = ("B_Inputs/AC_seed/", "B_Inputs/AD_demo_files/")', 'GENERATED = ("B_Inputs/",)')],
 "P10_everything_grandfathered": [('if authored < ENFORCED_FROM:', 'if True:')],
 "P11_git_error_passes": [('raise SystemExit(f"git', 'return ""  # f"git')],
 "P12_crlf_not_normalised": [(r'data.replace(b"\r\n", b"\n")', 'data')],
 "P13_deleted_charged": [('if before is None:\n            continue', 'if before is None:\n            missing.append(path); continue')],
 "P14_added_charged_via_filter": [('--diff-filter=MR', '--diff-filter=MRA')],
 "P15_old_read_at_commit": [('candidates = old_candidates(head, path)', 'candidates = old_candidates(sha, path)')],
}
res = []
for name, subs in M.items():
    d = here/name/"A_Codes"/"AZ_tools"; d.mkdir(parents=True, exist_ok=True)
    src = orig
    for a, b in subs:
        assert a in src, (name, a)
        src = src.replace(a, b)
    (d/"check_snapshots.py").write_text(src, encoding="utf-8")
    shutil.copy(SRC/"test_check_snapshots.py", d/"test_check_snapshots.py")
    p = subprocess.run([sys.executable, str(d/"test_check_snapshots.py")], capture_output=True, text=True, timeout=900)
    fails = [l.strip() for l in p.stdout.splitlines() if "FAIL" in l]
    res.append((name, p.returncode, fails[:3]))
    print(name, "KILLED" if p.returncode else "SURVIVED", fails[:3], flush=True)
