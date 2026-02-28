# main.py
from pathlib import Path
import sys

from lexer import tokenize
from parser import parse
from interpreter import interpret
from ppy_errors import PseudoPyError, make_error


def main() -> int:
    try:
        if len(sys.argv) != 2:
            raise make_error("PPY-CLI-001")

        file_path = Path(sys.argv[1])

        if not file_path.exists():
            raise make_error("PPY-IO-404", path=file_path)

        if file_path.suffix != ".ppy":
            raise make_error("PPY-IO-002", path=file_path)

        source = file_path.read_text(encoding="utf-8")
        tokens = tokenize(source)
        ast = parse(tokens)
        interpret(ast)
        return 0
    except PseudoPyError as exc:
        print(exc)
        return 1
    except Exception as exc:
        print(make_error("PPY-INTERNAL-001", detail=str(exc)))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
