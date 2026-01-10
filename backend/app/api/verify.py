from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import logging
import uuid

from app.database import get_db, get_s3_client
from app.dependencies import get_current_user
from app.models.user import User
from app.models.verification import Verification, DocumentType, VerificationStatus
from app.schemas.verify import (
    UploadDocumentResponse,
    VerificationStatusResponse,
    MyVerificationsResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=UploadDocumentResponse)
async def upload_verification_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    skill_name: str = Form(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Module D: Verification & Trust Layer - Document Upload
    
    Upload verification document (ID, Certificate, etc.)
    Triggers OCR processing via Celery task.
    
    This is the pathway from "Claimed Skills" to "Verified Skills".
    """
    # Validate document type
    try:
        doc_type = DocumentType[document_type.upper()]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid document type. Must be one of: {[t.value for t in DocumentType]}"
        )
    
    # Validate file size (max 5MB)
    MAX_FILE_SIZE = 5 * 1024 * 1024
    contents = await file.read()
    file_size = len(contents)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds 5MB limit"
        )
    
    # Validate file type
    allowed_extensions = [".jpg", ".jpeg", ".png", ".pdf"]
    file_extension = file.filename.split(".")[-1].lower()
    
    if f".{file_extension}" not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {allowed_extensions}"
        )
    
    try:
        # Generate unique filename
        verification_id = uuid.uuid4()
        s3_key = f"verifications/{user.id}/{verification_id}.{file_extension}"
        
        # Upload to S3/MinIO
        s3_client = get_s3_client()
        from app.config import settings
        s3_client.put_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=s3_key,
            Body=contents,
            ContentType=file.content_type,
        )
        
        logger.info(f"Uploaded file to S3: {s3_key}")
        
        # Create verification record
        verification = Verification(
            id=verification_id,
            user_id=user.id,
            document_type=doc_type,
            s3_url=s3_key,
            file_size=file_size,
            status=VerificationStatus.PENDING,
        )
        
        db.add(verification)
        await db.commit()
        await db.refresh(verification)
        
        # Queue OCR processing task (Celery)
        from app.tasks.ocr_tasks import process_verification
        process_verification.delay(str(verification.id))
        
        logger.info(f"Queued OCR processing for verification {verification.id}")
        
        return UploadDocumentResponse(
            verification_id=str(verification.id),
            status="PROCESSING",
            estimated_time="2-5 minutes",
            message="Document uploaded successfully. Processing will complete shortly.",
        )
    
    except Exception as e:
        logger.error(f"Error uploading document: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document. Please try again."
        )


@router.get("/status/{verification_id}", response_model=VerificationStatusResponse)
async def get_verification_status(
    verification_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check status of a verification request.
    """
    result = await db.execute(
        select(Verification).where(
            Verification.id == verification_id,
            Verification.user_id == user.id,
        )
    )
    verification = result.scalar_one_or_none()
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification not found"
        )
    
    return VerificationStatusResponse(
        verification_id=str(verification.id),
        status=verification.status.value,
        document_type=verification.document_type.value,
        created_at=verification.created_at,
        verified_at=verification.verified_at,
        rejection_reason=verification.rejection_reason,
        extracted_skill=verification.extracted_skill,
        trust_score_delta=verification.trust_score_delta,
    )


@router.get("/my-verifications", response_model=MyVerificationsResponse)
async def get_my_verifications(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all verifications for current user.
    """
    result = await db.execute(
        select(Verification)
        .where(Verification.user_id == user.id)
        .order_by(Verification.created_at.desc())
    )
    verifications = result.scalars().all()
    
    # Build response
    verification_list = []
    verified_count = 0
    pending_count = 0
    
    for v in verifications:
        verification_list.append(
            VerificationStatusResponse(
                verification_id=str(v.id),
                status=v.status.value,
                document_type=v.document_type.value,
                created_at=v.created_at,
                verified_at=v.verified_at,
                rejection_reason=v.rejection_reason,
                extracted_skill=v.extracted_skill,
                trust_score_delta=v.trust_score_delta,
            )
        )
        
        if v.status == VerificationStatus.VERIFIED:
            verified_count += 1
        elif v.status in [VerificationStatus.PENDING, VerificationStatus.PROCESSING]:
            pending_count += 1
    
    return MyVerificationsResponse(
        verifications=verification_list,
        total_count=len(verification_list),
        verified_count=verified_count,
        pending_count=pending_count,
    )
