"""
Custom logging handlers for the ecommerce platform.
"""
import logging
import json
import os
import time
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from django.conf import settings
from django.utils import timezone


class JsonFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the log record.
    """
    def __init__(self, *args, **kwargs):
        self.fmt_dict = kwargs.pop("fmt_dict", {})
        super().__init__(*args, **kwargs)
    
    def format(self, record):
        record_dict = self._prepare_log_dict(record)
        return json.dumps(record_dict)
    
    def _prepare_log_dict(self, record):
        record_dict = {
            "timestamp": timezone.now().isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if available
        if record.exc_info:
            record_dict["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add extra fields from record
        for key, value in self.fmt_dict.items():
            if key == "asctime":
                # Format the time as specified
                value = self.formatTime(record, self.datefmt)
            elif key == "message":
                value = record.getMessage()
            elif hasattr(record, key):
                value = getattr(record, key)
            
            record_dict[key] = value
        
        # Add any extra attributes from the record
        for key, value in record.__dict__.items():
            if key not in ["args", "exc_info", "exc_text", "stack_info", "lineno", 
                          "funcName", "created", "msecs", "relativeCreated", 
                          "levelname", "levelno", "pathname", "filename", 
                          "module", "name", "thread", "threadName", 
                          "processName", "process", "message"]:
                if not key.startswith("_"):
                    record_dict[key] = value
        
        return record_dict


class SecurityRotatingFileHandler(RotatingFileHandler):
    """
    A rotating file handler that ensures file permissions are set correctly for security logs.
    """
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0, encoding=None, delay=False):
        super().__init__(filename, mode, maxBytes, backupCount, encoding, delay)
        # Ensure log directory exists
        os.makedirs(os.path.dirname(filename), exist_ok=True)
    
    def _open(self):
        """
        Open the log file with restricted permissions.
        """
        stream = super()._open()
        # Set file permissions to be readable/writable only by owner
        if os.name == 'posix':  # Unix/Linux/MacOS
            try:
                import stat
                os.chmod(self.baseFilename, stat.S_IRUSR | stat.S_IWUSR)
            except OSError:
                pass
        return stream


class BusinessMetricsHandler(logging.Handler):
    """
    Handler for business metrics that can be integrated with monitoring systems.
    """
    def __init__(self, metrics_file=None):
        super().__init__()
        self.metrics_file = metrics_file or os.path.join(settings.BASE_DIR, 'logs', 'business_metrics.jsonl')
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.metrics_file), exist_ok=True)
    
    def emit(self, record):
        """
        Write business metrics to a JSONL file for later processing.
        """
        if not hasattr(record, 'metric_name'):
            return
        
        try:
            msg = self.format(record)
            with open(self.metrics_file, 'a', encoding='utf-8') as f:
                f.write(f"{msg}\n")
        except Exception:
            self.handleError(record)


class DatabaseLogHandler(logging.Handler):
    """
    Handler that writes log messages to the database.
    
    Note: This handler should be used sparingly and only for important events
    to avoid database performance issues.
    """
    def emit(self, record):
        """
        Save the log record to the database.
        """
        from apps.logs.models import SystemLog
        
        try:
            # Avoid circular imports by importing here
            msg = self.format(record)
            
            # Create log entry
            SystemLog.objects.create(
                level=record.levelname,
                logger_name=record.name,
                message=msg,
                source=getattr(record, 'source', 'system'),
                event_type=getattr(record, 'event_type', 'general'),
                user_id=getattr(record, 'user_id', None),
                ip_address=getattr(record, 'ip_address', None),
                request_path=getattr(record, 'request_path', None),
                extra_data=getattr(record, 'extra_data', {})
            )
        except Exception:
            self.handleError(record)


class SlackHandler(logging.Handler):
    """
    Handler for sending critical log messages to Slack.
    """
    def __init__(self, webhook_url=None):
        super().__init__()
        self.webhook_url = webhook_url or getattr(settings, 'SLACK_WEBHOOK_URL', None)
    
    def emit(self, record):
        """
        Send the log message to Slack.
        """
        if not self.webhook_url:
            return
        
        try:
            import requests
            
            msg = self.format(record)
            payload = {
                "text": f"*{record.levelname}*: {msg}",
                "attachments": [
                    {
                        "color": self._get_color_for_level(record.levelno),
                        "fields": [
                            {
                                "title": "Logger",
                                "value": record.name,
                                "short": True
                            },
                            {
                                "title": "Time",
                                "value": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "short": True
                            }
                        ]
                    }
                ]
            }
            
            # Add exception info if available
            if record.exc_info:
                payload["attachments"][0]["fields"].append({
                    "title": "Exception",
                    "value": f"{record.exc_info[0].__name__}: {str(record.exc_info[1])}",
                    "short": False
                })
            
            # Add extra fields
            for key, value in record.__dict__.items():
                if key not in ["args", "exc_info", "exc_text", "stack_info", "lineno", 
                              "funcName", "created", "msecs", "relativeCreated", 
                              "levelname", "levelno", "pathname", "filename", 
                              "module", "name", "thread", "threadName", 
                              "processName", "process", "message"] and not key.startswith("_"):
                    payload["attachments"][0]["fields"].append({
                        "title": key,
                        "value": str(value),
                        "short": True
                    })
            
            requests.post(self.webhook_url, json=payload, timeout=5)
        except Exception:
            self.handleError(record)
    
    def _get_color_for_level(self, levelno):
        """
        Return a color based on the log level.
        """
        if levelno >= logging.CRITICAL:
            return "danger"  # Red
        elif levelno >= logging.ERROR:
            return "#E74C3C"  # Light red
        elif levelno >= logging.WARNING:
            return "warning"  # Yellow
        elif levelno >= logging.INFO:
            return "good"  # Green
        return "#3498DB"  # Blue for DEBUG and below