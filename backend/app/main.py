"""
main.py

FastAPI app for the honeypot - VERSION 3.5
handles incoming messages and returns responses.
FULL FEATURED: images, metrics, fingerprinting, emotional states!

endpoints:
- POST /api/message - main endpoint for receiving scam messages
- GET /health - health check for monitoring
- GET /stats - session statistics (debug)
- GET /session/{id} - get session details
- POST /api/force-callback - manually trigger callback
- GET /api/image/{type} - generate fake images on demand
- GET /api/metrics - global engagement metrics
- GET /api/scammers - known scammer fingerprints
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from app.config import API_SECRET_KEY
from app.scam_detector import detect_scam, analyze_conversation
from app.intelligence import extract_from_text, extract_from_conversation, generate_agent_notes
from app.session_manager import session_store
from app.agent import get_agent_response
from app.automation import automation
from app.language_detector import detect_language, get_language_name
from app.image_generator import check_image_request, generate_image_for_request, image_gen
from app.smart_tactics import get_tactical_response, advance_conversation, get_stage

# NEW MODULES - v3.5
from app.fake_identity import get_fake_identity
from app.scam_classifier import classify_scam, get_tactics_for_scam
from app.time_metrics import time_tracker
from app.emotional_state import EmotionalContext, emotion_manager
from app.scammer_fingerprint import scammer_db
from app.alert_webhooks import alert_new_session, alert_intel_extracted, alert_repeat_scammer

# track emotional states per session
emotional_states: dict = {}
# track fake identities per session (using module's cache is automatic)


# --- pydantic models ---

class Message(BaseModel):
    sender: str
    text: str
    timestamp: Optional[str] = None

class Metadata(BaseModel):
    channel: Optional[str] = "SMS"
    language: Optional[str] = "English"
    locale: Optional[str] = "IN"

class MessageRequest(BaseModel):
    sessionId: str = Field(..., description="unique session identifier")
    message: Message
    conversationHistory: Optional[List[Message]] = []
    metadata: Optional[Metadata] = None

class MessageResponse(BaseModel):
    status: str
    reply: str
    image_url: Optional[str] = None
    image_type: Optional[str] = None


# --- app setup ---

app = FastAPI(
    title="ScamShield API",
    description="""
# ScamShield API v4.0

AI-powered scam detection and engagement system.

## Features
- 🛡️ **Scam Detection**: Multi-layer AI analysis with pattern matching
- 🤖 **Honeypot Engine**: Engage and waste scammers' time
- 🌐 **Multi-language**: Support for 10+ Indian languages
- 📊 **Analytics**: Comprehensive threat intelligence
- 🔒 **Secure**: JWT authentication + API key support

## Authentication
- **JWT Bearer Token**: For user dashboard access
- **API Key**: For programmatic access (X-API-Key header)

