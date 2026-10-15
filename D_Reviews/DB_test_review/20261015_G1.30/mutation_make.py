import sys, pathlib
src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
SUB = "    runner.submit(_store_evidence_then_seed_report, session_factory, staged, batch_id, loaded_status)\n"
RESTORE_PRE = ("    with session_factory() as db:\n        batch = db.get(ImportBatch, batch_id)\n"
               "        batch.status = loaded_status\n        db.commit()\n")
FINAL = ("    with session_factory() as db:\n        batch = db.get(ImportBatch, seed_batch_id)\n"
         "        batch.status = loaded_status\n        db.commit()\n")
assert SUB in src and FINAL in src
TRY = ("    stage = \"Seed evidence analysis\"\n    try:\n        if documents_batch_id:\n"
       "            doc_batch.analyse_job(session_factory, documents_batch_id, None)\n"
       "        stage = \"Seeded example report\"\n        report_service.seed_previous_report(session_factory)\n"
       "    except BaseException as exc:\n        import_service.record_job_failure(session_factory, seed_batch_id, stage, exc)\n        raise\n")
assert TRY in src
m = {}
m["m1_restore_before_submit"] = src.replace(SUB, RESTORE_PRE + SUB)
m["m2_drop_final_restore"] = src.replace(FINAL, "    pass\n")
m["m3_drop_failure_wrapper"] = src.replace(TRY, "    if documents_batch_id:\n        doc_batch.analyse_job(session_factory, documents_batch_id, None)\n    report_service.seed_previous_report(session_factory)\n")
m["m4_restore_after_submit"] = src.replace(FINAL, "    pass\n").replace(SUB, SUB + RESTORE_PRE)
m["m5_wrap_report_only"] = src.replace(TRY, "    if documents_batch_id:\n        doc_batch.analyse_job(session_factory, documents_batch_id, None)\n    stage = \"Seeded example report\"\n    try:\n        report_service.seed_previous_report(session_factory)\n    except BaseException as exc:\n        import_service.record_job_failure(session_factory, seed_batch_id, stage, exc)\n        raise\n")
m["m6_stage_label_frozen"] = src.replace("        stage = \"Seeded example report\"\n", "")
m["m7_restore_between_analysis_and_report"] = src.replace(FINAL, "    pass\n").replace(
    "        stage = \"Seeded example report\"\n",
    "        stage = \"Seeded example report\"\n        with session_factory() as db:\n            db.get(ImportBatch, seed_batch_id).status = loaded_status\n            db.commit()\n")
for k, v in m.items():
    assert v != src, k
    pathlib.Path(k + ".py").write_text(v, encoding="utf-8")
    print(k)
