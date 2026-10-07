"""Build the inputs the functional scenarios need, into <run>/inputs/.

Columns always come from the template registry (`app.ingestion.registry`), never hand-typed, so a
registry change cannot leave a generated file silently wrong. Files in B_Inputs are copied, never
uploaded in place or modified.

Usage (from A_Codes/AB_backend, with the backend venv):
    python ../AF_e2e/functional/prepare_inputs.py <run folder>
"""
import csv
import shutil
import sys
import zipfile
from pathlib import Path

from app.ingestion.registry import get_template

#  …/A_Codes/AF_e2e/functional/prepare_inputs.py → parents[3] is the repository root
PROJECT = Path(__file__).resolve().parents[3]
SEED = PROJECT / "B_Inputs" / "AC_seed"
DEMO = PROJECT / "B_Inputs" / "AD_demo_files"


def _row(template_id: str, values: dict[str, str]) -> dict[str, str]:
    """A full row for a template: every registry column, blank unless given."""
    template = get_template(template_id)
    unknown = set(values) - {c.name for c in template.columns}
    if unknown:
        raise SystemExit(f"{template_id}: no such column(s): {sorted(unknown)}")
    return {c.name: values.get(c.name, "") for c in template.columns}


def _write_csv(path: Path, template_id: str, rows: list[dict[str, str]]) -> None:
    columns = [c.name for c in get_template(template_id).columns]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  {path.name}: {len(rows)} row(s), {len(columns)} registry columns")


def main(run: Path) -> None:
    inputs = run / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)

    # Copies of committed inputs — never uploaded from B_Inputs directly.
    shutil.copy2(DEMO / "T02_new_models_demo.xlsx", inputs / "T02_new_models_demo.xlsx")
    shutil.copy2(DEMO / "T04_findings_demo_errors.csv", inputs / "T04_findings_demo_errors.csv")
    evidence = inputs / "evidence"
    if evidence.exists():
        shutil.rmtree(evidence)
    shutil.copytree(SEED / "documents", evidence)
    print(f"  evidence/: {sum(1 for p in evidence.rglob('*') if p.is_file())} seed PDFs copied")

    # FS-06: a T02 row whose validator is also the owner (INV-03).
    _write_csv(inputs / "T02_sod_breach.csv", "T02", [_row("T02", {
        "model_id": "M-0902", "model_name": "FS-06 SoD breach", "model_type": "Credit Risk",
        "model_subtype": "PD", "purpose": "Validator equals owner; must be rejected.",
        "business_line": "Business Banking", "owner_id": "U-003", "developer_id": "U-021",
        "validator_id": "U-003", "lifecycle_phase": "Validation", "version": "v1.0",
        "q_materiality": "2", "q_complexity": "2", "q_reliance": "2", "q_regulatory_use": "2",
    })])

    # FS-23: U-040 re-imported with MRC Member removed, keeping Executive.
    users = inputs / "T01_role_removed.csv"
    _write_csv(users, "T01", [_row("T01", {
        "user_id": "U-040", "full_name": "Robert Diaz", "email": "r.diaz@demo-bank.example",
        "role": "Executive", "business_line": "Enterprise Risk", "active": "Y",
    })])

    # FS-15 / FS-17: small valid PDFs, distinct bytes so duplicate detection is exercised.
    def pdf(text: str) -> bytes:
        body = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET"
        objs = [
            "1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj",
            "2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj",
            "3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]"
            "/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj",
            "4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj",
            f"5 0 obj<</Length {len(body)}>>stream\n{body}\nendstream endobj",
        ]
        out = "%PDF-1.4\n"
        offsets = []
        for o in objs:
            offsets.append(len(out))
            out += o + "\n"
        start = len(out)
        out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n"
        out += "".join(f"{off:010d} 00000 n \n" for off in offsets)
        out += (f"trailer<</Size {len(objs) + 1}/Root 1 0 R>>\nstartxref\n{start}\n%%EOF\n")
        return out.encode("latin-1")

    for name, text in (("ft_tor_v1.pdf", "FS-15 Terms of Reference v1"),
                       ("ft_tor_v2.pdf", "FS-15 Terms of Reference v2 revised"),
                       ("ft_completeness.pdf", "FS-17 evidence closing a completeness gap")):
        (inputs / name).write_bytes(pdf(text))
        print(f"  {name}: {len(pdf(text))} bytes")

    # FS-16: a ZIP with a T17 manifest, nested folders and one deliberately broken PDF (DOC-10).
    manifest = inputs / "ft_manifest.csv"
    _write_csv(manifest, "T17", [_row("T17", {
        "relative_path": "Model_Governance/Credit_Risk/M-0012/Governance/FT_MDD.pdf",
        "model_id": "M-0012", "document_type": "Model Development Document", "version": "1.0",
        "title": "FS-16 manifest-classified MDD",
    })])
    zip_path = inputs / "ft_evidence.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("Model_Governance/Credit_Risk/M-0012/Governance/FT_MDD.pdf", pdf("FS-16 MDD"))
        z.writestr("Model_Governance/Credit_Risk/M-0012/Validation/FT_Validation_Report.pdf",
                   pdf("FS-16 Validation Report 2026"))
        z.writestr("Model_Governance/Credit_Risk/M-0012/Governance/FT_broken.pdf", b"not a pdf at all")
        z.writestr("manifest.csv", manifest.read_bytes())
    print(f"  ft_evidence.zip: 4 entries (3 PDFs, 1 deliberately broken, plus a T17 manifest)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    main(Path(sys.argv[1]))