## Rate Limits
- 60 requests/minute per IP
- 1000 requests/hour per IP
    """,
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Authentication", "description": "User registration, login, OAuth"},
        {"name": "Users", "description": "User profile and settings"},
        {"name": "Scans", "description": "Scan messages for scams"},
        {"name": "Threats", "description": "Manage blocked threats"},
        {"name": "Subscriptions", "description": "Subscription plans and billing"},
        {"name": "Analytics", "description": "Dashboard statistics and trends"},
        {"name": "Admin", "description": "Administrative functions"},
        {"name": "Contact", "description": "Contact form"},
        {"name": "Health", "description": "Health checks and monitoring"},
        {"name": "Export", "description": "Data export functionality"},
        {"name": "Honeypot", "description": "Scammer engagement engine"},
    ]
)

# cors - allow all for hackathon demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
from app.core.middleware import (
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware
)

# Security headers (outermost - runs first on response)
app.add_middleware(SecurityHeadersMiddleware)

# Request logging
app.add_middleware(RequestLoggingMiddleware, log_body=False)

# Rate limiting (innermost - runs first on request)
app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=60,
    requests_per_hour=1000
)


# --- MongoDB Connection ---
@app.on_event("startup")
async def startup_db():
    """Connect to MongoDB on startup"""
    try:
        from app.db.mongodb import connect_to_mongodb
        from app.services.subscription_service import SubscriptionService
        await connect_to_mongodb()
        # Initialize default subscription plans
        await SubscriptionService.initialize_default_plans()
        print("[API] Database connected and initialized")
    except Exception as e:
        print(f"[API] Warning: Could not connect to MongoDB: {e}")
        print("[API] Running without database - some features disabled")


@app.on_event("shutdown")
async def shutdown_db():
    """Close MongoDB connection on shutdown"""
    try:
        from app.db.mongodb import close_mongodb_connection
        await close_mongodb_connection()
    except Exception:
        pass


# --- Include API v1 Router ---
from app.api.v1.router import api_router
app.include_router(api_router, prefix="/api/v1")


# --- auth ---

async def verify_api_key(x_api_key: str = Header(...)):
    """check api key in header"""
    if x_api_key != API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="invalid api key")
    return x_api_key


# --- endpoints ---

@app.get("/")
async def root():
    """just a hello"""
    return {
        "message": "Honeypot API is running",
        "version": "3.5.0",
        "features": [
            "multi-language (10 Indian languages)",
            "auto-callback to GUVI",
            "4 free AI providers with fallback",
            "image generation (fake screenshots)",
            "smart tactics engine",
            "fake victim identity generator",
            "scam type classifier",
            "time wasting metrics",
            "emotional state simulation",
            "scammer fingerprinting",
            "Discord/Telegram alerts"
        ],
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """health check for uptime monitoring"""
    from app.ai_providers import ai
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "ai_providers": ai.get_available_providers()
    }


@app.get("/stats")
async def stats(api_key: str = Depends(verify_api_key)):
    """session statistics - for debugging"""
    base_stats = session_store.stats()
    base_stats["active_sessions"] = session_store.list_sessions()
    return base_stats


@app.get("/session/{session_id}")
async def get_session(session_id: str, api_key: str = Depends(verify_api_key)):
    """get details of a specific session"""
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    
    engagement = automation.analyze_engagement_quality(session)
    
    # get fake identity for this session
    identity = get_fake_identity(session_id)
    identity_dict = identity.to_dict() if identity else None
    
    # get emotional state
    emotion = emotional_states.get(session_id)
    emotional_info = {
        "state": emotion.current_state.value,
        "transitions": emotion.transition_count,
        "modifier": emotion.get_state_modifier()
    } if emotion else None
    
    # get time metrics
    metrics = time_tracker.get_metrics(session_id)
    
    return {
        "session_id": session_id,
        "scam_detected": session.scam_detected,
        "scam_confidence": session.scam_confidence,
        "message_count": session.message_count,
        "callback_sent": session.callback_sent,
        "engagement": engagement,
        "intel": session.intel.to_dict(),
        "status": automation.get_engagement_status(session),
        "fake_identity": identity_dict,
        "emotional_state": emotional_info,
        "metrics": metrics
    }


@app.post("/api/force-callback/{session_id}")
async def force_callback(session_id: str, api_key: str = Depends(verify_api_key)):
    """manually trigger callback for a session"""
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="session not found")
    
    if session.callback_sent:
        return {"status": "already_sent", "message": "callback was already sent"}
    
    result = automation.process_callback(session)
    return {"status": "success" if result.get("success") else "failed", "result": result}


@app.get("/api/image/{image_type}")
async def generate_image(
    image_type: str,
    bank: Optional[str] = "SBI",
    amount: Optional[str] = "₹500",
    status: Optional[str] = "pending",
    api_key: str = Depends(verify_api_key)
):
    """
    generate fake images on demand
    
    image_type options:
    - bank_balance: fake bank balance screenshot
    - upi_payment: fake UPI payment screenshot (status: pending/success/failed)
    - otp: fake OTP message screenshot
    - id_card: fake blurred ID card (aadhar/pan)
    - bank_statement: fake bank statement
    - wallet: fake wallet balance
    - error: fake error screen
    """
    
    if image_type == "bank_balance":
        result = image_gen.generate_bank_screenshot(bank_name=bank, balance=amount)
    elif image_type == "upi_payment":
        result = image_gen.generate_upi_screenshot(amount=amount, status=status)
    elif image_type == "otp":
        result = image_gen.generate_otp_screenshot()
    elif image_type == "id_card":
        result = image_gen.generate_id_screenshot(doc_type="aadhar")
    elif image_type == "bank_statement":
        result = image_gen.generate_bank_statement(bank_name=bank)
    elif image_type == "wallet":
        result = image_gen.generate_wallet_screenshot(balance=amount)
    elif image_type == "error":
        result = image_gen.generate_error_screenshot(error_type="network")
    else:
        raise HTTPException(status_code=400, detail=f"Unknown image type: {image_type}")
    
    if result.get("success"):
        # redirect to the image URL
        return RedirectResponse(url=result["image_url"])
    else:
        return result


@app.get("/api/metrics")
async def get_metrics(api_key: str = Depends(verify_api_key)):
    """get global engagement metrics - how much time we've wasted scammers!"""
    return time_tracker.get_global_metrics()


