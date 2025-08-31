"""
Configuration Management for QA Testing Framework

Handles configuration for different environments (development, staging, production)
and provides centralized access to framework settings.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from .interfaces import Environment


class ConfigManager:
    """Manages configuration for different test environments"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.current_environment = Environment.DEVELOPMENT
        self._config_cache = {}
        self._load_configurations()
    
    def _load_configurations(self) -> None:
        """Load all environment configurations"""
        for env in Environment:
            config_file = self.config_dir / f"{env.value}.yaml"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    self._config_cache[env] = yaml.safe_load(f)
            else:
                self._config_cache[env] = self._get_default_config(env)
    
    def _get_default_config(self, environment: Environment) -> Dict[str, Any]:
        """Get default configuration for environment"""
        base_config = {
            "database": {
                "host": "localhost",
                "port": 5432,
                "name": f"qa_test_{environment.value}",
                "user": "qa_user",
                "password": "qa_password"
            },
            "web": {
                "base_url": f"http://localhost:3000",
                "timeout": 30,
                "implicit_wait": 10,
                "browsers": ["chrome", "firefox"]
            },
            "mobile": {
                "appium_server": "http://localhost:4723",
                "platform_name": "Android",
                "device_name": "emulator-5554",
                "app_package": "com.ecommerce.app",
                "timeout": 30
            },
            "api": {
                "base_url": f"http://localhost:8000/api/v1",
                "timeout": 30,
                "auth_endpoint": "/auth/login",
                "rate_limit": 1000
            },
            "reporting": {
                "output_dir": f"reports/{environment.value}",
                "formats": ["html", "json", "xml"],
                "screenshot_on_failure": True,
                "detailed_logs": True
            },
            "test_data": {
                "users_count": 50,
                "products_count": 500,
                "categories_count": 20,
                "cleanup_after_test": True
            },
            "notifications": {
                "email": {
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "test_email": "qa.test@example.com"
                },
                "sms": {
                    "provider": "twilio",
                    "test_number": "+1234567890"
                }
            },
            "payment_gateways": {
                "stripe": {
                    "sandbox_mode": True,
                    "api_key": "sk_test_sandbox_key"
                },
                "paypal": {
                    "sandbox_mode": True,
                    "client_id": "test_client_id"
                }
            }
        }
        
        # Environment-specific overrides
        if environment == Environment.STAGING:
            base_config["web"]["base_url"] = "https://staging.ecommerce.com"
            base_config["api"]["base_url"] = "https://staging-api.ecommerce.com/api/v1"
        elif environment == Environment.PRODUCTION:
            base_config["web"]["base_url"] = "https://ecommerce.com"
            base_config["api"]["base_url"] = "https://api.ecommerce.com/api/v1"
            base_config["test_data"]["cleanup_after_test"] = False
        
        return base_config
    
    def get_config(self, environment: Optional[Environment] = None) -> Dict[str, Any]:
        """Get configuration for specified environment"""
        env = environment or self.current_environment
        return self._config_cache.get(env, {})
    
    def get_section(self, section: str, environment: Optional[Environment] = None) -> Dict[str, Any]:
        """Get specific configuration section"""
        config = self.get_config(environment)
        return config.get(section, {})
    
    def get_value(self, key_path: str, environment: Optional[Environment] = None, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'database.host')"""
        config = self.get_config(environment)
        keys = key_path.split('.')
        
        value = config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set_environment(self, environment: Environment) -> None:
        """Set current active environment"""
        self.current_environment = environment
    
    def get_current_environment(self) -> Environment:
        """Get current active environment"""
        return self.current_environment
    
    def update_config(self, section: str, updates: Dict[str, Any], environment: Optional[Environment] = None) -> None:
        """Update configuration section"""
        env = environment or self.current_environment
        if env not in self._config_cache:
            self._config_cache[env] = {}
        
        if section not in self._config_cache[env]:
            self._config_cache[env][section] = {}
        
        self._config_cache[env][section].update(updates)
    
    def save_config(self, environment: Environment) -> None:
        """Save configuration to file"""
        config_file = self.config_dir / f"{environment.value}.yaml"
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            yaml.dump(self._config_cache[environment], f, default_flow_style=False)
    
    def load_from_env_vars(self, prefix: str = "QA_TEST_") -> None:
        """Load configuration overrides from environment variables"""
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower().replace('_', '.')
                
                # Try to parse as JSON for complex values
                try:
                    parsed_value = json.loads(value)
                except (json.JSONDecodeError, ValueError):
                    parsed_value = value
                
                self._set_nested_value(config_key, parsed_value)
    
    def _set_nested_value(self, key_path: str, value: Any) -> None:
        """Set nested configuration value using dot notation"""
        keys = key_path.split('.')
        config = self._config_cache[self.current_environment]
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value


# Global configuration instance
config_manager = ConfigManager()


def get_config(section: Optional[str] = None, environment: Optional[Environment] = None) -> Dict[str, Any]:
    """Convenience function to get configuration"""
    if section:
        return config_manager.get_section(section, environment)
    return config_manager.get_config(environment)


def get_value(key_path: str, default: Any = None, environment: Optional[Environment] = None) -> Any:
    """Convenience function to get configuration value"""
    return config_manager.get_value(key_path, environment, default)