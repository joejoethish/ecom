"""
Utility Functions for QA Testing Framework

Common helper functions and utilities used across all testing modules.
"""

import uuid
import hashlib
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import json
import yaml


def generate_unique_id(prefix: str = "") -> str:
    """Generate unique identifier with optional prefix"""
    unique_id = str(uuid.uuid4())
    return f"{prefix}_{unique_id}" if prefix else unique_id


def generate_timestamp_id(prefix: str = "") -> str:
    """Generate timestamp-based ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"{prefix}_{timestamp}" if prefix else timestamp


def generate_test_email(domain: str = "qatest.com") -> str:
    """Generate unique test email address"""
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"test_{random_string}_{timestamp}@{domain}"


def generate_test_phone() -> str:
    """Generate test phone number"""
    # Generate a US format test phone number
    area_code = random.randint(200, 999)
    exchange = random.randint(200, 999)
    number = random.randint(1000, 9999)
    return f"+1{area_code}{exchange}{number}"


def generate_random_string(length: int = 10, include_digits: bool = True) -> str:
    """Generate random string of specified length"""
    chars = string.ascii_letters
    if include_digits:
        chars += string.digits
    return ''.join(random.choices(chars, k=length))


def generate_random_password(length: int = 12) -> str:
    """Generate secure random password"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    password = ''.join(random.choices(chars, k=length))
    
    # Ensure password has at least one of each type
    if not any(c.islower() for c in password):
        password = password[:-1] + random.choice(string.ascii_lowercase)
    if not any(c.isupper() for c in password):
        password = password[:-1] + random.choice(string.ascii_uppercase)
    if not any(c.isdigit() for c in password):
        password = password[:-1] + random.choice(string.digits)
    
    return password


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system usage"""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename


def ensure_directory(path: Union[str, Path]) -> Path:
    """Ensure directory exists, create if it doesn't"""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Load JSON file with error handling"""
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise ValueError(f"Error loading JSON file {file_path}: {e}")


def save_json_file(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """Save data to JSON file"""
    file_path = Path(file_path)
    ensure_directory(file_path.parent)
    
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def load_yaml_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Load YAML file with error handling"""
    try:
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError) as e:
        raise ValueError(f"Error loading YAML file {file_path}: {e}")


def save_yaml_file(data: Dict[str, Any], file_path: Union[str, Path]) -> None:
    """Save data to YAML file"""
    file_path = Path(file_path)
    ensure_directory(file_path.parent)
    
    with open(file_path, 'w') as f:
        yaml.dump(data, f, default_flow_style=False)


def calculate_hash(data: str) -> str:
    """Calculate SHA-256 hash of string data"""
    return hashlib.sha256(data.encode()).hexdigest()


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string"""
    if seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}m {remaining_seconds:.2f}s"
    else:
        hours = int(seconds // 3600)
        remaining_minutes = int((seconds % 3600) // 60)
        remaining_seconds = seconds % 60
        return f"{hours}h {remaining_minutes}m {remaining_seconds:.2f}s"


def format_timestamp(timestamp: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string"""
    return timestamp.strftime(format_str)


def parse_timestamp(timestamp_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """Parse string to datetime"""
    return datetime.strptime(timestamp_str, format_str)


def get_relative_time(timestamp: datetime) -> str:
    """Get relative time description (e.g., '2 hours ago')"""
    now = datetime.now()
    diff = now - timestamp
    
    if diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"


def retry_with_backoff(func, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """Retry function with exponential backoff"""
    import time
    
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            
            delay = min(base_delay * (2 ** attempt), max_delay)
            time.sleep(delay)


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def unflatten_dict(d: Dict[str, Any], sep: str = '.') -> Dict[str, Any]:
    """Unflatten dictionary with dot notation keys"""
    result = {}
    for key, value in d.items():
        keys = key.split(sep)
        current = result
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
    return result


def validate_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """Basic phone number validation"""
    import re
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    # Check if it's a valid length (10-15 digits)
    return 10 <= len(digits_only) <= 15


def mask_sensitive_data(data: str, mask_char: str = '*', visible_chars: int = 4) -> str:
    """Mask sensitive data showing only last few characters"""
    if len(data) <= visible_chars:
        return mask_char * len(data)
    
    masked_length = len(data) - visible_chars
    return mask_char * masked_length + data[-visible_chars:]


def generate_test_data_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate summary of test data for reporting"""
    summary = {
        'total_items': 0,
        'categories': {},
        'generated_at': datetime.now().isoformat()
    }
    
    for category, items in data.items():
        if isinstance(items, list):
            count = len(items)
            summary['categories'][category] = count
            summary['total_items'] += count
    
    return summary


class TestDataGenerator:
    """Helper class for generating test data"""
    
    @staticmethod
    def generate_user_data(user_type: str = "customer") -> Dict[str, Any]:
        """Generate realistic user test data"""
        first_names = ["John", "Jane", "Mike", "Sarah", "David", "Lisa", "Chris", "Emma"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]
        
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        
        return {
            'first_name': first_name,
            'last_name': last_name,
            'email': generate_test_email(),
            'phone': generate_test_phone(),
            'password': generate_random_password(),
            'user_type': user_type
        }
    
    @staticmethod
    def generate_product_data(category: str = "electronics") -> Dict[str, Any]:
        """Generate realistic product test data"""
        product_names = {
            'electronics': ["Smartphone", "Laptop", "Tablet", "Headphones", "Camera"],
            'clothing': ["T-Shirt", "Jeans", "Dress", "Jacket", "Shoes"],
            'books': ["Novel", "Textbook", "Biography", "Cookbook", "Guide"],
            'home': ["Chair", "Table", "Lamp", "Cushion", "Vase"]
        }
        
        names = product_names.get(category, ["Generic Product"])
        base_name = random.choice(names)
        
        return {
            'name': f"{base_name} {generate_random_string(4)}",
            'category': category,
            'price': round(random.uniform(10.0, 1000.0), 2),
            'stock_quantity': random.randint(0, 100),
            'description': f"High-quality {base_name.lower()} for testing purposes"
        }
    
    @staticmethod
    def generate_address_data() -> Dict[str, Any]:
        """Generate realistic address test data"""
        streets = ["Main St", "Oak Ave", "Pine Rd", "Elm Dr", "Cedar Ln"]
        cities = ["Springfield", "Franklin", "Georgetown", "Madison", "Riverside"]
        states = ["CA", "NY", "TX", "FL", "IL"]
        
        return {
            'street': f"{random.randint(100, 9999)} {random.choice(streets)}",
            'city': random.choice(cities),
            'state': random.choice(states),
            'postal_code': f"{random.randint(10000, 99999)}",
            'country': "US"
        }