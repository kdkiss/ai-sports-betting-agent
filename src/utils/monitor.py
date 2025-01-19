import psutil
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import asyncio
from collections import deque
import statistics
from .logger import Logger

class SystemMonitor:
    """Monitors system health and performance metrics."""
    
    def __init__(
        self,
        logger: Logger,
        metrics_window: int = 3600,  # 1 hour
        check_interval: int = 60     # 1 minute
    ):
        self.logger = logger
        self.metrics_window = metrics_window
        self.check_interval = check_interval
        
        # Initialize metrics storage
        self.metrics: Dict[str, deque] = {
            'cpu_usage': deque(maxlen=metrics_window),
            'memory_usage': deque(maxlen=metrics_window),
            'api_response_times': deque(maxlen=metrics_window),
            'analysis_times': deque(maxlen=metrics_window),
            'error_counts': deque(maxlen=metrics_window),
            'request_counts': deque(maxlen=metrics_window)
        }
        
        # Track API health
        self.api_health: Dict[str, Dict[str, Any]] = {
            'sports_data': {'healthy': True, 'last_check': None},
            'odds': {'healthy': True, 'last_check': None},
            'weather': {'healthy': True, 'last_check': None},
            'deepseek': {'healthy': True, 'last_check': None}
        }
        
        # Performance thresholds
        self.thresholds = {
            'cpu_usage': 80.0,  # 80% CPU usage
            'memory_usage': 85.0,  # 85% memory usage
            'api_response_time': 5.0,  # 5 seconds
            'analysis_time': 10.0,  # 10 seconds
            'error_rate': 0.1  # 10% error rate
        }
    
    async def start_monitoring(self):
        """Start the monitoring loop."""
        while True:
            try:
                await self.check_system_health()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                self.logger.error(
                    "monitoring_error",
                    error=str(e)
                )
                await asyncio.sleep(self.check_interval)
    
    async def check_system_health(self):
        """Check and log system health metrics."""
        try:
            # Get current metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            # Update metrics
            self.metrics['cpu_usage'].append(cpu_percent)
            self.metrics['memory_usage'].append(memory_percent)
            
            # Calculate averages
            metrics = self.get_current_metrics()
            
            # Check for concerning metrics
            alerts = self.check_thresholds(metrics)
            
            # Log health check
            self.logger.log_system_health({
                'timestamp': datetime.now().isoformat(),
                'metrics': metrics,
                'alerts': alerts,
                'api_health': self.api_health
            })
            
            # Take action if needed
            if alerts:
                await self.handle_alerts(alerts)
                
        except Exception as e:
            self.logger.error(
                "health_check_failed",
                error=str(e)
            )
    
    def record_api_call(
        self,
        api_name: str,
        success: bool,
        response_time: float
    ):
        """Record an API call result."""
        # Update API health
        self.api_health[api_name] = {
            'healthy': success,
            'last_check': datetime.now().isoformat()
        }
        
        # Record response time if successful
        if success:
            self.metrics['api_response_times'].append(response_time)
        
        # Update request and error counts
        self.metrics['request_counts'].append(1)
        if not success:
            self.metrics['error_counts'].append(1)
        else:
            self.metrics['error_counts'].append(0)
    
    def record_analysis(self, duration: float):
        """Record an analysis duration."""
        self.metrics['analysis_times'].append(duration)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Calculate current system metrics."""
        now = datetime.now()
        
        # Calculate averages
        metrics = {
            'timestamp': now.isoformat(),
            'cpu_usage_avg': statistics.mean(self.metrics['cpu_usage'])
            if self.metrics['cpu_usage'] else 0,
            'memory_usage_avg': statistics.mean(self.metrics['memory_usage'])
            if self.metrics['memory_usage'] else 0,
            'api_response_time_avg': statistics.mean(self.metrics['api_response_times'])
            if self.metrics['api_response_times'] else 0,
            'analysis_time_avg': statistics.mean(self.metrics['analysis_times'])
            if self.metrics['analysis_times'] else 0
        }
        
        # Calculate error rate
        total_requests = sum(self.metrics['request_counts'])
        total_errors = sum(self.metrics['error_counts'])
        metrics['error_rate'] = (
            total_errors / total_requests if total_requests > 0 else 0
        )
        
        # Add current values
        metrics.update({
            'cpu_usage_current': psutil.cpu_percent(interval=None),
            'memory_usage_current': psutil.virtual_memory().percent,
            'disk_usage_percent': psutil.disk_usage('/').percent
        })
        
        return metrics
    
    def check_thresholds(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check if any metrics exceed thresholds."""
        alerts = []
        
        # Check CPU usage
        if metrics['cpu_usage_avg'] > self.thresholds['cpu_usage']:
            alerts.append({
                'type': 'cpu_usage',
                'value': metrics['cpu_usage_avg'],
                'threshold': self.thresholds['cpu_usage'],
                'severity': 'high'
            })
        
        # Check memory usage
        if metrics['memory_usage_avg'] > self.thresholds['memory_usage']:
            alerts.append({
                'type': 'memory_usage',
                'value': metrics['memory_usage_avg'],
                'threshold': self.thresholds['memory_usage'],
                'severity': 'high'
            })
        
        # Check API response times
        if metrics['api_response_time_avg'] > self.thresholds['api_response_time']:
            alerts.append({
                'type': 'api_response_time',
                'value': metrics['api_response_time_avg'],
                'threshold': self.thresholds['api_response_time'],
                'severity': 'medium'
            })
        
        # Check analysis times
        if metrics['analysis_time_avg'] > self.thresholds['analysis_time']:
            alerts.append({
                'type': 'analysis_time',
                'value': metrics['analysis_time_avg'],
                'threshold': self.thresholds['analysis_time'],
                'severity': 'medium'
            })
        
        # Check error rate
        if metrics['error_rate'] > self.thresholds['error_rate']:
            alerts.append({
                'type': 'error_rate',
                'value': metrics['error_rate'],
                'threshold': self.thresholds['error_rate'],
                'severity': 'high'
            })
        
        return alerts
    
    async def handle_alerts(self, alerts: List[Dict[str, Any]]):
        """Handle system alerts."""
        for alert in alerts:
            # Log alert
            self.logger.warning(
                "system_alert",
                alert_type=alert['type'],
                value=alert['value'],
                threshold=alert['threshold'],
                severity=alert['severity']
            )
            
            # Take action based on severity
            if alert['severity'] == 'high':
                await self.handle_high_severity_alert(alert)
            elif alert['severity'] == 'medium':
                await self.handle_medium_severity_alert(alert)
    
    async def handle_high_severity_alert(self, alert: Dict[str, Any]):
        """Handle high severity alerts."""
        if alert['type'] == 'cpu_usage':
            # Log detailed CPU information
            cpu_times = psutil.cpu_times_percent()
            self.logger.critical(
                "high_cpu_usage",
                user=cpu_times.user,
                system=cpu_times.system,
                idle=cpu_times.idle
            )
            
        elif alert['type'] == 'memory_usage':
            # Log detailed memory information
            memory = psutil.virtual_memory()
            self.logger.critical(
                "high_memory_usage",
                total=memory.total,
                available=memory.available,
                percent=memory.percent
            )
            
        elif alert['type'] == 'error_rate':
            # Log error rate details
            self.logger.critical(
                "high_error_rate",
                rate=alert['value'],
                threshold=alert['threshold']
            )
    
    async def handle_medium_severity_alert(self, alert: Dict[str, Any]):
        """Handle medium severity alerts."""
        if alert['type'] == 'api_response_time':
            # Log API performance details
            self.logger.warning(
                "slow_api_response",
                average_time=alert['value'],
                threshold=alert['threshold']
            )
            
        elif alert['type'] == 'analysis_time':
            # Log analysis performance details
            self.logger.warning(
                "slow_analysis",
                average_time=alert['value'],
                threshold=alert['threshold']
            )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current system health status."""
        metrics = self.get_current_metrics()
        alerts = self.check_thresholds(metrics)
        
        return {
            'status': 'unhealthy' if alerts else 'healthy',
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics,
            'alerts': alerts,
            'api_health': self.api_health
        } 