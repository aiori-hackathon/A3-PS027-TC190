"""
Benchmark Suite Package for PS-027
"""

from .targets import BENCHMARK_TARGETS
from .runner import BenchmarkRunner

__all__ = ["BENCHMARK_TARGETS", "BenchmarkRunner"]
