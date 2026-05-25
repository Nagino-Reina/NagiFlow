"""Calculator skill plugin."""

from __future__ import annotations

import ast
import math
import operator
from typing import Any

from nagiflow.plugin.base import BasePlugin, BaseSkill, PluginMeta, SkillMeta, SkillParameter
from nagiflow.plugin.registry import registry

_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub,
    ast.Mult: operator.mul, ast.Div: operator.truediv,
    ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.USub: operator.neg, ast.UAdd: operator.pos,
}
_FNS: dict[str, Any] = {
    "abs": abs, "round": round,
    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "log": math.log, "log2": math.log2, "log10": math.log10, "exp": math.exp,
    "floor": math.floor, "ceil": math.ceil,
    "pi": math.pi, "e": math.e, "inf": math.inf,
}


def _eval(node: ast.expr) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return float(node.value)
        raise ValueError(f"Unsupported constant: {node.value}")
    if isinstance(node, ast.Name):
        if node.id in _FNS:
            v = _FNS[node.id]
            if callable(v):
                raise ValueError(f"'{node.id}' must be called.")
            return float(v)
        raise ValueError(f"Unknown name: {node.id}")
    if isinstance(node, ast.BinOp):
        fn = _OPS.get(type(node.op))
        if fn is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return fn(_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp):
        fn = _OPS.get(type(node.op))
        if fn is None:
            raise ValueError(f"Unsupported unary: {type(node.op).__name__}")
        return fn(_eval(node.operand))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name) or node.func.id not in _FNS:
            raise ValueError("Only whitelisted math functions are allowed.")
        fn = _FNS[node.func.id]
        if not callable(fn):
            raise ValueError(f"'{node.func.id}' is a constant.")
        return fn(*[_eval(a) for a in node.args])
    raise ValueError(f"Unsupported AST node: {type(node).__name__}")


class CalculatorSkill(BaseSkill):
    meta = SkillMeta(
        name="calculator",
        display_name="Calculator",
        description=(
            "Evaluate a mathematical expression. Supports +, -, *, /, **, sqrt, "
            "sin, cos, tan, log, exp, floor, ceil, abs, round. Constants pi and e."
        ),
        parameters=[
            SkillParameter(name="expression", type="string", description="Math expression", required=True),
        ],
        is_builtin=True,
    )

    async def execute(self, expression: str, **kwargs: Any) -> str:
        try:
            tree = ast.parse(expression, mode="eval")
            return str(_eval(tree.body))
        except Exception as exc:
            return f"Calculation error: {exc}"


class SkillCalculatorPlugin(BasePlugin):
    meta = PluginMeta(name="skill_calculator", version="1.0.0", description="Safe AST-based math evaluator.")

    async def setup(self) -> None:
        registry.register_skill(CalculatorSkill)
