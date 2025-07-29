"""
Email service for password reset notifications.
Handles email template rendering, sending, and error handling.
"""
import logging
from typing import Optional, Tuple, Dict, Any
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
# from django.contrib.sites.models import Site  # Not needed
from django.urls import reverse
from smtplib import SMTPException
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class PasswordResetEmailService:
    """
    Service class for sending password reset emails.
    Handles template rendering, email composition, and delivery.
    """
    
    # Email configuration
    FROM_EMAIL = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
    SUPPORT_EMAIL = getattr(settings, 'SUPPORT_EMAIL', 'support@example.com')
    SITE_NAME = getattr(settings, 'SITE_NAME', 'E-commerce Platform')
    FRONTEND_URL = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    
    # Email templates
    HTML_TEMPLATE = 'emails/password_reset.html'
    TEXT_TEMPLATE = 'emails/password_reset.txt'
    
    @staticmethod
    def _get_reset_url(token: str) -> str:
        """
        Generate the password reset URL with token.
        Requirements: 2.3 - Include reset link with token as URL parameter
        """
        return f"{PasswordResetEmailService.FRONTEND_URL}/auth/reset-password/{token}"
    
    @staticmethod
    def _get_email_context(user, token: str, request_ip: str = '') -> Dict[str, Any]:
        """
        Prepare context data for email template rendering.
        Requirements: 2.4 - Include clear instructions and consistent branding
        """
        reset_url = PasswordResetEmailService._get_reset_url(token)
        current_time = timezone.now()
        expiry_time = current_time + timezone.timedelta(hours=1)
        
        context = {
            'user': user,
            'reset_url': reset_url,
            'site_name': PasswordResetEmailService.SITE_NAME,
            'support_email': PasswordResetEmailService.SUPPORT_EMAIL,
            'request_ip': request_ip or 'Unknown',
            'request_time': current_time.strftime('%B %d, %Y at %I:%M %p %Z'),
            'expiry_time': expiry_time.strftime('%B %d, %Y at %I:%M %p %Z'),
        }
        
        return context
    
    @staticmethod
    def _render_email_templates(context: Dict[str, Any]) -> Tuple[str, str]:
        """
        Render both HTML and text email templates.
        Requirements: 2.4 - Clear instructions and branding
        """
        try:
            # Render HTML template
            html_content = render_to_string(
                PasswordResetEmailService.HTML_TEMPLATE, 
                context
            )
            
            # Render text template
            text_content = render_to_string(
                PasswordResetEmailService.TEXT_TEMPLATE, 
                context
            )
            
            return html_content, text_content
            
        except Exception as e:
            logger.error(f"Failed to render email templates: {str(e)}")
            raise EmailRenderingError(f"Template rendering failed: {str(e)}")
    
    @staticmethod
    def _create_email_message(
        user, 
        html_content: str, 
        text_content: str
    ) -> EmailMultiAlternatives:
        """
        Create email message with both HTML and text content.
        """
        subject = f"Password Reset Request - {PasswordResetEmailService.SITE_NAME}"
        
        # Create email message
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=PasswordResetEmailService.FROM_EMAIL,
            to=[user.email],
            headers={
                'X-Priority': '1',  # High priority
                'X-MSMail-Priority': 'High',
                'Importance': 'high',
            }
        )
        
        # Attach HTML version
        email.attach_alternative(html_content, "text/html")
        
        return email
    
    @staticmethod
    def send_password_reset_email(
        user, 
        token: str, 
        request_ip: str = ''
    ) -> Tuple[bool, Optional[str]]:
        """
        Send password reset email to user.
        
        Args:
            user: User instance
            token: Password reset token
            request_ip: IP address of the request
            
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
            
        Requirements: 2.3, 2.4, 6.4 - Send email with reset link and error handling
        """
        try:
            # Validate inputs
            if not user or not user.email:
                logger.error("Invalid user or email address provided")
                return False, "Invalid user information"
            
            if not token:
                logger.error("No token provided for password reset email")
                return False, "Invalid reset token"
            
            # Prepare email context
            context = PasswordResetEmailService._get_email_context(
                user=user,
                token=token,
                request_ip=request_ip
            )
            
            # Render email templates
            html_content, text_content = PasswordResetEmailService._render_email_templates(context)
            
            # Create email message
            email = PasswordResetEmailService._create_email_message(
                user=user,
                html_content=html_content,
                text_content=text_content
            )
            
            # Send email
            email.send(fail_silently=False)
            
            logger.info(f"Password reset email sent successfully to: {user.email}")
            return True, None
            
        except EmailRenderingError as e:
            logger.error(f"Email template rendering failed: {str(e)}")
            return False, "Failed to prepare email content"
            
        except SMTPException as e:
            logger.error(f"SMTP error sending password reset email: {str(e)}")
            return False, "Failed to send email due to server error"
            
        except ConnectionError as e:
            logger.error(f"Connection error sending password reset email: {str(e)}")
            return False, "Failed to connect to email server"
            
        except Exception as e:
            logger.error(f"Unexpected error sending password reset email: {str(e)}")
            return False, "An unexpected error occurred while sending email"
    
    @staticmethod
    def send_password_reset_confirmation_email(
        user, 
        request_ip: str = ''
    ) -> Tuple[bool, Optional[str]]:
        """
        Send confirmation email after successful password reset.
        This is an additional security feature to notify users of password changes.
        """
        try:
            current_time = timezone.now()
            
            context = {
                'user': user,
                'site_name': PasswordResetEmailService.SITE_NAME,
                'support_email': PasswordResetEmailService.SUPPORT_EMAIL,
                'request_ip': request_ip or 'Unknown',
                'reset_time': current_time.strftime('%B %d, %Y at %I:%M %p %Z'),
            }
            
            subject = f"Password Successfully Reset - {PasswordResetEmailService.SITE_NAME}"
            
            # Simple text message for confirmation
            text_content = f"""
Hello{' ' + user.first_name if user.first_name else ''},

This email confirms that your password for {PasswordResetEmailService.SITE_NAME} was successfully reset on {context['reset_time']}.

If you did not make this change, please contact our support team immediately at {PasswordResetEmailService.SUPPORT_EMAIL}.

For your security:
- Your account is now secured with your new password
- All active sessions have been logged out
- Consider enabling two-factor authentication if available

---
{PasswordResetEmailService.SITE_NAME}
This email was sent from {context['request_ip']} at {context['reset_time']}

If you have any questions, please contact us at {PasswordResetEmailService.SUPPORT_EMAIL}
"""
            
            # Create and send email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=PasswordResetEmailService.FROM_EMAIL,
                to=[user.email],
            )
            
            email.send(fail_silently=False)
            
            logger.info(f"Password reset confirmation email sent to: {user.email}")
            return True, None
            
        except Exception as e:
            logger.error(f"Failed to send password reset confirmation email: {str(e)}")
            return False, "Failed to send confirmation email"
    
    @staticmethod
    def test_email_configuration() -> Tuple[bool, str]:
        """
        Test email configuration and connectivity.
        Useful for debugging email setup issues.
        """
        try:
            from django.core.mail import get_connection
            
            # Test email connection
            connection = get_connection()
            connection.open()
            connection.close()
            
            logger.info("Email configuration test successful")
            return True, "Email configuration is working correctly"
            
        except Exception as e:
            logger.error(f"Email configuration test failed: {str(e)}")
            return False, f"Email configuration error: {str(e)}"
    
    @staticmethod
    def get_email_stats() -> Dict[str, Any]:
        """
        Get email service statistics for monitoring.
        """
        try:
            from django.core.mail import get_connection
            
            stats = {
                'service_name': 'PasswordResetEmailService',
                'from_email': PasswordResetEmailService.FROM_EMAIL,
                'support_email': PasswordResetEmailService.SUPPORT_EMAIL,
                'site_name': PasswordResetEmailService.SITE_NAME,
                'frontend_url': PasswordResetEmailService.FRONTEND_URL,
                'html_template': PasswordResetEmailService.HTML_TEMPLATE,
                'text_template': PasswordResetEmailService.TEXT_TEMPLATE,
                'connection_class': str(type(get_connection())),
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get email stats: {str(e)}")
            return {'error': str(e)}


class EmailRenderingError(Exception):
    """Custom exception for email template rendering errors."""
    pass


class EmailDeliveryError(Exception):
    """Custom exception for email delivery errors."""
    pass


# Convenience functions for backward compatibility and easier imports
def send_password_reset_email(user, token: str, request_ip: str = '') -> Tuple[bool, Optional[str]]:
    """
    Convenience function to send password reset email.
    """
    return PasswordResetEmailService.send_password_reset_email(user, token, request_ip)


def send_password_reset_confirmation_email(user, request_ip: str = '') -> Tuple[bool, Optional[str]]:
    """
    Convenience function to send password reset confirmation email.
    """
    return PasswordResetEmailService.send_password_reset_confirmation_email(user, request_ip)


def test_email_configuration() -> Tuple[bool, str]:
    """
    Convenience function to test email configuration.
    """
    return PasswordResetEmailService.test_email_configuration()