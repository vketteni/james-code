"""Performance assertion utilities for James Code testing."""

import time
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import json

import pytest

from .metrics import PerformanceMetrics, PerformanceSnapshot
from .benchmarks import BenchmarkResult, BenchmarkStats


def assert_performance_within_limits(result: Union[BenchmarkResult, BenchmarkStats],
                                    max_duration: float,
                                    max_memory_mb: Optional[float] = None,
                                    max_cpu_percent: Optional[float] = None,
                                    min_ops_per_second: Optional[float] = None):
    """Assert that performance metrics are within specified limits.
    
    Args:
        result: Benchmark result or stats to check
        max_duration: Maximum allowed duration in seconds
        max_memory_mb: Maximum allowed memory usage in MB
        max_cpu_percent: Maximum allowed CPU usage percentage
        min_ops_per_second: Minimum required operations per second
        
    Raises:
        AssertionError: If performance limits are exceeded
    """
    if isinstance(result, BenchmarkStats):
        # Use average values for stats
        duration = result.avg_duration
        memory_usage = result.avg_memory_usage.get("rss_mb", 0)
        ops_per_second = result.avg_operations_per_second
        cpu_usage = 0  # BenchmarkStats doesn't track CPU currently
    else:
        # Use direct values for result
        duration = result.duration
        memory_usage = result.memory_usage.get("rss_mb", 0)
        ops_per_second = result.operations_per_second
        cpu_usage = result.cpu_usage
    
    # Check duration
    assert duration <= max_duration, \
        f"Performance exceeded time limit: {duration:.3f}s > {max_duration}s"
    
    # Check memory if specified
    if max_memory_mb is not None:
        assert memory_usage <= max_memory_mb, \
            f"Memory usage exceeded limit: {memory_usage:.2f}MB > {max_memory_mb}MB"
    
    # Check CPU if specified
    if max_cpu_percent is not None:
        assert cpu_usage <= max_cpu_percent, \
            f"CPU usage exceeded limit: {cpu_usage:.2f}% > {max_cpu_percent}%"
    
    # Check operations per second if specified
    if min_ops_per_second is not None:
        assert ops_per_second >= min_ops_per_second, \
            f"Operations per second below minimum: {ops_per_second:.2f} < {min_ops_per_second}"


def assert_no_performance_regression(current_result: Union[BenchmarkResult, BenchmarkStats],
                                   baseline_file: Path,
                                   tolerance_percent: float = 10.0,
                                   save_new_baseline: bool = False):
    """Assert that performance has not regressed compared to baseline.
    
    Args:
        current_result: Current benchmark result
        baseline_file: Path to baseline performance file
        tolerance_percent: Allowed performance degradation percentage
        save_new_baseline: Whether to save current result as new baseline
        
    Raises:
        AssertionError: If performance regression detected
    """
    # Extract current metrics
    if isinstance(current_result, BenchmarkStats):
        current_duration = current_result.avg_duration
        current_memory = current_result.avg_memory_usage.get("rss_mb", 0)
        current_ops_per_sec = current_result.avg_operations_per_second
    else:
        current_duration = current_result.duration
        current_memory = current_result.memory_usage.get("rss_mb", 0)
        current_ops_per_sec = current_result.operations_per_second
    
    # Load baseline if exists
    if baseline_file.exists():
        with open(baseline_file, 'r') as f:
            baseline = json.load(f)
        
        baseline_duration = baseline.get("duration", 0)
        baseline_memory = baseline.get("memory_mb", 0)
        baseline_ops_per_sec = baseline.get("ops_per_second", 0)
        
        # Check for regressions
        if baseline_duration > 0:
            duration_increase = ((current_duration - baseline_duration) / baseline_duration) * 100
            assert duration_increase <= tolerance_percent, \
                f"Performance regression detected: {duration_increase:.1f}% slower than baseline"
        
        if baseline_memory > 0:
            memory_increase = ((current_memory - baseline_memory) / baseline_memory) * 100
            assert memory_increase <= tolerance_percent, \
                f"Memory regression detected: {memory_increase:.1f}% more memory than baseline"
        
        if baseline_ops_per_sec > 0:
            ops_decrease = ((baseline_ops_per_sec - current_ops_per_sec) / baseline_ops_per_sec) * 100
            assert ops_decrease <= tolerance_percent, \
                f"Throughput regression detected: {ops_decrease:.1f}% fewer ops/sec than baseline"
    
    # Save new baseline if requested or if no baseline exists
    if save_new_baseline or not baseline_file.exists():
        baseline_file.parent.mkdir(parents=True, exist_ok=True)
        
        new_baseline = {
            "duration": current_duration,
            "memory_mb": current_memory,
            "ops_per_second": current_ops_per_sec,
            "timestamp": time.time(),
            "benchmark_name": getattr(current_result, 'name', 'unknown')
        }
        
        with open(baseline_file, 'w') as f:
            json.dump(new_baseline, f, indent=2)


