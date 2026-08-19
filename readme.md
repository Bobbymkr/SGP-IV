# 🚦 Adaptive Traffic Signal Timer

> AI-powered adaptive traffic signal control system with real-time vehicle detection, dynamic signal timing optimization, and predictive analytics.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Ultralytics-orange.svg)](https://ultralytics.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 Overview

The Adaptive Traffic Signal Timer is an intelligent traffic management system that uses computer vision (YOLOv8) and reinforcement learning (DQN) to optimize traffic signal timing in real-time. The system continuously monitors traffic flow through cameras, detects vehicles, and dynamically adjusts signal phases to minimize wait times, reduce congestion, and improve overall traffic efficiency.

### ✨ Key Features

| Feature | Description |
|---------|-------------|
| **🚗 Real-time Vehicle Detection** | YOLOv8-based detection with tracking across multiple cameras |
| **🧠 Adaptive Signal Control** | Multiple algorithms: DQN (AI), Webster, Fixed-time, Fuzzy Logic |
| **📊 Predictive Analytics** | Traffic forecasting with GNN/Transformer models |
| **🌤️ Environmental Adaptation** | Weather, time-of-day, events, and pedestrian integration |
| **🚑 Emergency Vehicle Priority** | Optical, audio, and V2X-based preemption |
| **📈 Live Dashboard** | Streamlit-based real-time monitoring and control |
| **🔌 REST API** | FastAPI for integration with external systems |
| **🐳 Production Ready** | Docker, Kubernetes, monitoring, CI/CD |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Adaptive Traffic Signal System           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Cameras    │───▶│   Detection  │───▶│   Control    │      │
│  │  (Multi-view)│    │   Engine     │    │  Algorithms  │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│         │                   │                   │                │
│         ▼                   ▼                   ▼                │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  V2X/Weather │    │   Analytics  │    │   Digital    │      │
│  │   Events     │    │  Forecaster  │    │    Twin      │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    FastAPI + Streamlit                     │  │
│  │              REST API │ Live Dashboard │ WebSocket         │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
adaptive-traffic-signal/
├── .github/
│   └── workflows/          # CI/CD pipelines
├── configs/
│   ├── development.yaml    # Development config
│   ├── staging.yaml        # Staging config
│   ├── production.yaml     # Production config
│   └── docker/
│       ├── Dockerfile
│       ├── docker-compose.yml
│       ├── nginx.conf
│       └── monitoring/     # Prometheus, Grafana configs
├── docs/                   # Documentation
├── scripts/                # Operational scripts
├── src/
│   └── adaptive_traffic/
│       ├── __init__.py
│       ├── config/         # Configuration management
│       │   └── settings.py
│       ├── core/           # Core domain logic
│       │   ├── detection/  # YOLOv8 vehicle detection
│       │   ├── control/    # Signal control algorithms
│       │   ├── simulation/ # Traffic simulation engine
│       │   └── analytics/  # Predictive analytics
│       ├── api/            # FastAPI REST API
│       │   ├── main.py
│       │   └── routes/
│       │       ├── health.py
│       │       ├── signals.py
│       │       ├── detection.py
│       │       └── analytics.py
│       └── ui/             # Streamlit Dashboard
│           ├── app.py
│           ├── pages/
│           └── components/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── performance/
│   └── security/
├── .env.example            # Environment variables template
├── pyproject.toml          # Python packaging & tool config
├── Makefile                # Common development commands
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
├── README.md
└── LICENSE
```

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for production)
- CUDA-enabled GPU (recommended for detection)

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/adaptive-traffic-signal.git
cd adaptive-traffic-signal

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Install dependencies
make install-dev

# Copy environment template
cp .env.example .env

# Run tests
make test

# Start development servers
make run-dev        # FastAPI on http://localhost:8000
make run-demo       # Streamlit on http://localhost:8501
```

### Production Deployment

```bash
# Build and start all services
make docker-build
make docker-up

# Services available at:
# - API: http://localhost:8000
# - Dashboard: http://localhost:8501
# - Grafana: http://localhost:3000
# - Prometheus: http://localhost:9090
```

---

## 🎮 Usage

### Running the Dashboard

```bash
# Development
make run-demo

# Or directly
streamlit run src/adaptive_traffic/ui/app.py
```

Navigate to `http://localhost:8501` for the interactive dashboard with:
- 🏠 **System Overview** - Architecture and key metrics
- 📊 **Dashboard** - Real-time traffic monitoring
- 🎮 **Live Demo** - Interactive traffic simulation
- 📈 **Algorithm Comparison** - Performance benchmarks
- 🌍 **Impact Metrics** - Environmental & economic benefits
- ⚙️ **Settings** - Configuration management

### Running the API Server

```bash
# Development
make run-dev

# Or directly
uvicorn adaptive_traffic.api.main:app --reload --host 0.0.0.0 --port 8000
```

API Documentation: `http://localhost:8000/docs`

#### Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/health` | Health check |
| `GET /api/v1/signals` | List all signal controllers |
| `POST /api/v1/detection/detect` | Detect vehicles in image |
| `POST /api/v1/analytics/forecast` | Get traffic forecast |
| `GET /api/v1/analytics/recommendations/{id}` | Get timing recommendations |

### Running Simulations

```python
from adaptive_traffic.core.simulation.engine import create_simulation, create_intersection

# Create simulation
sim = create_simulation({
    'time_step': 0.1,
    'max_time': 3600,
    'generation_rates': {
        'north': 600,
        'south': 600,
        'east': 400,
        'west': 400
    }
})

# Add intersection
intersection = create_intersection({
    'id': 'main',
    'lanes_per_direction': 2,
    'lane_length': 200,
    'signal_timing': {
        'NS_green': 30, 'NS_yellow': 5,
        'EW_green': 30, 'EW_yellow': 5
    }
})
sim.add_intersection(intersection)

# Run simulation
for _ in range(1000):
    sim.step()
    if _ % 100 == 0:
        print(sim.get_network_stats())
```

---

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test categories
make test-unit
make test-integration
make test-performance
make test-security

# With coverage
make test-cov
```

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Unit tests
│   ├── test_config.py
│   ├── test_detection/
│   ├── test_control/
│   └── test_simulation/
├── integration/             # Integration tests
│   └── test_api.py
├── performance/             # Benchmarks
│   └── test_benchmarks.py
└── security/                # Security tests
    └── test_vulnerabilities.py
```

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `development` | Environment: development/staging/production |
| `API_HOST` | `0.0.0.0` | API server host |
| `API_PORT` | `8000` | API server port |
| `YOLO_MODEL_PATH` | `yolov8n.pt` | YOLO model path |
| `CONTROLLER_TYPE` | `dqn` | Signal controller: dqn/fixed/webster/fuzzy |
| `MIN_GREEN_TIME` | `10` | Minimum green time (seconds) |
| `MAX_GREEN_TIME` | `60` | Maximum green time (seconds) |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection |
| `DATABASE_URL` | `sqlite+aiosqlite:///./adaptive_traffic.db` | Database URL |

See `.env.example` for complete list.

### YAML Configuration

Environment-specific configs in `configs/`:
- `development.yaml` - Local development
- `staging.yaml` - Staging environment
- `production.yaml` - Production

---

## 📊 Monitoring

### Metrics Endpoints

- **Prometheus**: `http://localhost:9090/metrics`
- **Grafana**: `http://localhost:3000` (admin/admin123)
- **API Health**: `http://localhost:8000/api/v1/health`

### Key Metrics

- `traffic_wait_time_seconds` - Average vehicle wait time
- `traffic_throughput_vehicles_per_hour` - Intersection throughput
- `signal_cycle_length_seconds` - Current cycle length
- `detection_accuracy` - Vehicle detection accuracy
- `system_uptime_seconds` - Service uptime

---

## 🛡️ Security

- **Authentication**: JWT-based API authentication
- **CORS**: Configurable origin policies
- **Rate Limiting**: Per-endpoint rate limits
- **Input Validation**: Pydantic schema validation
- **Security Scanning**: Bandit, Safety in CI/CD

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Run pre-commit: `make pre-commit`
4. Run tests: `make test`
5. Commit changes: `git commit -m 'Add amazing feature'`
6. Push branch: `git push origin feature/amazing-feature`
7. Open Pull Request

### Code Standards

- **Formatting**: Black (line length 100)
- **Imports**: isort (Black profile)
- **Linting**: flake8
- **Types**: mypy (strict mode)
- **Docstrings**: Google style

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Ultralytics YOLOv8** - State-of-the-art object detection
- **FastAPI** - Modern, fast web framework
- **Streamlit** - Rapid dashboard development
- **PyTorch** - Deep learning framework
- **OpenCV** - Computer vision library

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/your-org/adaptive-traffic-signal/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/adaptive-traffic-signal/discussions)
- **Email**: team@adaptivesignal.io

---

**Built with ❤️ by the Adaptive Traffic Signal Team**