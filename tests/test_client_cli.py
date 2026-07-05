import socket

import pytest

import client_cli


class FakeSocket:
    def __init__(self, recv_chunks, connect_error=None):
        self._recv_chunks = list(recv_chunks)
        self._connect_error = connect_error
        self.sent = []
        self.closed = False

    def connect(self, addr):
        if self._connect_error:
            raise self._connect_error

    def recv(self, _bufsize):
        if not self._recv_chunks:
            return b""
        return self._recv_chunks.pop(0)

    def sendall(self, data):
        self.sent.append(data)

    def close(self):
        self.closed = True


def test_connection_refused_exits(monkeypatch, capsys):
    monkeypatch.setattr(
        client_cli.socket,
        "socket",
        lambda *a, **k: FakeSocket([], connect_error=ConnectionRefusedError()),
    )
    with pytest.raises(SystemExit) as exc:
        client_cli.main()
    assert exc.value.code == 1
    assert "Could not connect" in capsys.readouterr().out


def test_interactive_session_sends_input_and_exits(monkeypatch, capsys):
    fake = FakeSocket(
        [
            b"Select option: ",
            b"Enter function name: ",
            b"Select option: ",
        ]
    )
    monkeypatch.setattr(client_cli.socket, "socket", lambda *a, **k: fake)
    inputs = iter(["3", "add", "7"])
    monkeypatch.setattr("builtins.input", lambda *a, **k: next(inputs))

    client_cli.main()

    assert fake.sent == [b"3\n", b"add\n", b"7\n"]
    assert fake.closed is True


def test_server_closes_connection_ends_loop(monkeypatch):
    fake = FakeSocket([b""])
    monkeypatch.setattr(client_cli.socket, "socket", lambda *a, **k: fake)

    client_cli.main()

    assert fake.sent == []
    assert fake.closed is True


def test_keyboard_interrupt_is_handled(monkeypatch, capsys):
    fake = FakeSocket([b"Select option: "])
    monkeypatch.setattr(client_cli.socket, "socket", lambda *a, **k: fake)

    def raise_interrupt(*a, **k):
        raise KeyboardInterrupt()

    monkeypatch.setattr("builtins.input", raise_interrupt)

    client_cli.main()

    assert "Exiting..." in capsys.readouterr().out
    assert fake.closed is True
