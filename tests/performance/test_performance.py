#!/usr/bin/env python3
"""
System Stress Tests for Adaptive Traffic Signal System.

NOTE (2026-09-18 cleanup): quarantined classes targeting the deleted
Code/YOLO/darkflow modules (TestVehicleDetectionPerformance,
TestSimulationPerformance, TestPerformanceRegression) were removed.
See docs/TEST_CLEANUP_LOG.md for the deletion record + restore hashes.
Only the live TestSystemStress remains here; real pipeline perf is gated
by scripts/bench_sim.py, scripts/bench_detect.py, scripts/bench_decide.py
and evals/runner.py — not by these synthetic FFT/RNG loops.
"""

import gc
import time
import unittest
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np


class TestSystemStress(unittest.TestCase):
    """Stress tests for the entire system"""

    def test_01_high_load_stress_test(self):
        """Test: System stability under high load"""
        stress_duration = 30  # seconds
        stress_threads = 8
        operations_per_thread = 100

        results = {"successful_operations": 0, "failed_operations": 0, "errors": []}

        def stress_operation(thread_id):
            """Simulate high-load operations"""
            thread_results = {"success": 0, "failed": 0, "errors": []}

            for i in range(operations_per_thread):
                try:
                    # Simulate vehicle detection
                    start_time = time.time()

                    # Mock intensive computation
                    data = np.random.random((1000, 1000))
                    result = np.fft.fft2(data)

                    computation_time = time.time() - start_time

                    # Simulate signal calculation
                    green_time = np.random.randint(10, 60)

                    # Simulate dashboard update
                    dashboard_data = {
                        "vehicle_count": np.random.randint(0, 50),
                        "signal_time": green_time,
                        "computation_time": computation_time,
                    }

                    thread_results["success"] += 1

                    # Small delay to simulate real work
                    time.sleep(0.01)

                except Exception as e:
                    thread_results["failed"] += 1
                    thread_results["errors"].append(f"Thread {thread_id}, Op {i}: {str(e)}")

            return thread_results

        # Run stress test
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=stress_threads) as executor:
            futures = [executor.submit(stress_operation, i) for i in range(stress_threads)]

            for future in as_completed(futures):
                thread_results = future.result()
                results["successful_operations"] += thread_results["success"]
                results["failed_operations"] += thread_results["failed"]
                results["errors"].extend(thread_results["errors"])

        end_time = time.time()
        total_duration = end_time - start_time

        # Calculate metrics
        total_operations = results["successful_operations"] + results["failed_operations"]
        success_rate = (
            results["successful_operations"] / total_operations if total_operations > 0 else 0
        )
        operations_per_second = total_operations / total_duration

        # Stress test assertions
        self.assertGreater(
            success_rate, 0.95, f"Success rate {success_rate:.2%} below 95% threshold"
        )
        self.assertLess(
            total_duration,
            stress_duration * 2,
            f"Stress test took {total_duration:.1f}s, expected <{stress_duration * 2}s",
        )

        print("Stress Test Results:")
        print(f"  Duration: {total_duration:.1f}s")
        print(f"  Total Operations: {total_operations}")
        print(f"  Successful: {results['successful_operations']}")
        print(f"  Failed: {results['failed_operations']}")
        print(f"  Success Rate: {success_rate:.2%}")
        print(f"  Operations/Second: {operations_per_second:.1f}")

        if results["errors"]:
            print(f"  Errors: {len(results['errors'])}")
            for error in results["errors"][:5]:  # Show first 5 errors
                print(f"    {error}")

    def test_02_memory_leak_stress_test(self):
        """Test: No memory leaks under extended operation"""
        try:
            import psutil

            process = psutil.Process()
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_samples = [initial_memory]

            # Run extended operation
            for cycle in range(50):  # 50 cycles
                # Simulate system workload
                data = []
                for i in range(100):
                    data.append(np.random.random((100, 100)))

                # Process data
                for array in data:
                    result = np.mean(array)

                # Clean up
                del data
                gc.collect()

                # Sample memory every 5 cycles
                if cycle % 5 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_samples.append(current_memory)

                    print(f"Cycle {cycle:2d}: Memory = {current_memory:.1f}MB")

            final_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = final_memory - initial_memory

            # Check for memory leaks
            memory_growth_rate = memory_increase / 50  # MB per cycle

            self.assertLess(
                memory_increase,
                100,
                f"Memory increased by {memory_increase:.1f}MB, possible leak detected",
            )
            self.assertLess(
                memory_growth_rate,
                2.0,
                f"Memory growth rate {memory_growth_rate:.2f}MB/cycle too high",
            )

            print("Memory Leak Test Results:")
            print(f"  Initial Memory: {initial_memory:.1f}MB")
            print(f"  Final Memory: {final_memory:.1f}MB")
            print(f"  Total Increase: {memory_increase:.1f}MB")
            print(f"  Growth Rate: {memory_growth_rate:.2f}MB/cycle")

        except ImportError:
            self.skipTest("psutil not available for memory testing")

    def test_03_resource_exhaustion_recovery(self):
        """Test: System recovery from resource exhaustion"""
        # Test memory exhaustion recovery
        try:
            import psutil

            process = psutil.Process()
            baseline_memory = process.memory_info().rss / 1024 / 1024

            # Simulate memory exhaustion
            large_data = []
            try:
                # Keep allocating until we hit a reasonable limit
                for i in range(1000):
                    large_data.append(np.random.random((1000, 1000)))

                    current_memory = process.memory_info().rss / 1024 / 1024
                    if current_memory > baseline_memory + 500:  # 500MB increase
                        break

            except MemoryError:
                pass  # Expected at some point

            # Clean up and test recovery
            del large_data
            gc.collect()
            time.sleep(2)  # Allow for cleanup

            recovered_memory = process.memory_info().rss / 1024 / 1024
            memory_recovery = (
                baseline_memory + 100 - recovered_memory
            )  # Should be close to baseline

            # System should recover memory
            self.assertLess(
                recovered_memory,
                baseline_memory + 200,
                f"System failed to recover from memory exhaustion: {recovered_memory:.1f}MB",
            )

            print("Resource Recovery Test:")
            print(f"  Baseline Memory: {baseline_memory:.1f}MB")
            print(f"  Recovered Memory: {recovered_memory:.1f}MB")
            print(f"  Recovery Success: {memory_recovery > 0}")

        except ImportError:
            self.skipTest("psutil not available for resource testing")


if __name__ == "__main__":
    # Configure test runner
    unittest.main(verbosity=2)
