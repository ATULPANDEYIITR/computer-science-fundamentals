from __future__ import annotations

from dataclasses import dataclass
from functools import reduce
from typing import Callable, Iterable, TypeVar

T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")


# Pure function: same inputs always produce the same output and no external
# state is modified.
def calculate_total(prices: tuple[float, ...]) -> float:
    if any(price < 0 for price in prices):
        raise ValueError("Prices cannot be negative.")
    return sum(prices)


# Pure function used as a higher-order function argument.
def apply_discount(total: float, discount_rate: float) -> float:
    if total < 0:
        raise ValueError("Total cannot be negative.")
    if not 0 <= discount_rate <= 1:
        raise ValueError("Discount rate must be between 0 and 1.")
    return round(total * (1 - discount_rate), 2)


# Higher-order function: receives a function and applies it to every value.
def transform(values: Iterable[T], operation: Callable[[T], U]) -> tuple[U, ...]:
    return tuple(operation(value) for value in values)


# Function composition keeps transformations explicit and avoids mutation.
def compose(
    first: Callable[[T], U],
    second: Callable[[U], V],
) -> Callable[[T], V]:
    return lambda value: second(first(value))


@dataclass(frozen=True)
class Order:
    order_id: int
    customer: str
    items: tuple[float, ...]
    discount_rate: float = 0.0

    def subtotal(self) -> float:
        return calculate_total(self.items)

    def total(self) -> float:
        return apply_discount(self.subtotal(), self.discount_rate)


def add_item(order: Order, price: float) -> Order:
    # Frozen dataclasses prevent accidental mutation. A new value is returned.
    if price < 0:
        raise ValueError("Item price cannot be negative.")
    return Order(
        order_id=order.order_id,
        customer=order.customer,
        items=order.items + (price,),
        discount_rate=order.discount_rate,
    )


def update_discount(order: Order, discount_rate: float) -> Order:
    if not 0 <= discount_rate <= 1:
        raise ValueError("Discount rate must be between 0 and 1.")
    return Order(
        order_id=order.order_id,
        customer=order.customer,
        items=order.items,
        discount_rate=discount_rate,
    )


def filter_orders(
    orders: Iterable[Order],
    predicate: Callable[[Order], bool],
) -> tuple[Order, ...]:
    return tuple(filter(predicate, orders))


def map_totals(orders: Iterable[Order]) -> tuple[float, ...]:
    return tuple(map(lambda order: order.total(), orders))


def reduce_total(orders: Iterable[Order]) -> float:
    return reduce(lambda accumulator, order: accumulator + order.total(), orders, 0.0)


def demonstrate_lambda_pipeline(orders: tuple[Order, ...]) -> tuple[float, ...]:
    # The pipeline is composed from pure transformations.
    eligible = filter_orders(
        orders,
        lambda order: order.total() >= 1000,
    )

    discounted_totals = transform(
        eligible,
        lambda order: round(order.total() * 0.95, 2),
    )

    return discounted_totals


def validate_orders(orders: Iterable[Order]) -> None:
    seen_ids: set[int] = set()

    for order in orders:
        if order.order_id <= 0:
            raise ValueError("Order IDs must be positive.")
        if not order.customer.strip():
            raise ValueError("Customer name cannot be empty.")
        if order.order_id in seen_ids:
            raise ValueError(f"Duplicate order ID: {order.order_id}")
        seen_ids.add(order.order_id)

        if not order.items:
            raise ValueError(f"Order {order.order_id} must contain an item.")
        if any(price < 0 for price in order.items):
            raise ValueError(f"Order {order.order_id} contains a negative price.")
        if not 0 <= order.discount_rate <= 1:
            raise ValueError(
                f"Order {order.order_id} has an invalid discount rate."
            )


def main() -> None:
    orders = (
        Order(101, "Acme Ltd", (650.0, 500.0), 0.10),
        Order(102, "Beta Systems", (400.0, 250.0), 0.05),
        Order(103, "Gamma Labs", (1500.0, 750.0), 0.15),
    )

    validate_orders(orders)

    original = orders[0]
    updated = add_item(original, 200.0)
    discounted = update_discount(updated, 0.20)

    print("Functional Programming Order Model")
    print("----------------------------------")
    print(f"Original order:   {original.items}, total={original.total():.2f}")
    print(f"Updated order:    {updated.items}, total={updated.total():.2f}")
    print(f"Discounted order: {discounted.items}, total={discounted.total():.2f}")

    totals = map_totals(orders)
    print(f"\nOrder totals: {totals}")
    print(f"Combined total: {reduce_total(orders):.2f}")

    high_value = filter_orders(
        orders,
        lambda order: order.total() >= 1000,
    )
    print(
        "High-value orders:",
        tuple(order.order_id for order in high_value),
    )

    print(
        "Pipeline result:",
        demonstrate_lambda_pipeline(orders),
    )

    # Explicit function composition.
    tax = lambda amount: round(amount * 1.18, 2)
    service_fee = lambda amount: round(amount + 50.0, 2)
    final_amount = compose(tax, service_fee)

    print(f"Composed transformation: {final_amount(1000.0):.2f}")

    # Demonstrate a failure condition without terminating the program.
    try:
        update_discount(original, 1.5)
    except ValueError as exc:
        print(f"Validation failure handled: {exc}")


if __name__ == "__main__":
    main()
