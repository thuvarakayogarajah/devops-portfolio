def test_stats_on_empty_board(client):
    response = client.get("/api/tasks/stats")
    assert response.status_code == 200
    assert response.get_json() == {"total": 0, "done": 0, "open": 0}


def test_stats_with_mixed_tasks(client):
    ids = [
        client.post("/api/tasks", json={"title": title}).get_json()["id"]
        for title in ("Buy milk", "Write the report", "Call mom")
    ]
    client.put(f"/api/tasks/{ids[0]}", json={"done": True})

    body = client.get("/api/tasks/stats").get_json()
    assert body == {"total": 3, "done": 1, "open": 2}


def test_stats_when_all_tasks_done(client):
    for title in ("Buy milk", "Write the report"):
        task_id = client.post("/api/tasks", json={"title": title}).get_json()["id"]
        client.put(f"/api/tasks/{task_id}", json={"done": True})

    body = client.get("/api/tasks/stats").get_json()
    assert body["total"] == 2
    assert body["done"] == 2
    assert body["open"] == 0


def test_stats_reflects_deleted_tasks(client):
    task_id = client.post("/api/tasks", json={"title": "Temporary"}).get_json()["id"]
    client.delete(f"/api/tasks/{task_id}")

    body = client.get("/api/tasks/stats").get_json()
    assert body == {"total": 0, "done": 0, "open": 0}
