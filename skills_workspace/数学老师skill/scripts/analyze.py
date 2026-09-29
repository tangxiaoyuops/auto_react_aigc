#!/usr/bin/env python3
import argparse
import json
import sys
import ast
import operator
import re
import math

# 支持的运算符映射
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

def safe_eval_expr(expr_str):
    """安全地计算数学表达式"""
    try:
        node = ast.parse(expr_str, mode='eval').body
        return _eval_node(node)
    except Exception as e:
        raise ValueError(f"表达式解析错误：{str(e)}")

def _eval_node(node):
    if isinstance(node, ast.Num): # Python < 3.8
        return node.n
    elif isinstance(node, ast.Constant): # Python >= 3.8
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("不支持的常量类型")
    elif isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        op_type = type(node.op)
        if op_type not in OPERATORS:
            raise ValueError(f"不支持的运算符：{op_type}")
        return OPERATORS[op_type](left, right)
    elif isinstance(node, ast.UnaryOp):
        operand = _eval_node(node.operand)
        op_type = type(node.op)
        if op_type not in OPERATORS:
            raise ValueError(f"不支持的一元运算符：{op_type}")
        return OPERATORS[op_type](operand)
    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == 'sqrt':
            val = _eval_node(node.args[0])
            if val < 0:
                raise ValueError("不能对负数开平方")
            return math.sqrt(val)
        else:
            raise ValueError("仅支持 sqrt() 函数")
    else:
        raise ValueError(f"不支持的表达式结构：{type(node)}")

def solve_linear_equation(equation_str):
    """求解一元一次方程 ax + b = c"""
    # 清理空格
    eq = equation_str.replace(" ", "")
    
    # 简单解析器：假设格式为 ax+b=c 或 ax-b=c 等
    # 使用正则提取系数
    # 模式：左侧包含 x，右侧是常数
    if '=' not in eq:
        raise ValueError("方程必须包含 '=' 符号")
    
    left_part, right_part = eq.split('=')
    
    # 将右侧移到左侧，变成 ax + b = 0 的形式，即 ax = -b
    # 这里采用简化策略：解析出 x 的系数和常数项
    
    def parse_side(side):
        # 这是一个非常简化的解析器，仅处理简单情况如 2x+3, -x, 5
        # 生产环境建议使用 sympy
        terms = re.split(r'(?=[+-])', side)
        coef_x = 0
        const = 0
        for term in terms:
            if not term:
                continue
            if 'x' in term:
                c_str = term.replace('x', '')
                if c_str == '' or c_str == '+':
                    c = 1
                elif c_str == '-':
                    c = -1
                else:
                    c = float(c_str)
                coef_x += c
            else:
                const += float(term)
        return coef_x, const

    try:
        a1, b1 = parse_side(left_part)
        # 右侧移项变号
        a2, b2 = parse_side(right_part)
        
        # 方程变为：(a1 - a2)x + (b1 - b2) = 0
        # 即 Ax = B  =>  (a1-a2)x = -(b1-b2) = b2 - b1
        A = a1 - a2
        B = b2 - b1
        
        if A == 0:
            if B == 0:
                return "无穷多解"
            else:
                return "无解"
        
        result = B / A
        # 格式化输出
        if result.is_integer():
            return int(result)
        return round(result, 6)
    except Exception as e:
        raise ValueError(f"方程求解失败：{str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Math Solver Skill")
    parser.add_argument('--expression', type=str, help="Math expression to evaluate")
    parser.add_argument('--equation', type=str, help="Linear equation to solve (e.g., 2x+1=5)")
    parser.add_argument('--mode', type=str, default='auto', choices=['auto', 'eval', 'solve'], help="Operation mode")
    
    args = parser.parse_args()
    
    response = {
        "status": "success",
        "result": None,
        "steps": [],
        "input_type": None,
        "error": None
    }
    
    try:
        if args.mode == 'auto':
            if args.equation:
                args.mode = 'solve'
            elif args.expression:
                args.mode = 'eval'
            else:
                raise ValueError("未提供表达式或方程参数")
        
        if args.mode == 'eval' or (args.mode == 'auto' and args.expression):
            if not args.expression:
                raise ValueError("缺少 expression 参数")
            response["input_type"] = "expression"
            response["steps"].append(f"解析表达式：{args.expression}")
            result = safe_eval_expr(args.expression)
            response["result"] = result
            response["steps"].append(f"计算结果：{result}")
            
        elif args.mode == 'solve' or (args.mode == 'auto' and args.equation):
            if not args.equation:
                raise ValueError("缺少 equation 参数")
            response["input_type"] = "equation"
            response["steps"].append(f"识别方程：{args.equation}")
            response["steps"].append("移项合并同类项")
            response["steps"].append("求解 x")
            result = solve_linear_equation(args.equation)
            response["result"] = result
            response["steps"].append(f"解得：x = {result}")
            
        else:
            raise ValueError("未知的操作模式或缺少必要参数")
            
    except Exception as e:
        response["status"] = "error"
        response["error"] = str(e)
        response["result"] = None

    print(json.dumps(response, ensure_ascii=False))

if __name__ == "__main__":
    main()