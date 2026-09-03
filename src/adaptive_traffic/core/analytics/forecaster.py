"""
Predictive Analytics Module
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class TrafficForecast:
    """Traffic flow forecast"""

    timestamp: datetime
    horizon_hours: int
    flow_predictions: dict[str, list[float]]  # direction -> hourly predictions
    speed_predictions: dict[str, list[float]]
    congestion_predictions: dict[str, list[float]]
    confidence_intervals: dict[str, tuple[list[float], list[float]]]


class TrafficForecaster:
    """Traffic flow forecasting using time series analysis"""

    def __init__(self, config: dict):
        self.config = config
        self.horizon = config.get("forecast_horizon", 24)  # hours
        self.history_window = config.get("history_window", 168)  # hours (1 week)

        # Historical data storage
        self.flow_history: dict[str, list[float]] = {}
        self.speed_history: dict[str, list[float]] = {}
        self.timestamps: list[datetime] = []

        # Model parameters (simplified)
        self.seasonal_period = 24  # daily seasonality
        self.trend_window = 24 * 7  # weekly trend

    def update(
        self,
        timestamp: datetime,
        flow_data: dict[str, float],
        speed_data: dict[str, float] | None = None,
    ):
        """Update historical data"""
        self.timestamps.append(timestamp)

        for direction, flow in flow_data.items():
            if direction not in self.flow_history:
                self.flow_history[direction] = []
            self.flow_history[direction].append(flow)

        if speed_data:
            for direction, speed in speed_data.items():
                if direction not in self.speed_history:
                    self.speed_history[direction] = []
                self.speed_history[direction].append(speed)

        # Trim history
        max_len = self.history_window
        for direction in self.flow_history:
            if len(self.flow_history[direction]) > max_len:
                self.flow_history[direction] = self.flow_history[direction][-max_len:]
        for direction in self.speed_history:
            if len(self.speed_history[direction]) > max_len:
                self.speed_history[direction] = self.speed_history[direction][-max_len:]

        if len(self.timestamps) > max_len:
            self.timestamps = self.timestamps[-max_len:]

    def forecast(self, current_time: datetime) -> TrafficForecast:
        """Generate traffic forecast"""
        predictions = {}
        speed_preds = {}
        congestion_preds = {}
        confidence_intervals = {}

        for direction in self.flow_history:
            if len(self.flow_history[direction]) < 48:  # Need minimum history
                # Return naive forecast
                predictions[direction] = [0] * self.horizon
                speed_preds[direction] = [0] * self.horizon
                congestion_preds[direction] = [0] * self.horizon
                confidence_intervals[direction] = ([0] * self.horizon, [0] * self.horizon)
                continue

            # Simple seasonal naive + trend forecast
            flow_pred, flow_ci = self._forecast_series(self.flow_history[direction], current_time)
            predictions[direction] = flow_pred
            confidence_intervals[direction] = flow_ci

            # Speed forecast (inverse relationship with flow)
            if direction in self.speed_history:
                speed_pred, _ = self._forecast_series(self.speed_history[direction], current_time)
                speed_preds[direction] = speed_pred
            else:
                speed_preds[direction] = [50] * self.horizon

            # Congestion prediction (flow / capacity)
            capacity = self.config.get("capacity", {}).get(direction, 1800)
            congestion_preds[direction] = [min(1.0, f / capacity) for f in flow_pred]

        return TrafficForecast(
            timestamp=current_time,
            horizon_hours=self.horizon,
            flow_predictions=predictions,
            speed_predictions=speed_preds,
            congestion_predictions=congestion_preds,
            confidence_intervals=confidence_intervals,
        )

    def _forecast_series(
        self, history: list[float], current_time: datetime
    ) -> tuple[list[float], tuple[list[float], list[float]]]:
        """Forecast single time series using seasonal naive + linear trend"""
        n = len(history)

        # Calculate trend (linear regression on recent data)
        recent = history[-min(self.trend_window, n) :]
        x = np.arange(len(recent))
        if len(recent) > 1:
            trend_coeff = np.polyfit(x, recent, 1)[0]
        else:
            trend_coeff = 0

        # Seasonal pattern (average of same hour on previous days)
        seasonal = np.zeros(24)
        seasonal_counts = np.zeros(24)

        for i, val in enumerate(history):
            if self.timestamps and i < len(self.timestamps):
                hour = self.timestamps[i].hour
            else:
                hour = i % 24
            seasonal[hour] += val
            seasonal_counts[hour] += 1

        for h in range(24):
            if seasonal_counts[h] > 0:
                seasonal[h] /= seasonal_counts[h]

        # Generate forecast
        forecast = []
        lower_ci = []
        upper_ci = []

        # Calculate historical error for confidence intervals
        errors = []
        for i in range(max(24, n - 24), n):
            pred_idx = (i - 24) % 24
            pred = seasonal[pred_idx] + trend_coeff * (i - (n - 24))
            errors.append(abs(history[i] - pred))

        error_std = np.std(errors) if errors else 50

        for h in range(self.horizon):
            future_time = current_time + timedelta(hours=h + 1)
            hour = future_time.hour

            # Seasonal + trend
            base_pred = seasonal[hour] + trend_coeff * (n + h)
            forecast.append(max(0, base_pred))

            # Confidence interval (±2 std)
            lower_ci.append(max(0, base_pred - 2 * error_std))
            upper_ci.append(base_pred + 2 * error_std)

        return forecast, (lower_ci, upper_ci)

    def get_recent_average(self, direction: str, hours: int = 24) -> float:
        """Get recent average flow"""
        if direction not in self.flow_history:
            return 0.0
        history = self.flow_history[direction]
        return np.mean(history[-min(hours, len(history)) :])


class DigitalTwin:
    """Infrastructure Digital Twin for real-time simulation"""

    def __init__(self, config: dict):
        self.config = config
        self.forecaster = TrafficForecaster(config)
        self.current_state: dict = {}
        self.anomaly_threshold = config.get("anomaly_threshold", 3.0)  # std deviations

    def update_state(self, intersection_data: dict):
        """Update digital twin state from real sensors"""
        self.current_state = intersection_data

        # Update forecaster
        if "timestamp" in intersection_data:
            timestamp = intersection_data["timestamp"]
        else:
            timestamp = datetime.now()

        flow_data = intersection_data.get("flows", {})
        speed_data = intersection_data.get("speeds", {})

        self.forecaster.update(timestamp, flow_data, speed_data)

        # Detect anomalies
        self._detect_anomalies(intersection_data)

    def _detect_anomalies(self, data: dict):
        """Detect anomalies in traffic data"""
        flows = data.get("flows", {})

        for direction, flow in flows.items():
            recent_avg = self.forecaster.get_recent_average(direction, 24)
            recent_std = np.std(self.forecaster.flow_history.get(direction, [])[-24:])

            if recent_std > 0:
                z_score = abs(flow - recent_avg) / recent_std
                if z_score > self.anomaly_threshold:
                    logger.warning(
                        f"Anomaly detected: {direction} flow={flow}, "
                        f"avg={recent_avg:.1f}, z={z_score:.1f}"
                    )

    def get_predictions(self) -> TrafficForecast:
        """Get current traffic predictions"""
        return self.forecaster.forecast(datetime.now())

    def simulate_scenario(self, scenario: dict) -> dict:
        """Simulate what-if scenario"""
        # Apply scenario modifications
        modified_flows = {}
        for direction, base_flow in self.current_state.get("flows", {}).items():
            modifier = scenario.get("flow_modifiers", {}).get(direction, 1.0)
            modified_flows[direction] = base_flow * modifier

        # Return predicted impacts
        return {
            "scenario": scenario,
            "modified_flows": modified_flows,
            "predicted_congestion": {
                d: f / self.config.get("capacity", {}).get(d, 1800)
                for d, f in modified_flows.items()
            },
        }


class PredictiveAnalytics:
    """Main predictive analytics engine"""

    def __init__(self, config: dict):
        self.config = config
        self.forecaster = TrafficForecaster(config)
        self.digital_twin = DigitalTwin(config)
        self.prediction_cache: dict = {}
        self.cache_ttl = config.get("cache_ttl", 300)  # seconds

    def ingest_sensor_data(self, intersection_id: str, data: dict):
        """Ingest real-time sensor data"""
        # Update digital twin
        self.digital_twin.update_state(data)

        # Invalidate cache
        self.prediction_cache.pop(intersection_id, None)

    def get_forecast(self, intersection_id: str) -> TrafficForecast:
        """Get traffic forecast for intersection"""
        # Check cache
        cache_key = intersection_id
        if cache_key in self.prediction_cache:
            cached_time, forecast = self.prediction_cache[cache_key]
            if (datetime.now() - cached_time).total_seconds() < self.cache_ttl:
                return forecast

        # Generate new forecast
        forecast = self.digital_twin.get_predictions()

        # Cache result
        self.prediction_cache[cache_key] = (datetime.now(), forecast)

        return forecast

    def evaluate_scenario(self, scenario: dict) -> dict:
        """Evaluate what-if scenario"""
        return self.digital_twin.simulate_scenario(scenario)

    def get_recommendations(self, intersection_id: str) -> list[dict]:
        """Get signal timing recommendations based on predictions"""
        forecast = self.get_forecast(intersection_id)
        recommendations = []

        for direction in forecast.congestion_predictions:
            max_congestion = max(forecast.congestion_predictions[direction])
            avg_congestion = np.mean(forecast.congestion_predictions[direction])

            if max_congestion > 0.9:
                recommendations.append(
                    {
                        "type": "extend_green",
                        "direction": direction,
                        "reason": f"Predicted congestion > 90% (max: {max_congestion:.1%})",
                        "priority": "high",
                        "suggested_extension": 15,
                    }
                )
            elif avg_congestion > 0.7:
                recommendations.append(
                    {
                        "type": "adjust_timing",
                        "direction": direction,
                        "reason": f"Predicted average congestion {avg_congestion:.1%}",
                        "priority": "medium",
                        "suggested_extension": 5,
                    }
                )

        return recommendations


def create_forecaster(config: dict) -> TrafficForecaster:
    """Factory function to create forecaster"""
    return TrafficForecaster(config)


def create_digital_twin(config: dict) -> DigitalTwin:
    """Factory function to create digital twin"""
    return DigitalTwin(config)


def create_predictive_analytics(config: dict) -> PredictiveAnalytics:
    """Factory function to create predictive analytics engine"""
    return PredictiveAnalytics(config)
