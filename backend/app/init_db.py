"""
init_db.py - Database initialization and seeding script

Run this script to initialize the database with default plans,
create an admin user, and set up initial data.

Usage:
    python -m app.init_db
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.core.config import settings
from app.core.security import hash_password
from app.db.models.user import User, UserRole
from app.db.models.user_settings import UserSettings
from app.db.models.scan import ScanRequest
from app.db.models.threat import BlockedThreat, ThreatType, ThreatStatus
from app.db.models.subscription import Subscription, Plan, PlanTier, SubscriptionStatus
from app.db.models.session import HoneypotSession


async def init_database():
    """Initialize database connection and Beanie ODM."""
    print("🔌 Connecting to MongoDB...")
    
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    
    await init_beanie(
        database=client[settings.MONGODB_DB_NAME],
        document_models=[
            User,
            UserSettings,
            ScanRequest,
            BlockedThreat,
            Subscription,
            Plan,
            HoneypotSession,
        ]
    )
    
    print(f"✅ Connected to database: {settings.MONGODB_DB_NAME}")
    return client


async def create_indexes():
    """Create database indexes for better query performance."""
    print("📊 Creating indexes...")
    
    # Note: Beanie automatically creates indexes for Indexed() fields
    # Additional compound indexes can be added here if needed
    # Using get_settings().motor_collection for async motor operations
    
    try:
        # User indexes - additional indexes beyond Indexed() fields
        user_collection = User.get_settings().motor_collection
        await user_collection.create_index("verification_token")
        await user_collection.create_index("reset_token")
        await user_collection.create_index("api_key")
        
        # Scan indexes
        scan_collection = ScanRequest.get_settings().motor_collection
        await scan_collection.create_index("user_id")
        await scan_collection.create_index("created_at")
        await scan_collection.create_index([("user_id", 1), ("created_at", -1)])
        
        # Threat indexes
        threat_collection = BlockedThreat.get_settings().motor_collection
        await threat_collection.create_index("user_id")
        await threat_collection.create_index("status")
        await threat_collection.create_index("threat_type")
        await threat_collection.create_index("created_at")
        
        # Subscription indexes
        sub_collection = Subscription.get_settings().motor_collection
        await sub_collection.create_index("user_id")
        await sub_collection.create_index("status")
        
        # Session indexes
        session_collection = HoneypotSession.get_settings().motor_collection
        await session_collection.create_index("session_id", unique=True)
        await session_collection.create_index("user_id")
        await session_collection.create_index("expires_at")
        
        print("✅ Indexes created")
    except Exception as e:
        print(f"⚠️  Some indexes may already exist or couldn't be created: {e}")
        print("   Continuing anyway - Beanie creates basic indexes automatically")


async def seed_plans():
    """Create default subscription plans."""
    print("📦 Seeding subscription plans...")
    
    # Check if plans already exist
    existing_plans = await Plan.find_all().count()
    if existing_plans > 0:
        print("  ⏭️  Plans already exist, skipping...")
        return
    
    plans = [
        Plan(
            name="Free",
            tier=PlanTier.FREE,
            price_monthly=0,
            price_yearly=0,
            currency="INR",
            scan_limit_daily=10,
            scan_limit_monthly=300,
            history_retention_days=7,
            features=[
                "10 scans per day",
                "Basic threat detection",
                "Email alerts",
                "Community support"
            ],
            is_active=True
        ),
        Plan(
            name="Pro",
            tier=PlanTier.PRO,
            price_monthly=299,
            price_yearly=2999,
            currency="INR",
            scan_limit_daily=500,
            scan_limit_monthly=15000,
            history_retention_days=90,
            features=[
                "500 scans per day",
                "AI-powered analysis",
                "Real-time protection",
                "API access",
                "Custom webhooks",
                "Scan history (90 days)",
                "Priority support"
            ],
            is_active=True
        ),
        Plan(
            name="Enterprise",
            tier=PlanTier.ENTERPRISE,
            price_monthly=999,
            price_yearly=9999,
            currency="INR",
            scan_limit_daily=None,  # Unlimited
            scan_limit_monthly=None,
            history_retention_days=365,
            features=[
                "Unlimited scans",
                "Custom AI model training",
                "Dedicated account manager",
                "SLA guarantee",
                "Custom integrations",
                "White-label options",
                "Unlimited scan history",
                "24/7 premium support"
            ],
            is_active=True
        )
    ]
    
    for plan in plans:
        await plan.insert()
        print(f"  ✅ Created plan: {plan.name}")
    
    print(f"✅ Created {len(plans)} plans")


async def create_admin_user(
    email: str = None,
    password: str = None,
    name: str = "Admin"
) -> Optional[User]:
    """Create admin user if it doesn't exist."""
    print("👤 Creating admin user...")
    
    # Use environment variables or defaults
    admin_email = email or os.getenv("ADMIN_EMAIL", "admin@scamshield.io")
    admin_password = password or os.getenv("ADMIN_PASSWORD", "Admin@123!")
    
    # Check if admin exists
    existing_admin = await User.find_one(User.email == admin_email.lower())
    if existing_admin:
        print(f"  ⏭️  Admin user already exists: {admin_email}")
        return existing_admin
    
    # Create admin user
    admin = User(
        email=admin_email.lower(),
        password_hash=hash_password(admin_password),
        full_name=name,
        role=UserRole.ADMIN,
        is_verified=True,
        is_active=True
    )
    await admin.insert()
    
    # Create settings
    settings_obj = UserSettings(user_id=str(admin.id))
    await settings_obj.insert()
    
    # Create enterprise subscription
    enterprise_plan = await Plan.find_one(Plan.tier == PlanTier.ENTERPRISE)
    if enterprise_plan:
        subscription = Subscription(
            user_id=str(admin.id),
            plan_id=str(enterprise_plan.id),
            plan_tier=PlanTier.ENTERPRISE,
            status=SubscriptionStatus.ACTIVE
        )
        await subscription.insert()
    
    print(f"  ✅ Admin user created: {admin_email}")
    print(f"  ⚠️  Default password: {admin_password}")
    print("  🔒 Please change the admin password after first login!")
    
    return admin


