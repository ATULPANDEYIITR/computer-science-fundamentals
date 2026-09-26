#!/usr/bin/env python3
"""
Computer Performance: Clock Speed, CPI, IPC, Latency, Throughput, and Benchmarks

A self-contained study and demonstration program covering:
- Clock frequency and clock cycles
- CPU execution time
- CPI and IPC
- Latency and throughput
- Amdahl's Law
- Benchmark design and measurement
- Synthetic benchmark simulation
- Instruction mix analysis
- Pipeline intuition
- Cache/memory effects
- Variability and statistical summaries
- Performance comparisons
- Common measurement mistakes
- Practical performance engineering

The examples use only the Python standard library.
"""

from __future__ import annotations

import math
import random
import statistics
import time
from dataclasses import dataclass
from typing import Callable, Iterable, Sequence


# ---------------------------------------------------------------------------
# 1. FUNDAMENTAL PERFORMANCE QUANTITIES
# ---------------------------------------------------------------------------

def seconds_from_cycles(cycles: float, frequency_hz: float) -> float:
    """Convert a number of clock cycles into execution time."""
    if cycles < 0:
        raise ValueError("cycles cannot be negative")
    if frequency_hz <= 0:
        raise ValueError("frequency must be positive")
    return cycles / frequency_hz


def cycles_from_seconds(seconds: float, frequency_hz: float) -> float:
    """Convert execution time into clock cycles."""
    if seconds < 0:
        raise ValueError("seconds cannot be negative")
    if frequency_hz <= 0:
        raise ValueError("frequency must be positive")
    return seconds * frequency_hz


def execution_time(
    instruction_count: float,
    cpi: float,
    frequency_hz: float,
) -> float:
    """
    CPU execution time:

        CPU time = Instruction Count × CPI / Clock Rate

    This simplified model assumes one effective average CPI.
    """
    if instruction_count < 0:
        raise ValueError("instruction count cannot be negative")
    if cpi <= 0:
        raise ValueError("CPI must be positive")
    if frequency_hz <= 0:
        raise ValueError("clock rate must be positive")

    return instruction_count * cpi / frequency_hz


def average_cpi(
    instruction_counts: Sequence[int | float],
    cpis: Sequence[int | float],
) -> float:
    """
    Weighted average CPI.

    Average CPI is not normally the simple arithmetic mean of the
    instruction-class CPIs. It should be weighted by how many instructions
    of each class execute.
    """
    if len(instruction_counts) != len(cpis) or not instruction_counts:
        raise ValueError("instruction counts and CPIs must have equal nonzero length")

    total_instructions = sum(instruction_counts)
    if total_instructions <= 0:
        raise ValueError("total instruction count must be positive")

    if any(count < 0 for count in instruction_counts):
        raise ValueError("instruction counts cannot be negative")
    if any(cpi <= 0 for cpi in cpis):
        raise ValueError("each CPI must be positive")

    total_cycles = sum(count * cpi for count, cpi in zip(instruction_counts, cpis))
    return total_cycles / total_instructions


def ipc_from_cpi(cpi: float) -> float:
    """
    IPC = Instructions Per Cycle.

    For a simple single-stream model, IPC is approximately 1/CPI.
    Real superscalar processors can have IPC above 1, so IPC = 1/CPI
    should not be blindly applied to every modern CPU measurement.
    """
    if cpi <= 0:
        raise ValueError("CPI must be positive")
    return 1.0 / cpi


def cycles_per_second(frequency_hz: float) -> float:
    """A clock of N Hz has N clock cycles per second."""
    if frequency_hz <= 0:
        raise ValueError("frequency must be positive")
    return frequency_hz


# ---------------------------------------------------------------------------
# 2. UNIT CONVERSION
# ---------------------------------------------------------------------------

def format_frequency(hz: float) -> str:
    """Human-readable frequency."""
    if hz >= 1e9:
        return f"{hz / 1e9:.3f} GHz"
    if hz >= 1e6:
        return f"{hz / 1e6:.3f} MHz"
    if hz >= 1e3:
        return f"{hz / 1e3:.3f} kHz"
    return f"{hz:.3f} Hz"


