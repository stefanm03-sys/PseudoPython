# interpreter.py
import subprocess

from ppy_errors import make_error
from runtime import Environment, truthy, ensure_number


class _LoopStopSignal(Exception):
    pass


class _LoopRestartSignal(Exception):
    pass


def interpret(ast: dict):
    env = Environment()
    execute_program(ast, env, loop_depth=0)







def execute_program(node: dict, env: Environment, loop_depth: int = 0):
    if node.get("type") != "program":
        raise make_error("PPY-RUNTIME-002")
    for stmt in node["statements"]:
        execute_stmt(stmt, env, loop_depth=loop_depth)


def execute_stmt(stmt: dict, env: Environment, loop_depth: int = 0):
    t = stmt["type"]

    if t == "let":
        env.define(stmt["name"], eval_expr(stmt["value"], env))
    elif t == "assign":
        env.assign(stmt["name"], eval_expr(stmt["value"], env))
    elif t == "print":
        print(eval_expr(stmt["value"], env))
    elif t == "is":
        value = eval_expr(stmt["value"], env)
        if not isinstance(value, bool):
            raise make_error("PPY-TYPE-006", actual_type=type(value).__name__)
        print("true" if value else "false")
    elif t == "stop":
        if loop_depth <= 0:
            raise make_error("PPY-RUNTIME-006")
        raise _LoopStopSignal()
    elif t == "restart":
        if loop_depth <= 0:
            raise make_error("PPY-RUNTIME-007")
        raise _LoopRestartSignal()
    elif t == "if":
        if truthy(eval_expr(stmt["condition"], env)):
            for s in stmt["then"]:
                execute_stmt(s, env, loop_depth=loop_depth)
        else:
            matched = False
            for branch in stmt.get("elifs", []):
                if truthy(eval_expr(branch["condition"], env)):
                    for s in branch["body"]:
                        execute_stmt(s, env, loop_depth=loop_depth)
                    matched = True
                    break
            if not matched:
                for s in stmt["else"]:
                    execute_stmt(s, env, loop_depth=loop_depth)
    elif t == "while":
        while truthy(eval_expr(stmt["condition"], env)):
            try:
                for s in stmt["body"]:
                    execute_stmt(s, env, loop_depth=loop_depth + 1)
            except _LoopRestartSignal:
                continue
            except _LoopStopSignal:
                break
    elif t == "execute":
        cmd_value = eval_expr(stmt["value"], env)
        if not isinstance(cmd_value, str):
            raise make_error("PPY-TYPE-002", actual_type=type(cmd_value).__name__)
        try:
            subprocess.run(["cmd", "/c", cmd_value], check=True)
        except subprocess.CalledProcessError as exc:
            raise make_error(
                "PPY-EXEC-001",
                return_code=exc.returncode,
                command=cmd_value,
            ) from exc

    elif t == "repeat_amt":
        n = eval_expr(stmt["count"], env)
        if not isinstance(n, int):
            raise make_error("PPY-TYPE-003", actual_type=type(n).__name__)
        if n < 0:
            raise make_error("PPY-RUNTIME-003", count=n)
        i = 0
        while i < n:
            try:
                for s in stmt["body"]:
                    execute_stmt(s, env, loop_depth=loop_depth + 1)
            except _LoopRestartSignal:
                i = 0
                continue
            except _LoopStopSignal:
                break
            i += 1


    else:
        raise make_error("PPY-RUNTIME-004", stmt_type=t)


def eval_expr(expr: dict, env: Environment):
    t = expr["type"]

    if t == "number":
        return expr["value"]
    if t == "string":
        return expr["value"]
    if t == "none":
        return expr["value"]
    if t == "bool":
        return expr["value"]
    if t == "var":
        return env.get(expr["name"])
    if t == "ask":
        prompt_value = eval_expr(expr["prompt"], env)
        if not isinstance(prompt_value, str):
            raise make_error("PPY-TYPE-004")

        # Allow ask("...", int) with bare identifiers, or ask("...", "int") as a string.
        data_type_expr = expr.get("data_type")
        if data_type_expr is None:
            data_type_value = "text"
        elif data_type_expr.get("type") == "var":
            data_type_value = data_type_expr["name"]
        else:
            data_type_value = eval_expr(data_type_expr, env)
            if not isinstance(data_type_value, str):
                raise make_error("PPY-TYPE-005")

        data_type = data_type_value.strip().lower()
        raw_input = input(prompt_value + " ")

        if data_type in {"text", "string", "str"}:
            return raw_input
        if data_type in {"int", "integer"}:
            try:
                return int(raw_input)
            except ValueError as exc:
                raise make_error("PPY-INPUT-001") from exc
        if data_type in {"float", "number", "decimal"}:
            try:
                return float(raw_input)
            except ValueError as exc:
                raise make_error("PPY-INPUT-002") from exc
        if data_type in {"bool", "boolean"}:
            normalized = raw_input.strip().lower()
            if normalized in {"true", "t", "yes", "y", "1"}:
                return True
            if normalized in {"false", "f", "no", "n", "0"}:
                return False
            raise make_error("PPY-INPUT-003")

        raise make_error("PPY-INPUT-004", data_type=data_type_value)
    if t == "neg":
        v = eval_expr(expr["value"], env)
        ensure_number(v, "-")
        return -v

    if t in {"add", "sub", "mul", "div", "eq", "ne", "gt", "lt", "ge", "le", "and", "or"}:
        left = eval_expr(expr["left"], env)
        right = eval_expr(expr["right"], env)

        if t == "add":
            return left + right
        if t == "sub":
            ensure_number(left, "-"); ensure_number(right, "-")
            return left - right
        if t == "mul":
            ensure_number(left, "*"); ensure_number(right, "*")
            return left * right
        if t == "div":
            ensure_number(left, "/"); ensure_number(right, "/")
            return left / right
        if t == "eq":
            return left == right
        if t == "ne":
            return left != right
        if t == "gt":
            return left > right
        if t == "lt":
            return left < right
        if t == "ge":
            return left >= right
        if t == "le":
            return left <= right
        if t == "and":
            return truthy(left) and truthy(right)
        if t == "or":
            return truthy(left) or truthy(right)

    raise make_error("PPY-RUNTIME-005", expr_type=t)
