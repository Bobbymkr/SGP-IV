# Run All Tests

Execute the comprehensive test suite.

## Usage
```
/test-all [coverage]
```

## Examples
```
/test-all
/test-all true
```

## Implementation
```bash
#!/bin/bash
set -euo pipefail

COVERAGE=${1:-false}

cd /path/to/project
source .venv/bin/activate

if [ "$COVERAGE" = "true" ]; then
  python -m pytest tests/ -v --cov=src --cov=Code --cov-report=term-missing --cov-report=html
else
  python -m pytest tests/ -v --tb=short
fi

echo "Test suite complete."
```

## Test Categories
- Unit: `tests/test_*_unit.py`
- Integration: `tests/test_integration.py`
- Performance: `tests/test_performance.py`
- Security: `tests/test_security.py`
- Edge Cases: `tests/test_edge_cases.py`