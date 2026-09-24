"""Calculator tool (Cordis 风格 @tool 装饰器定义)。"""
import ast
import operator
from typing import Any

from app.tools.base import tool, inventory


@tool(
    name="calculator",
    description="安全地执行一个数学表达式计算，例如 '1+2*3'。用于需要精确数值计算的场景。",
    parameters={
        "expression": {"type": "string", "required": True, "description": "要计算的数学表达式，如 '(12+34)*2'"},
    },
    output="计算结果的 dict",
)
async def execute(expression: str) -> dict:
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_node(tree.body)
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"expression": expression, "error": str(e)}


def _eval_node(node: Any) -> Any:
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
    }
    functions = {"abs": abs, "round": round, "min": min, "max": max}

    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.BinOp):
        op = operators.get(type(node.op))
        if not op:
            raise ValueError(f"Unsupported operator: {type(node.op)}")
        return op(_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        if isinstance(node.op, ast.USub):
            return -operand
        if isinstance(node.op, ast.UAdd):
            return +operand
        raise ValueError(f"Unsupported unary operator: {type(node.op)}")
    if isinstance(node, ast.Call):
        func_name = node.func.id
        if func_name in functions:
            args = [_eval_node(arg) for arg in node.args]
            return functions[func_name](*args)
        raise ValueError(f"Unsupported function: {func_name}")
    raise ValueError(f"Unsupported node type: {type(node)}")


# 注册到进程级注册表
inventory.register(execute)