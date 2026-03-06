# parser.py
from lark import Lark, Transformer, v_args
from lark.exceptions import UnexpectedInput
import re

from ppy_errors import make_error

GRAMMAR = r"""
?start: program

program: statement*

?statement: let_stmt
          | assign_stmt
          | print_stmt
          | is_stmt
          | do_stmt
          | function_stmt
          | call_stmt
          | wait_stmt
          | execute_stmt
          | stop_stmt
          | restart_stmt
          | if_stmt
          | while_stmt
          | repeat_amt_stmt

let_stmt: "var" NAME "is" expr      -> let_stmt
assign_stmt: NAME "is" expr         -> assign_stmt
print_stmt: ("state" | "stateStr" | "stateInt" | "stateFloat" | "stateBool") "(" expr ")" -> print_stmt
is_stmt: "is" expr                   -> is_stmt
do_stmt: "do" expr                  -> print_stmt
function_stmt: "function" NAME "(" param_list_opt ")" program "endpt" -> function_stmt
             | "function" NAME "(" param_list_opt ")" "{" program "}" -> function_stmt
             | "function" NAME program "endpt"                        -> function_stmt_noparams
             | "function" NAME "{" program "}"                        -> function_stmt_noparams
call_stmt: NAME "(" arg_list_opt ")" -> call_stmt
wait_stmt: "wait" "(" wait_arg ")"  -> wait_stmt
execute_stmt: "execute" "(" expr ")"      -> execute_stmt
stop_stmt: "stop"                         -> stop_stmt
         | "Stop"                         -> stop_stmt
restart_stmt: "restart"                   -> restart_stmt
            | "Restart"                   -> restart_stmt

if_stmt: "when" expr ","? "do"? program elif_block* else_block? "endpt" -> if_stmt
       | "when" expr ","? "do"? "{" program "}" elif_block_brace* else_block_brace? -> if_stmt
elif_block: "butIf" expr ","? "do"? program                              -> elif_block
elif_block_brace: "butIf" expr ","? "do"? "{" program "}"               -> elif_block
else_block: ("else" | "otherwise") program                           -> else_block
else_block_brace: ("else" | "otherwise") "{" program "}"             -> else_block

while_stmt: "repeat" "when" expr ","? "do"? program "endpt"          -> while_stmt
          | "repeat" "when" expr ","? "do"? "{" program "}"          -> while_stmt
repeat_amt_stmt: "repeat" "amt" "(" expr ")" program "endpt"         -> repeat_amt_stmt
               | "repeat" "amt" "(" expr ")" "{" program "}"         -> repeat_amt_stmt

?wait_arg: DURATION                  -> duration_value
         | expr

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
     | "true"                        -> true
     | "false"                       -> false
     | "none"                        -> none_lit
     | "blank"                      -> none_lit
     | ask_expr
     | NAME                          -> var
     | "(" expr ")"

ask_expr: "ask" "(" expr ("," expr)? ")" -> ask_expr
        | "ask" "(" ")"                   -> ask_expr_empty
param_list_opt: param_list |              -> empty_params
arg_list_opt: arg_list |                  -> empty_args
param_list: NAME ("," NAME)*
arg_list: expr ("," expr)*

NAME: /[a-zA-Z_][a-zA-Z0-9_]*/
DURATION: /\d+(\.\d+)?(ms|s|m)/
NUMBER: /\d+(\.\d+)?/
STRING: /"([^"\\]|\\.)*"/

%import common.WS
%ignore WS
%ignore /#[^\n]*/
%ignore /\/\*[\s\S]*?\*\//
%ignore /\/\/\s*\n[\s\S]*?\n\s*\/\//
%ignore /\/\/[^\n]*/
"""

_parser = Lark(
    GRAMMAR,
    parser="lalr",
    start="start",
)

_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
_ASSIGN_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s+is\b")
_CALL_RE = re.compile(r"^([a-zA-Z_][a-zA-Z0-9_]*)\s*\(")
_VALID_LINE_STARTERS = {
    "var",
    "state",
    "stateStr",
    "stateInt",
    "stateFloat",
    "stateBool",
    "is",
    "do",
    "when",
    "butIf",
    "else",
    "otherwise",
    "repeat",
    "endpt",
    "stop",
    "restart",
    "ask",
    "execute",
    "wait",
    "function",
}


