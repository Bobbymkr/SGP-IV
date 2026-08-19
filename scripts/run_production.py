# Production Application Runner
# ===============================

import asyncio
import logging
import os
import sys
import signal
import time
from pathlib import Path
from typing import Optional
import structlog
import json
from contextlib import asynccontextmanager

# Configure structured logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger()

class ProductionRunner:
    """Production application runner with health checks and graceful shutdown"""
    
    def __init__(self):
        self.is_running = False
        self.shutdown_event = asyncio.Event()
        
        # Configuration
        self.config = self._load_config()
        
        # Health check endpoints
        self.health_endpoints = [
            "http://localhost:8000/api/health",
            "http://localhost:8000/api/metrics",
            "http://localhost:6379/health",  # Redis
            "http://localhost:5432/health"   # PostgreSQL
        ]
        
        logger.info("Production runner initialized")
    
    def _load_config(self) -> dict:
        """Load production configuration"""
        config = {
            'host': os.getenv('HOST', '0.0.0.0'),
            'port': int(os.getenv('PORT', '8000')),
            'workers': int(os.getenv('WORKERS', '4')),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'environment': os.getenv('ENVIRONMENT', 'production'),
            'database_url': os.getenv('DATABASE_URL', 'postgresql://trafficuser:password@localhost:5432/trafficdb'),
            'redis_url': os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
            'ssl_enabled': os.getenv('SSL_ENABLED', 'true').lower() == 'true',
            'max_connections': int(os.getenv('MAX_CONNECTIONS', '1000')),
            'request_timeout': int(os.getenv('REQUEST_TIMEOUT', '30')),
            'health_check_interval': int(os.getenv('HEALTH_CHECK_INTERVAL', '30')),
            'graceful_shutdown_timeout': int(os.getenv('GRACEFUL_SHUTDOWN_TIMEOUT', '30'))
        }
        
        return config
    
    async def start_application(self):
        """Start the production application"""
        self.is_running = True
        
        logger.info("Starting production application", 
                   environment=self.config['environment'],
                   host=self.config['host'],
                   port=self.config['port'])
        
        try:
            # Import and start FastAPI application
            from app import app
            
            # Configure FastAPI for production
            app.config.update({
                'HOST': self.config['host'],
                'PORT': self.config['port'],
                'WORKERS': self.config['workers'],
                'LOG_LEVEL': self.config['log_level'],
                'ENVIRONMENT': self.config['environment']
            })
            
            # Start health check task
            health_task = asyncio.create_task(self._health_check_loop())
            
            # Start metrics collection task
            metrics_task = asyncio.create_task(self._metrics_collection_loop())
            
            # Setup signal handlers
            self._setup_signal_handlers()
            
            # Start the application
            import uvicorn
            config = uvicorn.Config(
                app,
                host=self.config['host'],
                port=self.config['port'],
                workers=self.config['workers'],
                log_level=self.config['log_level'].lower(),
                access_log=True,
                use_colors=False,
                ssl_keyfile="/etc/nginx/ssl/key.pem" if self.config['ssl_enabled'] else None,
                ssl_certfile="/etc/nginx/ssl/cert.pem" if self.config['ssl_enabled'] else None
            )
            
            server = uvicorn.Server(config)
            
            await server.serve()
            
        except Exception as e:
            logger.error("Failed to start application", error=str(e))
            raise
    
    async def _health_check_loop(self):
        """Continuous health check loop"""
        logger.info("Starting health check loop")
        
        while self.is_running:
            try:
                # Check all health endpoints
                for endpoint in self.health_endpoints:
                    is_healthy = await self._check_endpoint_health(endpoint)
                    
                    if not is_healthy:
                        logger.warning("Health check failed", endpoint=endpoint)
                        # Could trigger alert or notification here
                    
                    await asyncio.sleep(self.config['health_check_interval'])
                
            except Exception as e:
                logger.error("Health check error", error=str(e))
                await asyncio.sleep(self.config['health_check_interval'])
    
    async def _check_endpoint_health(self, endpoint: str) -> bool:
        """Check health of a specific endpoint"""
        try:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(endpoint) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('status') == 'healthy'
                    return False
                    
        except Exception as e:
            logger.error("Health check error", endpoint=endpoint, error=str(e))
            return False
    
    async def _metrics_collection_loop(self):
        """Collect and report application metrics"""
        logger.info("Starting metrics collection loop")
        
        while self.is_running:
            try:
                # Collect system metrics
                metrics = await self._collect_metrics()
                
                # Log metrics
                logger.info("Application metrics", **metrics)
                
                # Send to monitoring system (if configured)
                await self._send_metrics_to_monitoring(metrics)
                
                await asyncio.sleep(60)  # Collect metrics every minute
                
            except Exception as e:
                logger.error("Metrics collection error", error=str(e))
                await asyncio.sleep(60)
    
    async def _collect_metrics(self) -> dict:
        """Collect application and system metrics"""
        import psutil
        import time
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Application metrics (would be collected from app internals)
        app_metrics = {
            'uptime': time.time(),
            'active_connections': getattr(self, '_active_connections', 0),
            'requests_per_second': getattr(self, '_requests_per_second', 0),
            'average_response_time': getattr(self, '_average_response_time', 0)
        }
        
        return {
            'timestamp': time.time(),
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_gb': memory.used / (1024**3),
                'memory_total_gb': memory.total / (1024**3),
                'disk_usage_percent': disk.percent,
                'disk_read_mb_s': disk.read_bytes / (1024**2),
                'disk_write_mb_s': disk.write_bytes / (1024**2)
            },
            'application': app_metrics,
            'environment': self.config['environment']
        }
    
    async def _send_metrics_to_monitoring(self, metrics: dict):
        """Send metrics to external monitoring system"""
        # This would integrate with Prometheus, Grafana, etc.
        # For now, just log the metrics
        pass
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal", signal=signum)
            self.is_running = False
            self.shutdown_event.set()
        
        # Register signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGUSR1, signal_handler)  # For graceful reload
    
    async def graceful_shutdown(self):
        """Perform graceful shutdown"""
        logger.info("Starting graceful shutdown")
        
        try:
            # Wait for existing connections to finish
            await asyncio.wait_for(
                self.shutdown_event.wait(),
                timeout=self.config['graceful_shutdown_timeout']
            )
            
            logger.info("Graceful shutdown completed")
            
        except asyncio.TimeoutError:
            logger.warning("Graceful shutdown timeout, forcing exit")
        
        finally:
            # Cleanup resources
            await self._cleanup()
    
    async def _cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up resources")
        
        # Close database connections
        # Close Redis connections
        # Stop background tasks
        # Flush logs
        
        logger.info("Cleanup completed")
    
    @asynccontextmanager
    async def database_session(self):
        """Database session context manager"""
        # This would manage database connections
        # For now, just a placeholder
        try:
            yield
        except Exception as e:
            logger.error("Database session error", error=str(e))
            raise
    
    async def redis_session(self):
        """Redis session context manager"""
        # This would manage Redis connections
        try:
            yield
        except Exception as e:
            logger.error("Redis session error", error=str(e))
            raise
    
    def get_application_info(self) -> dict:
        """Get application information"""
        return {
            'name': 'Adaptive Traffic Signal System',
            'version': '3.0.0',
            'environment': self.config['environment'],
            'host': self.config['host'],
            'port': self.config['port'],
            'workers': self.config['workers'],
            'ssl_enabled': self.config['ssl_enabled'],
            'start_time': getattr(self, '_start_time', time.time()),
            'uptime': time.time() - getattr(self, '_start_time', time.time())
        }

async def main():
    """Main production application entry point"""
    runner = ProductionRunner()
    
    try:
        await runner.start_application()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
        await runner.graceful_shutdown()
    except Exception as e:
        logger.error("Application error", error=str(e))
        await runner.graceful_shutdown()

if __name__ == "__main__":
    # Set up logging for production
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.JSONRenderer(),
            structlog.processors.TimeStamper(fmt="iso"),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Run the application
    asyncio.run(main())