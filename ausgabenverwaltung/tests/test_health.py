def test_health_is_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "version": "test"}


def test_ready_with_in_memory_repository(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ready"}


def test_metrics_are_exposed(client):
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"expenses_info" in response.data


def test_ready_reports_unavailable_database(app, client, monkeypatch):
    monkeypatch.setattr(app.extensions["repository"], "healthy", lambda: False)
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.get_json() == {"status": "unavailable"}