def _collect_validation_errors(source: str):
    errors = []
    in_slash_block = False
    in_star_block = False

    for line_no, raw in enumerate(source.splitlines(), start=1):
        s = raw.strip()
        if not s:
            continue

        if in_slash_block:
            if s == "//":
                in_slash_block = False
            continue
        if in_star_block:
            if "*/" in s:
                in_star_block = False
            continue

        if s == "//":
            in_slash_block = True
            continue
        if s.startswith("/*"):
            if "*/" not in s:
                in_star_block = True
            continue
        if s.startswith("#") or s.startswith("//"):
            continue

        # Drop trailing inline comments for validation purposes.
        if "#" in s:
            s = s.split("#", 1)[0].rstrip()
        if "//" in s:
            s = s.split("//", 1)[0].rstrip()
        if not s:
            continue

        if s in {"{", "}"}:
            continue
        if s.startswith("} "):
            s = s[1:].lstrip()

        if s.startswith("var "):
            rest = s[4:].strip()
            if not rest:
                errors.append(f"Line {line_no}: [PPY-VALID-001] Missing variable name after 'var'.")
                continue
            var_name = rest.split()[0]
            if not _NAME_RE.fullmatch(var_name):
                errors.append(
                    f"Line {line_no}: [PPY-VALID-001] Invalid variable name '{var_name}'."
                )
            continue

        if s.startswith("function "):
            rest = s[len("function "):].strip()
            if not rest:
                errors.append(f"Line {line_no}: [PPY-VALID-003] Missing function name after 'function'.")
                continue
            name = rest.split("(", 1)[0].split()[0]
            if not _NAME_RE.fullmatch(name):
                errors.append(
                    f"Line {line_no}: [PPY-VALID-003] Invalid function name '{name}'."
                )
            continue

        first = s.split()[0]
        if first in _VALID_LINE_STARTERS:
            continue
        if _ASSIGN_RE.match(s):
            continue
        if _CALL_RE.match(s):
            continue

        errors.append(
            f"Line {line_no}: [PPY-VALID-002] Invalid statement '{s}'."
        )

    return errors


def _format_multi_issue_message(issues):
    return "\n".join(f"{idx}. {msg}" for idx, msg in enumerate(issues, start=1))

@v_args(inline=True)
class ASTBuilder(Transformer):
    def stop_stmt(self):
        return {"type": "stop"}

    def restart_stmt(self):
        return {"type": "restart"}

    def execute_stmt(self, value):
        return {"type": "execute", "value": value}

    def wait_stmt(self, value):
        return {"type": "wait", "value": value}

    def empty_params(self):
        return []

    def empty_args(self):
        return []

    def param_list(self, *names):
        return [str(n) for n in names]

    def arg_list(self, *args):
        return list(args)

    def param_list_opt(self, values):
        return values

    def arg_list_opt(self, values):
        return values

    def program(self, *stmts):
        return {"type": "program", "statements": list(stmts)}

    def let_stmt(self, name, expr):
        return {"type": "let", "name": str(name), "value": expr}

    def assign_stmt(self, name, expr):
        return {"type": "assign", "name": str(name), "value": expr}

    def print_stmt(self, expr):
        return {"type": "print", "value": expr}

    def is_stmt(self, expr):
        return {"type": "is", "value": expr}

    def function_stmt(self, name, params, block):
        return {
            "type": "function_def",
            "name": str(name),
            "params": params,
            "body": block["statements"],
        }

    def function_stmt_noparams(self, name, block):
        return {
            "type": "function_def",
            "name": str(name),
            "params": [],
            "body": block["statements"],
        }

    def call_stmt(self, name, args):
        name_str = str(name)
        if name_str == "ask":
            return {"type": "ask_stmt", "args": args}
        return {"type": "call_stmt", "name": name_str, "args": args}

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

    def duration_value(self, tok):
        raw = str(tok)
        if raw.endswith("ms"):
            unit = "ms"
            n = raw[:-2]
        elif raw.endswith("s"):
            unit = "s"
            n = raw[:-1]
        else:
            unit = "m"
            n = raw[:-1]
        value = float(n) if "." in n else int(n)
        return {"type": "duration", "value": value, "unit": unit}

    def string(self, tok):
        raw = str(tok)
        return {"type": "string", "value": bytes(raw[1:-1], "utf-8").decode("unicode_escape")}

    def true(self):
        return {"type": "bool", "value": True}

    def false(self):
        return {"type": "bool", "value": False}

    def none_lit(self):
        return {"type": "none", "value": None}

    def var(self, tok):
        return {"type": "var", "name": str(tok)}

    def ask_expr(self, prompt, data_type=None):
        return {"type": "ask", "prompt": prompt, "data_type": data_type}

    def ask_expr_empty(self):
        return {
            "type": "ask",
            "prompt": {"type": "string", "value": ""},
            "data_type": None,
        }

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
    precheck_errors = _collect_validation_errors(source)

    try:
        tree = _parser.parse(source)
        ast = ASTBuilder().transform(tree)
        if precheck_errors:
            raise make_error(
                "PPY-PARSE-002",
                count=len(precheck_errors),
                detail=_format_multi_issue_message(precheck_errors),
            )
        return ast
    except UnexpectedInput as exc:
        detail = str(exc).splitlines()[0] if str(exc) else "Invalid syntax"
        line = getattr(exc, "line", "?")
        column = getattr(exc, "column", "?")
        all_errors = list(precheck_errors)
        all_errors.append(
            f"Line {line}, column {column}: [PPY-PARSE-001] {detail}"
        )
        raise make_error(
            "PPY-PARSE-002",
            count=len(all_errors),
            detail=_format_multi_issue_message(all_errors),
        ) from exc
