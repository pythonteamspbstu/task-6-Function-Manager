import requests

import client_http


class FakeResponse:
    def __init__(self, status_code=200, data=None):
        self.status_code = status_code
        self.ok = 200 <= status_code < 400
        self._data = data if data is not None else {}

    def json(self):
        return self._data


def test_print_separator(capsys):
    client_http.print_separator()
    out = capsys.readouterr().out
    assert out.strip() == "-" * 40


def test_main_runs_full_demo(monkeypatch, capsys):
    calls = []

    def fake_post(url, json=None):
        calls.append(("POST", url, json))
        if url.endswith("/execute"):
            return FakeResponse(200, {"result": 25})
        return FakeResponse(200, {"name": "sum_sq"})

    def fake_get(url):
        calls.append(("GET", url))
        return FakeResponse(200, [{"name": "sum_sq"}])

    def fake_put(url, json=None):
        calls.append(("PUT", url, json))
        return FakeResponse(200, {"name": "sum_sq"})

    def fake_delete(url):
        calls.append(("DELETE", url))
        return FakeResponse(200, {"status": "deleted"})

    monkeypatch.setattr(client_http.requests, "post", fake_post)
    monkeypatch.setattr(client_http.requests, "get", fake_get)
    monkeypatch.setattr(client_http.requests, "put", fake_put)
    monkeypatch.setattr(client_http.requests, "delete", fake_delete)

    client_http.main()

    out = capsys.readouterr().out
    assert "HTTP Client Demo" in out
    assert "Listing functions" in out
    assert "Deleting 'sum_sq'" in out

    methods = [c[0] for c in calls]
    assert methods == ["POST", "GET", "POST", "PUT", "POST", "DELETE"]


def test_main_handles_connection_error(monkeypatch, capsys):
    def boom(*args, **kwargs):
        raise requests.exceptions.ConnectionError()

    monkeypatch.setattr(client_http.requests, "post", boom)

    # Mirror the __main__ guard behaviour.
    try:
        client_http.main()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Make sure server.py is running.")

    assert "Could not connect" in capsys.readouterr().out
