"""Seed generator tests (A_Codes/AD_seed/generate_seed.py).

Covers the evidence-tree sync, which used to `shutil.rmtree` the committed tree before rewriting it.
rmtree deletes as it goes, so a PermissionError part way through — routine in a OneDrive-synced working
copy — left the tree partly destroyed and the rewrite never ran. Four committed PDFs were lost that
way once (recovered from git). These tests pin the ordering that prevents it.

Also covers `_unchanged`, which decides whether a template needs rewriting at all, so that a
regeneration dirties only the files whose content actually changed (G0.15).
"""
import importlib.util
import io
import re
import zipfile
from pathlib import Path

import pytest

from app.ingestion import fileio
from app.ingestion.registry import get_template

GENERATOR = Path(__file__).resolve().parents[2] / "AD_seed" / "generate_seed.py"


@pytest.fixture(scope="module")
def seed_module():
    spec = importlib.util.spec_from_file_location("generate_seed_sync", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _tree(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_sync_writes_new_files_and_prunes_obsolete_ones(seed_module, tmp_path):
    docs = tmp_path / "documents"
    (docs / "M-0001").mkdir(parents=True)
    (docs / "M-0001" / "stale.pdf").write_bytes(b"obsolete")
    (docs / "M-0001" / "keep.pdf").write_bytes(b"same")

    counts = seed_module.sync_documents(docs, [
        ("M-0001/keep.pdf", b"same"),          # byte-identical: must not be rewritten
        ("M-0001/new.pdf", b"fresh"),          # added
        ("M-0002/other.pdf", b"other"),        # new directory
    ])

    assert _tree(docs) == {"M-0001/keep.pdf": b"same", "M-0001/new.pdf": b"fresh",
                           "M-0002/other.pdf": b"other"}
    assert counts == {"written": 2, "unchanged": 1, "removed": 1, "locked": 0}


def test_sync_leaves_an_identical_file_untouched(seed_module, tmp_path):
    """The generator is deterministic, so a re-run should not rewrite files that have not changed.

    Rewriting them all churned git and touched every file in a synced folder for no reason.
    """
    docs = tmp_path / "documents"
    docs.mkdir()
    target = docs / "same.pdf"
    target.write_bytes(b"identical")
    before = target.stat().st_mtime_ns

    counts = seed_module.sync_documents(docs, [("same.pdf", b"identical")])

    assert counts["unchanged"] == 1 and counts["written"] == 0
    assert target.stat().st_mtime_ns == before, "an unchanged file must not be rewritten"


def test_sync_removes_directories_left_empty(seed_module, tmp_path):
    docs = tmp_path / "documents"
    (docs / "M-0001" / "Monitoring" / "2026_Q2").mkdir(parents=True)
    (docs / "M-0001" / "Monitoring" / "2026_Q2" / "report.pdf").write_bytes(b"x")

    seed_module.sync_documents(docs, [("M-0002/keep.pdf", b"y")])

    assert not (docs / "M-0001").exists(), "emptied directories should not be left behind"
    assert (docs / "M-0002" / "keep.pdf").read_bytes() == b"y"


def test_sync_never_deletes_before_the_new_content_is_written(seed_module, tmp_path, monkeypatch):
    """The regression: a failure while writing must leave the existing tree intact.

    `rmtree` first meant a mid-run failure destroyed committed files and wrote nothing. Writing
    first means the worst case is a superset of old and new, which a re-run repairs.
    """
    docs = tmp_path / "documents"
    docs.mkdir()
    (docs / "committed.pdf").write_bytes(b"precious")

    real_write_bytes = Path.write_bytes

    def explode(self, data):
        if self.name == "second.pdf":
            raise PermissionError("locked by the sync client")
        return real_write_bytes(self, data)

    monkeypatch.setattr(Path, "write_bytes", explode)
    with pytest.raises(PermissionError):
        seed_module.sync_documents(docs, [("first.pdf", b"a"), ("second.pdf", b"b")])
    monkeypatch.undo()

    # The pre-existing file survives: nothing was pruned, because pruning never ran.
    assert (docs / "committed.pdf").read_bytes() == b"precious"


def test_sync_reports_a_locked_obsolete_file_instead_of_failing(seed_module, tmp_path, monkeypatch):
    """A file that cannot be pruned is counted, not raised: the seed is already correct by then."""
    docs = tmp_path / "documents"
    docs.mkdir()
    (docs / "obsolete.pdf").write_bytes(b"old")

    real_unlink = Path.unlink

    def refuse(self, *args, **kwargs):
        if self.name == "obsolete.pdf":
            raise PermissionError("locked by the sync client")
        return real_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", refuse)
    counts = seed_module.sync_documents(docs, [("wanted.pdf", b"new")])
    monkeypatch.undo()

    assert counts["locked"] == 1 and counts["removed"] == 0
    assert (docs / "wanted.pdf").read_bytes() == b"new", "the seed is still complete"
    assert (docs / "obsolete.pdf").exists(), "the leftover remains, to be tidied on a later run"


# --- _unchanged: telling a real template change from a rewrite (G0.15) ---------------------------
#
# Writing a workbook twice never produces identical bytes: the zip stores a modification time per
# member, and openpyxl stamps docProps/core.xml with the time of the save. The generator used to
# rewrite every template on every run because of it, so `git status` could not show what a
# regeneration had actually changed, and an unintended file could ride along with an intended one.


def _restamp(data: bytes, when: tuple[int, int, int, int, int, int], modified: bytes) -> bytes:
    """The same workbook content, written at a different time — the churn, reproduced exactly."""
    with zipfile.ZipFile(io.BytesIO(data)) as src:
        members = [(i.filename, src.read(i.filename)) for i in src.infolist()]
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as dst:
        for name, payload in members:
            if name == "docProps/core.xml":
                payload = re.sub(rb"<dcterms:modified[^>]*>[^<]*</dcterms:modified>", modified, payload)
            dst.writestr(zipfile.ZipInfo(name, date_time=when), payload)
    return out.getvalue()


ROWS = [{"user_id": "U-001", "full_name": "A B", "email": "a@b.c", "role": "Admin",
         "business_line": "X", "active": "Y"}]
ALLOWED = {"role": ["Admin", "Auditor"]}


def _workbook(rows=None, allowed=None) -> bytes:
    return fileio.write_workbook(get_template("T01"), rows or ROWS, allowed or ALLOWED)


def test_unchanged_ignores_the_time_a_workbook_was_written(seed_module, tmp_path):
    """The whole point: same content, later save, no rewrite."""
    path = tmp_path / "T01_users.xlsx"
    path.write_bytes(_restamp(_workbook(), (2020, 1, 1, 0, 0, 0),
                              b"<dcterms:modified>2020-01-01T00:00:00Z</dcterms:modified>"))
    fresh = _workbook()

    assert path.read_bytes() != fresh, "a byte comparison would see a difference, which is the bug"
    assert seed_module._unchanged(path, fresh) is True


def test_unchanged_detects_a_changed_cell(seed_module, tmp_path):
    path = tmp_path / "T01_users.xlsx"
    path.write_bytes(_workbook())
    changed = _workbook(rows=[dict(ROWS[0], full_name="Someone Else")])

    assert seed_module._unchanged(path, changed) is False


def test_unchanged_detects_a_changed_instructions_sheet(seed_module, tmp_path):
    """Allowed values come from policy and live only in the instructions sheet.

    A comparison of the data rows alone would pass here, and the committed template would keep
    offering a dropdown the policy no longer allows.
    """
    path = tmp_path / "T01_users.xlsx"
    path.write_bytes(_workbook())
    repolicied = _workbook(allowed={"role": ["Admin", "Auditor", "Executive"]})

    assert seed_module._unchanged(path, repolicied) is False


def test_unchanged_detects_an_added_row(seed_module, tmp_path):
    path = tmp_path / "T01_users.xlsx"
    path.write_bytes(_workbook())
    extra = _workbook(rows=ROWS + [dict(ROWS[0], user_id="U-002")])

    assert seed_module._unchanged(path, extra) is False


def test_unchanged_compares_csv_byte_for_byte(seed_module, tmp_path):
    """CSV output is already deterministic, so there is nothing to normalise and nothing to forgive."""
    path = tmp_path / "T04_findings.csv"
    path.write_bytes(b"a,b\n1,2\n")

    assert seed_module._unchanged(path, b"a,b\n1,2\n") is True
    assert seed_module._unchanged(path, b"a,b\n1,3\n") is False


def test_unchanged_is_false_when_there_is_no_file_yet(seed_module, tmp_path):
    assert seed_module._unchanged(tmp_path / "absent.xlsx", _workbook()) is False


def test_unchanged_is_false_when_the_existing_file_is_not_a_workbook(seed_module, tmp_path):
    """A corrupt or truncated file is replaced rather than trusted."""
    path = tmp_path / "T01_users.xlsx"
    path.write_bytes(b"not a workbook at all")

    assert seed_module._unchanged(path, _workbook()) is False
