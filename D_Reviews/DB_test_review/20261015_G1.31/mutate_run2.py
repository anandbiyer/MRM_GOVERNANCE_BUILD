import subprocess, sys, pathlib
root = pathlib.Path(sys.argv[1]); py = sys.argv[2]
LABEL = 'flow.append(Paragraph(f"<b>{report[\'seeded_label\']}</b>", styles["Lede"]))'
RECON = 'f"Figures reconciled with the Command Center at generation, {generated}."'
M = {
 "M2_real_drop_reconciliation_line": [("app/reports/pdf.py", RECON, '""')],
 "M10_label_in_metadata_only": [("app/reports/pdf.py", LABEL,
     'doc.subject = report["seeded_label"]; doc.keywords = report["seeded_label"]')],
 "M11_reconciliation_only_on_seeded": [("app/reports/pdf.py", RECON,
     '(f"Figures reconciled with the Command Center at generation, {generated}." if report.get("is_seeded") else "")')],
}
for name in sys.argv[3:] or list(M):
    saved = {}
    for rel, old, new in M[name]:
        p = root / rel; src = saved.setdefault(p, p.read_text(encoding="utf-8"))
        cur = p.read_text(encoding="utf-8")
        assert cur.count(old) == 1, (name, cur.count(old))
        p.write_text(cur.replace(old, new), encoding="utf-8")
    try:
        r = subprocess.run([py, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_reports.py", "-k", "d14 or pdf"],
                           cwd=root, capture_output=True, text=True)
        tail = [l for l in r.stdout.splitlines() if l.startswith("FAILED") or " passed" in l or " failed" in l or "Error" in l]
        print(f"== {name}: {'KILLED' if r.returncode else 'SURVIVED'}"); print("\n".join(tail[-12:]), flush=True)
    finally:
        for p, src in saved.items():
            p.write_text(src, encoding="utf-8")
