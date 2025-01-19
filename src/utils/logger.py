import logging
import sys
from datetime import datetime
from pathlib import Path
import json
from typing import Any, Dict, Optional
import structlog
from structlog.stdlib import LoggerFactory

class Logger:
    """Configurable logging system for the sports betting analysis system."""
    
    def __init__(
        self,
        log_dir: str = "logs",
        log_level: str = "INFO",
        enable_console: bool = True,
        enable_file: bool = True
    ):
        self.log_dir = Path(log_dir)
        self.log_level = getattr(logging, log_level.upper())
        self.enable_console = enable_console
        self.enable_file = enable_file
        
        # Create log directory if it doesn't exist
        if enable_file:
            self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        self._configure_logging()
        
        # Create structured logger
        self.logger = structlog.get_logger()
    
    def _configure_logging(self):
        """Configure logging settings."""
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Configure standard logging
        handlers = []
        
        if self.enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self.log_level)
            handlers.append(console_handler)
        
        if self.enable_file:
            file_handler = logging.FileHandler(
                self.log_dir / f"{datetime.now().strftime('%Y%m%d')}.log"
            )
            file_handler.setLevel(self.log_level)
            handlers.append(file_handler)
        
        logging.basicConfig(
            level=self.log_level,
            format='%(message)s',
            handlers=handlers
        )
    
    def _log(
        self,
        level: str,
        event: str,
        **kwargs: Any
    ) -> None:
        """Log an event with structured data."""
        log_method = getattr(self.logger, level.lower())
        log_method(event, **kwargs)
    
    def info(self, event: str, **kwargs: Any) -> None:
        """Log an info event."""
        self._log('INFO', event, **kwargs)
    
    def warning(self, event: str, **kwargs: Any) -> None:
        """Log a warning event."""
        self._log('WARNING', event, **kwargs)
    
    def error(self, event: str, **kwargs: Any) -> None:
        """Log an error event."""
        self._log('ERROR', event, **kwargs)
    
    def debug(self, event: str, **kwargs: Any) -> None:
        """Log a debug event."""
        self._log('DEBUG', event, **kwargs)
    
    def critical(self, event: str, **kwargs: Any) -> None:
        """Log a critical event."""
        self._log('CRITICAL', event, **kwargs)
    
    def log_api_request(
        self,
        api_name: str,
        endpoint: str,
        params: Dict[str, Any],
        success: bool,
        response_time: float,
        error: Optional[str] = None
    ) -> None:
        """Log an API request."""
        self.info(
            "api_request",
            api_name=api_name,
            endpoint=endpoint,
            params=params,
            success=success,
            response_time=response_time,
            error=error
        )
    
    def log_analysis(
        self,
        analysis_type: str,
        context: Dict[str, Any],
        result: Dict[str, Any],
        duration: float
    ) -> None:
        """Log an analysis result."""
        self.info(
            "analysis_completed",
            analysis_type=analysis_type,
            context=context,
            result=result,
            duration=duration
        )
    
    def log_error(
        self,
        error: Exception,
        context: Dict[str, Any]
    ) -> None:
        """Log an error with context."""
        self.error(
            "error_occurred",
            error_type=type(error).__name__,
            error_message=str(error),
            **context
        )
    
    def log_cache(
        self,
        operation: str,
        key: str,
        success: bool,
        category: str = 'default'
    ) -> None:
        """Log a cache operation."""
        self.debug(
            "cache_operation",
            operation=operation,
            key=key,
            success=success,
            category=category
        )
    
    def log_performance(
        self,
        operation: str,
        duration: float,
        context: Dict[str, Any]
    ) -> None:
        """Log performance metrics."""
        self.info(
            "performance_metric",
            operation=operation,
            duration=duration,
            **context
        )
    
    def log_system_health(
        self,
        metrics: Dict[str, Any]
    ) -> None:
        """Log system health metrics."""
        self.info(
            "system_health",
            **metrics
        )
    
    def rotate_logs(self, max_days: int = 30) -> None:
        """Rotate old log files."""
        if not self.enable_file:
            return
            
        try:
            cutoff_date = datetime.now().timestamp() - (max_days * 86400)
            
            for log_file in self.log_dir.glob("*.log"):
                if log_file.stat().st_mtime < cutoff_date:
                    log_file.unlink()
        except Exception as e:
            self.error(
                "log_rotation_failed",
                error=str(e)
            ) 