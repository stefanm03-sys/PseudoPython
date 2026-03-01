from dataclasses import dataclass


ERROR_TEMPLATES = {
    "PPY-CLI-001": "[PPY-CLI-001] Usage: python main.py <file.ppy>",
    "PPY-IO-404": "[PPY-IO-404] File not found! Could be invalid: {path}",
    "PPY-IO-002": "[PPY-IO-002] Input file must end with .ppy! May be invalid: {path}",
    "PPY-PARSE-001": "[PPY-PARSE-001] Syntax error at line {line}, collumn {column}. Check for errors: {detail}",
    "PPY-RUNTIME-001": "[PPY-RUNTIME-001] Undefined variable. Possible error: {name}",
    "PPY-RUNTIME-002": "[PPY-RUNTIME-002] Top-level AST node must be program",
    "PPY-RUNTIME-003": "[PPY-RUNTIME-003] repeat amt(...) cannot be negative. Not possible: {count}",
    "PPY-RUNTIME-004": "[PPY-RUNTIME-004] Unknown statement type. What does this mean: {stmt_type}",
    "PPY-RUNTIME-005": "[PPY-RUNTIME-005] Unknown expression type. I dunno what that is: {expr_type}",
    "PPY-TYPE-001": "[PPY-TYPE-001] Operator '{op}' requires numbers, I got {actual_type}.",
    "PPY-TYPE-002": "[PPY-TYPE-002] execute(...) requires a string command, you gave me {actual_type}",
    "PPY-TYPE-003": "[PPY-TYPE-003] repeat amt(...) requires an integer count. You gave me {actual_type}",
    "PPY-TYPE-004": "[PPY-TYPE-004] ask(prompt, data?) requires prompt to be a string, you gave me {actual_type}",
    "PPY-TYPE-005": "[PPY-TYPE-005] ask(prompt, data?) data parameter must be a string or bare type name, invalid!",
    "PPY-INPUT-001": "[PPY-INPUT-001] ask(..., int) expected an integer value, but got something else: {input}",
    "PPY-INPUT-002": "[PPY-INPUT-002] ask(..., float) expected a decimal value, not an integer or other type",
    "PPY-INPUT-003": "[PPY-INPUT-003] ask(..., bool) expected true/false boolean input, didn't get that: {input}",
    "PPY-INPUT-004": "[PPY-INPUT-004] Unknown ask data type '{data_type}'. Use text, int, float, or bool.",
    "PPY-EXEC-001": "[PPY-EXEC-001] execute(...) command failed, try again or change code. (exit {return_code}): {command}",
    "PPY-INTERNAL-001": "[PPY-INTERNAL-001] Internal error: {detail}",
}


@dataclass
class PseudoPyError(Exception):
    code: str
    message: str

    def __str__(self) -> str:
        return self.message


def set_error_template(code: str, template: str) -> None:
    ERROR_TEMPLATES[code] = template


def make_error(code: str, **context) -> PseudoPyError:
    template = ERROR_TEMPLATES.get(code, f"[{code}] " + "{detail}")
    try:
        message = template.format(**context)
    except Exception:
        # Fallback if a template is customized with missing placeholders.
        message = f"[{code}] {context}"
    return PseudoPyError(code=code, message=message)
