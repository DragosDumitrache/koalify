import pytest
from pydantic import BaseModel

from koalify import F, all_of, any_of, And, Or


# ── Fixtures ────────────────────────────────────────────────────────


class Address(BaseModel):
    city: str
    zip_code: str


class User(BaseModel):
    name: str
    age: int
    status: str
    role: str
    score: float
    address: Address
    tags: list[str] = []


@pytest.fixture
def alice() -> User:
    return User(
        name="Alice",
        age=30,
        status="active",
        role="admin",
        score=92.5,
        address=Address(city="London", zip_code="EC1A"),
        tags=["vip", "beta"],
    )


@pytest.fixture
def bob() -> User:
    return User(
        name="Bob",
        age=17,
        status="inactive",
        role="viewer",
        score=45.0,
        address=Address(city="Paris", zip_code="75001"),
    )


# ── Equality ────────────────────────────────────────────────────────


class TestEquality:
    def test_eq_match(self, alice: User):
        assert (F.status == "active")(alice)

    def test_eq_no_match(self, bob: User):
        assert not (F.status == "active")(bob)

    def test_ne_match(self, bob: User):
        assert (F.status != "active")(bob)

    def test_ne_no_match(self, alice: User):
        assert not (F.status != "active")(alice)


# ── Numeric comparisons ────────────────────────────────────────────


class TestNumericComparisons:
    def test_gt(self, alice: User):
        assert (F.age > 18)(alice)
        assert not (F.age > 18)(User(**{**alice.model_dump(), "age": 18}))

    def test_ge(self, alice: User):
        assert (F.age >= 30)(alice)
        assert not (F.age >= 31)(alice)

    def test_lt(self, bob: User):
        assert (F.age < 18)(bob)
        assert not (F.age < 17)(bob)

    def test_le(self, bob: User):
        assert (F.age <= 17)(bob)
        assert not (F.age <= 16)(bob)


# ── Set inclusion ───────────────────────────────────────────────────


class TestSetInclusion:
    def test_in_set(self, alice: User):
        assert F.role.in_({"admin", "moderator"})(alice)

    def test_in_list(self, alice: User):
        assert F.role.in_(["admin", "moderator"])(alice)

    def test_not_in(self, bob: User):
        assert not F.role.in_({"admin", "moderator"})(bob)


# ── Between (inclusive) ─────────────────────────────────────────────


class TestBetween:
    def test_within_range(self, alice: User):
        assert F.score.between(80, 100)(alice)

    def test_at_lower_bound(self, alice: User):
        user = User(**{**alice.model_dump(), "score": 80.0})
        assert F.score.between(80, 100)(user)

    def test_at_upper_bound(self, alice: User):
        user = User(**{**alice.model_dump(), "score": 100.0})
        assert F.score.between(80, 100)(user)

    def test_outside_range(self, bob: User):
        assert not F.score.between(80, 100)(bob)


# ── Composite: AND / OR / NOT ───────────────────────────────────────


class TestComposite:
    def test_and(self, alice: User):
        rule = (F.status == "active") & (F.age >= 18)
        assert rule(alice)

    def test_and_fails_on_one(self, bob: User):
        rule = (F.status == "active") & (F.age >= 18)
        assert not rule(bob)

    def test_or(self, bob: User):
        rule = (F.status == "active") | (F.age < 18)
        assert rule(bob)

    def test_or_fails_all(self, bob: User):
        rule = (F.status == "active") | (F.age > 18)
        assert not rule(bob)

    def test_not(self, bob: User):
        rule = ~(F.status == "active")
        assert rule(bob)

    def test_not_negates_true(self, alice: User):
        rule = ~(F.status == "active")
        assert not rule(alice)

    def test_complex_composition(self, alice: User, bob: User):
        """(active AND adult) OR (admin with high score)"""
        rule = ((F.status == "active") & (F.age >= 18)) | (
            (F.role == "admin") & F.score.between(90, 100)
        )
        assert rule(alice)
        assert not rule(bob)


# ── Flattening ──────────────────────────────────────────────────────


class TestFlattening:
    def test_and_flattens(self):
        rule = (F.a == 1) & (F.b == 2) & (F.c == 3)
        assert isinstance(rule, And)
        assert len(rule.criteria) == 3

    def test_or_flattens(self):
        rule = (F.a == 1) | (F.b == 2) | (F.c == 3)
        assert isinstance(rule, Or)
        assert len(rule.criteria) == 3


# ── Nested field access ────────────────────────────────────────────


class TestNestedFields:
    def test_nested_eq(self, alice: User):
        assert (F.address.city == "London")(alice)

    def test_nested_ne(self, alice: User):
        assert not (F.address.city == "Paris")(alice)

    def test_two_levels(self, alice: User, bob: User):
        rule = (F.address.city == "London") & (F.status == "active")
        assert rule(alice)
        assert not rule(bob)


# ── Convenience helpers ─────────────────────────────────────────────


