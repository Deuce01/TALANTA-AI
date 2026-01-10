from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Dict, Any
import logging

from app.database import get_db
from app.dependencies import get_current_admin
from app.models.user import User, UserRole
from app.models.verification import Verification, VerificationStatus
from app.models.jobs import Job

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/metrics/overview")
async def get_overview_metrics(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Cabinet Secretary Dashboard - Overview Metrics
    
    High-level statistics for government decision-making.
    """
    # Total citizens
    total_citizens = await db.scalar(select(func.count(User.id)))
    
    # Verified citizens (those with Maisha Namba)
    verified_citizens = await db.scalar(
        select(func.count(User.id)).where(User.is_verified == True)
    )
    
    # Total verifications
    total_verifications = await db.scalar(select(func.count(Verification.id)))
    
    # Average trust score
    avg_trust_score = await db.scalar(select(func.avg(User.trust_score)))
    
    # Active jobs
    active_jobs = await db.scalar(
        select(func.count(Job.id)).where(Job.is_active == "ACTIVE")
    )
    
    return {
        "total_citizens": total_citizens or 0,
        "verified_citizens": verified_citizens or 0,
        "verification_rate": round((verified_citizens / total_citizens * 100), 2) if total_citizens else 0,
        "total_verifications": total_verifications or 0,
        "avg_trust_score": round(avg_trust_score, 2) if avg_trust_score else 0,
        "active_jobs": active_jobs or 0,
    }


@router.get("/metrics/skill-distribution")
async def get_skill_distribution(
    admin: User = Depends(get_current_admin),
    limit: int = 20,
) -> Dict[str, Any]:
    """
    Top skills by verified user count.
    Used for workforce planning.
    """
    from app.services.graph_service import GraphService
    
    graph_service = GraphService()
    skill_counts = await graph_service.get_skill_distribution(limit=limit)
    
    return {
        "skills": skill_counts,
        "total_unique_skills": len(skill_counts),
    }


@router.get("/metrics/verification-queue")
async def get_verification_queue(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Verification queue status by document type.
    """
    from app.models.verification import DocumentType
    
    queue_status = {}
    
    for doc_type in DocumentType:
        count = await db.scalar(
            select(func.count(Verification.id)).where(
                and_(
                    Verification.document_type == doc_type,
                    Verification.status.in_([VerificationStatus.PENDING, VerificationStatus.PROCESSING])
                )
            )
        )
        queue_status[doc_type.value] = count or 0
    
    total_pending = sum(queue_status.values())
    
    return {
        "by_document_type": queue_status,
        "total_pending": total_pending,
    }


@router.get("/reports/trust-score-distribution")
async def get_trust_score_distribution(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """
    Distribution of trust scores (histogram data).
    """
    from sqlalchemy import case
    
    # Create buckets: 0-20, 21-40, 41-60, 61-80, 81-100
    buckets = {
        "0-20": 0,
        "21-40": 0,
        "41-60": 0,
        "61-80": 0,
        "81-100": 0,
    }
    
    result = await db.execute(select(User.trust_score))
    scores = result.scalars().all()
    
    for score in scores:
        if score <= 20:
            buckets["0-20"] += 1
        elif score <= 40:
            buckets["21-40"] += 1
        elif score <= 60:
            buckets["41-60"] += 1
        elif score <= 80:
            buckets["61-80"] += 1
        else:
            buckets["81-100"] += 1
    
    return {
        "distribution": buckets,
        "total_users": len(scores),
    }


@router.post("/verifications/{verification_id}/override")
async def override_verification(
    verification_id: str,
    action: str,  # "approve" or "reject"
    reason: str = None,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Manual verification override by admin.
    Logged to audit trail.
    """
    if action not in ["approve", "reject"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action must be 'approve' or 'reject'"
        )
    
    result = await db.execute(
        select(Verification).where(Verification.id == verification_id)
    )
    verification = result.scalar_one_or_none()
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification not found"
        )
    
    from datetime import datetime
    from app.core.audit import log_audit_event
    
    if action == "approve":
        verification.status = VerificationStatus.VERIFIED
        verification.verified_at = datetime.utcnow()
        verification.verified_by = str(admin.id)
        verification.trust_score_delta = 10
        
        # Update user trust score
        user_result = await db.execute(
            select(User).where(User.id == verification.user_id)
        )
        user = user_result.scalar_one()
        old_score = user.trust_score
        user.trust_score = min(100, user.trust_score + 10)
        
        await log_audit_event(
            user_id=str(admin.id),
            action="MANUAL_VERIFICATION_APPROVE",
            entity_type="Verification",
            entity_id=str(verification.id),
            old_value={"status": "PENDING", "trust_score": old_score},
            new_value={"status": "VERIFIED", "trust_score": user.trust_score},
        )
    
    else:  # reject
        verification.status = VerificationStatus.REJECTED
        verification.rejection_reason = reason or "Rejected by admin"
        verification.verified_by = str(admin.id)
        
        await log_audit_event(
            user_id=str(admin.id),
            action="MANUAL_VERIFICATION_REJECT",
            entity_type="Verification",
            entity_id=str(verification.id),
            old_value={"status": "PENDING"},
            new_value={"status": "REJECTED", "reason": verification.rejection_reason},
        )
    
    await db.commit()
    
    return {
        "verification_id": str(verification.id),
        "status": verification.status.value,
        "message": f"Verification {action}d successfully",
    }
