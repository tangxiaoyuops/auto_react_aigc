"""Calculator tool"""
import ast
import operator


async def execute(expression: str) -> dict:
    """
    Execute mathematical expression
    
    Args:
        expression: Mathematical expression to evaluate
    
    Returns:
        Dictionary with result
    """
    try:
        # Parse expression
        tree = ast.parse(expression, mode='eval')
        
        # Safe evaluation
        result = _eval_node(tree.body)
        
        return {
            "expression": expression,
            "result": result
        }
    except Exception as e:
        return {
            "expression": expression,
            "error": str(e)
        }


def _eval_node(node):
    """Safely evaluate AST node"""
    # Supported operators
    operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
    }
    
    # Supported functions
    functions = {
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
    }
    
    if isinstance(node, ast.Num):
        return node.n
    elif isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        op = operators.get(type(node.op))
        if op:
            return op(left, right)
        else:
            raise ValueError(f"Unsupported operator: {type(node.op)}")
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        if isinstance(node.op, ast.USub):
            return -operand
        elif isinstance(node.op, ast.UAdd):
            return +operand
        else:
            raise ValueError(f"Unsupported unary operator: {type(node.op)}")
    elif isinstance(node, ast.Call):
        func_name = node.func.id
        if func_name in functions:
            args = [_eval_node(arg) for arg in node.args]
            return functions[func_name](*args)
        else:
            raise ValueError(f"Unsupported function: {func_name}")
    else:
        raise ValueError(f"Unsupported node type: {type(node)}")
