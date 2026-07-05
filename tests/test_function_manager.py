import math

import pytest

from function_manager import FunctionManager


@pytest.fixture
def manager():
    return FunctionManager()


def test_create_function_returns_definition(manager):
    result = manager.create_function("add", ["x", "y"], ["z"], "x + y")
    assert result == {
        "name": "add",
        "inputs": ["x", "y"],
        "outputs": ["z"],
        "expression": "x + y",
    }
    assert manager.functions["add"] == result


def test_create_function_duplicate_raises(manager):
    manager.create_function("add", ["x"], ["y"], "x")
    with pytest.raises(ValueError, match="already exists"):
        manager.create_function("add", ["x"], ["y"], "x")


def test_get_function_existing(manager):
    manager.create_function("f", ["x"], ["y"], "x")
    assert manager.get_function("f")["name"] == "f"


def test_get_function_missing_returns_none(manager):
    assert manager.get_function("nope") is None


def test_list_functions_empty(manager):
    assert manager.list_functions() == []


def test_list_functions_returns_all(manager):
    manager.create_function("a", ["x"], ["y"], "x")
    manager.create_function("b", ["x"], ["y"], "x + 1")
    names = {f["name"] for f in manager.list_functions()}
    assert names == {"a", "b"}


def test_update_function_replaces_definition(manager):
    manager.create_function("f", ["x"], ["y"], "x")
    updated = manager.update_function("f", ["a", "b"], ["c"], "a * b")
    assert updated == {
        "name": "f",
        "inputs": ["a", "b"],
        "outputs": ["c"],
        "expression": "a * b",
    }
    assert manager.get_function("f") == updated


def test_update_function_missing_raises(manager):
    with pytest.raises(ValueError, match="does not exist"):
        manager.update_function("ghost", ["x"], ["y"], "x")


def test_delete_function_existing_returns_true(manager):
    manager.create_function("f", ["x"], ["y"], "x")
    assert manager.delete_function("f") is True
    assert manager.get_function("f") is None


def test_delete_function_missing_returns_false(manager):
    assert manager.delete_function("nope") is False


def test_execute_function_basic(manager):
    manager.create_function("add", ["x", "y"], ["z"], "x + y")
    assert manager.execute_function("add", {"x": 2, "y": 3}) == 5


def test_execute_function_uses_math_namespace(manager):
    manager.create_function("root", ["x"], ["y"], "sqrt(x)")
    assert manager.execute_function("root", {"x": 16}) == 4.0


def test_execute_function_tuple_output(manager):
    manager.create_function("sd", ["x", "y"], ["a", "b"], "x + y, x - y")
    assert manager.execute_function("sd", {"x": 10, "y": 4}) == (14, 6)


def test_execute_function_not_found_raises(manager):
    with pytest.raises(ValueError, match="not found"):
        manager.execute_function("missing", {"x": 1})


def test_execute_function_missing_args_raises(manager):
    manager.create_function("add", ["x", "y"], ["z"], "x + y")
    with pytest.raises(ValueError, match="Missing arguments: y"):
        manager.execute_function("add", {"x": 1})


def test_execute_function_expression_error_raises(manager):
    manager.create_function("bad", ["x"], ["y"], "x / 0")
    with pytest.raises(ValueError, match="Execution error"):
        manager.execute_function("bad", {"x": 1})


def test_execute_function_builtins_are_blocked(manager):
    manager.create_function("danger", [], ["y"], "open('x')")
    with pytest.raises(ValueError, match="is not allowed"):
        manager.execute_function("danger", {})


def test_execute_function_constant_expression_no_inputs(manager):
    manager.create_function("pi_val", [], ["y"], "pi")
    assert manager.execute_function("pi_val", {}) == math.pi
