"""Base criterion type and composite operators (AND, OR, NOT)."""

from __future__ import annotations

from typing import Any


class Criterion:
    """A composable predicate that can be evaluated against any object with attributes."""

    def match(self, obj: Any) -> bool:
        raise NotImplementedError

    def __call__(self, obj: Any) -> bool:
        return self.match(obj)

    def __and__(self, other: Criterion) -> Criterion:
        left = self.criteria if isinstance(self, And) else (self,)
        right = other.criteria if isinstance(other, And) else (other,)
        return And(*left, *right)

    def __or__(self, other: Criterion) -> Criterion:
        left = self.criteria if isinstance(self, Or) else (self,)
        right = other.criteria if isinstance(other, Or) else (other,)
        return Or(*left, *right)

    def __invert__(self) -> Not:
        return Not(self)


class And(Criterion):
    def __init__(self, *criteria: Criterion):
        self.criteria = criteria

    def match(self, obj: Any) -> bool:
        return all(c.match(obj) for c in self.criteria)

    def __repr__(self) -> str:
        return f"({' & '.join(repr(c) for c in self.criteria)})"


class Or(Criterion):
    def __init__(self, *criteria: Criterion):
        self.criteria = criteria

    def match(self, obj: Any) -> bool:
        return any(c.match(obj) for c in self.criteria)

    def __repr__(self) -> str:
        return f"({' | '.join(repr(c) for c in self.criteria)})"


class Not(Criterion):
    def __init__(self, criterion: Criterion):
        self.criterion = criterion

    def match(self, obj: Any) -> bool:
        return not self.criterion.match(obj)

    def __repr__(self) -> str:
        return f"~{self.criterion!r}"


def all_of(*criteria: Criterion) -> And:
    """Combine criteria with AND (useful for dynamic / programmatic composition)."""
    return And(*criteria)


def any_of(*criteria: Criterion) -> Or:
    """Combine criteria with OR (useful for dynamic / programmatic composition)."""
    return Or(*criteria)
