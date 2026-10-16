"""G1.32 re-run mutants of app/services/reset_service.py (staged version). Loaded in memory by
mutation_plugin.py; the product file is never edited. Usage: python mutation_make.py <src> <outdir>"""
import sys, pathlib
src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
out = pathlib.Path(sys.argv[2])

def rep(s, old, new):
    assert old in s, old
    return s.replace(old, new, 1)

READ_FIRST = ("    running = reset_in_progress(db)\n    if running is not None:\n"
              "        raise _already_running(running)\n")
EXC = ("    except OperationalError as exc:\n        db.rollback()\n"
       "        if \"locked\" not in str(exc).lower() and \"busy\" not in str(exc).lower():\n"
       "            raise  # a real database failure, not contention, is not a conflict\n"
       "        claimed = False\n")
BASE_REL = ("                release_reset_lock(session_factory, holder, \"Failed\",\n"
            "                                   f\"{stage} failed: {len(missing)} required policy setting(s) missing\")\n")
START_REL = "        release_reset_lock(session_factory, holder, \"Failed\", _failure(stage, exc))\n        raise\n    # From here"
REGEN = ("        directory = directory or get_settings().seed_dir\n"
         "        if get_settings().regenerate_seed_on_reset:\n            regenerate_seed(directory)\n")
HANDOVER = "    runner.submit(_store_evidence_then_seed_report, session_factory, staged, batch_id, holder)\n"
m = {}
# N1: no read-first; straight to the claim (the pre-fix shape plus the new except)
m["N1_no_read_first"] = rep(src, READ_FIRST, "")
# N2: no OperationalError handling at all (the pre-fix behaviour on a locked claim)
m["N2_no_operational_except"] = rep(src, EXC, "")
# N3: every OperationalError is a conflict (message filter removed)
m["N3_any_operational_error_is_409"] = rep(src, EXC,
    "    except OperationalError as exc:\n        db.rollback()\n        claimed = False\n")
# N4: a locked claim treated as "go ahead" (claimed = True) - the dangerous inversion
m["N4_locked_claim_treated_as_claimed"] = rep(src, "        claimed = False\n    if not claimed:",
    "        claimed = True\n    if not claimed:")
# N5: no rollback in the except (session left failed)
m["N5_no_rollback_in_except"] = rep(src, "    except OperationalError as exc:\n        db.rollback()\n",
    "    except OperationalError as exc:\n")
# N6: read-first answers without naming the running batch
m["N6_read_first_does_not_name_batch"] = rep(src, READ_FIRST,
    "    running = reset_in_progress(db)\n    if running is not None:\n        raise _already_running(None)\n")
# B: the missing-baseline path returns without releasing (builder claim)
m["B_baseline_path_no_release"] = rep(src, BASE_REL, "")
# C: start_reset's own failure path does not release (builder claim)
m["C_start_reset_failure_no_release"] = rep(src, START_REL, "        raise\n    # From here")
# H: regenerate the seed before the check (builder claim, TR-74)
m["H_regenerate_before_check"] = rep(rep(src, REGEN, ""), READ_FIRST,
    "    directory = directory or get_settings().seed_dir\n"
    "    if get_settings().regenerate_seed_on_reset:\n        regenerate_seed(directory)\n" + READ_FIRST)
# H2: create the import batch before the check (TR-74, "no batch created")
m["H2_batch_before_check"] = rep(src, READ_FIRST,
    "    _probe = import_service.create_batch(db, None, [('probe.csv', b'x')], source='reset', batch_type='seed')\n"
    "    db.commit()\n" + READ_FIRST)
# A: release at handover (TR-76: the spy must now return, not recurse)
m["A_release_at_handover"] = rep(src, HANDOVER,
    "    release_reset_lock(session_factory, holder, \"Completed\")\n" + HANDOVER)
for k, v in m.items():
    assert v != src, k
    (out / (k + ".py")).write_text(v, encoding="utf-8")
    print(k)
