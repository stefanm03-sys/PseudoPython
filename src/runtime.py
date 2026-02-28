# runtime.py
from dataclasses import dataclass, field

from ppy_errors import make_error


@dataclass
class Environment:
    values: dict = field(default_factory=dict)

    def define(self, name: str, value):
        self.values[name] = value

    def assign(self, name: str, value):
        if name not in self.values:
            raise make_error("PPY-RUNTIME-001", name=name)
        self.values[name] = value

    def get(self, name: str):
        if name not in self.values:
            raise make_error("PPY-RUNTIME-001", name=name)
        return self.values[name]


def truthy(value) -> bool:
    return bool(value)


def ensure_number(value, op: str):
    if not isinstance(value, (int, float)):
        raise make_error("PPY-TYPE-001", op=op, actual_type=type(value).__name__)
