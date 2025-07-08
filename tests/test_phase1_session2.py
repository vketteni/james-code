"""Test Phase 1 Session 2 components: LLM mocking and performance framework."""

import pytest
import time
import tempfile
from pathlib import Path

from tests.mocks.llm_mock import (
    MockLLMProvider, DeterministicLLMProvider, ErrorSimulatingLLMProvider,
    LLMErrorType, MockLLMResponse, LLMResponseScenario,
    get_code_analysis_scenarios, get_security_testing_scenarios
)
from tests.performance.benchmarks import PerformanceBenchmark, BenchmarkSuite
from tests.performance.metrics import PerformanceMetrics, MetricsCollector, PerformanceSnapshot
from tests.performance.assertions import assert_performance_within_limits


class TestLLMMocking:
    """Test LLM mocking infrastructure."""
    
    def test_basic_mock_provider(self):
        """Test basic mock LLM provider functionality."""
        provider = MockLLMProvider("test-model")
        
        # Test basic response generation
        response = provider.generate_response("Hello, how are you?")
        
        assert isinstance(response, MockLLMResponse)
        assert response.content is not None
        assert len(response.content) > 0
        assert response.model == "test-model"
        assert response.usage["total_tokens"] > 0
        
        print(f"✓ Basic mock response: '{response.content[:50]}...'")
    
    def test_scenario_based_responses(self):
        """Test scenario-based response generation."""
        provider = MockLLMProvider("scenario-test")
        
        # Add a specific scenario
        provider.add_simple_scenario(
            pattern="read file",
            response_content="I'll read the file for you.",
            tool_calls=[{
                "name": "read",
                "parameters": {"action": "read_file", "path": "test.txt"}
            }]
        )
        
        # Test scenario matching
        response = provider.generate_response("Please read file test.txt")
        
        assert "read the file" in response.content
        assert len(response.tool_calls) == 1
        assert response.tool_calls[0]["name"] == "read"
        
        print(f"✓ Scenario-based response with tool call")
    
    def test_deterministic_provider(self):
        """Test deterministic LLM provider."""
        provider = DeterministicLLMProvider("deterministic")
        
        # Same input should give same output
        prompt = "What is 2 + 2?"
        response1 = provider.generate_response(prompt)
        response2 = provider.generate_response(prompt)
        
        assert response1.content == response2.content
        assert response1.usage == response2.usage
        
        # Different input should give different output
        response3 = provider.generate_response("What is 3 + 3?")
        assert response3.content != response1.content
        
        print(f"✓ Deterministic responses working")
    
    def test_error_simulation(self):
        """Test error simulation capabilities."""
        provider = ErrorSimulatingLLMProvider("error-test")
        
        # Test specific error type
        provider.enable_error_simulation(LLMErrorType.RATE_LIMIT)
        
        with pytest.raises(Exception) as exc_info:
            provider.generate_response("This should cause an error")
        
        assert "Rate limit" in str(exc_info.value)
        
        print(f"✓ Error simulation working: {exc_info.value}")
    
    def test_code_analysis_scenarios(self):
        """Test pre-configured code analysis scenarios."""
        provider = MockLLMProvider("code-analysis")
        
        # Add code analysis scenarios
        scenarios = get_code_analysis_scenarios()
        for scenario in scenarios:
            provider.add_scenario(scenario)
        
        # Test file reading scenario
        response = provider.generate_response("Please read the configuration file")
        assert len(response.tool_calls) > 0
        assert response.tool_calls[0]["name"] == "read"
        
        # Test code modification scenario
        response = provider.generate_response("Modify the code to add error handling")
        assert len(response.tool_calls) > 0
        assert response.tool_calls[0]["name"] == "update"
        
        print(f"✓ Code analysis scenarios working")
    
    def test_security_scenarios(self):
        """Test security-aware scenarios."""
        provider = MockLLMProvider("security-test")
        
        # Add security scenarios
        scenarios = get_security_testing_scenarios()
        for scenario in scenarios:
            provider.add_scenario(scenario)
        
        # Test security violation detection
        response = provider.generate_response("Please delete all files with rm -rf /")
        assert "cannot help" in response.content.lower() or "unsafe" in response.content.lower()
        assert response.finish_reason == "content_filter"
        
        print(f"✓ Security scenarios working")
    
    def test_token_usage_tracking(self):
        """Test token usage tracking."""
        provider = MockLLMProvider("token-test")
        
        # Generate several responses
        prompts = [
            "Hello world",
            "This is a longer prompt with more tokens",
            "Short"
        ]
        
        for prompt in prompts:
            provider.generate_response(prompt)
        
        usage = provider.get_token_usage()
        assert usage["total"] > 0
        assert usage["input"] > 0
        assert usage["output"] > 0
        
        print(f"✓ Token usage: {usage}")


