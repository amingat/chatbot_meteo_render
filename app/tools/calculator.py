import ast
import operator

from langchain_core.tools import tool


_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_safe_eval(node.left), _safe_eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_safe_eval(node.operand))
    raise ValueError('Expression non autorisée.')


@tool
def calculator_tool(expression: str) -> str:
    """Évalue une expression arithmétique sûre. Exemple: (18.5 * 4) / 3"""
    try:
        tree = ast.parse(expression, mode='eval')
        result = _safe_eval(tree)
        return f'Resultat: {result}'
    except Exception as exc:
        return f'Erreur de calcul: {exc}'
