"""Performance benchmarking utilities for James Code testing."""

import time
import psutil
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from contextlib import contextmanager
import statistics
import json

import pytest


@dataclass
class BenchmarkResult:
    """Result of a performance benchmark."""
    name: str
    duration: float
    memory_usage: Dict[str, float]
    cpu_usage: float
    iterations: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def operations_per_second(self) -> float:
        """Calculate operations per second."""
        if self.duration == 0:
            return 0
        return self.iterations / self.duration
    
    @property
    def avg_duration_per_operation(self) -> float:
        """Calculate average duration per operation."""
        if self.iterations == 0:
            return 0
        return self.duration / self.iterations


@dataclass
class BenchmarkStats:
    """Statistics for multiple benchmark runs."""
    name: str
    results: List[BenchmarkResult]
    
    @property
    def avg_duration(self) -> float:
        """Average duration across runs."""
        if not self.results:
            return 0
        return statistics.mean(r.duration for r in self.results)
    
    @property
    def min_duration(self) -> float:
        """Minimum duration across runs."""
        if not self.results:
            return 0
        return min(r.duration for r in self.results)
    
    @property
    def max_duration(self) -> float:
        """Maximum duration across runs."""
        if not self.results:
            return 0
        return max(r.duration for r in self.results)
    
    @property
    def std_deviation(self) -> float:
        """Standard deviation of durations."""
        if len(self.results) < 2:
            return 0
        return statistics.stdev(r.duration for r in self.results)
    
    @property
    def avg_memory_usage(self) -> Dict[str, float]:
        """Average memory usage across runs."""
        if not self.results:
            return {}
        
        # Get all memory keys
        all_keys = set()
        for result in self.results:
            all_keys.update(result.memory_usage.keys())
        
        avg_usage = {}
        for key in all_keys:
            values = [r.memory_usage.get(key, 0) for r in self.results]
            avg_usage[key] = statistics.mean(values)
        
        return avg_usage
    
    @property
    def avg_operations_per_second(self) -> float:
        """Average operations per second."""
        if not self.results:
            return 0
        return statistics.mean(r.operations_per_second for r in self.results)


