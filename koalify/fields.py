"""Field reference and accessor — the ``F.field_name`` entry point."""

from __future__ import annotations

from typing import Any

from koalify.comparisons import Between, Eq, Ge, Gt, In, Le, Lt, Ne


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

    def __eq__(self, value: Any) -> Eq:
        return Eq(self, value)

    def __ne__(self, value: Any) -> Ne:
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
