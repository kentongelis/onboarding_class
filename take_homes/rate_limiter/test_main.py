from fastapi.testclient import TestClient

import main

client = TestClient(main.app)

def setup_function():
    main.requests_by_user.clear()


def test_blocks_after_limit():
    for _ in range(main.LIMIT):
        assert client.get("/hello", headers={"X-User-ID": "alice"}).status_code == 200
    assert client.get("/hello", headers={"X-User-ID": "alice"}).status_code == 429


def test_users_are_separate():
    for _ in range(main.LIMIT):
        client.get("/hello", headers={"X-User-ID": "alice"})
    assert client.get("/hello", headers={"X-User-ID": "bob"}).status_code == 200


def test_resets_after_window():
    for _ in range(main.LIMIT):
        client.get("/hello", headers={"X-User-ID": "alice"})
    main.requests_by_user["alice"][0] -= main.WINDOW
    assert client.get("/hello", headers={"X-User-ID": "alice"}).status_code == 200