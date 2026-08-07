# Testing Patterns

## Arrange-Act-Assert

```python
def test_create_user():
    # arrange
    repo = InMemoryUserRepo()
    svc = UserService(repo)
    # act
    user = svc.register(email="a@b.com", password="secret123")
    # assert
    assert user.email == "a@b.com"
    assert repo.get(user.id) is not None
```

## Given-When-Then names

`test_given_expired_code_when_checkout_then_400`

## Integration test (HTTP)

```python
def test_create_order_api(client):
    r = client.post("/v1/orders", json={"items": [{"sku": "A", "qty": 1}]})
    assert r.status_code == 201
    assert r.json()["id"].startswith("ord_")
```

## Contract test sketch

Assert API responses match schema (pydantic/zod/openapi) on fixture payloads.

## Property-based

```python
from hypothesis import given, strategies as st

@given(st.integers(min_value=0, max_value=10_000))
def test_discount_never_negative(price):
    assert apply_discount(price, 100) >= 0
```

## Seeding

Fixed seed data builders (`UserFactory`) beat anonymous dicts scattered everywhere.

## Temporary files / dirs

Use `tmp_path` / `tempfile` — never write into the repo tree.