@app.get("/api/scammers")
async def get_known_scammers(api_key: str = Depends(verify_api_key)):
    """get list of known scammer fingerprints"""
    return scammer_db.get_known_scammers()


@app.post("/api/message", response_model=MessageResponse)
async def handle_message(request: MessageRequest, api_key: str = Depends(verify_api_key)):
    """
    main endpoint - receives messages and returns responses
    
    flow:
    1. get/create session, start timing
    2. create fake identity for session
    3. sync conversation history
    4. detect language
    5. classify scam type
    6. check for repeat scammer
    7. update emotional state
    8. check if scammer wants image/screenshot
    9. generate ai response with tactical approach
    10. extract intelligence & fingerprint scammer
    11. send callback if ready
    12. send alerts (Discord/Telegram)
    13. return response with optional image
    """
    
    # 1. get or create session, start timing
    session = session_store.get_or_create(request.sessionId)
    time_tracker.start_session(request.sessionId)
    
    # 2. get fake identity for this session (consistent throughout - uses cached generator)
    identity = get_fake_identity(request.sessionId)
    
    # initialize emotional state for session
    if request.sessionId not in emotional_states:
        emotional_states[request.sessionId] = EmotionalContext(session_id=request.sessionId)
    emotion = emotional_states[request.sessionId]
    
    # 3. sync conversation history from request
    if request.conversationHistory:
        for msg in request.conversationHistory:
            existing_texts = [m["text"] for m in session.conversation]
            if msg.text not in existing_texts:
                session.add_message(msg.sender, msg.text, msg.timestamp)
    
    # add the new incoming message
    session.add_message(
        request.message.sender,
        request.message.text,
        request.message.timestamp
    )
    
    # track message in metrics
    time_tracker.add_message(request.sessionId, is_scammer=True)
    
    # 4. detect language
    detected_lang = detect_language(request.message.text)
    lang_name = get_language_name(detected_lang)
    print(f"[LANG] Detected: {lang_name} for session {request.sessionId}")
    
    # 5. classify scam type - extract just the text from conversation
    conv_texts = [m.get("text", "") for m in session.conversation] if session.conversation else []
    scam_classification = classify_scam(request.message.text, conv_texts)
    scam_type = scam_classification.scam_type
    scam_tactics = scam_classification.suggested_tactics
    print(f"[SCAM TYPE] {scam_type} ({scam_classification.confidence:.0%})")
    
    # 6. detect scam intent (original detection)
    scam_result = detect_scam(request.message.text)
    
    # if not obvious, analyze full conversation
    if not scam_result["is_scam"] and session.message_count > 1:
        scam_result = analyze_conversation(session.conversation)
    
    # update session scam status
    if scam_result["is_scam"]:
        session.scam_detected = True
        session.scam_confidence = max(session.scam_confidence, scam_result["confidence"])
        print(f"[SCAM] Detected! Confidence: {scam_result['confidence']} Categories: {scam_result['categories']}")
        
        # alert on first detection (new session)
        if session.message_count == 1:
            alert_new_session(request.sessionId, request.message.text, scam_type)
    
    # 7. check for repeat scammer (based on extracted intel)
    temp_intel = extract_from_text(request.message.text)
    repeat_check = scammer_db.check_fingerprint(temp_intel.to_dict())
    
    if repeat_check.get("is_known"):
        print(f"[ALERT] Repeat scammer detected! Fingerprint: {repeat_check['fingerprint_id']}")
        alert_repeat_scammer(request.sessionId, repeat_check)
    
    # 8. update emotional state based on scammer's message
    emotion.transition(request.message.text)
    emotional_modifier = emotion.get_state_modifier()
    
    # 9. check if scammer is asking for image/screenshot
    image_request = check_image_request(request.message.text)
    image_url = None
    image_type = None
    
    if image_request["wants_image"]:
        print(f"[IMAGE] Scammer wants: {image_request['image_type']}")
        
        # get current tactics stage
        current_stage = get_stage(request.sessionId)
        
        # generate appropriate image based on stage
        if image_request["image_type"] == "otp" and current_stage in ["initial_confusion", "building_trust"]:
            # early stage - send error instead of OTP
            img_result = generate_image_for_request("error", error_type="network")
        else:
            img_result = generate_image_for_request(image_request["image_type"])
        
        if img_result.get("success"):
            image_url = img_result["image_url"]
            image_type = img_result["type"]
            print(f"[IMAGE] Generated: {image_type}")
    
    # 10. generate response
    if session.scam_detected:
        history = session.get_history_for_prompt()
        metadata_dict = request.metadata.model_dump() if request.metadata else {}
        
        # add detected language to metadata
        metadata_dict["detected_language"] = lang_name
        
        # add image context if we're sending one
        if image_url:
            metadata_dict["sending_image"] = True
            metadata_dict["image_type"] = image_type
        
        # add fake identity to metadata
        metadata_dict["victim_name"] = identity.full_name
        metadata_dict["victim_age"] = identity.age
        metadata_dict["victim_occupation"] = identity.occupation
        
        # add emotional state
        metadata_dict["emotional_state"] = emotion.current_state.value
        metadata_dict["emotional_modifier"] = emotional_modifier
        
        # add scam-specific tactics
        metadata_dict["scam_type"] = scam_type
        metadata_dict["recommended_tactics"] = scam_tactics[:2] if scam_tactics else []
        
        reply = get_agent_response(
            conversation_history=history,
            latest_message=request.message.text,
            metadata=metadata_dict
        )
        
        # if sending image, append image context to reply
        if image_url and image_type:
            image_messages = {
                "en": {
                    "bank_balance": "Here is my balance screenshot sir",
                    "upi_pending": "Payment is pending, see screenshot",
                    "upi_failed": "Sir payment failed! See the error",
                    "upi_success": "Done sir, payment sent! See proof",
                    "error_network": "Sir network problem! See error screenshot",
                    "otp_message": "Here is OTP screenshot",
                    "id_aadhar": "Here is my Aadhar photo sir",
                    "id_pan": "Here is my PAN card photo",
                    "bank_statement": "Here is my statement sir",
                    "wallet_balance": "Here is wallet balance sir"
                },
                "hi": {
                    "bank_balance": "ये रहा बैलेंस का स्क्रीनशॉट सर",
                    "upi_pending": "पेमेंट pending है, स्क्रीनशॉट देखिए",
                    "upi_failed": "सर पेमेंट fail हो गया! error देखिए",
                    "error_network": "सर नेटवर्क प्रॉब्लम है! error देखिए",
                    "otp_message": "ये रहा OTP का स्क्रीनशॉट"
                }
            }
            lang_msgs = image_messages.get(detected_lang, image_messages["en"])
            img_msg = lang_msgs.get(image_type, "Here is the screenshot sir")
            reply = f"{reply}\n\n📷 {img_msg}"
        
        # advance tactics stage
        advance_conversation(request.sessionId)
        
    else:
        # not detected as scam yet - respond neutrally in detected language
        neutral_responses = {
            "en": "Hello, I received your message. Can you please share more details?",
            "hi": "नमस्ते, मुझे आपका संदेश मिला। कृपया और जानकारी दें?",
            "ta": "வணக்கம், உங்கள் செய்தி கிடைத்தது. மேலும் விவரங்கள் தரவும்?",
            "te": "నమస్కారం, మీ సందేశం వచ్చింది. దయచేసి మరిన్ని వివరాలు చెప్పండి?",
        }
        reply = neutral_responses.get(detected_lang, neutral_responses["en"])
    
    # add our response to session
    session.add_message("user", reply)
    
    # track our message in metrics
    time_tracker.add_message(request.sessionId, is_scammer=False)
    
    # 11. extract intelligence
    session.intel = extract_from_conversation(session.conversation)
    latest_intel = extract_from_text(request.message.text)
    session.intel.merge(latest_intel)
    
    # fingerprint the scammer
    intel_dict = session.intel.to_dict()
    if intel_dict.get("phoneNumbers") or intel_dict.get("upiIds"):
        scammer_db.add_or_update_scammer(
            intel=intel_dict,
            session_id=request.sessionId,
            scam_type=scam_type
        )
        
        # alert if high-value intel extracted
        alert_intel_extracted(request.sessionId, intel_dict)
    
    # 12. check if we should send callback (using automation)
    if automation.should_send_callback(session):
        result = automation.process_callback(session)
        if result.get("success"):
            print(f"[CALLBACK] Sent for session {session.session_id}")
    
    # 13. return response with optional image
    return MessageResponse(
        status="success",
        reply=reply,
        image_url=image_url,
        image_type=image_type
    )


# --- run directly ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
