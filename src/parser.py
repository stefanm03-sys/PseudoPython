# parser.py
from lark import Lark, Transformer, v_args
from lark.exceptions import UnexpectedInput

from ppy_errors import make_error

GRAMMAR = r"""
?start: program

program: statement*

?statement: let_stmt
          | assign_stmt
          | print_stmt
          | execute_stmt
          | if_stmt
          | while_stmt
          | repeat_amt_stmt

let_stmt: "var" NAME "is" expr      -> let_stmt
assign_stmt: NAME "is" expr         -> assign_stmt
print_stmt: "state" "(" expr ")"          -> print_stmt
execute_stmt: "execute" "(" expr ")"      -> execute_stmt

if_stmt: "when" expr "do" program elif_block* else_block? "endpt" -> if_stmt
elif_block: "butIf" expr "do" program                              -> elif_block
else_block: "else" program                                          -> else_block

while_stmt: "repeat" "when" expr "do" program "endpt"          -> while_stmt
repeat_amt_stmt: "repeat" "amt" "(" expr ")" program "endpt" -> repeat_amt_stmt

?expr: or_expr

?or_expr: and_expr
        | or_expr "or" and_expr      -> or_op

?and_expr: equality
         | and_expr "and" equality   -> and_op

?equality: comparison
         | equality "==" comparison  -> eq
         | equality "!=" comparison  -> ne

?comparison: sum
           | comparison ">" sum      -> gt
           | comparison "<" sum      -> lt
           | comparison ">=" sum     -> ge
           | comparison "<=" sum     -> le

?sum: term
    | sum "+" term                   -> add
    | sum "-" term                   -> sub

?term: factor
     | term "*" factor               -> mul
     | term "/" factor               -> div

?factor: "-" factor                  -> neg
       | atom

?atom: NUMBER                        -> number
     | STRING                        -> string
     | "TRUE"                        -> true
     | "FALSE"                       -> false
     | ask_expr
     | NAME                          -> var
     | "(" expr ")"

ask_expr: "ask" "(" expr ("," expr)? ")" -> ask_expr

NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
NUMBER: /\d+(\.\d+)?/
STRING: /"([^"\\]|\\.)*"/

%import common.WS
%ignore WS
%ignore /#[^\n]*/
%ignore /\/\/[^\n]*/
"""

_parser = Lark(
    GRAMMAR,
    parser="lalr",
    start="start",
)

@v_args(inline=True)
class ASTBuilder(Transformer):
    def execute_stmt(self, value):
        return {"type": "execute", "value": value}


    def program(self, *stmts):
        return {"type": "program", "statements": list(stmts)}

    def let_stmt(self, name, expr):
        return {"type": "let", "name": str(name), "value": expr}

    def assign_stmt(self, name, expr):
        return {"type": "assign", "name": str(name), "value": expr}

    def print_stmt(self, expr):
        return {"type": "print", "value": expr}

    def if_stmt(self, cond, then_block, *rest):
        elifs = []
        else_body = []
        for item in rest:
            if item.get("type") == "elif":
                elifs.append(item)
            elif item.get("type") == "else":
                else_body = item["body"]
        return {
            "type": "if",
            "condition": cond,
            "then": then_block["statements"],
            "elifs": elifs,
            "else": else_body,
        }

    def elif_block(self, cond, block):
        return {"type": "elif", "condition": cond, "body": block["statements"]}

    def else_block(self, block):
        return {"type": "else", "body": block["statements"]}

    def while_stmt(self, cond, block):
        return {"type": "while", "condition": cond, "body": block["statements"]}

    def repeat_amt_stmt(self, count, block):
        return {"type": "repeat_amt", "count": count, "body": block["statements"]}

    def number(self, tok):
        s = str(tok)
        return {"type": "number", "value": float(s) if "." in s else int(s)}

    def string(self, tok):
        raw = str(tok)
        return {"type": "string", "value": bytes(raw[1:-1], "utf-8").decode("unicode_escape")}

    def true(self):
        return {"type": "bool", "value": True}

    def false(self):
        return {"type": "bool", "value": False}

    def var(self, tok):
        return {"type": "var", "name": str(tok)}

    def ask_expr(self, prompt, data_type=None):
        return {"type": "ask", "prompt": prompt, "data_type": data_type}

    def neg(self, x): return {"type": "neg", "value": x}
    def add(self, a, b): return {"type": "add", "left": a, "right": b}
    def sub(self, a, b): return {"type": "sub", "left": a, "right": b}
    def mul(self, a, b): return {"type": "mul", "left": a, "right": b}
    def div(self, a, b): return {"type": "div", "left": a, "right": b}
    def eq(self, a, b): return {"type": "eq", "left": a, "right": b}
    def ne(self, a, b): return {"type": "ne", "left": a, "right": b}
    def gt(self, a, b): return {"type": "gt", "left": a, "right": b}
    def lt(self, a, b): return {"type": "lt", "left": a, "right": b}
    def ge(self, a, b): return {"type": "ge", "left": a, "right": b}
    def le(self, a, b): return {"type": "le", "left": a, "right": b}
    def and_op(self, a, b): return {"type": "and", "left": a, "right": b}
    def or_op(self, a, b): return {"type": "or", "left": a, "right": b}

def parse(source: str):
    """
    Parse PseudoPy source text into a dictionary AST.
    """
    try:
        tree = _parser.parse(source)
        return ASTBuilder().transform(tree)
    except UnexpectedInput as exc:
        detail = str(exc).splitlines()[0] if str(exc) else "Invalid syntax"
        line = getattr(exc, "line", "?")
        column = getattr(exc, "column", "?")
        raise make_error("PPY-PARSE-001", line=line, column=column, detail=detail) from exc
