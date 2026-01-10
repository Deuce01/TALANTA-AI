from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.market import (
    GapAnalysisResponse,
    SkillGap,
    NearbyTrainingCentersResponse,
    JobSearchResponse,
)
from app.services.graph_service import GraphService
from app.services.vector_service import VectorService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/gap-analysis", response_model=GapAnalysisResponse)
async def analyze_skill_gaps(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Module C: Market Intelligence - Gap Analysis
    
    Analyzes user's skills vs market demand:
    1. Fetch user's verified skills from Neo4j
    2. Semantic search for matching jobs
    3. Identify missing skills
    4. Return actionable insights
    
    This is the "Shadow Curriculum" replacement.
    """
    try:
        graph_service = GraphService()
        vector_service = VectorService()
        
        # Get user skills from graph
        user_skills = await graph_service.get_user_skills(str(user.id))
        
        if not user_skills:
            return GapAnalysisResponse(
                missing_skills=[],
                matched_jobs_count=0,
                total_jobs_analyzed=0,
                user_skills=[],
            )
        
        # Find matching jobs using vector search
        matching_jobs = await vector_service.find_matching_jobs(
            user_skills=user_skills,
            top_k=50,
            db=db,
        )
        
        # Analyze skill gaps
        all_required_skills = set()
        for job in matching_jobs:
            all_required_skills.update(job.get("required_skills", []))
        
        user_skill_set = set(s.lower() for s in user_skills)
        missing_skills_set = all_required_skills - user_skill_set
        
        # Count jobs requiring each missing skill
        missing_skills = []
        for skill in missing_skills_set:
            jobs_requiring = sum(
                1 for job in matching_jobs 
                if skill.lower() in [s.lower() for s in job.get("required_skills", [])]
            )
            
            if jobs_requiring > 0:
                missing_skills.append(
                    SkillGap(
                        skill_name=skill.title(),
                        jobs_requiring=jobs_requiring,
                        demand_trend="rising",  # TODO: Calculate from time-series data
                    )
                )
        
        # Sort by demand
        missing_skills.sort(key=lambda x: x.jobs_requiring, reverse=True)
        
        return GapAnalysisResponse(
            missing_skills=missing_skills[:10],  # Top 10 gaps
            matched_jobs_count=len(matching_jobs),
            total_jobs_analyzed=len(matching_jobs),
            user_skills=[s.title() for s in user_skills],
        )
    
    except Exception as e:
        logger.error(f"Error in gap analysis: {e}", exc_info=True)
        return GapAnalysisResponse(
            missing_skills=[],
            matched_jobs_count=0,
            total_jobs_analyzed=0,
            user_skills=[],
        )


@router.get("/training-centers", response_model=NearbyTrainingCentersResponse)
async def find_training_centers(
    skill: str = Query(..., description="Skill to learn"),
    lat: Optional[float] = Query(None, description="User latitude"),
    long: Optional[float] = Query(None, description="User longitude"),
    radius_km: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Module C: DCI Engine - Training Center Recommendations
    
    Find government-accredited training centers teaching specific skills.
    Uses geospatial queries to find nearest facilities.
    """
    from sqlalchemy import select, func
    from app.models.jobs import TrainingCenter
    from app.schemas.market import TrainingCenterResponse, TrainingCenterCourse
    
    # Use user's location if not provided
    user_lat = lat or user.location_lat
    user_long = long or user.location_long
    
    if not user_lat or not user_long:
        return NearbyTrainingCentersResponse(
            centers=[],
            skill_searched=skill,
            total_found=0,
        )
    
    try:
        # Fetch all training centers (in production, use PostGIS distance query)
        result = await db.execute(
            select(TrainingCenter).where(TrainingCenter.is_active == "ACTIVE")
        )
        all_centers = result.scalars().all()
        
        # Filter centers offering the skill and calculate distance
        import math
        
        def calculate_distance(lat1, lon1, lat2, lon2):
            """Haversine formula for distance in km"""
            R = 6371  # Earth radius in km
            dlat = math.radians(lat2 - lat1)
            dlon = math.radians(lon2 - lon1)
            a = (math.sin(dlat/2)**2 + 
                 math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
                 math.sin(dlon/2)**2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            return R * c
        
        matching_centers = []
        for center in all_centers:
            # Check if center offers courses for this skill
            courses_for_skill = [
                course for course in center.courses 
                if skill.lower() in course.get("skill", "").lower()
            ]
            
            if not courses_for_skill:
                continue
            
            # Calculate distance
            distance = calculate_distance(
                user_lat, user_long,
                center.location_lat, center.location_long
            )
            
            if distance <= radius_km:
                matching_centers.append({
                    "center": center,
                    "distance": distance,
                    "courses": courses_for_skill,
                })
        
        # Sort by distance
        matching_centers.sort(key=lambda x: x["distance"])
        
        # Build response
        centers_response = []
        for item in matching_centers[:10]:  # Top 10 nearest
            center = item["center"]
            courses = [TrainingCenterCourse(**c) for c in item["courses"]]
            
            centers_response.append(
                TrainingCenterResponse(
                    id=str(center.id),
                    name=center.name,
                    accreditation=center.accreditation or "N/A",
                    courses=courses,
                    location_name=center.location_name,
                    distance_km=round(item["distance"], 2),
                    contact_phone=center.contact_phone,
                )
            )
        
        return NearbyTrainingCentersResponse(
            centers=centers_response,
            skill_searched=skill,
            total_found=len(centers_response),
        )
    
    except Exception as e:
        logger.error(f"Error finding training centers: {e}", exc_info=True)
        return NearbyTrainingCentersResponse(
            centers=[],
            skill_searched=skill,
            total_found=0,
        )


@router.get("/jobs", response_model=JobSearchResponse)
async def search_jobs(
    skill: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    min_salary: Optional[int] = Query(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Search jobs with filters.
    """
    from sqlalchemy import select, and_
    from app.models.jobs import Job
    from app.schemas.market import JobListing
    
    # Build query
    conditions = [Job.is_active == "ACTIVE"]
    
    if location:
        conditions.append(Job.location.ilike(f"%{location}%"))
    
    if min_salary:
        conditions.append(Job.salary_min >= min_salary)
    
    query = select(Job).where(and_(*conditions)).limit(50)
    
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    # Build response
    job_listings = []
    for job in jobs:
        salary_range = None
        if job.salary_min and job.salary_max:
            salary_range = f"{job.currency} {job.salary_min:,} - {job.salary_max:,}"
        
        job_listings.append(
            JobListing(
                id=str(job.id),
                title=job.title,
                company=job.company,
                location=job.location,
                salary_range=salary_range,
                required_skills=job.required_skills or [],
            )
        )
    
    return JobSearchResponse(
        jobs=job_listings,
        total_count=len(job_listings),
        filters_applied={"skill": skill, "location": location, "min_salary": min_salary},
    )
