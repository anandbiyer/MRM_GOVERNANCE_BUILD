"""Out-of-repo mutation plugin: MUT=<name> re-executes a patched copy of a module's source in place."""
import importlib
import inspect
import os

RS = "app.services.report_service"
RE = "app.services.reset_service"
PDF = "app.reports.pdf"
API = "app.api.admin"

M = {
    # --- REG-16 hash
    "R01_hash_constant": [(RS, 'return hashlib.sha256(canonical.encode("utf-8")).hexdigest()', 'return "0"*64')],
    "R02_hash_includes_changes_since": [(RS, 'if k != "changes_since"}', 'if True}')],
    "R03_cr52_decisions_in_approvals": [(RS, '"approvals": _approvals(rows),',
                                         '"approvals": {**_approvals(rows), "decisions_since_previous": decisions},')],
    "R04_s13_since_count_in_findings": [(RS, '"findings": _findings(db, summary, policy),',
                                         '"findings": {**_findings(db, summary, policy), "n_since": len(decisions)},')],
    "R05_hash_wallclock": [(RS, 'content = {k: v for k, v in sections.items() if k != "changes_since"}',
                            'content = {**{k: v for k, v in sections.items() if k != "changes_since"}, "t": __import__("time").time()}')],
    # --- REG-15 figures
    "R06_overdue_not_tier_ordered": [(RS, 'overdue.sort(key=lambda r: (TIER_ORDER.index(r["tier"]) if r["tier"] in TIER_ORDER else len(TIER_ORDER),',
                                      'overdue.sort(key=lambda r: (0,')],
    "R07_critical_is_lowest_severity": [(RS, 'for f in overdue_rows if f.severity == severities[0]),',
                                         'for f in overdue_rows if f.severity == severities[-1]),')],
    "R08_calendar_date": [(RS, '    on = today()\n    previous = latest(db)',
                           '    on = __import__("datetime").date.today()\n    previous = latest(db)')],
    "R09_stage_drops_a_column": [(RS, '"by_stage": _dist(summary["distributions"]["stage"]),',
                                  '"by_stage": _dist(summary["distributions"]["stage"])[:-1],')],
    "R10_overdue_findings_include_due_today": [(RS, 'f.due_date is not None and f.due_date < on',
                                                'f.due_date is not None and f.due_date <= on')],
    "R11_lowest_limit_constant": [(RS, 'limit = policy.int("report_lowest_scoring_limit")', 'limit = 10')],
    "R12_weakest_is_strongest": [(RS, 'weakest = min(applicable,', 'weakest = max(applicable,')],
    # --- REG-16 permission / audit
    "R13_service_no_permission_check": [(RS, 'if principal and not has_permission(principal.role, Permission.REPORT_GENERATE):', 'if False:')],
    "R14_no_audit": [(RS, '    audit.record(db, principal, action="generate", entity="model_risk_report", entity_id=report_id,\n                 after=',
                      '    (lambda *a, **k: None)(db, principal, action="generate", entity="model_risk_report", entity_id=report_id,\n                 after=')],
    "R15_audit_twice": [(RS, '    db.commit()\n    db.refresh(report)',
                         '    audit.record(db, principal, action="generate", entity="model_risk_report", entity_id=report_id, reason="x")\n    db.commit()\n    db.refresh(report)')],
    "R16_report_committed_before_audit": [(RS, '    db.add(report)\n    audit.record(db, principal, action="generate"',
                                           '    db.add(report)\n    db.commit()\n    audit.record(db, principal, action="generate"')],
    # --- REG-17 list / changes / reopen
    "R17_list_oldest_first": [(RS, 'return list(db.scalars(select(ModelRiskReport).order_by(ModelRiskReport.generated_at.desc(),\n                                                            ModelRiskReport.report_id.desc())))',
                               'return list(db.scalars(select(ModelRiskReport).order_by(ModelRiskReport.generated_at.asc(),\n                                                            ModelRiskReport.report_id.asc())))')],
    "R18_list_by_id_only": [(RS, 'return list(db.scalars(select(ModelRiskReport).order_by(ModelRiskReport.generated_at.desc(),\n                                                            ModelRiskReport.report_id.desc())))',
                             'return list(db.scalars(select(ModelRiskReport).order_by(ModelRiskReport.report_id.desc())))')],
    "R19_closed_empty": [(RS, '"findings_closed": [{"finding_id": f} for f in closed],', '"findings_closed": [],')],
    "R20_decisions_all_approvals": [(RS, 'for a in db.scalars(select(Approval)) if a.approval_id not in seen_before),',
                                     'for a in db.scalars(select(Approval))),')],
    "R21_tr61_no_legacy_fallback": [(RS, 'if "decisions_since_previous" in approvals and "decisions_recorded" not in changes:', 'if False:')],
    "R22_reopen_alters_content": [(RS, '    content = json.loads(get_store().get(report.storage_path).decode("utf-8"))\n    approvals,',
                                   '    content = json.loads(get_store().get(report.storage_path).decode("utf-8"))\n    content["inventory"]["total"] = -1\n    approvals,')],
    "R23_previous_id_wrong": [(RS, '"previous_report_id": previous.report_id,\n        "previous_generated_at"',
                               '"previous_report_id": None,\n        "previous_generated_at"')],
    # --- D14 / S11 / S12 seeded example
    "R24_d14_figures_as_of_is_business_date": [(RS, 'figures_as_of=today()))', 'figures_as_of=on))')],
    "R25_is_seeded_false": [(RS, 'is_seeded=True,', 'is_seeded=False,')],
    "R26_pdf_no_seeded_label": [(PDF, 'if report.get("seeded_label"):', 'if False:')],
    "R27_pdf_reconciliation_no_timestamp": [(PDF, 'f"Figures reconciled with the Command Center at generation, {generated}."',
                                             'f"Figures reconciled with the Command Center at generation."')],
    "R28_pdf_reconciliation_gone": [(PDF, 'f"Figures reconciled with the Command Center at generation, {generated}."', 'f""')],
    "R29_seed_shapes_a_figure": [(RS, '        on = today() - timedelta(days=SEED_REPORT_AGE_DAYS)\n',
                                  '        content["inventory"]["total"] = 0\n        on = today() - timedelta(days=SEED_REPORT_AGE_DAYS)\n')],
    # --- GEN-04 / GEN-05 at HEAD
    "G01_409_not_naming_batch": [(RE, "f\"A reset is already running: batch {lock.batch_id or '(being created)'}, \"",
                                  'f"A reset is already running: "')],
    "G02_regenerate_before_claim": [(RE, '    running = reset_in_progress(db)\n    if running is not None:',
                                     '    get_settings().regenerate_seed_on_reset and regenerate_seed(directory or get_settings().seed_dir)\n    running = reset_in_progress(db)\n    if running is not None:')],
    "G03_no_read_first": [(RE, '    running = reset_in_progress(db)\n    if running is not None:\n        raise _already_running(running)', '    pass')],
    "G04_locked_claim_is_500": [(RE, '        if "locked" not in str(exc).lower() and "busy" not in str(exc).lower():\n            raise', '        raise')],
    "G05_no_release_at_end": [(RE, '    finally:\n        release_reset_lock(session_factory, holder, outcome, reason)', '    finally:\n        pass')],
    "G06_release_before_report": [(RE, '        stage = "Seeded example report"\n        set_reset_stage(session_factory, holder, stage)\n',
                                   '        stage = "Seeded example report"\n        release_reset_lock(session_factory, holder, "Completed")\n')],
    "G07_status_never_in_progress": [(API, 'running = lock.holder is not None', 'running = False')],
    "G08_permission_after_lock": [(RE, '    if principal and not has_permission(principal.role, Permission.POLICY_EDIT):\n        raise ForbiddenError("Only an Admin can reset the application data.")\n', ''),
                                  (RE, '    holder = uuid.uuid4().hex\n',
                                   '    holder = uuid.uuid4().hex\n    if principal and not has_permission(principal.role, Permission.POLICY_EDIT):\n        raise ForbiddenError("Only an Admin can reset the application data.")\n')],
    "G09_no_release_on_job_failure": [(RE, '        import_service.record_job_failure(session_factory, batch_id, stage, exc)\n        release_reset_lock(session_factory, holder, "Failed", _failure(stage, exc))\n        raise',
                                       '        import_service.record_job_failure(session_factory, batch_id, stage, exc)\n        raise')],
    "G10_failure_not_marked_on_batch": [(RE, '        import_service.record_job_failure(session_factory, seed_batch_id, stage, exc)\n        raise', '        raise')],
    "G11_extra_handover_before_last_write": [(RE, '        # The last write before the handover (FT-04): the job continues from here.\n',
                                              '        runner.submit(lambda *a: None)\n')],
}


def pytest_configure(config):
    name = os.environ.get("MUT")
    if not name:
        return
    groups: dict[str, list] = {}
    for mod, old, new in M[name]:
        groups.setdefault(mod, []).append((old, new))
    for mod, subs in groups.items():
        m = importlib.import_module(mod)
        src = inspect.getsource(m)
        for old, new in subs:
            assert old in src, f"{name}: pattern not found in {mod}: {old[:70]!r}"
            src = src.replace(old, new, 1)
        exec(compile(src, m.__file__, "exec"), m.__dict__)
    print(f"\n[mut_g1x] applied {name}")
