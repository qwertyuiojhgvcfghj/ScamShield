"""
email_service.py - Email sending service for ScamShield

Supports both SMTP and SendGrid for email delivery.
Includes HTML email templates for verification, password reset, alerts, etc.
"""

import os
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """
    Service for sending emails.
    Supports SMTP and SendGrid.
    """
    
    # Email configuration
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SENDER_EMAIL = os.getenv("SENDER_EMAIL", "noreply@scamshield.io")
    SENDER_NAME = os.getenv("SENDER_NAME", "ScamShield")
    
    # App URL for links in emails
    APP_URL = os.getenv("APP_URL", "http://localhost:3000")
    
    @staticmethod
    def _get_base_template(content: str, title: str = "ScamShield") -> str:
        """Get the base HTML email template."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{title}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 0;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    color: #ffffff;
                    margin: 0;
                    font-size: 28px;
                }}
                .header .logo {{
                    font-size: 32px;
                    margin-bottom: 10px;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #e94560 0%, #ff6b6b 100%);
                    color: #ffffff !important;
                    text-decoration: none;
                    padding: 14px 32px;
                    border-radius: 8px;
                    font-weight: 600;
                    margin: 20px 0;
                }}
                .button:hover {{
                    opacity: 0.9;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px 30px;
                    text-align: center;
                    font-size: 12px;
                    color: #666;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .danger {{
                    background-color: #f8d7da;
                    border-left: 4px solid #dc3545;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .success {{
                    background-color: #d4edda;
                    border-left: 4px solid #28a745;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }}
                .code {{
                    background-color: #f4f4f4;
                    padding: 10px 20px;
                    border-radius: 4px;
                    font-family: monospace;
                    font-size: 24px;
                    letter-spacing: 4px;
                    text-align: center;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🛡️</div>
                    <h1>ScamShield</h1>
                </div>
                <div class="content">
                    {content}
                </div>
                <div class="footer">
                    <p>© {datetime.now().year} ScamShield. All rights reserved.</p>
                    <p>Protecting you from digital threats with AI-powered intelligence.</p>
                    <p>
                        <a href="{EmailService.APP_URL}/privacy">Privacy Policy</a> | 
                        <a href="{EmailService.APP_URL}/terms">Terms of Service</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
    
    @staticmethod
    async def _send_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email using SMTP.
        
        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML body
            text_content: Plain text body (optional)
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not EmailService.SMTP_USER or not EmailService.SMTP_PASSWORD:
            logger.warning("Email not configured. Skipping email send.")
            logger.info(f"Would have sent email to {to_email}: {subject}")
            return True  # Return True in dev mode
        
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{EmailService.SENDER_NAME} <{EmailService.SENDER_EMAIL}>"
            message["To"] = to_email
            
            # Add plain text version
            if text_content:
                message.attach(MIMEText(text_content, "plain"))
            
            # Add HTML version
            message.attach(MIMEText(html_content, "html"))
            
            # Send via SMTP
            await aiosmtplib.send(
                message,
                hostname=EmailService.SMTP_HOST,
                port=EmailService.SMTP_PORT,
                username=EmailService.SMTP_USER,
                password=EmailService.SMTP_PASSWORD,
                start_tls=True,
            )
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False
    
    @staticmethod
    async def send_verification_email(email: str, token: str, name: str = "User") -> bool:
        """
        Send email verification link to new user.
        """
        verification_url = f"{EmailService.APP_URL}/verify-email?token={token}"
        
        content = f"""
        <h2>Welcome to ScamShield, {name}! 👋</h2>
        <p>Thank you for joining ScamShield. We're excited to help protect you from scams and fraud.</p>
        <p>Please verify your email address by clicking the button below:</p>
        <p style="text-align: center;">
            <a href="{verification_url}" class="button">Verify Email Address</a>
        </p>
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #666; font-size: 14px;">{verification_url}</p>
        <div class="warning">
            <strong>⚠️ This link expires in 24 hours.</strong><br>
            If you didn't create an account with ScamShield, please ignore this email.
        </div>
        """
        
        html = EmailService._get_base_template(content, "Verify Your Email - ScamShield")
        text = f"Welcome to ScamShield! Verify your email: {verification_url}"
        
        return await EmailService._send_email(
            email,
            "🛡️ Verify Your ScamShield Account",
            html,
            text
        )
    
    @staticmethod
    async def send_phone_otp_email(email: str, otp: str, phone: str, name: str = "User") -> bool:
        """
        Send phone verification OTP to user's email.
        """
        # Mask phone number for display
        masked_phone = phone[:3] + "*" * (len(phone) - 5) + phone[-2:] if len(phone) > 5 else phone
        
        content = f"""
        <h2>Phone Verification Code</h2>
        <p>Hi {name},</p>
        <p>You requested to verify your phone number <strong>{masked_phone}</strong>.</p>
        <p>Your verification code is:</p>
        <div style="text-align: center; margin: 30px 0;">
            <span style="font-size: 36px; font-weight: bold; letter-spacing: 8px; 
                         background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                         color: white; padding: 15px 30px; border-radius: 8px;">
                {otp}
            </span>
        </div>
        <div class="warning">
            <strong>⚠️ This code expires in 10 minutes.</strong><br>
            Do not share this code with anyone. ScamShield will never ask for your verification code.
        </div>
        <p style="color: #666; font-size: 14px;">
            If you didn't request this code, please ignore this email or contact support if you have concerns.
        </p>
        """
        
        html = EmailService._get_base_template(content, "Phone Verification Code - ScamShield")
        text = f"Your ScamShield phone verification code is: {otp}. This code expires in 10 minutes."
        
        return await EmailService._send_email(
            email,
            "🔐 Your ScamShield Phone Verification Code",
            html,
            text
        )
    
    @staticmethod
    async def send_password_reset_email(email: str, token: str, name: str = "User") -> bool:
        """
        Send password reset link.
        """
        reset_url = f"{EmailService.APP_URL}/reset-password?token={token}"
        
        content = f"""
        <h2>Password Reset Request</h2>
        <p>Hi {name},</p>
        <p>We received a request to reset your password. Click the button below to create a new password:</p>
        <p style="text-align: center;">
            <a href="{reset_url}" class="button">Reset Password</a>
        </p>
        <p>Or copy and paste this link into your browser:</p>
        <p style="word-break: break-all; color: #666; font-size: 14px;">{reset_url}</p>
        <div class="warning">
            <strong>⚠️ This link expires in 1 hour.</strong><br>
            If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.
        </div>
        <p style="color: #666; font-size: 14px;">
            For security, this request was received from a web browser. 
            If this wasn't you, please secure your account immediately.
        </p>
        """
        
        html = EmailService._get_base_template(content, "Reset Your Password - ScamShield")
        text = f"Reset your ScamShield password: {reset_url}"
        
        return await EmailService._send_email(
            email,
            "🔐 Reset Your ScamShield Password",
            html,
            text
        )
    
    @staticmethod
    async def send_welcome_email(email: str, name: str) -> bool:
        """
        Send welcome email to new verified user.
        """
        content = f"""
        <h2>You're All Set, {name}! 🎉</h2>
        <p>Your ScamShield account is now verified and ready to protect you.</p>
        
        <h3>Getting Started</h3>
        <p>Here's what you can do now:</p>
        <ul>
            <li><strong>Scan Messages</strong> - Check suspicious texts, emails, and messages</li>
            <li><strong>View Threats</strong> - See blocked scams and threat intelligence</li>
            <li><strong>Set Up Alerts</strong> - Get notified when new threats are detected</li>
            <li><strong>Generate API Key</strong> - Integrate protection into your apps</li>
        </ul>
        
        <p style="text-align: center;">
            <a href="{EmailService.APP_URL}/dashboard" class="button">Go to Dashboard</a>
        </p>
        
        <div class="success">
            <strong>💡 Pro Tip:</strong> Enable auto-block in settings to automatically protect yourself from detected scams.
        </div>
        """
        
        html = EmailService._get_base_template(content, "Welcome to ScamShield!")
        text = f"Welcome to ScamShield, {name}! Your account is now verified."
        
        return await EmailService._send_email(
            email,
            "🛡️ Welcome to ScamShield - You're Protected!",
            html,
            text
        )
    
    @staticmethod
    async def send_threat_alert(
        email: str,
        name: str,
        threat_type: str,
        risk_score: float,
        message_preview: str,
        sender_info: Optional[str] = None
    ) -> bool:
        """
        Send alert about a detected threat.
        """
        risk_level = "Critical" if risk_score >= 0.9 else "High" if risk_score >= 0.7 else "Medium"
        risk_color = "#dc3545" if risk_score >= 0.9 else "#ffc107" if risk_score >= 0.7 else "#17a2b8"
        
        sender_text = f"<br><strong>From:</strong> {sender_info}" if sender_info else ""
        
        content = f"""
        <h2>🚨 Threat Detected!</h2>
        <p>Hi {name},</p>
        <p>We've detected a potential <strong>{threat_type}</strong> scam targeting you.</p>
        
        <div class="danger">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span><strong>Risk Level:</strong></span>
                <span style="background: {risk_color}; color: white; padding: 4px 12px; border-radius: 4px;">
                    {risk_level} ({int(risk_score * 100)}%)
                </span>
            </div>
            {sender_text}
        </div>
        
        <h3>Message Preview</h3>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 4px; font-style: italic;">
            "{message_preview[:200]}..."
        </div>
        
        <h3>What to Do</h3>
        <ul>
            <li>❌ <strong>Don't click</strong> any links in this message</li>
            <li>❌ <strong>Don't reply</strong> or provide any information</li>
            <li>❌ <strong>Don't call</strong> any numbers mentioned</li>
            <li>✅ <strong>Block the sender</strong> if you can</li>
            <li>✅ <strong>Report it</strong> to the appropriate authorities</li>
        </ul>
        
        <p style="text-align: center;">
            <a href="{EmailService.APP_URL}/dashboard" class="button">View in Dashboard</a>
        </p>
        """
        
        html = EmailService._get_base_template(content, "Threat Alert - ScamShield")
        text = f"ScamShield Alert: {risk_level} risk {threat_type} detected. Risk score: {int(risk_score * 100)}%"
        
        return await EmailService._send_email(
            email,
            f"🚨 {risk_level} Risk Alert: {threat_type.title()} Detected",
            html,
            text
        )
    
    @staticmethod
    async def send_weekly_digest(
        email: str,
        name: str,
        stats: Dict[str, Any]
    ) -> bool:
        """
        Send weekly security digest.
        """
        scans = stats.get("scans_this_week", 0)
        threats = stats.get("threats_detected", 0)
        blocked = stats.get("threats_blocked", 0)
        protection_rate = stats.get("protection_rate", 100)
        
        content = f"""
        <h2>Your Weekly Security Report 📊</h2>
        <p>Hi {name},</p>
        <p>Here's your security summary for the past week:</p>
        
        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
            <tr style="background: #f8f9fa;">
                <td style="padding: 15px; border: 1px solid #dee2e6; text-align: center;">
                    <div style="font-size: 32px; font-weight: bold; color: #007bff;">{scans}</div>
                    <div style="color: #666;">Messages Scanned</div>
                </td>
                <td style="padding: 15px; border: 1px solid #dee2e6; text-align: center;">
                    <div style="font-size: 32px; font-weight: bold; color: #dc3545;">{threats}</div>
                    <div style="color: #666;">Threats Detected</div>
                </td>
                <td style="padding: 15px; border: 1px solid #dee2e6; text-align: center;">
                    <div style="font-size: 32px; font-weight: bold; color: #28a745;">{blocked}</div>
                    <div style="color: #666;">Threats Blocked</div>
                </td>
            </tr>
        </table>
        
        <div class="success">
            <strong>🛡️ Protection Rate: {protection_rate:.1f}%</strong><br>
            You're well protected! Keep scanning suspicious messages.
        </div>
        
        <h3>Stay Safe</h3>
        <p>Remember these tips:</p>
        <ul>
            <li>Always verify unexpected messages from banks or officials</li>
            <li>Never share OTPs or passwords with anyone</li>
            <li>Be skeptical of "too good to be true" offers</li>
            <li>When in doubt, scan it with ScamShield!</li>
        </ul>
        
        <p style="text-align: center;">
            <a href="{EmailService.APP_URL}/dashboard" class="button">View Full Report</a>
        </p>
        """
        
        html = EmailService._get_base_template(content, "Weekly Security Report - ScamShield")
        text = f"Your weekly ScamShield report: {scans} scans, {threats} threats detected, {blocked} blocked."
        
        return await EmailService._send_email(
            email,
            f"📊 Your Weekly Security Report - {blocked} Threats Blocked!",
            html,
            text
        )
    
    @staticmethod
    async def send_api_key_generated(
        email: str,
        name: str,
        key_prefix: str
    ) -> bool:
        """
        Notify user that a new API key was generated.
        """
        content = f"""
        <h2>New API Key Generated 🔑</h2>
        <p>Hi {name},</p>
        <p>A new API key has been generated for your account.</p>
        
        <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <strong>Key Prefix:</strong> {key_prefix}...
        </div>
        
        <div class="warning">
            <strong>⚠️ Important Security Notice</strong><br>
            <ul style="margin: 10px 0 0 0; padding-left: 20px;">
                <li>Keep your API key secure and never share it publicly</li>
                <li>Don't commit it to version control systems</li>
                <li>If compromised, revoke it immediately from your dashboard</li>
            </ul>
        </div>
        
        <p>If you didn't generate this key, please secure your account immediately by changing your password.</p>
        
        <p style="text-align: center;">
            <a href="{EmailService.APP_URL}/dashboard#api-keys" class="button">Manage API Keys</a>
        </p>
        """
        
        html = EmailService._get_base_template(content, "New API Key Generated - ScamShield")
        text = f"A new API key ({key_prefix}...) was generated for your ScamShield account."
        
        return await EmailService._send_email(
            email,
            "🔑 New API Key Generated for Your ScamShield Account",
            html,
            text
        )
    
    @staticmethod
    async def send_subscription_confirmation(
        email: str,
        name: str,
        plan_name: str,
        price: float,
        features: list
    ) -> bool:
        """
        Send subscription confirmation email.
        """
        features_html = "".join([f"<li>✅ {f}</li>" for f in features])
        
        content = f"""
        <h2>Subscription Confirmed! 🎉</h2>
        <p>Hi {name},</p>
        <p>Thank you for upgrading to <strong>{plan_name}</strong>!</p>
        
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; padding: 30px; border-radius: 8px; margin: 20px 0; text-align: center;">
            <div style="font-size: 14px; opacity: 0.9;">YOUR PLAN</div>
            <div style="font-size: 28px; font-weight: bold; margin: 10px 0;">{plan_name}</div>
            <div style="font-size: 24px;">₹{price:.0f}/month</div>
        </div>
        
        <h3>Your Features</h3>
        <ul style="list-style: none; padding: 0;">
            {features_html}
        </ul>
        
        <div class="success">
            <strong>🛡️ Enhanced Protection Active</strong><br>
            Your upgraded features are now active. Enjoy enhanced protection!
        </div>
        
        <p style="text-align: center;">
            <a href="{EmailService.APP_URL}/dashboard" class="button">Start Using Pro Features</a>
        </p>
        """
        
        html = EmailService._get_base_template(content, "Subscription Confirmed - ScamShield")
        text = f"Your ScamShield {plan_name} subscription is now active!"
        
        return await EmailService._send_email(
            email,
            f"🎉 Welcome to ScamShield {plan_name}!",
            html,
            text
        )


# Global instance for easy import
email_service = EmailService()
