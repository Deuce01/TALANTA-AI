from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# ==================== Market Intelligence Schemas ====================

class SkillGap(BaseModel):
    """A skill gap identified for the user"""
    skill_name: str
    jobs_requiring: int
    avg_salary: Optional[int] = None
    demand_trend: str = "stable"  # rising, stable, falling


class GapAnalysisResponse(BaseModel):
    """Analysis of user's skill gaps vs market"""
    missing_skills: List[SkillGap]
    matched_jobs_count: int
    total_jobs_analyzed: int
    user_skills: List[str]


class TrainingCenterCourse(BaseModel):
    """Course offered by training center"""
    name: str
    skill: str
    duration: str
    cost: Optional[int] = None


class TrainingCenterResponse(BaseModel):
    """Training center information"""
    id: str
    name: str
    accreditation: str
    courses: List[TrainingCenterCourse]
    location_name: str
    distance_km: float
    contact_phone: Optional[str] = None


class NearbyTrainingCentersResponse(BaseModel):
    """Nearby training centers for a skill"""
    centers: List[TrainingCenterResponse]
    skill_searched: str
    total_found: int


class JobListing(BaseModel):
    """Job listing details"""
    id: str
    title: str
    company: Optional[str]
    location: Optional[str]
    salary_range: Optional[str]
    required_skills: List[str]
    match_score: Optional[float] = None  # 0-1 similarity score


class JobSearchResponse(BaseModel):
    """Job search results"""
    jobs: List[JobListing]
    total_count: int
    filters_applied: dict
