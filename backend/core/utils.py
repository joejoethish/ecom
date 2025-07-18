"""
Core utility functions for the ecommerce platform.
"""
import uuid
import hashlib
import secrets
import time
from typing import Any, Dict, Optional
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from PIL import Image
import io


def generate_unique_id() -> str:
    """Generate a unique identifier."""
    return str(uuid.uuid4())


def generate_order_number() -> str:
    """Generate a unique order number."""
    timestamp = str(int(time.time()))
    random_part = secrets.token_hex(4).upper()
    return f"ORD-{timestamp[-6:]}-{random_part}"


def generate_sku() -> str:
    """Generate a unique SKU."""
    return f"SKU-{secrets.token_hex(6).upper()}"


def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_slug(text: str) -> str:
    """Generate a URL-friendly slug from text."""
    import re
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')


def resize_image(image_file, max_width: int = 800, max_height: int = 600, quality: int = 85) -> ContentFile:
    """
    Resize an image while maintaining aspect ratio.
    """
    try:
        # Open the image
        img = Image.open(image_file)
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # Calculate new dimensions
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        
        # Save to bytes
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        return ContentFile(output.read())
    except Exception as e:
        raise ValueError(f"Error processing image: {str(e)}")


def validate_image_file(file) -> bool:
    """
    Validate if the uploaded file is a valid image.
    """
    try:
        # Check file size
        if file.size > getattr(settings, 'MAX_UPLOAD_SIZE', 5242880):  # 5MB default
            return False
        
        # Check file extension
        allowed_types = getattr(settings, 'ALLOWED_IMAGE_TYPES', 'jpg,jpeg,png,gif,webp').split(',')
        file_extension = file.name.split('.')[-1].lower()
        if file_extension not in allowed_types:
            return False
        
        # Try to open with PIL to validate it's a real image
        Image.open(file)
        file.seek(0)  # Reset file pointer
        
        return True
    except Exception:
        return False


def format_currency(amount: float, currency: str = 'USD') -> str:
    """Format amount as currency."""
    if currency == 'USD':
        return f"${amount:.2f}"
    return f"{amount:.2f} {currency}"


def calculate_discount_percentage(original_price: float, discounted_price: float) -> int:
    """Calculate discount percentage."""
    if original_price <= 0:
        return 0
    return int(((original_price - discounted_price) / original_price) * 100)


def paginate_queryset(queryset, page_size: int = 20, page: int = 1):
    """
    Paginate a queryset.
    """
    from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
    
    paginator = Paginator(queryset, page_size)
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    return {
        'results': page_obj.object_list,
        'pagination': {
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
            'previous_page': page_obj.previous_page_number() if page_obj.has_previous() else None,
        }
    }


def send_notification_email(to_email: str, subject: str, template: str, context: Dict[str, Any]):
    """
    Send notification email using Django's email system.
    """
    from django.core.mail import send_mail
    from django.template.loader import render_to_string
    from django.conf import settings
    
    try:
        html_message = render_to_string(template, context)
        send_mail(
            subject=subject,
            message='',  # Plain text version
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@ecommerce.com'),
            recipient_list=[to_email],
            html_message=html_message,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False


def create_response_data(success: bool = True, data: Any = None, message: str = None, errors: Dict = None) -> Dict:
    """
    Create standardized API response format.
    """
    response = {
        'success': success,
    }
    
    if data is not None:
        response['data'] = data
    
    if message:
        response['message'] = message
    
    if errors:
        response['errors'] = errors
    
    return response


