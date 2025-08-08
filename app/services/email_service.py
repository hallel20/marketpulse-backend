"""
Email service for sending notifications and transactional emails
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from jinja2 import Environment, FileSystemLoader
import emails

from app.config import get_settings

settings = get_settings()


class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.email_from = settings.EMAIL_FROM
        
        # Initialize Jinja2 environment for templates
        self.template_env = Environment(
            loader=FileSystemLoader("app/templates/email")
        )
        
        # Thread pool for async email sending
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def _send_email_sync(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send email synchronously"""
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.email_from
            msg["To"] = to_email
            
            # Add text part if provided
            if text_content:
                text_part = MIMEText(text_content, "plain")
                msg.attach(text_part)
            
            # Add HTML part
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send email asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor,
            self._send_email_sync,
            to_email,
            subject,
            html_content,
            text_content
        )
    
    async def send_welcome_email(self, to_email: str, user_name: str) -> bool:
        """Send welcome email to new users"""
        subject = "Welcome to MarketPulse Commerce!"
        
        # Render HTML template
        template = self.template_env.get_template("welcome.html")
        html_content = template.render(
            user_name=user_name,
            company_name="MarketPulse Commerce"
        )
        
        # Simple text content
        text_content = f"""
        Welcome to MarketPulse Commerce, {user_name}!
        
        Thank you for joining our marketplace. You can now start shopping for amazing products.
        
        Best regards,
        The MarketPulse Team
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)
    
    async def send_verification_email(
        self,
        to_email: str,
        user_name: str,
        verification_token: str
    ) -> bool:
        """Send email verification link"""
        subject = "Verify your MarketPulse Commerce account"
        
        # Create verification URL
        verification_url = f"https://marketpulse.com/verify-email?token={verification_token}"
        
        # Render HTML template
        template = self.template_env.get_template("email_verification.html")
        html_content = template.render(
            user_name=user_name,
            verification_url=verification_url,
            company_name="MarketPulse Commerce"
        )
        
        # Simple text content
        text_content = f"""
        Hi {user_name},
        
        Please verify your email address by clicking the link below:
        {verification_url}
        
        This link will expire in 24 hours.
        
        Best regards,
        The MarketPulse Team
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)
    
    async def send_password_reset_email(
        self,
        to_email: str,
        user_name: str,
        reset_token: str
    ) -> bool:
        """Send password reset email"""
        subject = "Reset your MarketPulse Commerce password"
        
        # Create reset URL
        reset_url = f"https://marketpulse.com/reset-password?token={reset_token}"
        
        # Render HTML template
        template = self.template_env.get_template("password_reset.html")
        html_content = template.render(
            user_name=user_name,
            reset_url=reset_url,
            company_name="MarketPulse Commerce"
        )
        
        # Simple text content
        text_content = f"""
        Hi {user_name},
        
        You requested to reset your password. Click the link below to set a new password:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        The MarketPulse Team
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)
    
    async def send_order_confirmation_email(
        self,
        to_email: str,
        user_name: str,
        order_number: str,
        order_total: str,
        order_items: list
    ) -> bool:
        """Send order confirmation email"""
        subject = f"Order Confirmation #{order_number}"
        
        # Render HTML template
        template = self.template_env.get_template("order_confirmation.html")
        html_content = template.render(
            user_name=user_name,
            order_number=order_number,
            order_total=order_total,
            order_items=order_items,
            company_name="MarketPulse Commerce"
        )
        
        # Simple text content
        text_content = f"""
        Hi {user_name},
        
        Thank you for your order! Your order #{order_number} has been confirmed.
        
        Order Total: {order_total}
        
        We'll send you another email when your order ships.
        
        Best regards,
        The MarketPulse Team
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)
    
    async def send_order_shipped_email(
        self,
        to_email: str,
        user_name: str,
        order_number: str,
        tracking_number: str,
        carrier: str
    ) -> bool:
        """Send order shipped notification"""
        subject = f"Your order #{order_number} has shipped!"
        
        # Create tracking URL (this would be carrier-specific)
        tracking_url = f"https://tracking.example.com/{tracking_number}"
        
        # Render HTML template
        template = self.template_env.get_template("order_shipped.html")
        html_content = template.render(
            user_name=user_name,
            order_number=order_number,
            tracking_number=tracking_number,
            carrier=carrier,
            tracking_url=tracking_url,
            company_name="MarketPulse Commerce"
        )
        
        # Simple text content
        text_content = f"""
        Hi {user_name},
        
        Great news! Your order #{order_number} has shipped.
        
        Carrier: {carrier}
        Tracking Number: {tracking_number}
        
        You can track your package at: {tracking_url}
        
        Best regards,
        The MarketPulse Team
        """
        
        return await self.send_email(to_email, subject, html_content, text_content)


# Email templates would be stored in app/templates/email/ directory
# For this demo, we'll create basic HTML templates
def create_email_templates():
    """Create basic email templates"""
    templates = {
        "welcome.html": """
<!DOCTYPE html>
<html>
<head>
    <title>Welcome to {{company_name}}</title>
</head>
<body>
    <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif;">
        <h1 style="color: #333;">Welcome to {{company_name}}!</h1>
        <p>Hi {{user_name}},</p>
        <p>Thank you for joining our marketplace. You can now start shopping for amazing products.</p>
        <p>Happy shopping!</p>
        <p>Best regards,<br>The {{company_name}} Team</p>
    </div>
</body>
</html>
        """,
        
        "email_verification.html": """
<!DOCTYPE html>
<html>
<head>
    <title>Verify your email</title>
</head>
<body>
    <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif;">
        <h1 style="color: #333;">Verify your email address</h1>
        <p>Hi {{user_name}},</p>
        <p>Please verify your email address by clicking the button below:</p>
        <p style="text-align: center;">
            <a href="{{verification_url}}" 
               style="background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">
                Verify Email Address
            </a>
        </p>
        <p>This link will expire in 24 hours.</p>
        <p>Best regards,<br>The {{company_name}} Team</p>
    </div>
</body>
</html>
        """,
        
        "password_reset.html": """
<!DOCTYPE html>
<html>
<head>
    <title>Reset your password</title>
</head>
<body>
    <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif;">
        <h1 style="color: #333;">Reset your password</h1>
        <p>Hi {{user_name}},</p>
        <p>You requested to reset your password. Click the button below to set a new password:</p>
        <p style="text-align: center;">
            <a href="{{reset_url}}" 
               style="background-color: #dc3545; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">
                Reset Password
            </a>
        </p>
        <p>This link will expire in 1 hour.</p>
        <p>If you didn't request this, please ignore this email.</p>
        <p>Best regards,<br>The {{company_name}} Team</p>
    </div>
</body>
</html>
        """,
        
        "order_confirmation.html": """
<!DOCTYPE html>
<html>
<head>
    <title>Order Confirmation</title>
</head>
<body>
    <div style="max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif;">
        <h1 style="color: #333;">Order Confirmation #{{order_number}}</h1>
        <p>Hi {{user_name}},</p>
        <p>Thank you for your order! Your order has been confirmed.</p>
        <div style="background-color: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 4px;">
            <h3>Order Details</h3>
            <p><strong>Order Number:</strong> {{order_number}}</p>
            <p><strong>Total:</strong> {{order_total}}</p>
        </div>
        <p>We'll send you another email when your order ships.</p>
        <p>Best regards,<br>The {{company_name}} Team</p>
    </div>
</body>
</html>
        """
    }
    
    return templates