def format_time(seconds: float) -> str:
    """Human-readable time with appropriate units."""
    if seconds < 1e-6:
        return f"{seconds * 1e9:.3f} ns"
    if seconds < 1e-3:
        return f"{seconds * 1e6:.3f} µs"
    if seconds < 1:
        return f"{seconds * 1e3:.3f} ms"
    return f"{seconds:.3f} s"


# ---------------------------------------------------------------------------
# 3. INSTRUCTION MIX MODEL
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class InstructionClass:
    name: str
    count: int
    cpi: float


def analyze_instruction_mix(classes: Sequence[InstructionClass]) -> dict[str, float]:
    """Calculate instruction count, cycles, weighted CPI, and IPC."""
    if not classes:
        raise ValueError("at least one instruction class is required")

    total_instructions = sum(item.count for item in classes)
    total_cycles = sum(item.count * item.cpi for item in classes)

    if total_instructions <= 0:
        raise ValueError("total instructions must be positive")

    return {
        "instructions": float(total_instructions),
        "cycles": float(total_cycles),
        "average_cpi": total_cycles / total_instructions,
        "simple_ipc": total_instructions / total_cycles,
    }


# ---------------------------------------------------------------------------
# 4. LATENCY VERSUS THROUGHPUT
# ---------------------------------------------------------------------------

def sequential_completion_time(
    jobs: int,
    latency_seconds: float,
) -> float:
    """
    If every job must wait for the previous job to finish,
    total time = jobs × latency.
    """
    if jobs < 0:
        raise ValueError("jobs cannot be negative")
    if latency_seconds < 0:
        raise ValueError("latency cannot be negative")
    return jobs * latency_seconds


def pipelined_completion_time(
    jobs: int,
    latency_seconds: float,
    initiation_interval_seconds: float,
) -> float:
    """
    Simplified pipeline model.

    The first result arrives after latency. After the pipeline is full,
    results can arrive every initiation interval.

        total ≈ latency + (jobs - 1) × initiation interval
    """
    if jobs < 0:
        raise ValueError("jobs cannot be negative")
    if latency_seconds < 0:
        raise ValueError("latency cannot be negative")
    if initiation_interval_seconds < 0:
        raise ValueError("initiation interval cannot be negative")
    if jobs == 0:
        return 0.0
    return latency_seconds + (jobs - 1) * initiation_interval_seconds


def throughput_per_second(interval_seconds: float) -> float:
    """Convert an initiation interval to ideal throughput."""
    if interval_seconds <= 0:
        raise ValueError("interval must be positive")
    return 1.0 / interval_seconds


# ---------------------------------------------------------------------------
# 5. AMDAHL'S LAW
# ---------------------------------------------------------------------------

def amdahl_speedup(
    improved_fraction: float,
    improvement_factor: float,
) -> float:
    """
    Amdahl's Law:

        Speedup = 1 / ((1 - p) + p/s)

    p = fraction of original execution time affected
    s = speedup of the affected portion
    """
    if not 0 <= improved_fraction <= 1:
        raise ValueError("fraction must be between 0 and 1")
    if improvement_factor <= 0:
        raise ValueError("improvement factor must be positive")

    return 1.0 / (
        (1.0 - improved_fraction)
        + improved_fraction / improvement_factor
    )


def maximum_amdahl_speedup(improved_fraction: float) -> float:
    """Theoretical limit when the improved portion becomes infinitely fast."""
    if not 0 <= improved_fraction < 1:
        raise ValueError("fraction must be in [0, 1)")
    return 1.0 / (1.0 - improved_fraction)


# ---------------------------------------------------------------------------
# 6. BENCHMARK DATA MODEL
# ---------------------------------------------------------------------------

@dataclass
class BenchmarkSample:
    elapsed_seconds: float


