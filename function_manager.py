import ast
import math
import operator
import re

SAFE_MATH_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "atan2": math.atan2,
    "log": math.log,
    "log2": math.log2,
    "log10": math.log10,
    "exp": math.exp,
    "pow": math.pow,
    "ceil": math.ceil,
    "floor": math.floor,
    "fabs": math.fabs,
    "factorial": math.factorial,
    "gcd": math.gcd,
    "degrees": math.degrees,
    "radians": math.radians,
    "hypot": math.hypot,
}

SAFE_MATH_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
    "inf": math.inf,
    "nan": math.nan,
}

_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

MAX_EXPRESSION_LENGTH = 1024
MAX_NAME_LENGTH = 64
_VALID_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _validate_identifier(value: str, label: str) -> None:
    if not value or not isinstance(value, str):
        raise ValueError(f"{label} must be a non-empty string.")
    if len(value) > MAX_NAME_LENGTH:
        raise ValueError(f"{label} exceeds maximum length of {MAX_NAME_LENGTH}.")
    if not _VALID_IDENTIFIER_RE.match(value):
        raise ValueError(
            f"{label} '{value}' is invalid — only letters, digits, and "
            f"underscores are allowed (must start with a letter or underscore)."
        )


def _validate_expression(expression: str) -> None:
    if not expression or not isinstance(expression, str):
        raise ValueError("Expression must be a non-empty string.")
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise ValueError(
            f"Expression exceeds maximum length of {MAX_EXPRESSION_LENGTH}."
        )
    try:
        ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Expression has invalid syntax: {exc}") from None


def safe_eval(expression: str, variables: dict) -> object:
    """Evaluate a mathematical expression using an AST walker.

    Only arithmetic operators, numeric literals, whitelisted math functions/
    constants, declared variables, and tuples of the above are permitted.
    """
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Invalid expression syntax: {exc}") from None

    def _eval_node(node):  # noqa: C901 — intentionally flat switch
        if isinstance(node, ast.Expression):
            return _eval_node(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError(f"Unsupported literal: {node.value!r}")

        if isinstance(node, ast.Name):
            name = node.id
            if name in variables:
                return variables[name]
            if name in SAFE_MATH_CONSTANTS:
                return SAFE_MATH_CONSTANTS[name]
            raise ValueError(f"Unknown variable or constant: '{name}'")

        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in _SAFE_OPERATORS:
                raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
            return _SAFE_OPERATORS[op_type](_eval_node(node.operand))

        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in _SAFE_OPERATORS:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
            left = _eval_node(node.left)
            right = _eval_node(node.right)
            if op_type is ast.Pow and isinstance(right, (int, float)) and right > 1000:
                raise ValueError("Exponent too large (max 1000).")
            return _SAFE_OPERATORS[op_type](left, right)

        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name):
                raise ValueError("Only simple function calls are allowed.")
            func_name = node.func.id
            if func_name not in SAFE_MATH_FUNCTIONS:
                raise ValueError(f"Function '{func_name}' is not allowed.")
            if node.keywords:
                raise ValueError("Keyword arguments are not allowed.")
            args = [_eval_node(a) for a in node.args]
            return SAFE_MATH_FUNCTIONS[func_name](*args)

        if isinstance(node, ast.Tuple):
            return tuple(_eval_node(el) for el in node.elts)

        raise ValueError(
            f"Unsupported expression element: {type(node).__name__}"
        )

    return _eval_node(tree)


from utils import build_function_record

class FunctionManager:
    def __init__(self):
        self.functions = {}

    def create_function(self, name: str, inputs: list[str], outputs: list[str], expression: str):
        _validate_identifier(name, "Function name")
        for inp in inputs:
            _validate_identifier(inp, "Input parameter")
        for out in outputs:
            _validate_identifier(out, "Output parameter")
        _validate_expression(expression)

        if name in self.functions:
            raise ValueError(f"Function '{name}' already exists.")

        self.functions[name] = build_function_record(name, inputs, outputs, expression)
        return self.functions[name]

    def get_function(self, name: str):
        if name not in self.functions:
            return None
        return self.functions[name]

    def list_functions(self):
        return list(self.functions.values())

    def update_function(self, name: str, inputs: list[str], outputs: list[str], expression: str):
        if name not in self.functions:
            raise ValueError(f"Function '{name}' does not exist.")

        for inp in inputs:
            _validate_identifier(inp, "Input parameter")
        for out in outputs:
            _validate_identifier(out, "Output parameter")
        _validate_expression(expression)

        self.functions[name] = build_function_record(name, inputs, outputs, expression)
        return self.functions[name]

    def delete_function(self, name: str):
        if name in self.functions:
            del self.functions[name]
            return True
        return False

    def execute_function(self, name: str, args: dict):
        func = self.get_function(name)
        if not func:
            raise ValueError(f"Function '{name}' not found.")

        missing_args = [arg for arg in func["inputs"] if arg not in args]
        if missing_args:
            raise ValueError(f"Missing arguments: {', '.join(missing_args)}")

        return safe_eval(func["expression"], args)
