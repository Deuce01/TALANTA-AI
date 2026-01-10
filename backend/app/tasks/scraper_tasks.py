from app.tasks.celery_app import celery_app
import logging
import random

logger = logging.getLogger(__name__)


@celery_app.task
def scrape_jobs():
    """
    Background task to scrape job listings from various sources.
    
    For MVP: Generates mock job data.
    In production: Integrate with BrighterMonday, MyJobMag, LinkedIn APIs.
    """
    from app.database import AsyncSessionLocal
    from app.models.jobs import Job
    from app.services.vector_service import VectorService
    import asyncio
    import uuid
    from datetime import datetime, timedelta
    
    logger.info("Starting job scraping task...")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(_scrape_jobs_async())
    loop.close()
    
    return result


async def _scrape_jobs_async():
    """Async implementation of job scraping"""
    
    # Mock job data for MVP
    job_templates = [
        {
            "title": "Plumber",
            "company": "KenWater Solutions",
            "description": "Experienced plumber needed for residential projects in Nairobi.",
            "required_skills": ["Plumbing", "Pipe Fitting"],
            "location": "Nairobi",
            "salary_min": 35000,
            "salary_max": 55000,
        },
        {
            "title": "Electrician",
            "company": "PowerGrid Kenya",
            "description": "Licensed electrician for commercial installations.",
            "required_skills": ["Electrical Wiring", "Troubleshooting"],
            "location": "Mombasa",
            "salary_min": 40000,
            "salary_max": 60000,
        },
        {
            "title": "Solar Installer",
            "company": "SunPower Africa",
            "description": "Solar panel installation and maintenance specialist.",
            "required_skills": ["Solar Installation", "Electrical Wiring"],
            "location": "Kisumu",
            "salary_min": 45000,
            "salary_max": 70000,
        },
        {
            "title": "Carpenter",
            "company": "WoodCraft Ltd",
            "description": "Skilled carpenter for furniture manufacturing.",
            "required_skills": ["Carpentry", "Wood Working"],
            "location": "Nakuru",
            "salary_min": 30000,
            "salary_max": 50000,
        },
        {
            "title": "Automotive Mechanic",
            "company": "AutoFix Garage",
            "description": "Experienced mechanic for vehicle repairs and maintenance.",
            "required_skills": ["Automotive Repair", "Diagnostics"],
            "location": "Nairobi",
            "salary_min": 35000,
            "salary_max": 65000,
        },
    ]
    
    async with AsyncSessionLocal() as db:
        jobs_created = 0
        
        for template in job_templates:
            # Create multiple variations
            for i in range(3):
                job = Job(
                    id=uuid.uuid4(),
                    title=template["title"],
                    company=f"{template['company']} - Branch {i+1}",
                    description=template["description"],
                    required_skills=template["required_skills"],
                    location=template["location"],
                    salary_min=template["salary_min"],
                    salary_max=template["salary_max"],
                    currency="KES",
                    is_active="ACTIVE",
                    source_name="MOCK_SCRAPER",
                    expires_at=datetime.utcnow() + timedelta(days=30),
                )
                
                db.add(job)
                jobs_created += 1
        
        await db.commit()
        
        logger.info(f"✓ Created {jobs_created} mock job listings")
        
        return {
            "jobs_created": jobs_created,
            "source": "mock",
            "timestamp": datetime.utcnow().isoformat(),
        }
