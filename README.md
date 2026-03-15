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
    & (F.role.in_("admin", "moderator", "editor"))
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

## Examples

### Dataclasses

```python
from dataclasses import dataclass
from koalify import F, all_of

@dataclass
class Order:
    product: str
    quantity: int
    price: float
    fulfilled: bool

needs_review = (F.quantity > 100) & (F.price >= 500) & (F.fulfilled == False)

order = Order(product="Widget", quantity=200, price=750.0, fulfilled=False)
needs_review(order)  # True
```

### Pydantic

```python
from pydantic import BaseModel
from koalify import F, any_of

class Address(BaseModel):
    city: str
    country: str

class Customer(BaseModel):
    name: str
    tier: str
    address: Address

is_priority = (F.tier.in_("gold", "platinum")) | (F.address.country == "US")

customer = Customer(name="Alice", tier="gold", address=Address(city="London", country="UK"))
is_priority(customer)  # True
```

### Item access (lists, dicts)

```python
from dataclasses import dataclass
from koalify import F

@dataclass
class Event:
    name: str
    tags: list[str]
    metadata: dict[str, str]

event = Event(name="deploy", tags=["prod", "urgent"], metadata={"region": "eu-west-1"})

# List indexing
(F.tags[0] == "prod")(event)  # True

# Dict key access
(F.metadata["region"] == "eu-west-1")(event)  # True

# Mix with attribute access and composition
is_urgent_prod = (F.tags[0] == "prod") & (F.tags[1] == "urgent")
is_urgent_prod(event)  # True
```

### Dynamic rule composition

```python
from koalify import F, all_of

def build_filter(min_age: int | None = None, status: str | None = None, roles: set[str] | None = None):
    criteria = []
    if min_age is not None:
        criteria.append(F.age >= min_age)
    if status is not None:
        criteria.append(F.status == status)
    if roles is not None:
        criteria.append(F.role.in_(*roles))
    return all_of(*criteria) if criteria else lambda _: True

user_filter = build_filter(min_age=18, roles={"admin", "editor"})
```

## API

| Symbol | Description |
|---|---|
| `F.field` | Reference a field (supports nesting: `F.a.b.c` and indexing: `F.a[0]`, `F.a["k"]`) |
| `==  !=  >  >=  <  <=` | Comparison operators on `FieldRef` |
| `.in_(*values)` | Set membership |
| `.between(lo, hi)` | Inclusive range check |
| `&` | AND (flattens nested ANDs) |
| `\|` | OR (flattens nested ORs) |
| `~` | NOT |
| `all_of(*criteria)` | AND from a list |
| `any_of(*criteria)` | OR from a list |

## How It Works

1. `F.field_name` returns a `FieldRef` — a lightweight path descriptor
2. Comparison operators (`==`, `>`, `.in_()`, etc.) produce `Criterion` objects
3. Criteria compose with `&`, `|`, and `~` (flattening nested groups automatically)
4. Calling a criterion resolves field values at runtime via `getattr` and `[]`

Works with dataclasses, Pydantic models, namedtuples, or any object with attributes.
Item access (`F.tags[0]`, `F.data["key"]`) delegates to the resolved value's `__getitem__`, so standard `IndexError` / `KeyError` exceptions propagate naturally.

## License

MIT