async def seed_sample_threats():
    """Create sample threat data for demo purposes."""
    print("🛡️ Seeding sample threats...")
    
    # Check if threats already exist
    existing_threats = await BlockedThreat.find_all().count()
    if existing_threats > 0:
        print("  ⏭️  Threats already exist, skipping...")
        return
    
    # Get admin user for associating sample threats
    admin = await User.find_one(User.role == UserRole.ADMIN)
    user_id = str(admin.id) if admin else "demo_user"
    
    sample_threats = [
        BlockedThreat(
            user_id=user_id,
            threat_type=ThreatType.PHISHING,
            status=ThreatStatus.BLOCKED,
            sender_info="scammer@fake-bank.com",
            message_preview="Dear Customer, Your account will be suspended. Click here to verify...",
            risk_score=0.95,
            action_taken="blocked"
        ),
        BlockedThreat(
            user_id=user_id,
            threat_type=ThreatType.LOTTERY,
            status=ThreatStatus.BLOCKED,
            sender_info="+91-9876543210",
            message_preview="Congratulations! You've won ₹50,00,000! Click here to claim your prize...",
            risk_score=0.88,
            action_taken="blocked"
        ),
        BlockedThreat(
            user_id=user_id,
            threat_type=ThreatType.TECH_SUPPORT,
            status=ThreatStatus.REPORTED,
            sender_info="+91-8765432109",
            message_preview="This is Microsoft Support. Your computer has a virus. Call us immediately...",
            risk_score=0.75,
            action_taken="reported"
        ),
        BlockedThreat(
            user_id=user_id,
            threat_type=ThreatType.BANKING,
            status=ThreatStatus.BLOCKED,
            sender_info="security@hdfc-verify.xyz",
            message_preview="Your HDFC Bank account is locked. Update your KYC now: http://hdfc-kyc.xyz...",
            risk_score=0.98,
            action_taken="blocked"
        ),
        BlockedThreat(
            user_id=user_id,
            threat_type=ThreatType.IMPERSONATION,
            status=ThreatStatus.BLOCKED,
            sender_info="support@amazon-refund.com",
            message_preview="Your Amazon order refund is pending. Please verify your bank details...",
            risk_score=0.82,
            action_taken="blocked"
        )
    ]
    
    for threat in sample_threats:
        await threat.insert()
    
    print(f"✅ Created {len(sample_threats)} sample threats")


async def print_summary():
    """Print database summary."""
    print("\n" + "=" * 50)
    print("📊 DATABASE SUMMARY")
    print("=" * 50)
    
    users = await User.find_all().count()
    plans = await Plan.find_all().count()
    threats = await BlockedThreat.find_all().count()
    scans = await ScanRequest.find_all().count()
    
    print(f"  👤 Users: {users}")
    print(f"  📦 Plans: {plans}")
    print(f"  🛡️ Threats: {threats}")
    print(f"  🔍 Scans: {scans}")
    print("=" * 50)


async def main():
    """Main initialization function."""
    print("\n" + "=" * 50)
    print("🚀 SCAMSHIELD DATABASE INITIALIZATION")
    print("=" * 50 + "\n")
    
    try:
        # Initialize database
        client = await init_database()
        
        # Create indexes
        await create_indexes()
        
        # Seed plans
        await seed_plans()
        
        # Create admin user
        await create_admin_user()
        
        # Seed sample threats (optional, for demo)
        await seed_sample_threats()
        
        # Print summary
        await print_summary()
        
        print("\n✅ Database initialization complete!")
        print("🌐 You can now start the ScamShield API server.\n")
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {str(e)}")
        raise
    finally:
        if 'client' in locals():
            client.close()


if __name__ == "__main__":
    asyncio.run(main())
