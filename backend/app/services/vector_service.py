from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
import numpy as np
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class VectorService:
    """
    Vector embeddings and semantic search service.
    
    Uses sentence-transformers for local, sovereign embeddings.
    """
    
    def __init__(self):
        try:
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info(f"Loaded embedding model: {settings.EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.model = None
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding vector for text.
        
        Returns:
            384-dimensional vector (for all-MiniLM-L6-v2)
        """
        if not self.model:
            # Return random vector as fallback
            return np.random.rand(settings.EMBEDDING_DIMENSION).tolist()
        
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts efficiently"""
        if not self.model:
            return [np.random.rand(settings.EMBEDDING_DIMENSION).tolist() for _ in texts]
        
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    async def find_matching_jobs(
        self,
        user_skills: List[str],
        top_k: int = 20,
        db=None,
    ) -> List[Dict[str, Any]]:
        """
        Find jobs matching user skills using semantic search.
        
        For MVP: Simple keyword matching.
        In production: Use pgvector similarity search.
        """
        from sqlalchemy import select
        from app.models.jobs import Job
        
        if not db:
            return []
        
        # For MVP: Fetch active jobs and do simple matching
        result = await db.execute(
            select(Job).where(Job.is_active == "ACTIVE").limit(100)
        )
        all_jobs = result.scalars().all()
        
        # Score jobs based on skill overlap
        scored_jobs = []
        user_skill_set = set(s.lower() for s in user_skills)
        
        for job in all_jobs:
            job_skills = set(s.lower() for s in (job.required_skills or []))
            overlap = len(user_skill_set & job_skills)
            
            if overlap > 0:
                scored_jobs.append({
                    "id": str(job.id),
                    "title": job.title,
                    "company": job.company,
                    "required_skills": job.required_skills,
                    "score": overlap,
                    "location": job.location,
                })
        
        # Sort by score
        scored_jobs.sort(key=lambda x: x["score"], reverse=True)
        
        return scored_jobs[:top_k]
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
