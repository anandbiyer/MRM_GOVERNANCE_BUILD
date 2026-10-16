"""R2 checkpoint G1.33 (test-outcome-reviewer, 2026-10-15). Mutants of check_snapshots.py at 3994f43,
each run against the self-test at 3994f43, from copies under this folder (the working tree is untouched).
P* are the Gate 1 exit mutants (mut_plt.py) ported to the new code; N* are new for the G1.33 change.
Run with PYTHONUTF8=1 so the Windows cp1252 crash (TR-94) does not count as a kill."""
import os, subprocess, sys, pathlib, shutil
from concurrent.futures import ThreadPoolExecutor
REPO = pathlib.Path(__file__).resolve().parents[4]
here = pathlib.Path(__file__).parent
show = lambda p: subprocess.run(["git", "show", f"3994f43:{p}"], cwd=REPO, capture_output=True, check=True).stdout.decode("utf-8")
orig = show("A_Codes/AZ_tools/check_snapshots.py"); test = show("A_Codes/AZ_tools/test_check_snapshots.py")
M = {
 "P0_identity": [],
 "P1_no_z_and_quotepath": [('"git", "-c", "core.quotePath=false", *args', '"git", *args'), ('"-r", "-z", "-M"', '"-r", "-M"'), (r'raw.split("\0")', r'raw.replace("\t","\n").split("\n")')],
 "P2_modified_only_no_renames": [('--diff-filter=MR', '--diff-filter=M')],
 "P2b_no_M": [('"-r", "-z", "-M",', '"-r", "-z",')],
 "P3_rename_base_at_destination": [('before = blob(f"{sha}^", src)', 'before = blob(f"{sha}^", dst)')],
 "P4_merges_charged": [('"rev-list", "--no-merges", "--reverse"', '"rev-list", "--reverse"')],
 "P5_mode_only_charged": [('if after is not None and digest(before) == digest(after):', 'if False:')],
 "P6_name_match_only": [('if any(digest(data) == want for _, data in candidates):', 'if candidates:')],
 "P7_count_not_printed": [('f"{edits} file edit(s) checked.")', 'f"")')],
 "P8_count_wrong": [('        checked += 1\n        want', '        want')],
 "P9_all_B_Inputs_generated": [('GENERATED = ("B_Inputs/AC_seed/", "B_Inputs/AD_demo_files/")', 'GENERATED = ("B_Inputs/",)')],
 "P10_everything_grandfathered": [('if committed < ENFORCED_FROM:', 'if True:')],
 "P10b_author_date": [('"--format=%cd"', '"--format=%ad"')],
 "P11_git_error_passes": [('raise SystemExit(f"git', 'return ""  # f"git')],
 "P12_crlf_not_normalised": [(r'data.replace(b"\r\n", b"\n")', 'data')],
 "P13_deleted_charged": [('if before is None:\n            continue', 'if before is None:\n            missing.append(dst); continue')],
 "P14_added_charged_via_filter": [('--diff-filter=MR', '--diff-filter=MRA')],
 "P15_old_read_at_commit": [('candidates = old_candidates(head, src)', 'candidates = old_candidates(sha, src)'), ('old_candidates(head, dst) if', 'old_candidates(sha, dst) if')],
 "N1_no_destination_candidates": [('+ (old_candidates(head, dst) if dst != src else [])', '')],
 "N2_no_source_candidates": [('candidates = old_candidates(head, src) + (old_candidates(head, dst) if dst != src else [])', 'candidates = old_candidates(head, dst)')],
 "N3_covered_by_destination_only": [('if covered(src) or covered(dst)]', 'if covered(dst)]')],
 "N4_pr_uses_base_sha": [('base = git("merge-base", pr_base, pr_head).strip()', 'base = pr_base')],
 "N5_pr_head_not_switched": [('        head = pr_head\n', '')],
 "N6_zero_sha_used_as_base": [('before and before != ZERO_SHA', 'before')],
 "N7_dispatch_vacuous": [('    else:\n        base = git("merge-base", default_branch, head).strip()', '    else:\n        base = head')],
 "N8_resolve_empty_guard_removed": [('if not base or not head:', 'if False:')],
 "N9_main_empty_guard_removed": [('if not base.strip():', 'if False:')],
 "N10_any_event_uses_before": [('elif event == "push" and before and before != ZERO_SHA:', 'elif before != ZERO_SHA:')],
 "N11_empty_range_exit0_on_unknown": [('listed = git("rev-list"', 'listed = (lambda *a: "")("rev-list"')],
 "N12_pure_rename_charged": [('if after is not None and digest(before) == digest(after):', 'if src == dst and after is not None and digest(before) == digest(after):')],
 "N13_rename_skips_check": [('        if status.startswith("R"):\n            pairs.append((fields[i + 1], fields[i + 2]))', '        if status.startswith("R"):\n            pass')],
}
def one(item):
    name, subs = item
    d = here / "mutants" / name / "A_Codes" / "AZ_tools"; d.mkdir(parents=True, exist_ok=True)
    src = orig
    for a, b in subs:
        assert a in src, (name, a); src = src.replace(a, b)
    (d / "check_snapshots.py").write_text(src, encoding="utf-8", newline="\n")
    (d / "test_check_snapshots.py").write_text(test, encoding="utf-8", newline="\n")
    env = dict(os.environ, PYTHONUTF8="1")
    p = subprocess.run([sys.executable, str(d / "test_check_snapshots.py")], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=1200)
    (here / "mutants" / f"{name}.txt").write_text(p.stdout + p.stderr, encoding="utf-8")
    fails = [l.strip() for l in p.stdout.splitlines() if l.strip().startswith("FAIL")]
    return name, p.returncode, fails
with ThreadPoolExecutor(6) as ex:
    for name, rc, fails in ex.map(one, M.items()):
        print(f"{name:36s} {'KILLED' if rc else 'SURVIVED'}  {fails[:3]}", flush=True)
