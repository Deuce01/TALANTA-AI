from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.database import get_db, get_redis
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    SuggestedAction,
    ExtractedEntities,
)
from app.services.chat_service import ChatService
from app.services.graph_service import GraphService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/message", response_model=ChatMessageResponse)
async def process_message(
    request: ChatMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
):
    """
    Module B: Conversational Profiling Engine
    
    Process user message through LLM pipeline:
    1. Classify intent (PROFILE_UPDATE, JOB_SEARCH, etc.)
    2. Extract entities (skills, location, experience)
    3. Update Neo4j graph with relationships
    4. Generate contextual response
    
    This is the "Neural Workforce Grid" in action.
    """
    try:
        # Initialize services
        chat_service = ChatService()
        graph_service = GraphService()
        
        # Get or create session
        session_id = request.session_id or f"session:{user.id}"
        
        # Process message through LLM
        result = await chat_service.process_message(
            user_id=str(user.id),
            message=request.text,
            session_id=session_id,
            redis_client=redis,
        )
        
        # If entities extracted, update graph
        if result.get("entities"):
            await graph_service.update_user_profile(
                user_id=str(user.id),
                entities=result["entities"],
            )
            logger.info(f"Updated graph for user {user.id}: {result['entities']}")
        
        # Generate suggested actions based on intent
        suggested_actions = []
        intent = result.get("intent", "GENERAL_CHAT")
        
        if intent == "PROFILE_UPDATE" and result.get("entities", {}).get("skills"):
            suggested_actions.append(
                SuggestedAction(
                    action_type="UPLOAD_CERTIFICATE",
                    label="📜 Upload Certificate to Verify Skills",
                    data={"skills": result["entities"]["skills"]}
                )
            )
        
        elif intent == "JOB_SEARCH":
            suggested_actions.append(
                SuggestedAction(
                    action_type="VIEW_JOBS",
                    label="💼 View Matching Jobs",
                )
            )
            suggested_actions.append(
                SuggestedAction(
                    action_type="GAP_ANALYSIS",
                    label="📊 Analyze My Skill Gaps",
                )
            )
        
        elif intent == "TRAINING_INQUIRY":
            suggested_actions.append(
                SuggestedAction(
                    action_type="FIND_TRAINING",
                    label="🎓 Find Nearby Training Centers",
                )
            )
        
        # Build response
        entities_extracted = None
        if result.get("entities"):
            entities_extracted = ExtractedEntities(**result["entities"])
        
        return ChatMessageResponse(
            reply_text=result["reply"],
            session_id=session_id,
            suggested_actions=suggested_actions,
            entities_extracted=entities_extracted,
            intent=intent,
        )
    
    except Exception as e:
        logger.error(f"Error processing chat message: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message. Please try again."
        )


@router.get("/history")
async def get_conversation_history(
    user: User = Depends(get_current_user),
    redis=Depends(get_redis),
):
    """
    Retrieve user's conversation history from Redis.
    """
    session_id = f"session:{user.id}"
    history_key = f"chat_history:{session_id}"
    
    history = await redis.lrange(history_key, 0, -1)
    
    import json
    messages = [json.loads(msg) for msg in history] if history else []
    
    return {
        "session_id": session_id,
        "messages": messages,
        "count": len(messages),
    }
