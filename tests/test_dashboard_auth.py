from job_automata.presentation.web import app as dashboard


def test_x_forwarded_for_does_not_bypass_local_only_auth(monkeypatch):
    monkeypatch.setattr(dashboard, "DASHBOARD_TOKEN", None)

    client = dashboard.app.test_client()
    response = client.get(
        "/api/stats",
        headers={"X-Forwarded-For": "127.0.0.1"},
        environ_overrides={"REMOTE_ADDR": "203.0.113.10"},
    )

    assert response.status_code == 403


def test_dashboard_token_requires_header_not_query_param(monkeypatch):
    monkeypatch.setattr(dashboard, "DASHBOARD_TOKEN", "secret-token")

    client = dashboard.app.test_client()

    query_response = client.get(
        "/api/stats",
        query_string={"token": "secret-token"},
        environ_overrides={"REMOTE_ADDR": "203.0.113.10"},
    )
    header_response = client.get(
        "/api/stats",
        headers={"X-Dashboard-Token": "secret-token"},
        environ_overrides={"REMOTE_ADDR": "203.0.113.10"},
    )

    assert query_response.status_code == 401
    assert header_response.status_code == 200
