from __future__ import annotations

import heapq
import json
import math
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class GreedyError(ValueError):
    """Raised when an input violates an algorithm's requirements."""


class Strategy(Enum):
    EARLIEST_FINISH = "earliest_finish"
    HIGHEST_RATIO = "highest_value_weight_ratio"


@dataclass(frozen=True)
class Activity:
    activity_id: str
    start: int
    finish: int

    def __post_init__(self):
        if not self.activity_id:
            raise GreedyError("Activity ID cannot be empty.")
        if self.start < 0:
            raise GreedyError("Activity start cannot be negative.")
        if self.finish <= self.start:
            raise GreedyError("Activity finish must exceed start.")


@dataclass(frozen=True)
class SelectionResult:
    selected: tuple[Activity, ...]
    rejected: tuple[Activity, ...]

    @property
    def count(self) -> int:
        return len(self.selected)


@dataclass(frozen=True)
class Item:
    item_id: str
    value: float
    weight: float

    def __post_init__(self):
        if not self.item_id:
            raise GreedyError("Item ID cannot be empty.")
        if not math.isfinite(self.value) or self.value < 0:
            raise GreedyError("Value must be finite and nonnegative.")
        if not math.isfinite(self.weight) or self.weight <= 0:
            raise GreedyError("Weight must be finite and positive.")


@dataclass
class HuffmanNode:
    frequency: int
    symbol: Optional[str] = None
    left: Optional["HuffmanNode"] = None
    right: Optional["HuffmanNode"] = None


class ActivitySelector:
    """Select the maximum number of compatible activities."""

    @staticmethod
    def select(activities: list[Activity]) -> SelectionResult:
        if len({a.activity_id for a in activities}) != len(activities):
            raise GreedyError("Activity IDs must be unique.")

        # Earliest finishing time leaves maximum room for future activities.
        ordered = sorted(
            activities,
            key=lambda a: (a.finish, a.start, a.activity_id)
        )

        selected = []
        rejected = []
        last_finish = -1

        for activity in ordered:
            if activity.start >= last_finish:
                selected.append(activity)
                last_finish = activity.finish
            else:
                rejected.append(activity)

        return SelectionResult(tuple(selected), tuple(rejected))


class FractionalKnapsack:
    """Maximize value when fractions of items are permitted."""

    @staticmethod
    def solve(items: list[Item], capacity: float) -> dict:
        if not math.isfinite(capacity) or capacity < 0:
            raise GreedyError("Capacity must be finite and nonnegative.")

        if len({item.item_id for item in items}) != len(items):
            raise GreedyError("Item IDs must be unique.")

        ordered = sorted(
            items,
            key=lambda item: (
                -(item.value / item.weight),
                item.item_id
            )
        )

        remaining = capacity
        total_value = 0.0
        selected = []

        for item in ordered:
            if remaining <= 0:
                break

            quantity = min(1.0, remaining / item.weight)

            if quantity <= 0:
                continue

            contribution = quantity * item.value

            selected.append({
                "item_id": item.item_id,
                "fraction": round(quantity, 6),
                "value": round(contribution, 6),
                "weight": round(quantity * item.weight, 6)
            })

            total_value += contribution
            remaining -= quantity * item.weight

        return {
            "selected": selected,
            "total_value": round(total_value, 6),
            "used_capacity": round(capacity - remaining, 6),
            "remaining_capacity": round(max(0.0, remaining), 6)
        }


class HuffmanCoding:
    """Build an optimal prefix-free binary code for known frequencies."""

    def __init__(self, frequencies: dict[str, int]):
        if not frequencies:
            raise GreedyError("Frequency table cannot be empty.")

        for symbol, frequency in frequencies.items():
            if not isinstance(symbol, str) or len(symbol) != 1:
                raise GreedyError("Each symbol must be one character.")
            if not isinstance(frequency, int) or isinstance(frequency, bool):
                raise GreedyError("Frequencies must be integers.")
            if frequency <= 0:
                raise GreedyError("Frequencies must be positive.")

        self.frequencies = dict(frequencies)
        self.root = self._build_tree()
        self.codes: dict[str, str] = {}
        self._generate_codes(self.root, "")

    def _build_tree(self) -> HuffmanNode:
        # The serial number makes equal-frequency choices deterministic.
        heap = []
        serial = 0

        for symbol, frequency in sorted(self.frequencies.items()):
            node = HuffmanNode(frequency, symbol)
            heapq.heappush(heap, (frequency, serial, node))
            serial += 1

        while len(heap) > 1:
            freq1, _, left = heapq.heappop(heap)
            freq2, _, right = heapq.heappop(heap)

            parent = HuffmanNode(freq1 + freq2, None, left, right)
            heapq.heappush(heap, (parent.frequency, serial, parent))
            serial += 1

        return heap[0][2]

    def _generate_codes(self, node: HuffmanNode, prefix: str):
        if node.symbol is not None:
            # A single-symbol alphabet still needs a usable codeword.
            self.codes[node.symbol] = prefix or "0"
            return

        if node.left is not None:
            self._generate_codes(node.left, prefix + "0")

        if node.right is not None:
            self._generate_codes(node.right, prefix + "1")

    def encode(self, text: str) -> str:
        if not isinstance(text, str):
            raise GreedyError("Input must be a string.")

        unknown = set(text) - self.codes.keys()

        if unknown:
            raise GreedyError(
                f"Unknown symbols: {sorted(unknown)}"
            )

        return "".join(self.codes[character] for character in text)

    def decode(self, encoded: str) -> str:
        if not isinstance(encoded, str):
            raise GreedyError("Encoded data must be a string.")

        if any(bit not in "01" for bit in encoded):
            raise GreedyError("Encoded data must contain only binary digits.")

        if self.root.symbol is not None:
            if encoded != "0" * len(encoded):
                raise GreedyError("Invalid single-symbol encoding.")
            return self.root.symbol * len(encoded)

        result = []
        node = self.root

        for bit in encoded:
            node = node.left if bit == "0" else node.right

            if node is None:
                raise GreedyError("Invalid encoded sequence.")

            if node.symbol is not None:
                result.append(node.symbol)
                node = self.root

        if node is not self.root:
            raise GreedyError("Incomplete Huffman codeword.")

        return "".join(result)

    def weighted_path_length(self) -> int:
        return sum(
            self.frequencies[symbol] * len(code)
            for symbol, code in self.codes.items()
        )

    def compression_report(self, original_text: str) -> dict:
        encoded = self.encode(original_text)
        original_bits = len(original_text) * 8

        return {
            "original_characters": len(original_text),
            "original_bits_assuming_ascii": original_bits,
            "encoded_bits": len(encoded),
            "codes": dict(sorted(self.codes.items())),
            "weighted_path_length": self.weighted_path_length(),
            "bit_savings": original_bits - len(encoded),
            "compression_ratio": (
                round(len(encoded) / original_bits, 4)
                if original_bits else 0.0
            )
        }