@dataclass
class BenchmarkResult:
    name: str
    samples: list[BenchmarkSample]

    @property
    def mean(self) -> float:
        return statistics.mean(sample.elapsed_seconds for sample in self.samples)

    @property
    def median(self) -> float:
        return statistics.median(sample.elapsed_seconds for sample in self.samples)

    @property
    def minimum(self) -> float:
        return min(sample.elapsed_seconds for sample in self.samples)

    @property
    def maximum(self) -> float:
        return max(sample.elapsed_seconds for sample in self.samples)

    @property
    def stdev(self) -> float:
        if len(self.samples) < 2:
            return 0.0
        return statistics.stdev(sample.elapsed_seconds for sample in self.samples)

    @property
    def coefficient_of_variation(self) -> float:
        if self.mean == 0:
            return 0.0
        return self.stdev / self.mean


def benchmark(
    name: str,
    function: Callable[[], object],
    repetitions: int = 7,
) -> BenchmarkResult:
    """
    Measure wall-clock execution time.

    Important:
    - time.perf_counter() is designed for measuring short elapsed intervals.
    - One timing is not enough to understand variability.
    - The function's result is deliberately ignored here because this utility
      focuses on elapsed time.
    """
    if repetitions <= 0:
        raise ValueError("repetitions must be positive")

    samples: list[BenchmarkSample] = []

    for _ in range(repetitions):
        start = time.perf_counter()
        function()
        end = time.perf_counter()
        samples.append(BenchmarkSample(end - start))

    return BenchmarkResult(name=name, samples=samples)


# ---------------------------------------------------------------------------
# 7. EXAMPLE ALGORITHMS FOR BENCHMARKING
# ---------------------------------------------------------------------------

def sum_with_loop(values: Sequence[int]) -> int:
    """Explicit Python loop."""
    total = 0
    for value in values:
        total += value
    return total


def sum_with_builtin(values: Sequence[int]) -> int:
    """Python's optimized built-in sum."""
    return sum(values)


def sum_with_generator(values: Sequence[int]) -> int:
    """Demonstrates generator-based processing."""
    return sum(value for value in values)


def demonstrate_benchmarking() -> list[BenchmarkResult]:
    values = list(range(100_000))

    # Warm-up reduces the chance that the first measurement represents
    # initialization effects rather than steady-state behavior.
    sum_with_loop(values)
    sum_with_builtin(values)
    sum_with_generator(values)

    return [
        benchmark("explicit loop", lambda: sum_with_loop(values)),
        benchmark("built-in sum", lambda: sum_with_builtin(values)),
        benchmark("generator + sum", lambda: sum_with_generator(values)),
    ]


# ---------------------------------------------------------------------------
# 8. SYNTHETIC CPU MODEL
# ---------------------------------------------------------------------------

@dataclass
class CPUModel:
    name: str
    frequency_hz: float
    cpi: float

    def time_for_instructions(self, instruction_count: int) -> float:
        return execution_time(
            instruction_count,
            self.cpi,
            self.frequency_hz,
        )

    def effective_ipc(self) -> float:
        return ipc_from_cpi(self.cpi)


def compare_cpus(
    instruction_count: int,
    cpus: Sequence[CPUModel],
) -> list[tuple[str, float, float]]:
    """Return CPU name, execution time, and effective IPC."""
    return [
        (
            cpu.name,
            cpu.time_for_instructions(instruction_count),
            cpu.effective_ipc(),
        )
        for cpu in cpus
    ]


# ---------------------------------------------------------------------------
# 9. CACHE/MEMORY EFFECT MODEL
# ---------------------------------------------------------------------------

