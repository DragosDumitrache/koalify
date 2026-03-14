"""
Compact DSL for matching criteria against any object with attributes.

Build criteria using field references and Python operators:

    from koalify import F

    rule = (F.status == "active") & (F.age >= 18)
    rule(my_model)  # True / False

Supports: ==  !=  >  >=  <  <=  .in_()  .between()  &  |  ~
Nested fields: F.address.city == "London"
Helpers: all_of(...), any_of(...) for dynamic composition.
"""

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


# ── Composite criteria ───────────────────────────────────────────────


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


# ── Leaf criteria (comparisons) ─────────────────────────────────────


class _Compare(Criterion):
    """Base for field-vs-value comparisons."""

    op: str

    def __init__(self, field: FieldRef, value: Any):
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
    def __init__(self, field: FieldRef, values: set | frozenset | list | tuple):
        self.field = field
        self.values = values

    def match(self, obj: Any) -> bool:
        return self.field.resolve(obj) in self.values

    def __repr__(self) -> str:
        return f"{self.field!r} in {self.values!r}"


class Between(Criterion):
    """Inclusive on both bounds: lower <= value <= upper."""

    def __init__(self, field: FieldRef, lower: Any, upper: Any):
        self.field = field
        self.lower = lower
        self.upper = upper

    def match(self, obj: Any) -> bool:
        return self.lower <= self.field.resolve(obj) <= self.upper

    def __repr__(self) -> str:
        return f"{self.lower!r} <= {self.field!r} <= {self.upper!r}"


# ── Field reference & accessor ──────────────────────────────────────


class FieldRef:
    """
    Reference to one (possibly nested) field on an object.

    Supports Python comparison operators to produce criteria, and
    attribute access for nested fields: F.address.city
    """

    def __init__(self, *path: str):
        self._path = path

    def resolve(self, obj: Any) -> Any:
        value: Any = obj
        for part in self._path:
            value = getattr(value, part)
        return value

    # ── nested access ────────────────────────────────────────────

    def __getattr__(self, name: str) -> FieldRef:
        if name.startswith("_"):
            raise AttributeError(name)
        return FieldRef(*self._path, name)

    # ── comparison operators → criteria ──────────────────────────

    def __eq__(self, value: Any) -> Eq:  # type: ignore[override]
        return Eq(self, value)

    def __ne__(self, value: Any) -> Ne:  # type: ignore[override]
        return Ne(self, value)

    def __gt__(self, value: Any) -> Gt:
        return Gt(self, value)

    def __ge__(self, value: Any) -> Ge:
        return Ge(self, value)

    def __lt__(self, value: Any) -> Lt:
        return Lt(self, value)

    def __le__(self, value: Any) -> Le:
        return Le(self, value)

    # ── set / range predicates ───────────────────────────────────

    def in_(self, values: set | frozenset | list | tuple) -> In:
        return In(self, values)

    def between(self, lower: Any, upper: Any) -> Between:
        return Between(self, lower, upper)

    # ── repr ─────────────────────────────────────────────────────

    def __repr__(self) -> str:
        return ".".join(self._path)

    def __hash__(self) -> int:
        return hash(self._path)


class _FieldAccessor:
    """Singleton entry-point: ``F.field_name`` creates a :class:`FieldRef`."""

    def __getattr__(self, name: str) -> FieldRef:
        return FieldRef(name)


F = _FieldAccessor()
"""Use ``F.field_name`` to reference fields in criteria."""


# ── Convenience constructors ────────────────────────────────────────


def all_of(*criteria: Criterion) -> And:
    """Combine criteria with AND (useful for dynamic / programmatic composition)."""
    return And(*criteria)


def any_of(*criteria: Criterion) -> Or:
    """Combine criteria with OR (useful for dynamic / programmatic composition)."""
    return Or(*criteria)
