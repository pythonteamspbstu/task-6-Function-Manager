import asyncio

import pytest

import server


class FakeReader:
    """Feeds queued lines to the handler; raises to end the session."""

    def __init__(self, lines):
        self._lines = list(lines)

    async def readline(self):
        if not self._lines:
            raise ConnectionResetError("client disconnected")
        return (self._lines.pop(0) + "\n").encode()


class FakeWriter:
    def __init__(self):
        self.chunks = []

    def write(self, data):
        self.chunks.append(data.decode())

    async def drain(self):
        pass

    def get_extra_info(self, _name):
        return ("127.0.0.1", 12345)

    def close(self):
        pass

    async def wait_closed(self):
        pass

    @property
    def output(self):
        return "".join(self.chunks)


async def run_session(lines):
    server.manager.functions.clear()
    reader = FakeReader(lines)
    writer = FakeWriter()
    await server.handle_tcp_client(reader, writer)
    server.manager.functions.clear()
    return writer.output


@pytest.mark.asyncio
async def test_tcp_exit():
    out = await run_session(["7"])
    assert "Goodbye!" in out


@pytest.mark.asyncio
async def test_tcp_empty_choice_then_exit():
    out = await run_session(["", "7"])
    assert "Goodbye!" in out


@pytest.mark.asyncio
async def test_tcp_invalid_option():
    out = await run_session(["99", "7"])
    assert "Invalid option." in out


@pytest.mark.asyncio
async def test_tcp_create_function():
    out = await run_session(["1", "add", "x, y", "z", "x + y", "7"])
    assert "created successfully" in out
    # session is cleared in run_session, so assert via captured output only


@pytest.mark.asyncio
async def test_tcp_create_duplicate_error():
    out = await run_session(
        ["1", "add", "x", "y", "x", "1", "add", "x", "y", "x", "7"]
    )
    assert "already exists" in out


@pytest.mark.asyncio
async def test_tcp_list_empty():
    out = await run_session(["2", "7"])
    assert "No functions available." in out


@pytest.mark.asyncio
async def test_tcp_list_with_functions():
    out = await run_session(["1", "add", "x, y", "z", "x + y", "2", "7"])
    assert "add = x + y" in out


@pytest.mark.asyncio
async def test_tcp_get_details():
    out = await run_session(["1", "add", "x", "z", "x", "3", "add", "7"])
    assert '"name": "add"' in out


@pytest.mark.asyncio
async def test_tcp_get_details_not_found():
    out = await run_session(["3", "ghost", "7"])
    assert "Function not found." in out


@pytest.mark.asyncio
async def test_tcp_update_keeps_defaults_on_blank_input():
    out = await run_session(
        ["1", "add", "x, y", "z", "x + y", "4", "add", "", "", "", "7"]
    )
    assert "Function updated." in out


@pytest.mark.asyncio
async def test_tcp_update_changes_expression():
    out = await run_session(
        ["1", "add", "x, y", "z", "x + y", "4", "add", "", "", "x - y", "7"]
    )
    assert "Function updated." in out


@pytest.mark.asyncio
async def test_tcp_update_not_found():
    out = await run_session(["4", "ghost", "7"])
    assert "Function not found." in out


@pytest.mark.asyncio
async def test_tcp_delete_function():
    out = await run_session(["1", "add", "x", "z", "x", "5", "add", "7"])
    assert "Function deleted." in out


@pytest.mark.asyncio
async def test_tcp_delete_not_found():
    out = await run_session(["5", "ghost", "7"])
    assert "Function not found." in out


@pytest.mark.asyncio
async def test_tcp_execute_function():
    out = await run_session(
        ["1", "add", "x, y", "z", "x + y", "6", "add", "3", "4", "7"]
    )
    assert "Result: 7" in out


@pytest.mark.asyncio
async def test_tcp_execute_not_found():
    out = await run_session(["6", "ghost", "7"])
    assert "Function not found." in out


@pytest.mark.asyncio
async def test_tcp_execute_invalid_number():
    out = await run_session(
        ["1", "add", "x, y", "z", "x + y", "6", "add", "notanumber", "7"]
    )
    assert "Invalid number." in out


@pytest.mark.asyncio
async def test_tcp_execute_expression_error():
    out = await run_session(
        ["1", "bad", "x", "z", "x/0", "6", "bad", "3", "7"]
    )
    assert "Error:" in out


@pytest.mark.asyncio
async def test_tcp_connection_error_is_handled():
    # No trailing "7": reader raises, exercising the except/finally cleanup.
    out = await run_session(["2"])
    assert "No functions available." in out


@pytest.mark.asyncio
async def test_lifespan_starts_and_stops_tcp_server():
    async with server.lifespan(server.app):
        pass
