from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Generic, TypeVar


# ============================================================
# Scope, binding, lifetime, and type-system demonstrations
# ============================================================

# Scope answers: "Where can this name be used?"
# Binding answers: "What entity does this name refer to?"
# Lifetime answers: "How long does the referenced object/value exist?"
# A type system answers: "What operations are valid for this value?"

MODULE_CONSTANT = "module scope"
counter = 0


def scope_demo() -> None:
    module_name = "module-visible from this function"

    def nested_function() -> None:
        nested_name = "local to nested_function"
        print("Nested scope:", nested_name)
        print("Enclosing scope:", module_name)
        print("Global scope:", MODULE_CONSTANT)

    nested_function()

    # Python resolves an unqualified name through local, enclosing,
    # global, and built-in scopes. This is commonly called LEGB.
    print("Function-local name:", module_name)


def closure_binding_demo() -> None:
    """Show late binding and explicit binding in Python closures."""

    functions_late: list[Callable[[], int]] = []

    for value in range(3):
        # The lambda closes over the variable 'value', not a frozen copy.
        functions_late.append(lambda: value)

    print("Late-bound closures:", [fn() for fn in functions_late])

    functions_early: list[Callable[[], int]] = []

    for value in range(3):
        # A default argument evaluates at function creation time,
        # giving the callable its own bound value.
        functions_early.append(lambda value=value: value)

    print("Explicitly captured values:", [fn() for fn in functions_early])


def global_binding_demo() -> None:
    global counter
    counter += 1
    print("Global binding after mutation:", counter)


def nonlocal_binding_demo() -> Callable[[], int]:
    state = 0

    def increment() -> int:
        nonlocal state
        state += 1
        return state

    return increment


# ============================================================
# Lifetime and resource management
# ============================================================

@dataclass
class Resource:
    name: str

    def __post_init__(self) -> None:
        print(f"Created resource: {self.name}")

    def close(self) -> None:
        print(f"Closed resource: {self.name}")


def lifetime_demo() -> None:
    resource = Resource("temporary-buffer")

    # The object is alive while a reference reaches it.
    alias = resource
    print("Same object through alias:", alias is resource)

    del alias

    # The context manager gives deterministic cleanup for resources.
    class ManagedResource:
        def __enter__(self) -> "ManagedResource":
            print("Acquired managed resource")
            return self

        def __exit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: Any,
        ) -> bool:
            print("Released managed resource")
            return False

    with ManagedResource():
        print("Resource is active inside the managed scope")

    # Reference-counted CPython implementations may destroy objects
    # immediately when their last reference disappears, but portable
    # Python code must not depend on that timing.
    resource.close()


# ============================================================
# Static and dynamic typing
# ============================================================

def dynamic_value_demo() -> None:
    value: Any = 42
    print("Initial runtime type:", type(value).__name__)

    value = "forty-two"
    print("Runtime type after rebinding:", type(value).__name__)

    # Python's type annotation is useful to static analyzers, but
    # the interpreter normally does not reject this reassignment.
    print("Dynamic value:", value)


def type_validation_demo(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("value must be an integer")

    return value * 2


T = TypeVar("T")


class Box(Generic[T]):
    """A generic container whose intended element type is represented by T."""

    def __init__(self, value: T) -> None:
        self.value = value

    def get(self) -> T:
        return self.value


def generic_type_demo() -> None:
    integer_box = Box[int](100)
    text_box = Box[str]("scope")

    print("Generic integer:", integer_box.get())
    print("Generic text:", text_box.get())


# ============================================================
# Structural and nominal behavior
# ============================================================

class Printable:
    def describe(self) -> str:
        raise NotImplementedError


class UserRecord(Printable):
    def __init__(self, user_id: int, name: str) -> None:
        self.user_id = user_id
        self.name = name

    def describe(self) -> str:
        return f"UserRecord(id={self.user_id}, name={self.name})"


def polymorphism_demo() -> None:
    objects: list[Printable] = [UserRecord(101, "Asha"), UserRecord(102, "Ravi")]

    for obj in objects:
        # The common interface determines what the caller may request.
        # Dynamic dispatch selects the implementation at runtime.
        print(obj.describe())


# ============================================================
# Mutable binding versus immutable rebinding
# ============================================================

def mutation_and_rebinding_demo() -> None:
    numbers = [10, 20]

    def mutate(items: list[int]) -> None:
        items.append(30)

    mutate(numbers)
    print("Mutation visible through shared object:", numbers)

    def rebind(items: list[int]) -> None:
        items = [999]
        print("Inside function after rebinding:", items)

    rebind(numbers)
    print("Caller object after rebinding:", numbers)


# ============================================================
# Type-driven dispatch and runtime failure
# ============================================================

def safe_add(left: Any, right: Any) -> Any:
    if type(left) is not type(right):
        raise TypeError(
            f"operands must have identical runtime types: "
            f"{type(left).__name__} and {type(right).__name__}"
        )

    return left + right


def type_system_demo() -> None:
    print("Integer addition:", safe_add(10, 20))
    print("String concatenation:", safe_add("scope", "binding"))

    try:
        safe_add(10, "20")
    except TypeError as exc:
        print("Rejected mixed operation:", exc)

    try:
        type_validation_demo(True)
    except TypeError as exc:
        print("Rejected bool-as-integer policy:", exc)


# ============================================================
# Name shadowing and resolution
# ============================================================

shadowed = "global"


def shadowing_demo() -> None:
    shadowed = "local"

    def nested() -> None:
        shadowed = "nested"
        print("Nested binding:", shadowed)

    nested()
    print("Function binding:", shadowed)
    print("Global binding:", globals()["shadowed"])


# ============================================================
# Dispatch table: data-driven binding
# ============================================================

def operation_table_demo() -> None:
    operations: dict[str, Callable[[int, int], int]] = {
        "add": lambda a, b: a + b,
        "multiply": lambda a, b: a * b,
        "maximum": max,
    }

    for name, operation in operations.items():
        print(f"{name}: {operation(6, 4)}")


# ============================================================
# Main executable demonstration
# ============================================================

def main() -> None:
    print("\n=== Scope ===")
    scope_demo()
    shadowing_demo()

    print("\n=== Binding ===")
    closure_binding_demo()
    global_binding_demo()
    increment = nonlocal_binding_demo()
    print("Nonlocal binding:", increment(), increment())
    operation_table_demo()

    print("\n=== Lifetime ===")
    lifetime_demo()
    mutation_and_rebinding_demo()

    print("\n=== Type systems ===")
    dynamic_value_demo()
    generic_type_demo()
    polymorphism_demo()
    type_system_demo()

    print("\n=== Production considerations ===")
    print(
        "Annotations improve static analysis but do not automatically "
        "turn Python into a statically typed runtime."
    )
    print(
        "Explicit resource-management protocols are safer than relying "
        "on garbage-collection timing for external resources."
    )
    print(
        "Closures should capture values intentionally when loop-variable "
        "late binding could change behavior."
    )


if __name__ == "__main__":
    main()
