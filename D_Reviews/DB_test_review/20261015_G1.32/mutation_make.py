"""G1.32 mutants of app/services/reset_service.py. Loaded in memory by mutation_plugin.py; the
product file is never edited. Usage: python mutation_make.py <reset_service.py> <outdir>"""
import sys, pathlib
src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
out = pathlib.Path(sys.argv[2])

def rep(s, old, new):
    assert old in s, old
    return s.replace(old, new, 1)

ACQ = ("    holder = uuid.uuid4().hex\n"
       "    if not acquire_reset_lock(db, holder, principal.user_id if principal else None):\n")
PERM = ("    if principal and not has_permission(principal.role, Permission.POLICY_EDIT):\n"
        "        raise ForbiddenError(\"Only an Admin can reset the application data.\")\n")
HANDOVER = "    runner.submit(_store_evidence_then_seed_report, session_factory, staged, batch_id, holder)\n"
BASE_REL = ("                release_reset_lock(session_factory, holder, \"Failed\",\n"
            "                                   f\"{stage} failed: {len(missing)} required policy setting(s) missing\")\n")
START_REL = "        release_reset_lock(session_factory, holder, \"Failed\", _failure(stage, exc))\n        raise\n    # From here"
REGEN = ("        directory = directory or get_settings().seed_dir\n"
         "        if get_settings().regenerate_seed_on_reset:\n            regenerate_seed(directory)\n")
m = {}
# A: release the lock at the handover instead of at the end of the job (the CR-53 window class)
m["A_release_at_handover"] = rep(src, HANDOVER,
    "    release_reset_lock(session_factory, holder, \"Completed\")\n" + HANDOVER)
# B: the missing-baseline path returns without releasing
m["B_baseline_path_no_release"] = rep(src, BASE_REL, "")
# C: start_reset's own failure path does not release
m["C_start_reset_failure_no_release"] = rep(src, START_REL, "        raise\n    # From here")
# D: non-atomic read-then-write claim (passes sequentially, races concurrently)
m["D_read_then_write_claim"] = rep(src,
    "    _ensure_lock_row(db)\n    claimed = db.execute(",
    "    _ensure_lock_row(db)\n    if _lock_row(db).holder is not None:\n        db.commit()\n        return False\n"
    "    claimed = db.execute(")
m["D_read_then_write_claim"] = rep(m["D_read_then_write_claim"],
    ".where(ResetLock.lock_id == LOCK_ID, ResetLock.holder.is_(None))\n        .values(holder=holder",
    ".where(ResetLock.lock_id == LOCK_ID)\n        .values(holder=holder")
# E: anyone can release
m["E_release_ignores_holder"] = rep(src,
    "                       .where(ResetLock.lock_id == LOCK_ID, ResetLock.holder == holder)\n                       .values(holder=None",
    "                       .where(ResetLock.lock_id == LOCK_ID)\n                       .values(holder=None")
# F: set_reset_stage ignores holder (a stale job can overwrite a running reset's stage/batch)
m["F_stage_ignores_holder"] = rep(src,
    "                   .where(ResetLock.lock_id == LOCK_ID, ResetLock.holder == holder)\n                   .values(**values)",
    "                   .where(ResetLock.lock_id == LOCK_ID)\n                   .values(**values)")
# G: a write after the handover (FT-04)
m["G_write_after_handover"] = rep(src, HANDOVER,
    HANDOVER + "    set_reset_stage(session_factory, holder, \"Handed over\")\n")
# H: regenerate the seed files before the claim (GEN-04 "nothing happened" on refusal)
m["H_regenerate_before_claim"] = rep(rep(src, REGEN, ""), ACQ,
    "    directory = directory or get_settings().seed_dir\n"
    "    if get_settings().regenerate_seed_on_reset:\n        regenerate_seed(directory)\n" + ACQ)
# I: claim before the permission check
m["I_claim_before_permission"] = rep(rep(src, PERM, ""), "    holder = uuid.uuid4().hex\n"
    "    if not acquire_reset_lock", "    holder = uuid.uuid4().hex\n"
    "    if not acquire_reset_lock")
m["I_claim_before_permission"] = rep(m["I_claim_before_permission"],
    "    stage = \"Seed preparation\"\n    try:\n",
    "    stage = \"Seed preparation\"\n" + PERM + "    try:\n")
# J: _reset_job's failure path does not release (only marks the batch)
m["J_job_failure_no_release"] = rep(src,
    "        import_service.record_job_failure(session_factory, batch_id, stage, exc)\n        release_reset_lock(session_factory, holder, \"Failed\", _failure(stage, exc))\n",
    "        import_service.record_job_failure(session_factory, batch_id, stage, exc)\n")
# K: the release in the last job moved out of `finally` into the success path only
m["K_no_finally"] = rep(src,
    "        report_service.seed_previous_report(session_factory)\n    except BaseException",
    "        report_service.seed_previous_report(session_factory)\n        release_reset_lock(session_factory, holder, outcome, reason)\n    except BaseException")
m["K_no_finally"] = rep(m["K_no_finally"], "    finally:\n        release_reset_lock(session_factory, holder, outcome, reason)\n", "")
# L: recovery does nothing
m["L_recovery_noop"] = rep(src, "    lock = reset_in_progress(db)\n    if lock is None:\n        return False\n",
    "    return False\n    lock = None\n")
for k, v in m.items():
    assert v != src, k
    (out / (k + ".py")).write_text(v, encoding="utf-8")
    print(k)
