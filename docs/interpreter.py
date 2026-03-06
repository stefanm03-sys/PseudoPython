# interpreter.py
import subprocess
import math
import time
from dataclasses import dataclass

from ppy_errors import make_error
from runtime import Environment, truthy, ensure_number


class _LoopStopSignal(Exception):
    pass


class _LoopRestartSignal(Exception):
    pass


MAX_LOOP_ITERATIONS = 100000


@dataclass
class _UserFunction:
    name: str
    params: list
    body: list
    closure: Environment


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _to_ppy_text(value):
    if value is None:
        return "none"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _ensure_finite_number(value, op: str):
    if _is_number(value):
        if not math.isfinite(float(value)):
            raise make_error("PPY-MATH-002", op=op, value=value)
    return value


def _invoke_function(name: str, arg_exprs: list, env: Environment, loop_depth: int):
    func_value = env.get(name)
    if not isinstance(func_value, _UserFunction):
        raise make_error("PPY-FUNC-002", name=name)

    args = [eval_expr(arg, env) for arg in arg_exprs]
    if len(args) != len(func_value.params):
        raise make_error(
            "PPY-FUNC-003",
            name=func_value.name,
            expected=len(func_value.params),
            actual=len(args),
        )

    local_env = Environment(parent=func_value.closure)
    for param_name, arg_value in zip(func_value.params, args):
        local_env.define(param_name, arg_value)

    for s in func_value.body:
        execute_stmt(s, local_env, loop_depth=loop_depth)


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
    elif t == "wait":
        delay_seconds = eval_wait_delay(stmt["value"], env)
        time.sleep(delay_seconds)
    elif t == "function_def":
        func = _UserFunction(
            name=stmt["name"],
            params=list(stmt.get("params", [])),
            body=list(stmt.get("body", [])),
            closure=env,
        )
        env.define(stmt["name"], func)
    elif t == "call_stmt":
        _invoke_function(stmt["name"], stmt.get("args", []), env, loop_depth)
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
        iterations = 0
        while truthy(eval_expr(stmt["condition"], env)):
            iterations += 1
            if iterations > MAX_LOOP_ITERATIONS:
                raise make_error("PPY-RUNTIME-008", limit=MAX_LOOP_ITERATIONS)
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
        if isinstance(n, float):
            if n.is_integer():
                n = int(n)
            else:
                raise make_error("PPY-TYPE-003", actual_type=type(n).__name__)
        if not isinstance(n, int):
            raise make_error("PPY-TYPE-003", actual_type=type(n).__name__)
        if n < 0:
            raise make_error("PPY-RUNTIME-003", count=n)
        i = 0
        iterations = 0
        while i < n:
            iterations += 1
            if iterations > MAX_LOOP_ITERATIONS:
                raise make_error("PPY-RUNTIME-008", limit=MAX_LOOP_ITERATIONS)
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
        if raw_input.strip() == "":
            return None

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
        return _ensure_finite_number(-v, "-")

    if t in {"add", "sub", "mul", "div", "eq", "ne", "gt", "lt", "ge", "le", "and", "or"}:
        left = eval_expr(expr["left"], env)
        right = eval_expr(expr["right"], env)

        if t == "add":
            if _is_number(left) and _is_number(right):
                return _ensure_finite_number(left + right, "+")
            if isinstance(left, str) or isinstance(right, str):
                return _to_ppy_text(left) + _to_ppy_text(right)
            raise make_error(
                "PPY-TYPE-008",
                op="+",
                left_type=type(left).__name__,
                right_type=type(right).__name__,
            )
        if t == "sub":
            ensure_number(left, "-"); ensure_number(right, "-")
            return _ensure_finite_number(left - right, "-")
        if t == "mul":
            if _is_number(left) and _is_number(right):
                return _ensure_finite_number(left * right, "*")
            if isinstance(left, str) and isinstance(right, int):
                return left * right
            if isinstance(left, int) and isinstance(right, str):
                return left * right
            raise make_error(
                "PPY-TYPE-008",
                op="*",
                left_type=type(left).__name__,
                right_type=type(right).__name__,
            )
        if t == "div":
            ensure_number(left, "/"); ensure_number(right, "/")
            if right == 0:
                raise make_error("PPY-MATH-001", left=left, right=right)
            return _ensure_finite_number(left / right, "/")
        if t == "eq":
            return left == right
        if t == "ne":
            return left != right
        if t == "gt":
            if (_is_number(left) and _is_number(right)) or (isinstance(left, str) and isinstance(right, str)):
                return left > right
            raise make_error(
                "PPY-TYPE-009",
                op=">",
                left_type=type(left).__name__,
                right_type=type(right).__name__,
            )
        if t == "lt":
            if (_is_number(left) and _is_number(right)) or (isinstance(left, str) and isinstance(right, str)):
                return left < right
            raise make_error(
                "PPY-TYPE-009",
                op="<",
                left_type=type(left).__name__,
                right_type=type(right).__name__,
            )
        if t == "ge":
            if (_is_number(left) and _is_number(right)) or (isinstance(left, str) and isinstance(right, str)):
                return left >= right
            raise make_error(
                "PPY-TYPE-009",
                op=">=",
                left_type=type(left).__name__,
                right_type=type(right).__name__,
            )
        if t == "le":
            if (_is_number(left) and _is_number(right)) or (isinstance(left, str) and isinstance(right, str)):
                return left <= right
            raise make_error(
                "PPY-TYPE-009",
                op="<=",
                left_type=type(left).__name__,
                right_type=type(right).__name__,
            )
        if t == "and":
            return right if truthy(left) else left
        if t == "or":
            return left if truthy(left) else right

    raise make_error("PPY-RUNTIME-005", expr_type=t)


def eval_wait_delay(value_expr: dict, env: Environment) -> float:
    if isinstance(value_expr, dict) and value_expr.get("type") == "duration":
        base = float(value_expr["value"])
        unit = value_expr["unit"]
        if unit == "ms":
            seconds = base / 1000.0
        elif unit == "m":
            seconds = base * 60.0
        else:
            seconds = base
    else:
        raw = eval_expr(value_expr, env)
        if not isinstance(raw, (int, float)):
            raise make_error("PPY-TYPE-007", actual_type=type(raw).__name__)
        seconds = float(raw)

    if seconds < 0:
        raise make_error("PPY-TYPE-007", actual_type="negative")
    return seconds