def greedy_choice_property() -> dict:
    """Demonstrate why locally optimal choices need structural justification."""

    # Earliest finish time is optimal for unweighted interval scheduling.
    activities = [
        Activity("A", 1, 4),
        Activity("B", 3, 5),
        Activity("C", 0, 6),
        Activity("D", 5, 7),
        Activity("E", 8, 9),
        Activity("F", 5, 9),
        Activity("G", 2, 3),
    ]

    result = ActivitySelector.select(activities)

    # Greedy by highest immediate value fails for 0/1 knapsack.
    knapsack_items = [
        Item("A", 60, 10),
        Item("B", 100, 20),
        Item("C", 120, 30)
    ]

    capacity = 50

    ratio_order = sorted(
        knapsack_items,
        key=lambda x: -(x.value / x.weight)
    )

    greedy_value = 0.0
    remaining = capacity

    for item in ratio_order:
        if item.weight <= remaining:
            greedy_value += item.value
            remaining -= item.weight

    # Dynamic programming provides the exact 0/1 optimum.
    dp = [0] * (capacity + 1)

    for item in knapsack_items:
        for weight in range(capacity, int(item.weight) - 1, -1):
            dp[weight] = max(
                dp[weight],
                dp[weight - int(item.weight)] + int(item.value)
            )

    return {
        "activity_selection": {
            "selected": [a.activity_id for a in result.selected],
            "rejected": [a.activity_id for a in result.rejected],
            "count": result.count
        },
        "zero_one_knapsack": {
            "greedy_ratio_value": greedy_value,
            "optimal_dynamic_programming_value": dp[capacity],
            "greedy_is_optimal": greedy_value == dp[capacity]
        }
    }


def run_tests():
    selector = ActivitySelector()

    result = selector.select([
        Activity("A", 1, 3),
        Activity("B", 3, 5),
        Activity("C", 2, 4)
    ])

    assert [a.activity_id for a in result.selected] == ["A", "B"]
    assert result.count == 2

    assert selector.select([]).count == 0

    fractional = FractionalKnapsack.solve(
        [
            Item("A", 60, 10),
            Item("B", 100, 20),
            Item("C", 120, 30)
        ],
        50
    )

    assert fractional["total_value"] == 240.0

    coder = HuffmanCoding({
        "a": 45,
        "b": 13,
        "c": 12,
        "d": 16,
        "e": 9,
        "f": 5
    })

    message = "abcdef"
    encoded = coder.encode(message)

    assert coder.decode(encoded) == message

    single = HuffmanCoding({"x": 10})
    assert single.decode(single.encode("xxxxx")) == "xxxxx"

    try:
        coder.encode("z")
        raise AssertionError("Unknown symbol should fail.")
    except GreedyError:
        pass

    try:
        coder.decode("102")
        raise AssertionError("Invalid binary input should fail.")
    except GreedyError:
        pass

    try:
        Activity("INVALID", 5, 5)
        raise AssertionError("Invalid interval should fail.")
    except GreedyError:
        pass

    print("All tests passed.")


def main():
    run_tests()

    activities = [
        Activity("A101", 1, 4),
        Activity("A102", 3, 5),
        Activity("A103", 0, 6),
        Activity("A104", 5, 7),
        Activity("A105", 8, 9),
        Activity("A106", 5, 9),
        Activity("A107", 2, 3)
    ]

    selection = ActivitySelector.select(activities)

    items = [
        Item("Gold", 60, 10),
        Item("Silver", 100, 20),
        Item("Copper", 120, 30)
    ]

    fractional = FractionalKnapsack.solve(items, 50)

    text = "greedy algorithms demonstrate efficient optimization"
    frequencies = dict(Counter(text))
    huffman = HuffmanCoding(frequencies)

    encoded = huffman.encode(text)

    report = {
        "activity_selection": {
            "selected": [
                {
                    "id": a.activity_id,
                    "start": a.start,
                    "finish": a.finish
                }
                for a in selection.selected
            ],
            "maximum_compatible_activities": selection.count
        },
        "fractional_knapsack": fractional,
        "huffman_coding": {
            **huffman.compression_report(text),
            "round_trip_verified": huffman.decode(encoded) == text
        },
        "greedy_choice_analysis": greedy_choice_property()
    }

    print(json.dumps(report, indent=2, ensure_ascii=False))

    # Optional report persistence.
    output = Path("greedy_algorithm_report.json")
    output.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8"
    )

    print(f"\nReport saved to: {output.resolve()}")


if __name__ == "__main__":
    main()
