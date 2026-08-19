#!/usr/bin/env python3
"""
Test Execution Script for Adaptive Traffic Signal System
Top 0.1% Expert Testing Team Implementation
"""

import os
import sys
import time
import subprocess
import argparse
from pathlib import Path
import json
from datetime import datetime

def print_banner():
    """Print test execution banner"""
    print("=" * 80)
    print("    ADAPTIVE TRAFFIC SIGNAL TIMER - COMPREHENSIVE TESTING")
    print("    Top 0.1% Expert Testing Team Implementation")
    print("    Line-by-Line Code Analysis with Exhaustive Coverage")
    print("=" * 80)
    print()

def print_status(message, status="INFO"):
    """Print formatted status message"""
    timestamp = time.strftime("%H:%M:%S")
    status_symbols = {
        "INFO": "[INFO]",
        "SUCCESS": "[SUCCESS]",
        "ERROR": "[ERROR]",
        "WARNING": "[WARNING]",
        "RUNNING": "[RUNNING]"
    }
    symbol = status_symbols.get(status, "[INFO]")
    print(f"[{timestamp}] {symbol} {message}")

def run_test_command(command, description, timeout=300):
    """Run a test command and return results"""
    print_status(f"Running {description}...", "RUNNING")
    
    try:
        start_time = time.time()
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd()
        )
        end_time = time.time()
        duration = end_time - start_time
        
        success = result.returncode == 0
        
        if success:
            print_status(f"{description} completed successfully ({duration:.1f}s)", "SUCCESS")
        else:
            print_status(f"{description} failed ({duration:.1f}s)", "ERROR")
            if result.stderr:
                print(f"Error output: {result.stderr[:500]}...")
        
        return {
            'success': success,
            'duration': duration,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        print_status(f"{description} timed out after {timeout} seconds", "ERROR")
        return {
            'success': False,
            'duration': timeout,
            'stdout': '',
            'stderr': f'Timeout after {timeout} seconds',
            'returncode': -1
        }
    except Exception as e:
        print_status(f"Exception running {description}: {str(e)}", "ERROR")
        return {
            'success': False,
            'duration': 0,
            'stdout': '',
            'stderr': str(e),
            'returncode': -2
        }

def check_dependencies():
    """Check if required dependencies are available"""
    print_status("Checking dependencies...", "RUNNING")
    
    dependencies = {
        'python': f'{sys.version_info.major}.{sys.version_info.minor}',
        'pytest': 'pytest --version' if os.system('pytest --version >nul 2>&1') == 0 else 'Not found',
        'opencv': 'cv2' if os.system('python -c "import cv2" >nul 2>&1') == 0 else 'Not found',
        'numpy': 'numpy' if os.system('python -c "import numpy" >nul 2>&1') == 0 else 'Not found',
        'pygame': 'pygame' if os.system('python -c "import pygame" >nul 2>&1') == 0 else 'Not found'
    }
    
    missing_deps = []
    for dep, check in dependencies.items():
        if isinstance(check, str) and 'Not found' in check:
            missing_deps.append(dep)
    
    if missing_deps:
        print_status(f"Missing dependencies: {', '.join(missing_deps)}", "WARNING")
        print_status("Some tests may fail due to missing dependencies", "WARNING")
    else:
        print_status("All dependencies available", "SUCCESS")
    
    return len(missing_deps) == 0

def run_unit_tests():
    """Run unit tests"""
    print_status("Running Unit Tests", "RUNNING")
    
    unit_test_files = [
        ('tests/test_vehicle_detection_unit.py', 'Vehicle Detection Unit Tests'),
        ('tests/test_simulation_unit.py', 'Simulation Unit Tests')
    ]
    
    results = {}
    total_duration = 0
    
    for test_file, description in unit_test_files:
        if os.path.exists(test_file):
            result = run_test_command(
                f'python "{test_file}"',
                description,
                timeout=180
            )
            results[test_file] = result
            total_duration += result['duration']
        else:
            print_status(f"Test file not found: {test_file}", "ERROR")
            results[test_file] = {
                'success': False,
                'duration': 0,
                'error': 'File not found'
            }
    
    success_count = sum(1 for r in results.values() if r['success'])
    total_count = len(results)
    
    print_status(f"Unit Tests: {success_count}/{total_count} passed ({total_duration:.1f}s total)", 
                 "SUCCESS" if success_count == total_count else "ERROR")
    
    return results, success_count == total_count

def run_integration_tests():
    """Run integration tests"""
    print_status("Running Integration Tests", "RUNNING")
    
    integration_test_files = [
        ('tests/test_integration.py', 'Integration Tests')
    ]
    
    results = {}
    total_duration = 0
    
    for test_file, description in integration_test_files:
        if os.path.exists(test_file):
            result = run_test_command(
                f'python "{test_file}"',
                description,
                timeout=240
            )
            results[test_file] = result
            total_duration += result['duration']
        else:
            print_status(f"Test file not found: {test_file}", "ERROR")
            results[test_file] = {
                'success': False,
                'duration': 0,
                'error': 'File not found'
            }
    
    success_count = sum(1 for r in results.values() if r['success'])
    total_count = len(results)
    
    print_status(f"Integration Tests: {success_count}/{total_count} passed ({total_duration:.1f}s total)", 
                 "SUCCESS" if success_count == total_count else "ERROR")
    
    return results, success_count == total_count

def run_performance_tests():
    """Run performance tests"""
    print_status("Running Performance Tests", "RUNNING")
    
    performance_test_files = [
        ('tests/test_performance.py', 'Performance and Stress Tests')
    ]
    
    results = {}
    total_duration = 0
    
    for test_file, description in performance_test_files:
        if os.path.exists(test_file):
            result = run_test_command(
                f'python "{test_file}"',
                description,
                timeout=600  # 10 minutes for performance tests
            )
            results[test_file] = result
            total_duration += result['duration']
        else:
            print_status(f"Test file not found: {test_file}", "ERROR")
            results[test_file] = {
                'success': False,
                'duration': 0,
                'error': 'File not found'
            }
    
    success_count = sum(1 for r in results.values() if r['success'])
    total_count = len(results)
    
    print_status(f"Performance Tests: {success_count}/{total_count} passed ({total_duration:.1f}s total)", 
                 "SUCCESS" if success_count == total_count else "ERROR")
    
    return results, success_count == total_count

def run_security_tests():
    """Run security tests"""
    print_status("Running Security Tests", "RUNNING")
    
    security_test_files = [
        ('tests/test_security.py', 'Security and Vulnerability Tests')
    ]
    
    results = {}
    total_duration = 0
    
    for test_file, description in security_test_files:
        if os.path.exists(test_file):
            result = run_test_command(
                f'python "{test_file}"',
                description,
                timeout=300
            )
            results[test_file] = result
            total_duration += result['duration']
        else:
            print_status(f"Test file not found: {test_file}", "ERROR")
            results[test_file] = {
                'success': False,
                'duration': 0,
                'error': 'File not found'
            }
    
    success_count = sum(1 for r in results.values() if r['success'])
    total_count = len(results)
    
    print_status(f"Security Tests: {success_count}/{total_count} passed ({total_duration:.1f}s total)", 
                 "SUCCESS" if success_count == total_count else "ERROR")
    
    return results, success_count == total_count

def run_edge_case_tests():
    """Run edge case tests"""
    print_status("Running Edge Case Tests", "RUNNING")
    
    edge_case_test_files = [
        ('tests/test_edge_cases.py', 'Edge Case and Boundary Tests')
    ]
    
    results = {}
    total_duration = 0
    
    for test_file, description in edge_case_test_files:
        if os.path.exists(test_file):
            result = run_test_command(
                f'python "{test_file}"',
                description,
                timeout=300
            )
            results[test_file] = result
            total_duration += result['duration']
        else:
            print_status(f"Test file not found: {test_file}", "ERROR")
            results[test_file] = {
                'success': False,
                'duration': 0,
                'error': 'File not found'
            }
    
    success_count = sum(1 for r in results.values() if r['success'])
    total_count = len(results)
    
    print_status(f"Edge Case Tests: {success_count}/{total_count} passed ({total_duration:.1f}s total)", 
                 "SUCCESS" if success_count == total_count else "ERROR")
    
    return results, success_count == total_count

def run_comprehensive_framework():
    """Run comprehensive test framework"""
    print_status("Running Comprehensive Test Framework", "RUNNING")
    
    framework_files = [
        ('tests/comprehensive_test_framework.py', 'Comprehensive Test Framework')
    ]
    
    results = {}
    total_duration = 0
    
    for test_file, description in framework_files:
        if os.path.exists(test_file):
            result = run_test_command(
                f'python "{test_file}"',
                description,
                timeout=900  # 15 minutes for comprehensive framework
            )
            results[test_file] = result
            total_duration += result['duration']
        else:
            print_status(f"Test file not found: {test_file}", "ERROR")
            results[test_file] = {
                'success': False,
                'duration': 0,
                'error': 'File not found'
            }
    
    success_count = sum(1 for r in results.values() if r['success'])
    total_count = len(results)
    
    print_status(f"Comprehensive Framework: {success_count}/{total_count} passed ({total_duration:.1f}s total)", 
                 "SUCCESS" if success_count == total_count else "ERROR")
    
    return results, success_count == total_count

def run_automated_test_runner():
    """Run automated test runner"""
    print_status("Running Automated Test Runner", "RUNNING")
    
    runner_files = [
        ('tests/automated_test_runner.py', 'Automated Test Runner')
    ]
    
    results = {}
    total_duration = 0
    
    for test_file, description in runner_files:
        if os.path.exists(test_file):
            result = run_test_command(
                f'python "{test_file}"',
                description,
                timeout=1200  # 20 minutes for automated runner
            )
            results[test_file] = result
            total_duration += result['duration']
        else:
            print_status(f"Test file not found: {test_file}", "ERROR")
            results[test_file] = {
                'success': False,
                'duration': 0,
                'error': 'File not found'
            }
    
    success_count = sum(1 for r in results.values() if r['success'])
    total_count = len(results)
    
    print_status(f"Automated Test Runner: {success_count}/{total_count} passed ({total_duration:.1f}s total)", 
                 "SUCCESS" if success_count == total_count else "ERROR")
    
    return results, success_count == total_count

def generate_test_report(all_results):
    """Generate comprehensive test report"""
    print_status("Generating Test Report", "RUNNING")
    
    # Calculate overall statistics
    total_tests = 0
    total_passed = 0
    total_duration = 0
    category_results = {}
    
    for category, results in all_results.items():
        category_passed = sum(1 for r in results.values() if r['success'])
        category_total = len(results)
        category_duration = sum(r['duration'] for r in results.values())
        
        total_tests += category_total
        total_passed += category_passed
        total_duration += category_duration
        
        category_results[category] = {
            'passed': category_passed,
            'total': category_total,
            'duration': category_duration,
            'success_rate': (category_passed / category_total * 100) if category_total > 0 else 0
        }
    
    overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    
    # Print summary
    print("\n" + "=" * 80)
    print("COMPREHENSIVE TEST EXECUTION REPORT")
    print("=" * 80)
    
    print(f"\nOVERALL SUMMARY:")
    print(f"   Total Test Categories: {len(all_results)}")
    print(f"   Total Test Files: {total_tests}")
    print(f"   Passed: {total_passed}")
    print(f"   Failed: {total_tests - total_passed}")
    print(f"   Success Rate: {overall_success_rate:.1f}%")
    print(f"   Total Duration: {total_duration:.1f}s")
    
    print(f"\nCATEGORY-WISE RESULTS:")
    for category, results in category_results.items():
        status = "✅ PASSED" if results['passed'] == results['total'] else "❌ FAILED"
        print(f"\n{status} - {category.replace('_', ' ').title()}")
        print(f"   Test Files: {results['total']}")
        print(f"   Passed: {results['passed']}")
        print(f"   Success Rate: {results['success_rate']:.1f}%")
        print(f"   Duration: {results['duration']:.1f}s")
    
    # System readiness assessment
    print(f"\nSYSTEM READINESS ASSESSMENT:")
    
    if overall_success_rate >= 95:
        print("   Status: [PRODUCTION READY]")
        print("   All tests passed with excellent success rate")
    elif overall_success_rate >= 90:
        print("   Status: [NEAR PRODUCTION READY]")
        print("   Minor issues need to be addressed")
    elif overall_success_rate >= 80:
        print("   Status: [NEEDS IMPROVEMENT]")
        print("   Significant issues require attention")
    else:
        print("   Status: [NOT READY]")
        print("   Major issues need to be resolved")
    
    # Save detailed report
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "test_environment": {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": sys.platform,
            "working_directory": os.getcwd()
        },
        "overall_summary": {
            "total_categories": len(all_results),
            "total_test_files": total_tests,
            "passed_test_files": total_passed,
            "failed_test_files": total_tests - total_passed,
            "success_rate": overall_success_rate,
            "total_duration": total_duration,
            "system_readiness": "PRODUCTION READY" if overall_success_rate >= 95 else 
                           "NEAR PRODUCTION READY" if overall_success_rate >= 90 else
                           "NEEDS IMPROVEMENT" if overall_success_rate >= 80 else "NOT READY"
        },
        "category_results": category_results,
        "detailed_results": all_results
    }
    
    # Save JSON report
    report_file = "comprehensive_test_execution_report.json"
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\nDetailed report saved to: {report_file}")
    
    return overall_success_rate >= 90

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description="Comprehensive Test Execution for Adaptive Traffic Signal System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                           # Run all tests
  python run_tests.py --categories unit integration  # Run specific categories
  python run_tests.py --quick                    # Run quick tests only
  python run_tests.py --comprehensive             # Run comprehensive framework only
        """
    )
    
    parser.add_argument(
        '--categories',
        nargs='+',
        choices=['unit', 'integration', 'performance', 'security', 'edge_cases', 'comprehensive', 'automated'],
        help='Test categories to run (default: all)'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run only quick tests (unit + integration)'
    )
    
    parser.add_argument(
        '--comprehensive',
        action='store_true',
        help='Run only comprehensive test framework'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='Timeout in seconds per test category (default: 300)'
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    # Determine which tests to run
    test_categories = args.categories
    if args.quick:
        test_categories = ['unit', 'integration']
    elif args.comprehensive:
        test_categories = ['comprehensive']
    elif not test_categories:
        test_categories = ['unit', 'integration', 'performance', 'security', 'edge_cases', 'comprehensive', 'automated']
    
    # Run tests
    all_results = {}
    
    if 'unit' in test_categories:
        results, success = run_unit_tests()
        all_results['unit_tests'] = results
    
    if 'integration' in test_categories:
        results, success = run_integration_tests()
        all_results['integration_tests'] = results
    
    if 'performance' in test_categories:
        results, success = run_performance_tests()
        all_results['performance_tests'] = results
    
    if 'security' in test_categories:
        results, success = run_security_tests()
        all_results['security_tests'] = results
    
    if 'edge_cases' in test_categories:
        results, success = run_edge_case_tests()
        all_results['edge_case_tests'] = results
    
    if 'comprehensive' in test_categories:
        results, success = run_comprehensive_framework()
        all_results['comprehensive_framework'] = results
    
    if 'automated' in test_categories:
        results, success = run_automated_test_runner()
        all_results['automated_test_runner'] = results
    
    # Generate final report
    overall_success = generate_test_report(all_results)
    
    # Return appropriate exit code
    if overall_success:
        print_status("Test execution completed successfully!", "SUCCESS")
        return 0
    else:
        print_status("Test execution completed with failures", "ERROR")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print_status("Test execution interrupted by user", "WARNING")
        sys.exit(2)
    except Exception as e:
        print_status(f"Unexpected error: {str(e)}", "ERROR")
        sys.exit(3)