class TestHelpers:
    def test_all_of(self, alice: User):
        rule = all_of(F.status == "active", F.age >= 18, F.role == "admin")
        assert rule(alice)

    def test_all_of_fails(self, bob: User):
        rule = all_of(F.status == "active", F.age >= 18)
        assert not rule(bob)

    def test_any_of(self, bob: User):
        rule = any_of(F.status == "active", F.age < 18)
        assert rule(bob)

    def test_any_of_fails(self, bob: User):
        rule = any_of(F.status == "active", F.age > 18)
        assert not rule(bob)

    def test_dynamic_composition(self, alice: User):
        """Build criteria from a list at runtime."""
        conditions = [F.status == "active", F.age >= 18]
        if alice.role == "admin":
            conditions.append(F.score.between(90, 100))
        rule = all_of(*conditions)
        assert rule(alice)


# ── Repr ────────────────────────────────────────────────────────────


class TestRepr:
    def test_simple_eq(self):
        assert repr(F.status == "active") == "status == 'active'"

    def test_nested_field(self):
        assert repr(F.address.city == "London") == "address.city == 'London'"

    def test_between(self):
        assert repr(F.score.between(80, 100)) == "80 <= score <= 100"

    def test_in(self):
        r = repr(F.role.in_(["a", "b"]))
        assert "role in" in r

    def test_and_repr(self):
        r = repr((F.a == 1) & (F.b == 2))
        assert "&" in r

    def test_or_repr(self):
        r = repr((F.a == 1) | (F.b == 2))
        assert "|" in r

    def test_not_repr(self):
        r = repr(~(F.a == 1))
        assert r.startswith("~")


# ── Edge cases ──────────────────────────────────────────────────────


class TestEdgeCases:
    def test_missing_field_raises(self, alice: User):
        with pytest.raises(AttributeError):
            (F.nonexistent == "x")(alice)

    def test_callable_interface(self, alice: User):
        """Criteria are callable — same as .match()"""
        rule = F.status == "active"
        assert rule(alice) == rule.match(alice)

    def test_single_criterion_all_of(self, alice: User):
        rule = all_of(F.status == "active")
        assert rule(alice)

    def test_double_negation(self, alice: User):
        rule = ~~(F.status == "active")
        assert rule(alice)


# ── Complex expression ──────────────────────────────────────────────


class TestComplexExpression:
    """
    Realistic policy rule mixing AND, OR, NOT, nested fields, set inclusion,
    numeric comparisons, and between — 10+ predicates deep.

    Policy:
        Grant access when ALL of:
          1. status is "active"
          2. age >= 18
          3. score between 50 and 100
          4. role is one of {admin, moderator, editor}
          5. name is NOT "root"
          6. city is London OR zip_code starts with "EC"  (nested OR)
        OR as a fallback:
          7. role == "superadmin"
          8. score > 95
          9. status != "banned"
         10. age < 65
    """

    POLICY = (
        (F.status == "active")
        & (F.age >= 18)
        & F.score.between(50, 100)
        & F.role.in_({"admin", "moderator", "editor"})
        & ~(F.name == "root")
        & ((F.address.city == "London") | (F.address.zip_code == "EC1A"))
    ) | (
        (F.role == "superadmin")
        & (F.score > 95)
        & (F.status != "banned")
        & (F.age < 65)
    )

    def _user(self, **overrides) -> User:
        defaults = dict(
            name="Alice",
            age=30,
            status="active",
            role="admin",
            score=92.5,
            address=Address(city="London", zip_code="EC1A"),
            tags=["vip"],
        )
        defaults.update(overrides)
        return User(**defaults)

    def test_full_match_primary_branch(self):
        assert self.POLICY(self._user())

    def test_inactive_status_fails_primary(self):
        assert not self.POLICY(self._user(status="inactive", role="viewer"))

    def test_underage_fails_primary(self):
        assert not self.POLICY(self._user(age=16, role="viewer"))

    def test_low_score_fails_primary(self):
        assert not self.POLICY(self._user(score=30.0, role="viewer"))

    def test_wrong_role_fails_primary(self):
        assert not self.POLICY(self._user(role="viewer"))

    def test_name_root_blocked(self):
        assert not self.POLICY(self._user(name="root", role="viewer"))

    def test_wrong_city_but_right_zip_passes(self):
        addr = Address(city="Manchester", zip_code="EC1A")
        assert self.POLICY(self._user(address=addr))

    def test_right_city_wrong_zip_passes(self):
        addr = Address(city="London", zip_code="W1A")
        assert self.POLICY(self._user(address=addr))

    def test_wrong_city_and_zip_fails(self):
        addr = Address(city="Paris", zip_code="75001")
        assert not self.POLICY(self._user(address=addr, role="viewer"))

    def test_fallback_superadmin_grants_access(self):
        assert self.POLICY(
            self._user(
                status="inactive",
                role="superadmin",
                score=99.0,
                age=40,
                address=Address(city="Nowhere", zip_code="00000"),
            )
        )

    def test_fallback_fails_when_banned(self):
        assert not self.POLICY(
            self._user(status="banned", role="superadmin", score=99.0, age=40)
        )

    def test_fallback_fails_when_score_too_low(self):
        assert not self.POLICY(
            self._user(status="ok", role="superadmin", score=80.0, age=40)
        )

    def test_fallback_fails_when_too_old(self):
        assert not self.POLICY(
            self._user(status="ok", role="superadmin", score=99.0, age=70)
        )