@dataclass
class MemoryAccessModel:
    compute_instructions: int
    base_cpi: float
    memory_accesses: int
    cache_hit_rate: float
    hit_penalty_cycles: float
    miss_penalty_cycles: float

    def total_cycles(self) -> float:
        if not 0 <= self.cache_hit_rate <= 1:
            raise ValueError("cache hit rate must be between 0 and 1")

        base_cycles = self.compute_instructions * self.base_cpi
        hits = self.memory_accesses * self.cache_hit_rate
        misses = self.memory_accesses - hits

        memory_penalty = (
            hits * self.hit_penalty_cycles
            + misses * self.miss_penalty_cycles
        )

        return base_cycles + memory_penalty

    def effective_cpi(self) -> float:
        return self.total_cycles() / self.compute_instructions


# ---------------------------------------------------------------------------
# 10. OUTLIER-RESISTANT BENCHMARK STATISTICS
# ---------------------------------------------------------------------------

def percentile(values: Sequence[float], percentile_value: float) -> float:
    """
    Linear interpolation percentile.

    A percentile is often more informative than an average when performance
    contains occasional long stalls.
    """
    if not values:
        raise ValueError("values cannot be empty")
    if not 0 <= percentile_value <= 100:
        raise ValueError("percentile must be between 0 and 100")

    ordered = sorted(values)

    if len(ordered) == 1:
        return ordered[0]

    position = (len(ordered) - 1) * percentile_value / 100
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return ordered[lower]

    fraction = position - lower
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


# ---------------------------------------------------------------------------
# 11. PERFORMANCE COUNTER INTERPRETATION
# ---------------------------------------------------------------------------

def derive_cpi_from_counters(
    cycles: int,
    retired_instructions: int,
) -> float:
    """
    CPI from measured hardware/software counters:

        CPI = cycles / instructions

    The exact meaning of counters depends on the processor and measurement
    environment. Retired instructions are not necessarily identical to every
    microarchitectural operation.
    """
    if cycles < 0 or retired_instructions <= 0:
        raise ValueError("invalid counter values")
    return cycles / retired_instructions


def derive_ipc_from_counters(
    cycles: int,
    retired_instructions: int,
) -> float:
    """IPC from measured instruction and cycle counts."""
    if cycles <= 0 or retired_instructions < 0:
        raise ValueError("invalid counter values")
    return retired_instructions / cycles


# ---------------------------------------------------------------------------
# 12. ENERGY/PERFORMANCE TRADE-OFF MODEL
# ---------------------------------------------------------------------------

def energy_for_execution(
    average_power_watts: float,
    execution_seconds: float,
) -> float:
    """Energy in joules = power in watts × time in seconds."""
    if average_power_watts < 0:
        raise ValueError("power cannot be negative")
    if execution_seconds < 0:
        raise ValueError("time cannot be negative")
    return average_power_watts * execution_seconds


# ---------------------------------------------------------------------------
# 13. VALIDATION OF PERFORMANCE CLAIMS
# ---------------------------------------------------------------------------

def relative_speedup(
    baseline_seconds: float,
    improved_seconds: float,
) -> float:
    """Speedup = baseline time / improved time."""
    if baseline_seconds <= 0 or improved_seconds <= 0:
        raise ValueError("execution times must be positive")
    return baseline_seconds / improved_seconds


def relative_performance_difference(
    baseline_seconds: float,
    new_seconds: float,
) -> float:
    """
    Positive value means the new execution time is greater than baseline.
    Negative means it is lower.

        (new - baseline) / baseline
    """
    if baseline_seconds <= 0:
        raise ValueError("baseline must be positive")
    return (new_seconds - baseline_seconds) / baseline_seconds


# ---------------------------------------------------------------------------
# 14. EDGE CASES AND COMMON PERFORMANCE MISTAKES
# ---------------------------------------------------------------------------

def demonstrate_edge_cases() -> None:
    print("\nEDGE CASES")

    cases = [
        ("zero instructions", lambda: execution_time(0, 1, 3e9)),
        ("invalid frequency", lambda: execution_time(100, 1, 0)),
        ("negative CPI", lambda: execution_time(100, -1, 3e9)),
    ]

    for name, operation in cases:
        try:
            result = operation()
            print(f"{name}: {result}")
        except ValueError as error:
            print(f"{name}: correctly rejected -> {error}")

    print(
        "Important distinction: a CPU with a higher clock frequency is not "
        "automatically faster because CPI, IPC, memory behavior, parallelism, "
        "and workload characteristics also affect execution time."
    )


