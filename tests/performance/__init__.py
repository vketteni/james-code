"""Performance testing framework for James Code."""

from .benchmarks import *
from .metrics import *
from .assertions import *

__all__ = [
    # Benchmark utilities
    'PerformanceBenchmark',
    'BenchmarkSuite',
    'benchmark_tool_operation',
    'benchmark_agent_workflow',
    
    # Metrics collection
    'PerformanceMetrics',
    'MetricsCollector',
    'ResourceMonitor',
    'MemoryTracker',
    
    # Performance assertions
    'assert_performance_within_limits',
    'assert_no_performance_regression',
    'assert_memory_usage_stable',
    'assert_response_time_acceptable',
    
    # Fixtures
    'performance_monitor',
    'benchmark_suite',
    'resource_tracker',
]