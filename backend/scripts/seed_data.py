"""
Seed script to populate database with initial data.

Run this after migrations to create test data.
"""

import asyncio
from app.database import AsyncSessionLocal
from app.models.user import User, UserRole
from app.models.jobs import Job, TrainingCenter
from app.services.graph_service import GraphService
import uuid
from datetime import datetime, timedelta


async def seed_training_centers():
    """Create sample training centers"""
    
    centers_data = [
        {
            "name": "Nairobi Technical Training Institute",
            "accreditation": "TVETA",
            "courses": [
                {"name": "Plumbing Certificate", "skill": "Plumbing", "duration": "6 months", "cost": 25000},
                {"name": "Electrical Installation", "skill": "Electrical Wiring", "duration": "8 months", "cost": 30000},
            ],
            "location_name": "Nairobi CBD",
            "location_lat": -1.286389,
            "location_long": 36.817223,
            "county": "Nairobi",
            "contact_phone": "+254712000001",
        },
        {
            "name": "Mombasa Youth Polytechnic",
            "accreditation": "KNEC",
            "courses": [
                {"name": "Solar Installation Diploma", "skill": "Solar Installation", "duration": "1 year", "cost": 45000},
                {"name": "Carpentry Level 2", "skill": "Carpentry", "duration": "6 months", "cost": 20000},
            ],
            "location_name": "Mombasa",
            "location_lat": -4.043477,
            "location_long": 39.668206,
            "county": "Mombasa",
            "contact_phone": "+254712000002",
        },
        {
            "name": "Kisumu National Polytechnic",
            "accreditation": "TVETA",
            "courses": [
                {"name": "Automotive Mechanics", "skill": "Automotive Repair", "duration": "1 year", "cost": 40000},
                {"name": "Welding Technology", "skill": "Welding", "duration": "8 months", "cost": 35000},
            ],
            "location_name": "Kisumu",
            "location_lat": -0.091702,
            "location_long": 34.767956,
            "county": "Kisumu",
            "contact_phone": "+254712000003",
        },
    ]
    
    async with AsyncSessionLocal() as db:
        for data in centers_data:
            center = TrainingCenter(
                id=uuid.uuid4(),
                **data
            )
            db.add(center)
        
        await db.commit()
        print(f"✓ Created {len(centers_data)} training centers")


async def seed_jobs():
    """Create sample jobs"""
    
    jobs_data = [
        {
            "title": "Senior Plumber",
            "company": "KenWater Solutions Ltd",
            "description": "Experienced plumber needed for residential and commercial projects in Nairobi. Must have 3+ years experience.",
            "required_skills": ["Plumbing", "Pipe Fitting"],
            "location": "Nairobi",
            "location_lat": -1.286389,
            "location_long": 36.817223,
            "salary_min": 45000,
            "salary_max": 65000,
        },
        {
            "title": "Certified Electrician",
            "company": "PowerGrid Kenya",
            "description": "Licensed electrician for commercial installations. ERC license required.",
            "required_skills": ["Electrical Wiring", "Troubleshooting"],
            "location": "Mombasa",
            "salary_min": 50000,
            "salary_max": 75000,
        },
        {
            "title": "Solar Installation Technician",
            "company": "SunPower Africa",
            "description": "Install and maintain solar panel systems for residential clients.",
            "required_skills": ["Solar Installation", "Electrical Wiring"],
            "location": "Kisumu",
            "salary_min": 55000,
            "salary_max": 80000,
        },
        {
            "title": "Furniture Carpenter",
            "company": "WoodCraft Ltd",
            "description": "Skilled carpenter for custom furniture manufacturing.",
            "required_skills": ["Carpentry", "Wood Working"],
            "location": "Nakuru",
            "salary_min": 35000,
            "salary_max": 55000,
        },
        {
            "title": "Auto Mechanic",
            "company": "AutoFix Garage",
            "description": "Experienced mechanic for vehicle diagnostics and repairs.",
            "required_skills": ["Automotive Repair", "Diagnostics"],
            "location": "Nairobi",
            "salary_min": 40000,
            "salary_max": 70000,
        },
    ]
    
    async with AsyncSessionLocal() as db:
        for data in jobs_data:
            job = Job(
                id=uuid.uuid4(),
                currency="KES",
                is_active="ACTIVE",
                source_name="SEED_DATA",
                expires_at=datetime.utcnow() + timedelta(days=30),
                **data
            )
            db.add(job)
        
        await db.commit()
        print(f"✓ Created {len(jobs_data)} job listings")


async def seed_admin_user():
    """Create admin user for dashboard access"""
    
    from app.core.security import hash_phone_number
    
    async with AsyncSessionLocal() as db:
        admin_phone = "+254700000000"
        admin = User(
            id=uuid.uuid4(),
            phone_hash=hash_phone_number(admin_phone),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            trust_score=100,
            is_active=True,
            is_verified=True,
        )
        db.add(admin)
        await db.commit()
        
        print(f"✓ Created admin user")
        print(f"  Phone: {admin_phone}")
        print(f"  Use OTP from login to get access token")


async def init_neo4j_graph():
    """Initialize Neo4j skills taxonomy"""
    
    graph_service = GraphService()
    await graph_service.init_skills_taxonomy()
    print("✓ Initialized Neo4j skills taxonomy")


async def main():
    """Run all seed functions"""
    
    print("\n🌱 Seeding TALANTA AI Database...\n")
    
    try:
        await init_neo4j_graph()
        await seed_training_centers()
        await seed_jobs()
        await seed_admin_user()
        
        print("\n✅ Database seeded successfully!\n")
        print("Next steps:")
        print("1. Start the application: docker-compose up")
        print("2. Test login with admin: POST /auth/login")
        print("3. Access API docs: http://localhost:8000/docs")
        print("4. Access Neo4j browser: http://localhost:7474")
        
    except Exception as e:
        print(f"\n❌ Seeding failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