class PerformanceBenchmark:
    """Performance benchmark runner for James Code operations."""
    
    def __init__(self, name: str):
        """Initialize benchmark.
        
        Args:
            name: Name of the benchmark
        """
        self.name = name
        self.results: List[BenchmarkResult] = []
        self._start_time: Optional[float] = None
        self._start_memory: Optional[Dict[str, float]] = None
        self._start_cpu: Optional[float] = None
    
    @contextmanager
    def measure(self, iterations: int = 1, metadata: Optional[Dict[str, Any]] = None):
        """Context manager for measuring performance.
        
        Args:
            iterations: Number of operations being measured
            metadata: Additional metadata to store
            
        Yields:
            None
        """
        # Start measurement
        self._start_time = time.time()
        self._start_memory = self._get_memory_usage()
        self._start_cpu = psutil.cpu_percent()
        
        try:
            yield
        finally:
            # End measurement
            end_time = time.time()
            end_memory = self._get_memory_usage()
            end_cpu = psutil.cpu_percent()
            
            # Calculate metrics
            duration = end_time - self._start_time
            memory_usage = {
                key: end_memory[key] - self._start_memory.get(key, 0)
                for key in end_memory
            }
            cpu_usage = end_cpu - self._start_cpu
            
            # Store result
            result = BenchmarkResult(
                name=self.name,
                duration=duration,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                iterations=iterations,
                metadata=metadata or {}
            )
            
            self.results.append(result)
    
    def run_benchmark(self, 
                     operation: Callable,
                     iterations: int = 1,
                     runs: int = 1,
                     warmup_runs: int = 0,
                     metadata: Optional[Dict[str, Any]] = None) -> BenchmarkStats:
        """Run a benchmark with multiple runs.
        
        Args:
            operation: Function to benchmark
            iterations: Number of iterations per run
            runs: Number of benchmark runs
            warmup_runs: Number of warmup runs (not measured)
            metadata: Additional metadata
            
        Returns:
            Benchmark statistics
        """
        # Warmup runs
        for _ in range(warmup_runs):
            operation()
        
        # Measured runs
        for run_num in range(runs):
            run_metadata = (metadata or {}).copy()
            run_metadata.update({"run_number": run_num + 1})
            
            with self.measure(iterations=iterations, metadata=run_metadata):
                for _ in range(iterations):
                    operation()
        
        return BenchmarkStats(name=self.name, results=self.results[-runs:])
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage.
        
        Returns:
            Memory usage dictionary in MB
        """
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": process.memory_percent(),
        }
    
    def get_stats(self) -> BenchmarkStats:
        """Get statistics for all results.
        
        Returns:
            Benchmark statistics
        """
        return BenchmarkStats(name=self.name, results=self.results)
    
    def reset(self):
        """Reset all benchmark results."""
        self.results.clear()


class BenchmarkSuite:
    """Suite of performance benchmarks."""
    
    def __init__(self, name: str):
        """Initialize benchmark suite.
        
        Args:
            name: Name of the suite
        """
        self.name = name
        self.benchmarks: Dict[str, PerformanceBenchmark] = {}
        self.suite_results: Dict[str, BenchmarkStats] = {}
    
    def add_benchmark(self, benchmark: PerformanceBenchmark):
        """Add a benchmark to the suite.
        
        Args:
            benchmark: Benchmark to add
        """
        self.benchmarks[benchmark.name] = benchmark
    
    def create_benchmark(self, name: str) -> PerformanceBenchmark:
        """Create and add a new benchmark.
        
        Args:
            name: Name of the benchmark
            
        Returns:
            Created benchmark
        """
        benchmark = PerformanceBenchmark(name)
        self.add_benchmark(benchmark)
        return benchmark
    
    def run_suite(self, 
                  iterations: int = 1,
                  runs: int = 3,
                  warmup_runs: int = 1) -> Dict[str, BenchmarkStats]:
        """Run all benchmarks in the suite.
        
        Args:
            iterations: Iterations per benchmark run
            runs: Number of runs per benchmark
            warmup_runs: Warmup runs per benchmark
            
        Returns:
            Dictionary of benchmark statistics
        """
        results = {}
        
        for name, benchmark in self.benchmarks.items():
            # This would need to be implemented based on specific benchmark needs
            # For now, we'll just get existing stats
            results[name] = benchmark.get_stats()
        
        self.suite_results = results
        return results
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of suite results.
        
        Returns:
            Summary dictionary
        """
        if not self.suite_results:
            return {"error": "No results available - run suite first"}
        
        summary = {
            "suite_name": self.name,
            "total_benchmarks": len(self.suite_results),
            "benchmarks": {}
        }
        
        for name, stats in self.suite_results.items():
            summary["benchmarks"][name] = {
                "avg_duration": stats.avg_duration,
                "min_duration": stats.min_duration,
                "max_duration": stats.max_duration,
                "std_deviation": stats.std_deviation,
                "avg_ops_per_sec": stats.avg_operations_per_second,
                "runs": len(stats.results)
            }
        
        return summary
    
    def export_results(self, file_path: Path):
        """Export results to JSON file.
        
        Args:
            file_path: Path to export file
        """
        summary = self.get_summary()
        
        with open(file_path, 'w') as f:
            json.dump(summary, f, indent=2)
    
    def reset_all(self):
        """Reset all benchmarks in the suite."""
        for benchmark in self.benchmarks.values():
            benchmark.reset()
        self.suite_results.clear()


