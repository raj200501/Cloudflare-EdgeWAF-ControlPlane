from fastapi.testclient import TestClient

from apps.edge.main import app

client = TestClient(app)


def test_policy_crud_and_deployments():
    created = client.post(
        "/api/policies/waf",
        json={
            "field": "query",
            "operator": "contains",
            "pattern": "union select",
            "reason": "sqli",
            "priority": 1,
        },
    )
    assert created.status_code == 200
    policy_id = created.json()["id"]

    listed = client.get("/api/policies/waf?page=1&page_size=10")
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1

    compiled = client.post("/api/deployments/compile")
    assert compiled.status_code == 200
    snapshot_id = compiled.json()["id"]

    activated = client.post(f"/api/deployments/activate/{snapshot_id}")
    assert activated.status_code == 200

    active = client.get("/api/deployments/active")
    assert active.status_code == 200

    deleted = client.delete(f"/api/policies/waf/{policy_id}")
    assert deleted.status_code == 204


def test_event_emission_and_pull_api():
    response = client.get("/home", headers={"x-forwarded-for": "1.2.3.4"})
    assert response.status_code in {200, 403, 429, 451}
    recent = client.get("/api/events?limit=5")
    assert recent.status_code == 200
    assert isinstance(recent.json()["items"], list)


def test_websocket_receives_events():
    with client.websocket_connect("/ws/events") as ws:
        client.get("/healthz")
        client.get("/dashboard", headers={"x-forwarded-for": "2.2.2.2"})
        payload = ws.receive_json()
        assert "decision" in payload
        assert "timings" in payload
