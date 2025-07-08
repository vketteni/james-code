"""Performance metrics collection and analysis for James Code testing."""

import time
import psutil
import threading
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path
import statistics
import json

import pytest


@dataclass
class PerformanceSnapshot:
    """Snapshot of performance metrics at a point in time."""
    timestamp: float
    memory_usage: Dict[str, float]
    cpu_usage: float
    disk_io: Dict[str, int]
    network_io: Dict[str, int]
    process_info: Dict[str, Any]
    
    @classmethod
    def capture(cls) -> 'PerformanceSnapshot':
        """Capture current performance snapshot.
        
        Returns:
            Performance snapshot
        """
        process = psutil.Process()
        
        # Memory info
        memory_info = process.memory_info()
        memory_usage = {
            "rss_mb": memory_info.rss / 1024 / 1024,
            "vms_mb": memory_info.vms / 1024 / 1024,
            "percent": process.memory_percent(),
            "available_mb": psutil.virtual_memory().available / 1024 / 1024,
            "total_mb": psutil.virtual_memory().total / 1024 / 1024
        }
        
        # Disk I/O
        try:
            disk_io_info = process.io_counters()
            disk_io = {
                "read_bytes": disk_io_info.read_bytes,
                "write_bytes": disk_io_info.write_bytes,
                "read_count": disk_io_info.read_count,
                "write_count": disk_io_info.write_count
            }
        except (psutil.AccessDenied, AttributeError):
            disk_io = {"read_bytes": 0, "write_bytes": 0, "read_count": 0, "write_count": 0}
        
        # Network I/O (system-wide)
        try:
            net_io_info = psutil.net_io_counters()
            network_io = {
                "bytes_sent": net_io_info.bytes_sent,
                "bytes_recv": net_io_info.bytes_recv,
                "packets_sent": net_io_info.packets_sent,
                "packets_recv": net_io_info.packets_recv
            }
        except AttributeError:
            network_io = {"bytes_sent": 0, "bytes_recv": 0, "packets_sent": 0, "packets_recv": 0}
        
        # Process info
        process_info = {
            "pid": process.pid,
            "num_threads": process.num_threads(),
            "num_fds": process.num_fds() if hasattr(process, 'num_fds') else 0,
            "create_time": process.create_time(),
            "status": process.status()
        }
        
        return cls(
            timestamp=time.time(),
            memory_usage=memory_usage,
            cpu_usage=process.cpu_percent(),
            disk_io=disk_io,
            network_io=network_io,
            process_info=process_info
        )


