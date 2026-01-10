from typing import Dict, Any, List, Optional
import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class ChatService:
    """
    LLM-powered conversational profiling service.
    
    Implements intent classification and entity extraction
    using Llama 3 (local) or GPT-4o (fallback).
    """
    
    def __init__(self):
        self.llm_provider = settings.LLM_PROVIDER
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize LLM based on provider"""
        # MVP Mode: Use keyword-based extraction (no LLM needed)
        if self.llm_provider == "mock":
            logger.info("✓ Using keyword-based extraction (MVP mode)")
            return None
        
        # Try Ollama
        if self.llm_provider == "ollama":
            try:
                from langchain_community.llms import Ollama
                llm = Ollama(
                    base_url=settings.OLLAMA_BASE_URL,
                    model=settings.LLM_MODEL,
                    temperature=settings.LLM_TEMPERATURE,
                )
                logger.info("✓ Using Ollama with Llama 3")
                return llm
            except Exception as e:
                logger.warning(f"Ollama not available: {e}. Falling back to keyword mode.")
                return None
        
        # Try OpenAI
        elif self.llm_provider == "openai" and settings.OPENAI_API_KEY:
            try:
                from langchain_community.llms import OpenAI
                llm = OpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    temperature=settings.LLM_TEMPERATURE,
                    max_tokens=settings.LLM_MAX_TOKENS,
                )
                logger.info("✓ Using OpenAI GPT")
                return llm
            except Exception as e:
                logger.warning(f"OpenAI not available: {e}. Falling back to keyword mode.")
                return None
        
        logger.info("✓ Using keyword-based extraction (fallback mode)")
        return None  # Fallback to keyword mode
    
    async def process_message(
        self,
        user_id: str,
        message: str,
        session_id: str,
        redis_client,
    ) -> Dict[str, Any]:
        """
        Process user message through LLM pipeline.
        
        Returns:
            {
                "reply": str,
                "intent": str,
                "entities": dict,
            }
        """
        # Get conversation history
        history = await self._get_history(session_id, redis_client)
        
        # Classify intent
        intent = await self._classify_intent(message, history)
        
        # Extract entities
        entities = await self._extract_entities(message, intent)
        
        # Generate response
        reply = await self._generate_response(message, intent, entities, history)
        
        # Save to history
        await self._save_to_history(session_id, message, reply, redis_client)
        
        return {
            "reply": reply,
            "intent": intent,
            "entities": entities,
        }
    
    async def _classify_intent(self, message: str, history: List) -> str:
        """
        Classify user intent using few-shot prompting.
        """
        prompt = f"""Classify the intent of this message from a job seeker:

Message: "{message}"

Intents:
- PROFILE_UPDATE: User sharing skills, experience, or personal info
- JOB_SEARCH: User looking for job opportunities
- TRAINING_INQUIRY: User asking about courses or training
- GENERAL_CHAT: Greetings or off-topic

Respond with ONLY the intent name."""
        
        if self.llm:
            try:
                intent = await self.llm.ainvoke(prompt)
                intent = intent.strip().upper()
                
                if intent in ["PROFILE_UPDATE", "JOB_SEARCH", "TRAINING_INQUIRY", "GENERAL_CHAT"]:
                    return intent
            except Exception as e:
                logger.error(f"LLM intent classification error: {e}")
        
        # Fallback: keyword matching
        message_lower = message.lower()
        if any(word in message_lower for word in ["i am", "i work", "i know", "my skill", "plumber", "electrician"]):
            return "PROFILE_UPDATE"
        elif any(word in message_lower for word in ["job", "work", "opportunity", "hiring"]):
            return "JOB_SEARCH"
        elif any(word in message_lower for word in ["learn", "course", "training", "school"]):
            return "TRAINING_INQUIRY"
        
        return "GENERAL_CHAT"
    
    async def _extract_entities(self, message: str, intent: str) -> Dict[str, Any]:
        """
        Extract structured entities from message.
        """
        if intent != "PROFILE_UPDATE":
            return {}
        
        prompt = f"""Extract skills, location, and experience from this message:

Message: "{message}"

Return JSON with:
{{
  "skills": ["skill1", "skill2"],
  "location": "location name or null",
  "experience_years": number or null
}}

Only include fields if explicitly mentioned."""
        
        if self.llm:
            try:
                response = await self.llm.ainvoke(prompt)
                # Try to parse JSON
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    entities = json.loads(json_match.group())
                    return entities
            except Exception as e:
                logger.error(f"Entity extraction error: {e}")
        
        # Fallback: Simple regex extraction
        entities = {}
        
        # Extract common skills
        skill_keywords = ["plumber", "plumbing", "electrician", "electrical", "carpenter", "mechanic", "driver", "welder", "mason"]
        found_skills = [skill for skill in skill_keywords if skill.lower() in message.lower()]
        
        if found_skills:
            entities["skills"] = [s.title() for s in found_skills]
        
        # Extract locations (basic Kenya locations)
        locations = ["nairobi", "mombasa", "kisumu", "nakuru", "eldoret", "thika", "kabete", "westlands"]
        for loc in locations:
            if loc in message.lower():
                entities["location"] = loc.title()
                break
        
        # Extract years of experience
        import re
        years_match = re.search(r'(\d+)\s*years?', message, re.IGNORECASE)
        if years_match:
            entities["experience_years"] = int(years_match.group(1))
        
        return entities
    
    async def _generate_response(
        self,
        message: str,
        intent: str,
        entities: Dict,
        history: List
    ) -> str:
        """Generate contextual response"""
        
        if intent == "PROFILE_UPDATE":
            skills_text = ", ".join(entities.get("skills", [])) if entities.get("skills") else "your skills"
            return f"Great! I've noted {skills_text}. To increase your trust score and get better job matches, consider uploading a certificate to verify your skills. Would you like to see job opportunities or find training to improve your skills?"
        
        elif intent == "JOB_SEARCH":
            return "I can help you find jobs! Based on your profile, I'll search for matching opportunities. You can also check your skill gaps to see what's in demand."
        
        elif intent == "TRAINING_INQUIRY":
            return "I can recommend government-accredited training centers near you. What skill would you like to learn or improve?"
        
        else:
            return "Hello! I'm TALANTA AI, here to help you find jobs and improve your skills. Tell me about your experience, or ask about job opportunities!"
    
    async def _get_history(self, session_id: str, redis_client) -> List:
        """Get conversation history from Redis"""
        history_key = f"chat_history:{session_id}"
        messages = await redis_client.lrange(history_key, -5, -1)  # Last 5
        
        return [json.loads(msg) for msg in messages] if messages else []
    
    async def _save_to_history(
        self,
        session_id: str,
        user_message: str,
        bot_reply: str,
        redis_client
    ):
        """Save conversation to Redis"""
        history_key = f"chat_history:{session_id}"
        
        from datetime import datetime
        entry = json.dumps({
            "timestamp": datetime.utcnow().isoformat(),
            "user": user_message,
            "bot": bot_reply,
        })
        
        await redis_client.rpush(history_key, entry)
        await redis_client.expire(history_key, 86400 * 7)  # 7 days TTL
