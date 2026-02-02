"""
contact.py - Contact form API endpoint
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

from app.services.email_service import email_service
from app.core.config import settings


router = APIRouter(prefix="/contact", tags=["Contact"])


class ContactFormRequest(BaseModel):
    """Contact form submission."""
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=5, max_length=200)
    message: str = Field(..., min_length=20, max_length=5000)
    phone: Optional[str] = Field(None, pattern=r"^\+?[0-9]{10,15}$")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john@example.com",
                "subject": "Question about ScamShield Pro",
                "message": "I'd like to know more about the enterprise features...",
                "phone": "+919876543210"
            }
        }


class ContactFormResponse(BaseModel):
    """Response after contact form submission."""
    success: bool
    message: str
    ticket_id: Optional[str] = None


async def send_contact_notification(form: ContactFormRequest):
    """Send notification email about new contact form submission."""
    try:
        # Email to admin
        admin_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #2563eb;">New Contact Form Submission</h2>
            
            <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p><strong>From:</strong> {form.name}</p>
                <p><strong>Email:</strong> {form.email}</p>
                <p><strong>Phone:</strong> {form.phone or 'Not provided'}</p>
                <p><strong>Subject:</strong> {form.subject}</p>
            </div>
            
            <div style="background: #fff; padding: 20px; border: 1px solid #e5e7eb; border-radius: 8px;">
                <h3>Message:</h3>
                <p style="white-space: pre-wrap;">{form.message}</p>
            </div>
            
            <p style="color: #6b7280; font-size: 12px; margin-top: 20px;">
                Received at: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
            </p>
        </div>
        """
        
        await email_service.send_email(
            to_email=settings.ADMIN_EMAIL if hasattr(settings, 'ADMIN_EMAIL') else "admin@scamshield.io",
            subject=f"[ScamShield Contact] {form.subject}",
            html_content=admin_html
        )
        
        # Auto-reply to user
        user_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #2563eb;">Thank You for Contacting ScamShield!</h2>
            
            <p>Hi {form.name},</p>
            
            <p>We've received your message and will get back to you within 24-48 hours.</p>
            
            <div style="background: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p><strong>Your message:</strong></p>
                <p style="white-space: pre-wrap;">{form.message[:500]}{'...' if len(form.message) > 500 else ''}</p>
            </div>
            
            <p>In the meantime, you can:</p>
            <ul>
                <li>Check our <a href="https://scamshield.io/faq">FAQ</a></li>
                <li>Visit our <a href="https://scamshield.io/docs">Documentation</a></li>
                <li>Follow us on social media for updates</li>
            </ul>
            
            <p>Best regards,<br>The ScamShield Team</p>
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
            <p style="color: #6b7280; font-size: 12px;">
                This is an automated response. Please do not reply to this email.
            </p>
        </div>
        """
        
        await email_service.send_email(
            to_email=form.email,
            subject="We received your message - ScamShield",
            html_content=user_html
        )
        
    except Exception as e:
        # Log error but don't fail the request
        print(f"Failed to send contact notification: {e}")


@router.post("", response_model=ContactFormResponse)
async def submit_contact_form(
    form: ContactFormRequest,
    background_tasks: BackgroundTasks
):
    """
    Submit a contact form.
    
    Sends notification to admin and auto-reply to user.
    """
    try:
        # Generate a ticket ID
        ticket_id = f"SCM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Send emails in background
        background_tasks.add_task(send_contact_notification, form)
        
        return ContactFormResponse(
            success=True,
            message="Thank you for your message! We'll get back to you within 24-48 hours.",
            ticket_id=ticket_id
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit contact form: {str(e)}"
        )


@router.get("/info")
async def get_contact_info():
    """Get contact information for ScamShield."""
    return {
        "email": "support@scamshield.io",
        "phone": "+91-1800-XXX-XXXX",
        "address": "ScamShield Technologies Pvt. Ltd.\nBangalore, Karnataka, India",
        "hours": "Monday - Friday, 9 AM - 6 PM IST",
        "social": {
            "twitter": "https://twitter.com/scamshield",
            "linkedin": "https://linkedin.com/company/scamshield",
            "github": "https://github.com/scamshield"
        }
    }
