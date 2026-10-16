"""Migration conventions the schema drift guard cannot check (plan G1.28, review finding CR-42).

`tests/test_postgres.py::test_migrations_match_orm_models` is the drift guard, and it is strong — but
it uses alembic's `compare_metadata`, which compares foreign keys by their **columns and referents**,
not by their names. So a migration that leaves a constraint unnamed passes it, and the checkpoint
evidence that covered `0007` ("PostgreSQL 4/4 green") could not have caught CR-42.

An unnamed constraint gets whatever name the database invents. The failure mode is specific and this
repository has already paid for it once: a later migration that drops the constraint by its
conventional name succeeds against a SQLite `create_all` schema and fails against a migrated
PostgreSQL one — the same shape as the `validation.report_document_id` drift that went unnoticed for
two phases because no PostgreSQL run existed to find it.

These are source checks rather than database checks on purpose: they need no infrastructure, so they
run in the ordinary `backend` CI job rather than only in `backend-postgres`, which self-skips.
"""
import re
from pathlib import Path

import pytest

VERSIONS = Path(__file__).resolve().parents[1] / "migrations" / "versions"
MIGRATIONS = sorted(p for p in VERSIONS.glob("*.py") if not p.name.startswith("__"))


def test_there_are_migrations_to_check():
    """Guard against the sweep going vacuous if the folder ever moves."""
    assert len(MIGRATIONS) >= 7, f"expected the migration chain, found {[p.name for p in MIGRATIONS]}"


@pytest.mark.parametrize("path", MIGRATIONS, ids=lambda p: p.stem)
def test_every_foreign_key_in_a_migration_is_named(path):
    """A migration declares foreign keys as named `ForeignKeyConstraint`s, never inline.

    `0002_governance_core.py` has a `_fk()` helper that exists purely to apply the naming convention,
    so the convention predates this test; `0007` was the one file that departed from it.
    """
    source = path.read_text(encoding="utf-8")

    inline = re.findall(r"sa\.ForeignKey\(", source)
    assert not inline, (
        f"{path.name}: {len(inline)} inline sa.ForeignKey(...) — an inline foreign key cannot carry a "
        f"name, and alembic's drift guard compares foreign keys by columns rather than by name, so "
        f"nothing else will notice. Use sa.ForeignKeyConstraint([col], [ref], name=\"fk_…\").")

    for constraint in re.findall(r"sa\.ForeignKeyConstraint\((?:[^()]|\([^()]*\))*\)", source):
        assert "name=" in constraint, (
            f"{path.name}: a ForeignKeyConstraint without name= — {constraint[:90]}…")


def test_the_naming_convention_is_followed_consistently():
    """Every named constraint reads `fk_<table>_<column>_<referenced table>`.

    Checked across the whole chain rather than per file, so a new migration inventing its own style
    fails here instead of being discovered by a reviewer.
    """
    bad = []
    for path in MIGRATIONS:
        for name in re.findall(r'name="(fk_[^"]+)"', path.read_text(encoding="utf-8")):
            if not re.fullmatch(r"fk_[a-z0-9_]+", name):
                bad.append(f"{path.name}: {name}")
    assert not bad, f"foreign key names outside the convention: {bad}"
