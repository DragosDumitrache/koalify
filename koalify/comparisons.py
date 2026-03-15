"""Leaf criteria: field-vs-value comparisons."""

from __future__ import annotations

from typing import Any

from koalify.criteria import Criterion


class _Compare(Criterion):
    """Base for field-vs-value comparisons."""

    op: str

    def __init__(self, field: Any, value: Any):
        self.field = field
        self.value = value

    def __repr__(self) -> str:
        return f"{self.field!r} {self.op} {self.value!r}"


class Eq(_Compare):
    op = "=="

    def match(self, obj: Any) -> bool:
        return self.field.resolve(obj) == self.value


class Ne(_Compare):
    op = "!="

    def match(self, obj: Any) -> bool:
        return self.field.resolve(obj) != self.value


class Gt(_Compare):
    op = ">"

    def match(self, obj: Any) -> bool:
        return self.field.resolve(obj) > self.value


class Ge(_Compare):
    op = ">="

    def match(self, obj: Any) -> bool:
        return self.field.resolve(obj) >= self.value


class Lt(_Compare):
    op = "<"

    def match(self, obj: Any) -> bool:
        return self.field.resolve(obj) < self.value


class Le(_Compare):
    op = "<="

    def match(self, obj: Any) -> bool:
        return self.field.resolve(obj) <= self.value


class In(Criterion):
    def __init__(self, field: Any, values: set | frozenset | list | tuple):
        self.field = field
        self.values = values

    def match(self, obj: Any) -> bool:
        return self.field.resolve(obj) in self.values

    def __repr__(self) -> str:
        return f"{self.field!r} in {self.values!r}"


class Between(Criterion):
    """Inclusive on both bounds: lower <= value <= upper."""

    def __init__(self, field: Any, lower: Any, upper: Any):
        self.field = field
        self.lower = lower
        self.upper = upper

    def match(self, obj: Any) -> bool:
        return self.lower <= self.field.resolve(obj) <= self.upper

    def __repr__(self) -> str:
        return f"{self.lower!r} <= {self.field!r} <= {self.upper!r}"