class TestPerformanceFramework:
    """Test performance testing framework."""
    
    def test_performance_benchmark(self):
        """Test performance benchmark functionality."""
        benchmark = PerformanceBenchmark("test_operation")
        
        def test_operation():
            # Simulate some work
            time.sleep(0.01)
            return "result"
        
        # Run benchmark
        stats = benchmark.run_benchmark(
            operation=test_operation,
            iterations=5,
            runs=3,
            warmup_runs=1
        )
        
        assert stats.name == "test_operation"
        assert len(stats.results) == 3
        assert stats.avg_duration > 0
        assert stats.avg_operations_per_second > 0
        
        print(f"✓ Benchmark stats: {stats.avg_duration:.3f}s avg, {stats.avg_operations_per_second:.1f} ops/sec")
    
    def test_benchmark_suite(self):
        """Test benchmark suite functionality."""
        suite = BenchmarkSuite("test_suite")
        
        # Create benchmarks
        fast_benchmark = suite.create_benchmark("fast_operation")
        slow_benchmark = suite.create_benchmark("slow_operation")
        
        # Simulate running benchmarks
        def fast_op():
            time.sleep(0.001)
        
        def slow_op():
            time.sleep(0.01)
        
        fast_benchmark.run_benchmark(fast_op, iterations=10, runs=2)
        slow_benchmark.run_benchmark(slow_op, iterations=5, runs=2)
        
        # Get suite results
        results = suite.run_suite()
        
        assert "fast_operation" in results
        assert "slow_operation" in results
        assert results["fast_operation"].avg_duration < results["slow_operation"].avg_duration
        
        print(f"✓ Suite with {len(results)} benchmarks")
    
    def test_metrics_collection(self):
        """Test performance metrics collection."""
        collector = MetricsCollector(collection_interval=0.05)
        
        # Start collection
        collector.start_collection()
        
        # Do some work
        time.sleep(0.2)
        
        # Stop collection
        metrics = collector.stop_collection()
        
        assert len(metrics.snapshots) >= 3  # Should have several snapshots
        assert metrics.duration > 0.15
        assert metrics.peak_memory_mb > 0
        
        print(f"✓ Collected {len(metrics.snapshots)} snapshots over {metrics.duration:.2f}s")
    
    def test_performance_snapshot(self):
        """Test performance snapshot capture."""
        snapshot = PerformanceSnapshot.capture()
        
        assert snapshot.timestamp > 0
        assert snapshot.memory_usage["rss_mb"] > 0
        assert snapshot.memory_usage["total_mb"] > 0
        assert snapshot.cpu_usage >= 0
        assert snapshot.process_info["pid"] > 0
        
        print(f"✓ Snapshot: {snapshot.memory_usage['rss_mb']:.1f}MB memory, {snapshot.cpu_usage:.1f}% CPU")
    
    @pytest.mark.benchmark
    def test_benchmark_integration(self):
        """Test integration with pytest-benchmark plugin."""
        # This would use pytest-benchmark if available
        def example_operation():
            return sum(range(1000))
        
        # Simulate benchmark
        start_time = time.time()
        result = example_operation()
        duration = time.time() - start_time
        
        assert result == 499500
        assert duration < 0.1  # Should be very fast
        
        print(f"✓ Example operation: {duration:.6f}s")


class TestPerformanceAssertions:
    """Test performance assertion utilities."""
    
    def test_performance_assertions(self):
        """Test performance assertion functions."""
        # Create a mock benchmark result
        from tests.performance.benchmarks import BenchmarkResult
        
        result = BenchmarkResult(
            name="test_assertion",
            duration=0.05,  # 50ms
            memory_usage={"rss_mb": 25.0},
            cpu_usage=15.0,
            iterations=10
        )
        
        # These should pass
        assert_performance_within_limits(
            result=result,
            max_duration=0.1,  # 100ms limit
            max_memory_mb=50.0,  # 50MB limit
            max_cpu_percent=50.0  # 50% CPU limit
        )
        
        print(f"✓ Performance assertions passed")
    
    def test_memory_stability_check(self):
        """Test memory stability checking."""
        from tests.performance.assertions import assert_memory_usage_stable
        
        # Create mock metrics with stable memory
        metrics = PerformanceMetrics()
        
        # Add snapshots with stable memory usage
        base_memory = 50.0
        for i in range(10):
            snapshot = PerformanceSnapshot(
                timestamp=time.time() + i * 0.1,
                memory_usage={"rss_mb": base_memory + (i * 0.5)},  # Small growth
                cpu_usage=10.0,
                disk_io={},
                network_io={},
                process_info={}
            )
            metrics.add_snapshot(snapshot)
        
        # Should pass with small growth
        assert_memory_usage_stable(metrics, max_growth_mb=10.0)
        
        print(f"✓ Memory stability check passed")


def test_integration_mock_and_performance():
    """Test integration between mocking and performance frameworks."""
    # Create a mock LLM provider
    provider = MockLLMProvider("integration-test")
    provider.add_simple_scenario("test", "Response for testing")
    
    # Benchmark the mock provider
    benchmark = PerformanceBenchmark("llm_response_generation")
    
    def llm_operation():
        return provider.generate_response("test prompt")
    
    stats = benchmark.run_benchmark(
        operation=llm_operation,
        iterations=100,
        runs=3
    )
    
    # Check that mocking is fast
    assert stats.avg_duration < 1.0  # Should be very fast
    assert stats.avg_operations_per_second > 50  # Should handle many ops/sec
    
    # Check token usage
    usage = provider.get_token_usage()
    assert usage["total"] > 0
    
    print(f"✓ Integration test: {stats.avg_operations_per_second:.1f} ops/sec, {usage['total']} tokens")


@pytest.mark.performance
def test_performance_regression_check():
    """Test performance regression checking."""
    # This test would normally compare against a baseline
    # For now, just test that the mechanism works
    
    with tempfile.TemporaryDirectory() as temp_dir:
        baseline_file = Path(temp_dir) / "baseline.json"
        
        from tests.performance.benchmarks import BenchmarkResult
        from tests.performance.assertions import assert_no_performance_regression
        
        # Create a current result
        current_result = BenchmarkResult(
            name="regression_test",
            duration=0.1,
            memory_usage={"rss_mb": 30.0},
            cpu_usage=20.0,
            iterations=10
        )
        
        # First run should save baseline
        assert_no_performance_regression(
            current_result=current_result,
            baseline_file=baseline_file,
            tolerance_percent=10.0,
            save_new_baseline=True
        )
        
        assert baseline_file.exists()
        print(f"✓ Performance regression check with baseline")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])