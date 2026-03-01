# runtime.py
from dataclasses import dataclass, field
from typing import Optional

from ppy_errors import make_error


@dataclass
class Environment:
    values: dict = field(default_factory=dict)
    parent: Optional["Environment"] = None

    def define(self, name: str, value):
        self.values[name] = value

    def assign(self, name: str, value):
        if name in self.values:
            self.values[name] = value
            return
        if self.parent is not None:
            self.parent.assign(name, value)
            return
        raise make_error("PPY-RUNTIME-001", name=name)

    def get(self, name: str):
        if name in self.values:
            return self.values[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise make_error("PPY-RUNTIME-001", name=name)


def truthy(value) -> bool:
    return bool(value)


def ensure_number(value, op: str):
    if not isinstance(value, (int, float)):
        raise make_error("PPY-TYPE-001", op=op, actual_type=type(value).__name__)