def assert_memory_usage_stable(metrics: PerformanceMetrics,
                              max_growth_mb: float = 50.0,
                              max_variance_percent: float = 20.0):
    """Assert that memory usage remains stable during operation.
    
    Args:
        metrics: Performance metrics to analyze
        max_growth_mb: Maximum allowed memory growth in MB
        max_variance_percent: Maximum allowed variance percentage
        
    Raises:
        AssertionError: If memory usage is unstable
    """
    if len(metrics.snapshots) < 2:
        return  # Not enough data
    
    memory_values = [snapshot.memory_usage["rss_mb"] for snapshot in metrics.snapshots]
    
    # Check total growth
    memory_growth = memory_values[-1] - memory_values[0]
    assert memory_growth <= max_growth_mb, \
        f"Memory growth exceeded limit: {memory_growth:.2f}MB > {max_growth_mb}MB"
    
    # Check variance
    import statistics
    if len(memory_values) > 1:
        mean_memory = statistics.mean(memory_values)
        variance = statistics.variance(memory_values)
        variance_percent = (variance ** 0.5 / mean_memory) * 100 if mean_memory > 0 else 0
        
        assert variance_percent <= max_variance_percent, \
            f"Memory variance too high: {variance_percent:.1f}% > {max_variance_percent}%"


def assert_response_time_acceptable(response_times: List[float],
                                  max_avg_time: float,
                                  max_p95_time: Optional[float] = None,
                                  max_p99_time: Optional[float] = None):
    """Assert that response times are acceptable.
    
    Args:
        response_times: List of response times in seconds
        max_avg_time: Maximum acceptable average response time
        max_p95_time: Maximum acceptable 95th percentile response time
        max_p99_time: Maximum acceptable 99th percentile response time
        
    Raises:
        AssertionError: If response times are unacceptable
    """
    if not response_times:
        return
    
    import statistics
    
    # Check average
    avg_time = statistics.mean(response_times)
    assert avg_time <= max_avg_time, \
        f"Average response time too high: {avg_time:.3f}s > {max_avg_time}s"
    
    # Check percentiles if specified
    if max_p95_time is not None:
        sorted_times = sorted(response_times)
        p95_index = int(len(sorted_times) * 0.95)
        p95_time = sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
        
        assert p95_time <= max_p95_time, \
            f"95th percentile response time too high: {p95_time:.3f}s > {max_p95_time}s"
    
    if max_p99_time is not None:
        sorted_times = sorted(response_times)
        p99_index = int(len(sorted_times) * 0.99)
        p99_time = sorted_times[p99_index] if p99_index < len(sorted_times) else sorted_times[-1]
        
        assert p99_time <= max_p99_time, \
            f"99th percentile response time too high: {p99_time:.3f}s > {max_p99_time}s"


def assert_throughput_meets_target(operations_completed: int,
                                 duration: float,
                                 min_ops_per_second: float):
    """Assert that throughput meets target.
    
    Args:
        operations_completed: Number of operations completed
        duration: Total duration in seconds
        min_ops_per_second: Minimum required operations per second
        
    Raises:
        AssertionError: If throughput is below target
    """
    if duration == 0:
        return
    
    actual_ops_per_second = operations_completed / duration
    assert actual_ops_per_second >= min_ops_per_second, \
        f"Throughput below target: {actual_ops_per_second:.2f} < {min_ops_per_second} ops/sec"


def assert_resource_efficiency(metrics: PerformanceMetrics,
                             max_cpu_utilization: float = 80.0,
                             max_memory_per_operation: Optional[float] = None,
                             operations_count: int = 1):
    """Assert that resource usage is efficient.
    
    Args:
        metrics: Performance metrics to analyze
        max_cpu_utilization: Maximum acceptable CPU utilization percentage
        max_memory_per_operation: Maximum memory per operation in MB
        operations_count: Number of operations performed
        
    Raises:
        AssertionError: If resource usage is inefficient
    """
    # Check CPU efficiency
    if metrics.avg_cpu_percent > max_cpu_utilization:
        assert False, \
            f"CPU utilization too high: {metrics.avg_cpu_percent:.1f}% > {max_cpu_utilization}%"
    
    # Check memory efficiency per operation
    if max_memory_per_operation is not None and operations_count > 0:
        memory_per_operation = metrics.peak_memory_mb / operations_count
        assert memory_per_operation <= max_memory_per_operation, \
            f"Memory per operation too high: {memory_per_operation:.2f}MB > {max_memory_per_operation}MB"


