#!/usr/bin/env python3
"""
Automated Test Runner for Adaptive Traffic Signal System
Top 0.1% Expert Testing Team Implementation
"""

import os
import sys
import time
import json
import subprocess
import threading
import asyncio
from pathlib import Path
from datetime import datetime
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_runner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomatedTestRunner:
    """Comprehensive automated test runner"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.test_results = {}
        self.start_time = time.time()
        
        # Test configuration
        self.test_config = {
            'test_categories': [
                'unit_tests',
                'integration_tests',
                'performance_tests',
                'security_tests',
                'comprehensive_framework'
            ],
            'timeout_seconds': 300,  # 5 minutes per test category
            'parallel_execution': True,
            'generate_reports': True,
            'coverage_threshold': 90.0,
            'performance_thresholds': {
                'vehicle_detection_ms': 2000,
                'simulation_fps': 30,
                'memory_usage_mb': 800
            }
        }
        
        # Test files
        self.test_files = {
            'unit_tests': [
                'tests/test_vehicle_detection_unit.py',
                'tests/test_simulation_unit.py'
            ],
            'integration_tests': [
                'tests/test_integration.py'
            ],
            'performance_tests': [
                'tests/test_performance.py'
            ],
            'security_tests': [
                'tests/test_security.py'
            ],
            'comprehensive_framework': [
                'tests/comprehensive_test_framework.py'
            ]
        }
    
    def run_all_tests(self, categories: list = None) -> dict:
        """Run all specified test categories"""
        if categories is None:
            categories = self.test_config['test_categories']
        
        logger.info("Starting Automated Test Runner for Adaptive Traffic Signal System")
        logger.info("=" * 80)
        
        # Check project structure
        if not self._validate_project_structure():
            return {'success': False, 'error': 'Project structure validation failed'}
        
        # Run tests for each category
        for category in categories:
            if category in self.test_files:
                logger.info(f"\nRunning {category.replace('_', ' ').title()}...")
                result = self._run_test_category(category)
                self.test_results[category] = result
                
                if not result['success']:
                    logger.error(f"Test category {category} failed: {result.get('error', 'Unknown error')}")
                else:
                    logger.info(f"Test category {category} completed successfully")
        
        # Generate comprehensive report
        if self.test_config['generate_reports']:
            self._generate_test_report()
        
        # Calculate overall success
        total_categories = len(self.test_results)
        successful_categories = sum(1 for r in self.test_results.values() if r['success'])
        overall_success = successful_categories == total_categories
        
        return {
            'success': overall_success,
            'total_categories': total_categories,
            'successful_categories': successful_categories,
            'test_results': self.test_results,
            'duration': time.time() - self.start_time
        }
    
    def _validate_project_structure(self) -> bool:
        """Validate project structure"""
        required_paths = [
            'Code/YOLO/darkflow',
            'tests',
            'src',
            'app.py'
        ]
        
        for path in required_paths:
            full_path = self.project_root / path
            if not full_path.exists():
                logger.error(f"Required path not found: {full_path}")
                return False
        
        logger.info("Project structure validation passed")
        return True
    
    def _run_test_category(self, category: str) -> dict:
        """Run tests for a specific category"""
        test_files = self.test_files[category]
        category_results = {
            'success': True,
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'errors': [],
            'duration': 0,
            'details': {}
        }
        
        start_time = time.time()
        
        for test_file in test_files:
            if not os.path.exists(test_file):
                error_msg = f"Test file not found: {test_file}"
                logger.error(error_msg)
                category_results['errors'].append(error_msg)
                category_results['success'] = False
                continue
            
            # Run individual test file
            test_result = self._run_test_file(test_file)
            
            # Aggregate results
            category_results['total_tests'] += test_result.get('total_tests', 0)
            category_results['passed_tests'] += test_result.get('passed_tests', 0)
            category_results['failed_tests'] += test_result.get('failed_tests', 0)
            
            if test_result.get('success', False):
                category_results['details'][test_file] = test_result
            else:
                category_results['errors'].extend(test_result.get('errors', [test_result.get('error', 'Unknown error')]))
                category_results['success'] = False
        
        category_results['duration'] = time.time() - start_time
        
        return category_results
    
    def _run_test_file(self, test_file: str) -> dict:
        """Run a single test file"""
        logger.info(f"  Running {test_file}...")
        
        result = {
            'success': False,
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'errors': [],
            'duration': 0,
            'output': '',
            'coverage': {}
        }
        
        start_time = time.time()
        
        try:
            # Determine test runner based on file type
            if 'comprehensive_test_framework.py' in test_file:
                # Run async framework
                cmd = [sys.executable, test_file]
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.test_config['timeout_seconds'],
                    cwd=self.project_root
                )
            else:
                # Run standard unittest
                cmd = [sys.executable, '-m', 'unittest', test_file, '-v']
                process = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.test_config['timeout_seconds'],
                    cwd=self.project_root
                )
            
            result['output'] = process.stdout + process.stderr
            result['return_code'] = process.returncode
            
            # Parse test results
            if process.returncode == 0:
                result['success'] = True
                
                # Parse unittest output
                result.update(self._parse_unittest_output(process.stdout))
            
            else:
                result['errors'].append(f"Test execution failed with return code {process.returncode}")
                if process.stderr:
                    result['errors'].append(process.stderr)
        
        except subprocess.TimeoutExpired:
            error_msg = f"Test execution timed out after {self.test_config['timeout_seconds']} seconds"
            logger.error(error_msg)
            result['errors'].append(error_msg)
        
        except Exception as e:
            error_msg = f"Exception running test file: {str(e)}"
            logger.error(error_msg)
            result['errors'].append(error_msg)
        
        result['duration'] = time.time() - start_time
        
        return result
    
    def _parse_unittest_output(self, output: str) -> dict:
        """Parse unittest output to extract test counts"""
        parsed = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'errors': 0,
            'skipped': 0
        }
        
        lines = output.split('\n')
        
        for line in lines:
            # Look for test result summary
            if 'Ran' in line and 'tests' in line:
                # Example: "Ran 25 tests in 2.345s"
                import re
                match = re.search(r'Ran (\d+) tests', line)
                if match:
                    parsed['total_tests'] = int(match.group(1))
            
            elif 'OK' in line and 'FAILED' not in line:
                # All tests passed
                parsed['passed_tests'] = parsed['total_tests']
            
            elif 'FAILED' in line:
                # Some tests failed
                if 'errors=' in line:
                    # Example: "FAILED (errors=1)"
                    error_match = re.search(r'errors=(\d+)', line)
                    if error_match:
                        parsed['errors'] = int(error_match.group(1))
                
                if 'failures=' in line:
                    # Example: "FAILED (failures=2)"
                    failure_match = re.search(r'failures=(\d+)', line)
                    if failure_match:
                        parsed['failed_tests'] = int(failure_match.group(1))
                
                # Calculate passed tests
                parsed['passed_tests'] = (parsed['total_tests'] - 
                                        parsed['failed_tests'] - 
                                        parsed['errors'] - 
                                        parsed['skipped'])
        
        return parsed
    
    def _generate_test_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "=" * 80)
        logger.info("COMPREHENSIVE TEST REPORT - ADAPTIVE TRAFFIC SIGNAL SYSTEM")
        logger.info("=" * 80)
        
        # Calculate overall statistics
        total_tests = sum(r.get('total_tests', 0) for r in self.test_results.values())
        total_passed = sum(r.get('passed_tests', 0) for r in self.test_results.values())
        total_failed = sum(r.get('failed_tests', 0) for r in self.test_results.values())
        total_errors = sum(len(r.get('errors', [])) for r in self.test_results.values())
        total_duration = sum(r.get('duration', 0) for r in self.test_results.values())
        
        success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        logger.info(f"\nOVERALL SUMMARY:")
        logger.info(f"   Total Test Categories: {len(self.test_results)}")
        logger.info(f"   Total Tests: {total_tests}")
        logger.info(f"   Passed: {total_passed}")
        logger.info(f"   Failed: {total_failed}")
        logger.info(f"   Errors: {total_errors}")
        logger.info(f"   Success Rate: {success_rate:.1f}%")
        logger.info(f"   Total Duration: {total_duration:.2f}s")
        
        # Category-wise results
        logger.info(f"\nCATEGORY-WISE RESULTS:")
        for category, results in self.test_results.items():
            status = "PASSED" if results['success'] else "FAILED"
            category_name = category.replace('_', ' ').title()
            
            logger.info(f"\n{status} - {category_name}")
            logger.info(f"  Tests: {results.get('total_tests', 0)}")
            logger.info(f"  Passed: {results.get('passed_tests', 0)}")
            logger.info(f"  Failed: {results.get('failed_tests', 0)}")
            logger.info(f"  Duration: {results.get('duration', 0):.2f}s")
            
            if results.get('errors'):
                logger.info(f"  Errors:")
                for error in results['errors'][:3]:  # Show first 3 errors
                    logger.info(f"    - {error}")
        
        # Performance summary
        perf_results = self.test_results.get('performance_tests', {})
        if perf_results.get('details'):
            logger.info(f"\nPERFORMANCE SUMMARY:")
            for test_file, details in perf_results['details'].items():
                if 'Performance' in test_file or 'performance' in test_file.lower():
                    logger.info(f"  {test_file}:")
                    logger.info(f"    Duration: {details.get('duration', 0):.2f}s")
                    logger.info(f"    Success: {details.get('success', False)}")
        
        # Security summary
        security_results = self.test_results.get('security_tests', {})
        if security_results.get('details'):
            logger.info(f"\nSECURITY SUMMARY:")
            for test_file, details in security_results['details'].items():
                if 'security' in test_file.lower():
                    logger.info(f"  {test_file}:")
                    logger.info(f"    Duration: {details.get('duration', 0):.2f}s")
                    logger.info(f"    Success: {details.get('success', False)}")
        
        # System readiness assessment
        logger.info(f"\nSYSTEM READINESS ASSESSMENT:")
        
        successful_categories = sum(1 for r in self.test_results.values() if r['success'])
        total_categories = len(self.test_results)
        
        if successful_categories == total_categories and success_rate >= 95:
            logger.info("   Status: PRODUCTION READY")
            logger.info("   All test categories passed with high success rate")
        elif successful_categories >= total_categories * 0.8 and success_rate >= 90:
            logger.info("   Status: NEAR PRODUCTION READY")
            logger.info("   Minor issues need to be addressed")
        elif successful_categories >= total_categories * 0.6 and success_rate >= 80:
            logger.info("   Status: NEEDS IMPROVEMENT")
            logger.info("   Significant issues require attention")
        else:
            logger.info("   Status: NOT READY")
            logger.info("   Major issues need to be resolved")
        
        # Save detailed report
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "test_configuration": self.test_config,
            "overall_summary": {
                "total_categories": total_categories,
                "successful_categories": successful_categories,
                "total_tests": total_tests,
                "passed_tests": total_passed,
                "failed_tests": total_failed,
                "total_errors": total_errors,
                "success_rate": success_rate,
                "total_duration": total_duration,
                "system_readiness": self._assess_system_readiness(successful_categories, total_categories, success_rate)
            },
            "category_results": self.test_results
        }
        
        # Save JSON report
        report_file = self.project_root / "automated_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        logger.info(f"\nDetailed report saved to: {report_file}")
    
    def _assess_system_readiness(self, successful_categories: int, 
                                total_categories: int, success_rate: float) -> str:
        """Assess overall system readiness"""
        if successful_categories == total_categories and success_rate >= 95:
            return "PRODUCTION READY"
        elif successful_categories >= total_categories * 0.8 and success_rate >= 90:
            return "NEAR PRODUCTION READY"
        elif successful_categories >= total_categories * 0.6 and success_rate >= 80:
            return "NEEDS IMPROVEMENT"
        else:
            return "NOT READY"

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Automated Test Runner for Adaptive Traffic Signal System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python automated_test_runner.py                    # Run all tests
  python automated_test_runner.py --categories unit_tests integration_tests  # Run specific categories
  python automated_test_runner.py --timeout 600    # Set timeout to 10 minutes
  python automated_test_runner.py --no-reports      # Don't generate reports
        """
    )
    
    parser.add_argument(
        '--categories',
        nargs='+',
        choices=['unit_tests', 'integration_tests', 'performance_tests', 'security_tests', 'comprehensive_framework'],
        help='Test categories to run (default: all)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='Timeout in seconds per test category (default: 300)'
    )
    
    parser.add_argument(
        '--no-reports',
        action='store_true',
        help='Don\'t generate test reports'
    )
    
    parser.add_argument(
        '--project-root',
        default='.',
        help='Project root directory (default: current directory)'
    )
    
    args = parser.parse_args()
    
    # Create test runner
    runner = AutomatedTestRunner(args.project_root)
    
    # Configure based on arguments
    if args.timeout:
        runner.test_config['timeout_seconds'] = args.timeout
    
    if args.no_reports:
        runner.test_config['generate_reports'] = False
    
    # Run tests
    try:
        results = runner.run_all_tests(args.categories)
        
        # Print final status
        if results['success']:
            logger.info("\n🎉 All tests completed successfully!")
            return 0
        else:
            logger.error(f"\n❌ Some tests failed. {results['successful_categories']}/{results['total_categories']} categories passed.")
            return 1
    
    except KeyboardInterrupt:
        logger.info("\n⚠️ Test execution interrupted by user")
        return 2
    except Exception as e:
        logger.error(f"\n💥 Unexpected error: {str(e)}")
        return 3

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)