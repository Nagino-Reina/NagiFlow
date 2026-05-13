"""
Built-in calculator skill.

Evaluates mathematical expressions safely using Python's ``ast`` module
(no ``eval``).  Supports arithmetic, trigonometry, and common math functions.
"""

import ast
import math
import operator
from typing import Any

from nagiflow.skills.base import BaseSkill, SkillMeta, SkillParameter
from nagiflow.skills.registry import skill_registry

_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_SAFE_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log2": math.log2,
    "log10": math.log10,
    "exp": math.exp,
    "floor": math.floor,
    "ceil": math.ceil,
    "pi": math.pi,
    "e": math.e,
    "inf": math.inf,
}


def _safe_eval(node: ast.expr) -> float:
    """Recursively evaluate an AST node using only whitelisted operations."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError(f"Unsupported constant: {node.value}")

    if isinstance(node, ast.Name):
        if node.id in _SAFE_FUNCTIONS:
            val = _SAFE_FUNCTIONS[node.id]
            if callable(val):
                raise ValueError(f"'{node.id}' must be called with arguments.")
            return float(val)  # type: ignore[arg-type]
        raise ValueError(f"Unknown name: {node.id}")

    if isinstance(node, ast.BinOp):
        op_fn = _SAFE_OPERATORS.get(type(node.op))
        if op_fn is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op_fn(_safe_eval(node.left), _safe_eval(node.right))

    if isinstance(node, ast.UnaryOp):
        op_fn = _SAFE_OPERATORS.get(type(node.op))
        if op_fn is None:
            raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
        return op_fn(_safe_eval(node.operand))

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _SAFE_FUNCTIONS:
            raise ValueError("Only whitelisted math functions are allowed.")
        fn = _SAFE_FUNCTIONS[node.func.id]
        if not callable(fn):
            raise ValueError(f"'{node.func.id}' is a constant, not a function.")
        args = [_safe_eval(arg) for arg in node.args]
        return fn(*args)  # type: ignore[operator]

    raise ValueError(f"Unsupported AST node: {type(node).__name__}")


@skill_registry.register
class CalculatorSkill(BaseSkill):
    """Evaluate a mathematical expression and return the numeric result."""

    meta = SkillMeta(
        name="calculator",
        display_name="Calculator",
        description=(
            "Evaluate a mathematical expression. Supports arithmetic operators (+, -, *, /, **), "
            "and math functions: sqrt, sin, cos, tan, log, log2, log10, exp, floor, ceil, abs, round. "
            "Constants pi and e are available. Example: 'sqrt(2) * pi'"
        ),
        parameters=[
            SkillParameter(
                name="expression",
                type="string",
                description="A mathematical expression to evaluate",
                required=True,
            ),
        ],
        is_builtin=True,
    )

    async def execute(self, expression: str, **kwargs: Any) -> str:
        try:
            tree = ast.parse(expression, mode="eval")
            result = _safe_eval(tree.body)
            return str(result)
        except Exception as exc:
            return f"Calculation error: {exc}"