def assert_no_memory_leaks(initial_snapshot: PerformanceSnapshot,
                          final_snapshot: PerformanceSnapshot,
                          max_growth_mb: float = 10.0):
    """Assert that no significant memory leaks occurred.
    
    Args:
        initial_snapshot: Initial performance snapshot
        final_snapshot: Final performance snapshot
        max_growth_mb: Maximum acceptable memory growth in MB
        
    Raises:
        AssertionError: If memory leak detected
    """
    initial_memory = initial_snapshot.memory_usage["rss_mb"]
    final_memory = final_snapshot.memory_usage["rss_mb"]
    memory_growth = final_memory - initial_memory
    
    assert memory_growth <= max_growth_mb, \
        f"Potential memory leak detected: {memory_growth:.2f}MB growth > {max_growth_mb}MB"


def assert_performance_scalability(results: List[BenchmarkResult],
                                 max_degradation_percent: float = 50.0):
    """Assert that performance scales reasonably with load.
    
    Args:
        results: List of benchmark results with increasing load
        max_degradation_percent: Maximum acceptable performance degradation
        
    Raises:
        AssertionError: If performance doesn't scale well
    """
    if len(results) < 2:
        return
    
    # Sort by iterations (load)
    sorted_results = sorted(results, key=lambda r: r.iterations)
    
    # Compare first and last results
    baseline_ops_per_sec = sorted_results[0].operations_per_second
    final_ops_per_sec = sorted_results[-1].operations_per_second
    
    if baseline_ops_per_sec > 0:
        degradation_percent = ((baseline_ops_per_sec - final_ops_per_sec) / baseline_ops_per_sec) * 100
        assert degradation_percent <= max_degradation_percent, \
            f"Performance degradation too high: {degradation_percent:.1f}% > {max_degradation_percent}%"


class PerformanceReporter:
    """Generate performance reports for test results."""
    
    @staticmethod
    def generate_report(results: Dict[str, BenchmarkStats], 
                       output_file: Path):
        """Generate a performance report.
        
        Args:
            results: Dictionary of benchmark results
            output_file: Output file path
        """
        report = {
            "timestamp": time.time(),
            "summary": {
                "total_benchmarks": len(results),
                "avg_duration": sum(stats.avg_duration for stats in results.values()) / len(results) if results else 0,
                "total_operations": sum(sum(r.iterations for r in stats.results) for stats in results.values())
            },
            "benchmarks": {}
        }
        
        for name, stats in results.items():
            report["benchmarks"][name] = {
                "avg_duration": stats.avg_duration,
                "min_duration": stats.min_duration,
                "max_duration": stats.max_duration,
                "std_deviation": stats.std_deviation,
                "avg_ops_per_second": stats.avg_operations_per_second,
                "runs": len(stats.results),
                "total_iterations": sum(r.iterations for r in stats.results)
            }
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
    
    @staticmethod
    def compare_reports(current_file: Path, 
                       baseline_file: Path,
                       output_file: Path):
        """Compare two performance reports.
        
        Args:
            current_file: Current report file
            baseline_file: Baseline report file
            output_file: Comparison output file
        """
        with open(current_file, 'r') as f:
            current = json.load(f)
        
        with open(baseline_file, 'r') as f:
            baseline = json.load(f)
        
        comparison = {
            "timestamp": time.time(),
            "current_report": str(current_file),
            "baseline_report": str(baseline_file),
            "comparisons": {}
        }
        
        for name in current["benchmarks"]:
            if name in baseline["benchmarks"]:
                current_bench = current["benchmarks"][name]
                baseline_bench = baseline["benchmarks"][name]
                
                duration_change = ((current_bench["avg_duration"] - baseline_bench["avg_duration"]) / 
                                 baseline_bench["avg_duration"]) * 100 if baseline_bench["avg_duration"] > 0 else 0
                
                ops_change = ((current_bench["avg_ops_per_second"] - baseline_bench["avg_ops_per_second"]) / 
                            baseline_bench["avg_ops_per_second"]) * 100 if baseline_bench["avg_ops_per_second"] > 0 else 0
                
                comparison["comparisons"][name] = {
                    "duration_change_percent": duration_change,
                    "ops_per_second_change_percent": ops_change,
                    "current_duration": current_bench["avg_duration"],
                    "baseline_duration": baseline_bench["avg_duration"],
                    "current_ops_per_sec": current_bench["avg_ops_per_second"],
                    "baseline_ops_per_sec": baseline_bench["avg_ops_per_second"]
                }
        
        with open(output_file, 'w') as f:
            json.dump(comparison, f, indent=2)