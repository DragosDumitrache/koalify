# koalify

A compact predicate DSL for matching criteria against any Python object. Zero runtime dependencies.

## Installation

```bash
pip install koalify
```

## Quick Start

```python
from koalify import F, all_of, any_of

# Build rules with Python operators
is_eligible = (
    (F.status == "active")
    & (F.age >= 18)
    & (F.role.in_({"admin", "moderator", "editor"}))
    & F.score.between(50, 100)
)

# Evaluate against any object with attributes
is_eligible(user)  # True / False

# Nested fields
lives_in_london = F.address.city == "London"

# Compose with OR / NOT
can_access = is_eligible | (lives_in_london & ~(F.status == "banned"))

# Dynamic composition from a list
conditions = [F.status == "active", F.age >= 18]
rule = all_of(*conditions)
```

## API

| Symbol | Description |
|---|---|
| `F.field` | Reference a field (supports nesting: `F.a.b.c`) |
| `==  !=  >  >=  <  <=` | Comparison operators on `FieldRef` |
| `.in_(values)` | Set membership |
| `.between(lo, hi)` | Inclusive range check |
| `&` | AND (flattens nested ANDs) |
| `\|` | OR (flattens nested ORs) |
| `~` | NOT |
| `all_of(*criteria)` | AND from a list |
| `any_of(*criteria)` | OR from a list |

## How It Works

`F.field_name` returns a `FieldRef`. Comparison operators on `FieldRef` produce `Criterion` objects. Criteria compose with `&`, `|`, and `~`. Calling a criterion resolves field values via `getattr` — works with dataclasses, Pydantic models, namedtuples, or any object with attributes.

## License

MIT
