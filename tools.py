"""Tools the agent can call. Each tool is a plain function plus a JSON schema."""

import ast
import json
import operator

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _eval(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        left, right = _eval(node.left), _eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ValueError("exponent too large")
        return _OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("unsupported expression")


def calculator(expression: str) -> str:
    """Safely evaluate an arithmetic expression (no names, calls, or attributes)."""
    tree = ast.parse(expression, mode="eval")
    result = _eval(tree.body)
    if isinstance(result, float) and result.is_integer():
        result = int(result)
    return str(result)


def position_size(
    account_balance: float,
    risk_percent: float,
    stop_loss_pips: float,
    pip_value_per_lot: float = 10.0,
) -> str:
    """Forex position sizing: lots = (balance * risk%) / (stop pips * pip value per lot)."""
    values = (account_balance, risk_percent, stop_loss_pips, pip_value_per_lot)
    if any(v <= 0 for v in values):
        raise ValueError("all inputs must be positive")
    risk_amount = account_balance * risk_percent / 100
    lots = risk_amount / (stop_loss_pips * pip_value_per_lot)
    return json.dumps({"risk_amount": round(risk_amount, 2), "lots": round(lots, 2)})


TOOL_FUNCS = {"calculator": calculator, "position_size": position_size}

TOOL_SCHEMAS = [
    {
        "name": "calculator",
        "description": "Evaluate an arithmetic expression with + - * / % ** and parentheses.",
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "e.g. (12+8)*3"}},
            "required": ["expression"],
        },
    },
    {
        "name": "position_size",
        "description": (
            "Compute forex position size in lots from account balance, risk percent, "
            "stop-loss distance in pips, and pip value per standard lot (default 10)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "account_balance": {"type": "number"},
                "risk_percent": {"type": "number", "description": "e.g. 1 for 1%"},
                "stop_loss_pips": {"type": "number"},
                "pip_value_per_lot": {"type": "number"},
            },
            "required": ["account_balance", "risk_percent", "stop_loss_pips"],
        },
    },
]


def run_tool(name: str, args: dict) -> str:
    if name not in TOOL_FUNCS:
        raise KeyError(f"unknown tool: {name}")
    return TOOL_FUNCS[name](**args)