def benchmark_tool_operation(tool_class, 
                            operation_params: Dict[str, Any],
                            context,
                            iterations: int = 10,
                            runs: int = 3) -> BenchmarkStats:
    """Benchmark a tool operation.
    
    Args:
        tool_class: Tool class to benchmark
        operation_params: Parameters for the operation
        context: Execution context
        iterations: Iterations per run
        runs: Number of runs
        
    Returns:
        Benchmark statistics
    """
    tool_name = tool_class.__name__
    benchmark = PerformanceBenchmark(f"{tool_name}_operation")
    
    def operation():
        tool = tool_class()
        return tool.execute(context, **operation_params)
    
    return benchmark.run_benchmark(
        operation=operation,
        iterations=iterations,
        runs=runs,
        warmup_runs=1,
        metadata={
            "tool_class": tool_name,
            "operation_params": operation_params
        }
    )


def benchmark_agent_workflow(agent,
                            workflow_steps: List[Dict[str, Any]],
                            iterations: int = 5,
                            runs: int = 3) -> BenchmarkStats:
    """Benchmark an agent workflow.
    
    Args:
        agent: Agent instance
        workflow_steps: List of workflow steps
        iterations: Iterations per run
        runs: Number of runs
        
    Returns:
        Benchmark statistics
    """
    benchmark = PerformanceBenchmark("agent_workflow")
    
    def workflow():
        for step in workflow_steps:
            # This would execute workflow steps
            # Implementation depends on agent interface
            pass
    
    return benchmark.run_benchmark(
        operation=workflow,
        iterations=iterations,
        runs=runs,
        warmup_runs=1,
        metadata={
            "workflow_steps": len(workflow_steps),
            "agent_type": type(agent).__name__
        }
    )


class ContinuousPerformanceMonitor:
    """Monitor performance continuously during testing."""
    
    def __init__(self, sample_interval: float = 0.1):
        """Initialize continuous monitor.
        
        Args:
            sample_interval: Sampling interval in seconds
        """
        self.sample_interval = sample_interval
        self.samples: List[Dict[str, Any]] = []
        self.monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
    
    def start_monitoring(self):
        """Start continuous monitoring."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop)
        self._monitor_thread.start()
    
    def stop_monitoring(self) -> List[Dict[str, Any]]:
        """Stop monitoring and return samples.
        
        Returns:
            List of performance samples
        """
        self.monitoring = False
        
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1.0)
        
        return self.samples.copy()
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        process = psutil.Process()
        
        while self.monitoring:
            try:
                # Collect sample
                memory_info = process.memory_info()
                sample = {
                    "timestamp": time.time(),
                    "memory_rss_mb": memory_info.rss / 1024 / 1024,
                    "memory_vms_mb": memory_info.vms / 1024 / 1024,
                    "memory_percent": process.memory_percent(),
                    "cpu_percent": process.cpu_percent(),
                    "num_threads": process.num_threads(),
                    "open_files": len(process.open_files()),
                }
                
                self.samples.append(sample)
                
                time.sleep(self.sample_interval)
                
            except Exception:
                # Process might have ended or access denied
                break
    
    def get_peak_memory(self) -> float:
        """Get peak memory usage in MB.
        
        Returns:
            Peak memory usage
        """
        if not self.samples:
            return 0
        return max(sample["memory_rss_mb"] for sample in self.samples)
    
    def get_avg_cpu(self) -> float:
        """Get average CPU usage.
        
        Returns:
            Average CPU percentage
        """
        if not self.samples:
            return 0
        return statistics.mean(sample["cpu_percent"] for sample in self.samples)
    
    def reset(self):
        """Reset all samples."""
        self.samples.clear()


@pytest.fixture
def performance_benchmark():
    """Provide a performance benchmark for testing."""
    benchmark = PerformanceBenchmark("test_benchmark")
    yield benchmark
    benchmark.reset()


@pytest.fixture
def benchmark_suite():
    """Provide a benchmark suite for testing."""
    suite = BenchmarkSuite("test_suite")
    yield suite
    suite.reset_all()


@pytest.fixture
def continuous_monitor():
    """Provide a continuous performance monitor."""
    monitor = ContinuousPerformanceMonitor()
    yield monitor
    if monitor.monitoring:
        monitor.stop_monitoring()
    monitor.reset()