from app.tasks.celery_app import celery_app
from app.services.ocr_service import OCRService
from app.database import get_s3_client
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def process_verification(self, verification_id: str):
    """
    Background task to process document verification via OCR.
    
    Steps:
    1. Fetch verification record from DB
    2. Download document from S3
    3. Run OCR extraction
    4. Parse document-specific fields
    5. Validate against user profile
    6. Update verification status
    7. Update Neo4j if verified
    8. Update user trust score
    """
    from app.database import AsyncSessionLocal
    from app.models.verification import Verification, VerificationStatus, DocumentType
    from app.models.user import User
    from app.services.graph_service import GraphService
    from sqlalchemy import select
    import asyncio
    from datetime import datetime
    
    logger.info(f"Processing verification: {verification_id}")
    
    try:
        # Run async code in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_process_verification_async(verification_id))
        loop.close()
        
        return result
    
    except Exception as e:
        logger.error(f"Verification processing failed: {e}", exc_info=True)
        # Retry on failure
        self.retry(exc=e, countdown=60)  # Retry after 1 minute


async def _process_verification_async(verification_id: str):
    """Async implementation of verification processing"""
    
    async with AsyncSessionLocal() as db:
        # Fetch verification
        result = await db.execute(
            select(Verification).where(Verification.id == verification_id)
        )
        verification = result.scalar_one_or_none()
        
        if not verification:
            logger.error(f"Verification {verification_id} not found")
            return {"error": "Verification not found"}
        
        # Update status to PROCESSING
        verification.status = VerificationStatus.PROCESSING
        await db.commit()
        
        # Download document from S3
        s3_client = get_s3_client()
        try:
            from app.config import settings
            response = s3_client.get_object(
                Bucket=settings.S3_BUCKET_NAME,
                Key=verification.s3_url
            )
            image_bytes = response['Body'].read()
        except Exception as e:
            logger.error(f"S3 download failed: {e}")
            verification.status = VerificationStatus.REJECTED
            verification.rejection_reason = "Failed to retrieve document from storage"
            await db.commit()
            return {"error": "S3 download failed"}
        
        # Initialize OCR service
        ocr_service = OCRService()
        
        # Extract text
        ocr_results = ocr_service.extract_text(image_bytes)
        verification.ocr_data = {
            "results": [{"text": r["text"], "confidence": r["confidence"]} for r in ocr_results]
        }
        
        # Parse based on document type
        if verification.document_type == DocumentType.NATIONAL_ID:
            parsed = ocr_service.parse_kenyan_id(ocr_results)
            verification.extracted_name = parsed.get("full_name")
            verification.extracted_serial = parsed.get("id_number")
        
        elif verification.document_type in [DocumentType.CERTIFICATE, DocumentType.DIPLOMA]:
            parsed = ocr_service.parse_certificate(ocr_results)
            verification.extracted_skill = parsed.get("skill")
            verification.extracted_serial = parsed.get("serial")
            verification.extracted_institution = parsed.get("institution")
        
        # Fetch user for validation
        user_result = await db.execute(
            select(User).where(User.id == verification.user_id)
        )
        user = user_result.scalar_one()
        
        # Validation logic
        is_valid = True
        rejection_reasons = []
        
        # Mock KNQA API check (in production, call real API)
        if verification.extracted_serial:
            # TODO: Call KNQA API to verify serial number
            # mock_valid = mock_knqa_check(verification.extracted_serial)
            pass
        else:
            is_valid = False
            rejection_reasons.append("Serial number not found in document")
        
        # Name matching (if ID provided)
        if verification.document_type == DocumentType.NATIONAL_ID and verification.extracted_name:
            # Update user's full name if not set
            if not user.full_name:
                user.full_name = verification.extracted_name
        
        # Decide verification outcome
        if is_valid and not rejection_reasons:
            verification.status = VerificationStatus.VERIFIED
            verification.verified_at = datetime.utcnow()
            verification.verified_by = "SYSTEM"
            verification.trust_score_delta = 10
            
            # Update user trust score
            user.trust_score = min(100, user.trust_score + 10)
            
            # Update user verification status if ID verified
            if verification.document_type == DocumentType.NATIONAL_ID:
                user.is_verified = True
            
            # Update Neo4j if skill verified
            if verification.extracted_skill:
                graph_service = GraphService()
                await graph_service.verify_skill(
                    user_id=str(user.id),
                    skill_name=verification.extracted_skill
                )
            
            logger.info(f"✓ Verification approved: {verification_id}")
        
        else:
            verification.status = VerificationStatus.REJECTED
            verification.rejection_reason = "; ".join(rejection_reasons) if rejection_reasons else "Validation failed"
            logger.info(f"✗ Verification rejected: {verification_id}")
        
        await db.commit()
        
        return {
            "verification_id": str(verification.id),
            "status": verification.status.value,
            "trust_score_delta": verification.trust_score_delta,
        }