@dataclass
class PerformanceMetrics:
    """Collection of performance metrics over time."""
    snapshots: List[PerformanceSnapshot] = field(default_factory=list)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    
    def add_snapshot(self, snapshot: PerformanceSnapshot):
        """Add a performance snapshot.
        
        Args:
            snapshot: Snapshot to add
        """
        self.snapshots.append(snapshot)
        
        if self.start_time is None:
            self.start_time = snapshot.timestamp
        self.end_time = snapshot.timestamp
    
    @property
    def duration(self) -> float:
        """Total duration of metrics collection.
        
        Returns:
            Duration in seconds
        """
        if self.start_time is None or self.end_time is None:
            return 0
        return self.end_time - self.start_time
    
    @property
    def peak_memory_mb(self) -> float:
        """Peak memory usage in MB.
        
        Returns:
            Peak memory usage
        """
        if not self.snapshots:
            return 0
        return max(snapshot.memory_usage["rss_mb"] for snapshot in self.snapshots)
    
    @property
    def avg_memory_mb(self) -> float:
        """Average memory usage in MB.
        
        Returns:
            Average memory usage
        """
        if not self.snapshots:
            return 0
        return statistics.mean(snapshot.memory_usage["rss_mb"] for snapshot in self.snapshots)
    
    @property
    def avg_cpu_percent(self) -> float:
        """Average CPU usage percentage.
        
        Returns:
            Average CPU percentage
        """
        if not self.snapshots:
            return 0
        cpu_values = [s.cpu_usage for s in self.snapshots if s.cpu_usage > 0]
        return statistics.mean(cpu_values) if cpu_values else 0
    
    @property
    def peak_cpu_percent(self) -> float:
        """Peak CPU usage percentage.
        
        Returns:
            Peak CPU percentage
        """
        if not self.snapshots:
            return 0
        return max(snapshot.cpu_usage for snapshot in self.snapshots)
    
    @property
    def total_disk_read_mb(self) -> float:
        """Total disk read in MB.
        
        Returns:
            Total disk read
        """
        if len(self.snapshots) < 2:
            return 0
        
        start_read = self.snapshots[0].disk_io["read_bytes"]
        end_read = self.snapshots[-1].disk_io["read_bytes"]
        return (end_read - start_read) / 1024 / 1024
    
    @property
    def total_disk_write_mb(self) -> float:
        """Total disk write in MB.
        
        Returns:
            Total disk write
        """
        if len(self.snapshots) < 2:
            return 0
        
        start_write = self.snapshots[0].disk_io["write_bytes"]
        end_write = self.snapshots[-1].disk_io["write_bytes"]
        return (end_write - start_write) / 1024 / 1024
    
    def get_memory_trend(self) -> List[Dict[str, float]]:
        """Get memory usage trend over time.
        
        Returns:
            List of time/memory points
        """
        return [
            {
                "time": snapshot.timestamp - self.start_time if self.start_time else 0,
                "memory_mb": snapshot.memory_usage["rss_mb"]
            }
            for snapshot in self.snapshots
        ]
    
    def get_cpu_trend(self) -> List[Dict[str, float]]:
        """Get CPU usage trend over time.
        
        Returns:
            List of time/CPU points
        """
        return [
            {
                "time": snapshot.timestamp - self.start_time if self.start_time else 0,
                "cpu_percent": snapshot.cpu_usage
            }
            for snapshot in self.snapshots
        ]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of performance metrics.
        
        Returns:
            Summary dictionary
        """
        return {
            "duration": self.duration,
            "snapshots_count": len(self.snapshots),
            "memory": {
                "peak_mb": self.peak_memory_mb,
                "avg_mb": self.avg_memory_mb,
                "trend": self.get_memory_trend()
            },
            "cpu": {
                "peak_percent": self.peak_cpu_percent,
                "avg_percent": self.avg_cpu_percent,
                "trend": self.get_cpu_trend()
            },
            "disk_io": {
                "total_read_mb": self.total_disk_read_mb,
                "total_write_mb": self.total_disk_write_mb
            }
        }
    
    def export_to_json(self, file_path: Path):
        """Export metrics to JSON file.
        
        Args:
            file_path: Path to export file
        """
        summary = self.get_summary()
        
        with open(file_path, 'w') as f:
            json.dump(summary, f, indent=2)


class MetricsCollector:
    """Collector for performance metrics during testing."""
    
    def __init__(self, collection_interval: float = 0.1):
        """Initialize metrics collector.
        
        Args:
            collection_interval: Interval between collections in seconds
        """
        self.collection_interval = collection_interval
        self.metrics = PerformanceMetrics()
        self.collecting = False
        self._collection_thread: Optional[threading.Thread] = None
    
    def start_collection(self):
        """Start collecting performance metrics."""
        if self.collecting:
            return
        
        self.collecting = True
        self._collection_thread = threading.Thread(target=self._collection_loop)
        self._collection_thread.start()
    
    def stop_collection(self) -> PerformanceMetrics:
        """Stop collecting metrics and return results.
        
        Returns:
            Collected performance metrics
        """
        self.collecting = False
        
        if self._collection_thread:
            self._collection_thread.join(timeout=1.0)
        
        return self.metrics
    
    def collect_snapshot(self):
        """Collect a single performance snapshot."""
        snapshot = PerformanceSnapshot.capture()
        self.metrics.add_snapshot(snapshot)
    
    def _collection_loop(self):
        """Main collection loop."""
        while self.collecting:
            try:
                self.collect_snapshot()
                time.sleep(self.collection_interval)
            except Exception:
                # Handle errors gracefully
                break
    
    def reset(self):
        """Reset all collected metrics."""
        self.metrics = PerformanceMetrics()


class ResourceMonitor:
    """Monitor specific resource usage patterns."""
    
    def __init__(self):
        """Initialize resource monitor."""
        self.memory_alerts: List[Dict[str, Any]] = []
        self.cpu_alerts: List[Dict[str, Any]] = []
        self.disk_alerts: List[Dict[str, Any]] = []
        
        # Thresholds
        self.memory_threshold_mb = 500  # 500MB
        self.cpu_threshold_percent = 80  # 80%
        self.disk_io_threshold_mb = 100  # 100MB/s
    
    def check_resource_limits(self, snapshot: PerformanceSnapshot):
        """Check if resource limits are exceeded.
        
        Args:
            snapshot: Performance snapshot to check
        """
        # Check memory
        if snapshot.memory_usage["rss_mb"] > self.memory_threshold_mb:
            alert = {
                "timestamp": snapshot.timestamp,
                "type": "memory",
                "value": snapshot.memory_usage["rss_mb"],
                "threshold": self.memory_threshold_mb,
                "message": f"Memory usage exceeded: {snapshot.memory_usage['rss_mb']:.1f}MB"
            }
            self.memory_alerts.append(alert)
        
        # Check CPU
        if snapshot.cpu_usage > self.cpu_threshold_percent:
            alert = {
                "timestamp": snapshot.timestamp,
                "type": "cpu",
                "value": snapshot.cpu_usage,
                "threshold": self.cpu_threshold_percent,
                "message": f"CPU usage exceeded: {snapshot.cpu_usage:.1f}%"
            }
            self.cpu_alerts.append(alert)
    
    def get_alerts(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all resource alerts.
        
        Returns:
            Dictionary of alerts by type
        """
        return {
            "memory": self.memory_alerts,
            "cpu": self.cpu_alerts,
            "disk": self.disk_alerts
        }
    
    def has_violations(self) -> bool:
        """Check if any resource violations occurred.
        
        Returns:
            True if violations occurred
        """
        return (len(self.memory_alerts) > 0 or 
                len(self.cpu_alerts) > 0 or 
                len(self.disk_alerts) > 0)
    
    def reset(self):
        """Reset all alerts."""
        self.memory_alerts.clear()
        self.cpu_alerts.clear()
        self.disk_alerts.clear()


