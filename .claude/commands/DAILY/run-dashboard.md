# Run Streamlit Dashboard

Launch the enhanced Streamlit dashboard for traffic visualization.

## Usage
```
/run-dashboard [port]
```

## Examples
```
/run-dashboard
/run-dashboard 8502
```

## Implementation
```bash
#!/bin/bash
set -euo pipefail

PORT=${1:-8501}

cd /path/to/project
source .venv/bin/activate

streamlit run enhanced_demo.py \
  --server.port $PORT \
  --server.address 0.0.0.0 \
  --browser.gatherUsageStats false
```

## Access
Open http://localhost:$PORT in browser.
