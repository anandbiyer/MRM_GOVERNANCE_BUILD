"""Reviewer probe (not in repo): PLT-01 over the report endpoints, which the sweep omits."""
import re

from app.services import report_service
from tests.conftest import ADMIN, MRC, login

NAIVE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?$")


def _walk(node, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from _walk(v, f"{path}.{k}")
    elif isinstance(node, list):
        for n, v in enumerate(node):
            yield from _walk(v, f"{path}[{n}]")
    elif isinstance(node, str) and NAIVE.match(node):
        yield path, node


def test_probe_report_timestamps(loaded_client, loaded_session):
    report_service.seed_previous_report(loaded_session)
    h = login(loaded_client, *MRC)
    gen = loaded_client.post("/api/reports/model-risk", headers=h).json()
    naive = list(_walk(gen, "POST"))
    rid = gen["report_id"]
    for ep in ("/api/reports/model-risk", f"/api/reports/model-risk/{rid}", "/api/admin/reset/status"):
        naive += list(_walk(loaded_client.get(ep, headers=login(loaded_client, *ADMIN)).json(), ep))
    print("NAIVE:", naive)
    assert naive == []