class MemoryTracker:
    """Track memory usage patterns for leak detection."""
    
    def __init__(self):
        """Initialize memory tracker."""
        self.baseline: Optional[float] = None
        self.measurements: List[Dict[str, Any]] = []
        self.leak_threshold_mb = 50  # 50MB increase considered potential leak
    
    def set_baseline(self):
        """Set baseline memory usage."""
        snapshot = PerformanceSnapshot.capture()
        self.baseline = snapshot.memory_usage["rss_mb"]
    
    def measure(self, label: str = "measurement"):
        """Take a memory measurement.
        
        Args:
            label: Label for this measurement
        """
        snapshot = PerformanceSnapshot.capture()
        measurement = {
            "timestamp": snapshot.timestamp,
            "label": label,
            "memory_mb": snapshot.memory_usage["rss_mb"],
            "delta_from_baseline": snapshot.memory_usage["rss_mb"] - (self.baseline or 0)
        }
        self.measurements.append(measurement)
    
    def detect_leaks(self) -> List[Dict[str, Any]]:
        """Detect potential memory leaks.
        
        Returns:
            List of potential leak indicators
        """
        if not self.measurements or self.baseline is None:
            return []
        
        leaks = []
        
        # Check for sustained growth
        if len(self.measurements) >= 3:
            recent_measurements = self.measurements[-3:]
            growth_trend = all(
                m["memory_mb"] > self.measurements[i]["memory_mb"] 
                for i, m in enumerate(recent_measurements[1:], 1)
            )
            
            if growth_trend:
                total_growth = recent_measurements[-1]["memory_mb"] - recent_measurements[0]["memory_mb"]
                if total_growth > self.leak_threshold_mb:
                    leaks.append({
                        "type": "sustained_growth",
                        "growth_mb": total_growth,
                        "start_time": recent_measurements[0]["timestamp"],
                        "end_time": recent_measurements[-1]["timestamp"]
                    })
        
        # Check for large jumps
        for i in range(1, len(self.measurements)):
            delta = self.measurements[i]["memory_mb"] - self.measurements[i-1]["memory_mb"]
            if delta > self.leak_threshold_mb:
                leaks.append({
                    "type": "large_jump",
                    "jump_mb": delta,
                    "timestamp": self.measurements[i]["timestamp"],
                    "from_label": self.measurements[i-1]["label"],
                    "to_label": self.measurements[i]["label"]
                })
        
        return leaks
    
    def get_memory_growth(self) -> float:
        """Get total memory growth from baseline.
        
        Returns:
            Memory growth in MB
        """
        if not self.measurements or self.baseline is None:
            return 0
        
        current_memory = self.measurements[-1]["memory_mb"]
        return current_memory - self.baseline
    
    def reset(self):
        """Reset all measurements."""
        self.baseline = None
        self.measurements.clear()


@pytest.fixture
def performance_metrics():
    """Provide performance metrics for testing."""
    metrics = PerformanceMetrics()
    yield metrics


@pytest.fixture
def metrics_collector():
    """Provide metrics collector for testing."""
    collector = MetricsCollector()
    yield collector
    if collector.collecting:
        collector.stop_collection()
    collector.reset()


@pytest.fixture
def resource_monitor():
    """Provide resource monitor for testing."""
    monitor = ResourceMonitor()
    yield monitor
    monitor.reset()


@pytest.fixture
def memory_tracker():
    """Provide memory tracker for testing."""
    tracker = MemoryTracker()
    yield tracker
    tracker.reset()