# ---------------------------------------------------------------------------
# 15. MAIN EDUCATIONAL DEMONSTRATION
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 78)
    print("COMPUTER PERFORMANCE STUDY")
    print("Clock Speed | CPI | IPC | Latency | Throughput | Benchmarks")
    print("=" * 78)

    # Basic clock-speed example.
    frequency = 3.5e9
    print("\n1. CLOCK SPEED")
    print(f"Clock frequency: {format_frequency(frequency)}")
    print(f"Cycles per second: {cycles_per_second(frequency):,.0f}")
    print(f"One clock period: {format_time(1 / frequency)}")

    # CPU-time equation.
    print("\n2. CPU EXECUTION TIME")
    instructions = 1_000_000_000
    cpi = 1.5
    cpu_time = execution_time(instructions, cpi, frequency)
    cycles = instructions * cpi

    print(f"Instructions: {instructions:,}")
    print(f"CPI: {cpi}")
    print(f"Total cycles: {cycles:,.0f}")
    print(f"CPU time: {format_time(cpu_time)}")

    # CPI and IPC.
    print("\n3. CPI AND IPC")
    print(f"CPI = {cpi:.3f}")
    print(f"Simple reciprocal IPC model = {ipc_from_cpi(cpi):.3f}")
    print(
        "Interpretation: lower CPI means fewer cycles per instruction. "
        "Higher IPC means more instructions completed per cycle."
    )

    # Instruction mix.
    print("\n4. INSTRUCTION MIX")
    classes = [
        InstructionClass("integer arithmetic", 500_000, 1.0),
        InstructionClass("load/store", 300_000, 2.0),
        InstructionClass("branch", 100_000, 4.0),
        InstructionClass("floating point", 100_000, 3.0),
    ]
    mix = analyze_instruction_mix(classes)

    for item in classes:
        print(
            f"{item.name:20s} "
            f"count={item.count:8,d} "
            f"CPI={item.cpi:.1f}"
        )

    print(f"Total instructions: {mix['instructions']:,.0f}")
    print(f"Total cycles: {mix['cycles']:,.0f}")
    print(f"Weighted average CPI: {mix['average_cpi']:.3f}")
    print(f"IPC under simple model: {mix['simple_ipc']:.3f}")

    # Clock-speed comparison.
    print("\n5. CLOCK SPEED IS NOT THE WHOLE STORY")
    test_instructions = 2_000_000_000
    cpus = [
        CPUModel("CPU A: 3.0 GHz, CPI 1.0", 3.0e9, 1.0),
        CPUModel("CPU B: 4.0 GHz, CPI 1.5", 4.0e9, 1.5),
        CPUModel("CPU C: 3.2 GHz, CPI 0.8", 3.2e9, 0.8),
    ]

    comparison = compare_cpus(test_instructions, cpus)
    for name, elapsed, effective_ipc in comparison:
        print(
            f"{name:28s} "
            f"time={format_time(elapsed):>12s} "
            f"IPC={effective_ipc:.3f}"
        )

    # Latency and throughput.
    print("\n6. LATENCY VERSUS THROUGHPUT")
    jobs = 100
    latency = 10e-6
    interval = 2e-6

    sequential = sequential_completion_time(jobs, latency)
    pipelined = pipelined_completion_time(jobs, latency, interval)

    print(f"Jobs: {jobs}")
    print(f"Individual latency: {format_time(latency)}")
    print(f"Sequential completion: {format_time(sequential)}")
    print(f"Pipelined completion: {format_time(pipelined)}")
    print(f"Ideal pipelined throughput: {throughput_per_second(interval):,.0f} jobs/s")

    # Amdahl's Law.
    print("\n7. AMDAHL'S LAW")
    fraction = 0.80
    improvement = 5.0
    speedup = amdahl_speedup(fraction, improvement)
    limit = maximum_amdahl_speedup(fraction)

    print(f"Improved fraction: {fraction:.0%}")
    print(f"Improvement factor: {improvement:.1f}×")
    print(f"System speedup: {speedup:.3f}×")
    print(f"Theoretical maximum: {limit:.3f}×")

    # Memory effects.
    print("\n8. MEMORY AND CACHE EFFECTS")
    memory_model = MemoryAccessModel(
        compute_instructions=1_000_000,
        base_cpi=1.0,
        memory_accesses=200_000,
        cache_hit_rate=0.95,
        hit_penalty_cycles=2.0,
        miss_penalty_cycles=100.0,
    )

    total_cycles = memory_model.total_cycles()
    effective_cpi = memory_model.effective_cpi()

    print(f"Total modeled cycles: {total_cycles:,.0f}")
    print(f"Effective CPI: {effective_cpi:.3f}")

    # Hardware-counter example.
    print("\n9. PERFORMANCE COUNTERS")
    measured_cycles = 4_500_000_000
    retired_instructions = 3_000_000_000

    measured_cpi = derive_cpi_from_counters(
        measured_cycles,
        retired_instructions,
    )
    measured_ipc = derive_ipc_from_counters(
        measured_cycles,
        retired_instructions,
    )

    print(f"Measured cycles: {measured_cycles:,}")
    print(f"Retired instructions: {retired_instructions:,}")
    print(f"Measured CPI: {measured_cpi:.3f}")
    print(f"Measured IPC: {measured_ipc:.3f}")

    # Benchmark examples.
    print("\n10. PYTHON MICRO-BENCHMARK")
    results = demonstrate_benchmarking()

    for result in results:
        print(
            f"{result.name:20s} "
            f"mean={format_time(result.mean):>12s} "
            f"median={format_time(result.median):>12s} "
            f"min={format_time(result.minimum):>12s} "
            f"max={format_time(result.maximum):>12s} "
            f"stdev={format_time(result.stdev):>12s}"
        )

    # Percentiles demonstrate tail behavior.
    all_samples = [
        sample.elapsed_seconds
        for result in results
        for sample in result.samples
    ]

    print("\n11. PERCENTILE ANALYSIS")
    print(f"Combined P50: {format_time(percentile(all_samples, 50))}")
    print(f"Combined P95: {format_time(percentile(all_samples, 95))}")
    print(f"Combined P99: {format_time(percentile(all_samples, 99))}")

    # Speedup.
    print("\n12. SPEEDUP")
    baseline = results[0].median
    optimized = results[1].median
    print(f"Baseline median: {format_time(baseline)}")
    print(f"Optimized median: {format_time(optimized)}")
    print(f"Measured speedup: {relative_speedup(baseline, optimized):.3f}×")

    # Energy trade-off.
    print("\n13. PERFORMANCE AND ENERGY")
    power = 65.0
    energy = energy_for_execution(power, cpu_time)
    print(f"Average power: {power:.1f} W")
    print(f"Execution time: {format_time(cpu_time)}")
    print(f"Energy: {energy:.6f} J")

    demonstrate_edge_cases()

    print("\n" + "=" * 78)
    print("KEY RELATIONSHIPS")
    print("=" * 78)
    print("CPU time = Instruction Count × CPI / Clock Rate")
    print("CPI = Clock Cycles / Instructions")
    print("IPC = Instructions / Clock Cycles")
    print("Ideal reciprocal relationship in a simple model: IPC ≈ 1 / CPI")
    print("Speedup = Old Execution Time / New Execution Time")
    print("Throughput = Completed Work / Unit Time")
    print("Latency = Time required for one operation or result")
    print("Amdahl: Speedup = 1 / ((1-p) + p/s)")
    print("\nBenchmarking must control workload, environment, warm-up, repetitions,")
    print("compiler/runtime effects, background activity, and measurement overhead.")


if __name__ == "__main__":
    main()
