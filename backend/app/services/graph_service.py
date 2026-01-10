from typing import List, Dict, Any, Optional
from neo4j import Session
import logging

from app.database import Neo4jConnection

logger = logging.getLogger(__name__)


class GraphService:
    """
    Neo4j graph operations for talent-skill-job relationships.
    
    Implements the "Neural Workforce Grid" intelligence layer.
    """
    
    def __init__(self):
        self.driver = Neo4jConnection.get_driver()
    
    async def update_user_profile(self, user_id: str, entities: Dict[str, Any]):
        """
        Update user profile in Neo4j based on extracted entities.
        
        Creates/updates:
        - User node
        - Skill nodes
        - Location node
        - CLAIMS relationships
        """
        with self.driver.session() as session:
            # Create/merge user node
            session.run(
                """
                MERGE (u:User {id: $user_id})
                SET u.last_updated = datetime()
                """,
                user_id=user_id
            )
            
            # Add skills
            if "skills" in entities and entities["skills"]:
                for skill in entities["skills"]:
                    session.run(
                        """
                        MATCH (u:User {id: $user_id})
                        MERGE (s:Skill {name: $skill_name})
                        MERGE (u)-[r:CLAIMS]->(s)
                        SET r.claimed_at = datetime(),
                            r.confidence = 0.7
                        """,
                        user_id=user_id,
                        skill_name=skill.title()
                    )
                    logger.info(f"Added CLAIMS relationship: {user_id} -> {skill}")
            
            # Add location
            if "location" in entities and entities["location"]:
                session.run(
                    """
                    MATCH (u:User {id: $user_id})
                    MERGE (l:Location {name: $location_name})
                    MERGE (u)-[r:LOCATED_IN]->(l)
                    SET r.updated_at = datetime()
                    """,
                    user_id=user_id,
                    location_name=entities["location"]
                )
            
            # Add experience if available
            if "experience_years" in entities:
                session.run(
                    """
                    MATCH (u:User {id: $user_id})
                    SET u.experience_years = $years
                    """,
                    user_id=user_id,
                    years=entities["experience_years"]
                )
    
    async def get_user_skills(self, user_id: str) -> List[str]:
        """
        Get all skills (claimed + verified) for a user.
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {id: $user_id})-[:CLAIMS|VERIFIED_IN]->(s:Skill)
                RETURN DISTINCT s.name as skill
                """,
                user_id=user_id
            )
            
            skills = [record["skill"] for record in result]
            return skills
    
    async def verify_skill(self, user_id: str, skill_name: str):
        """
        Upgrade skill from CLAIMS to VERIFIED_IN relationship.
        Called after successful certificate verification.
        """
        with self.driver.session() as session:
            session.run(
                """
                MATCH (u:User {id: $user_id})-[c:CLAIMS]->(s:Skill {name: $skill_name})
                DELETE c
                CREATE (u)-[:VERIFIED_IN {verified_at: datetime(), method: 'CERTIFICATE'}]->(s)
                """,
                user_id=user_id,
                skill_name=skill_name
            )
            logger.info(f"Verified skill: {user_id} -> {skill_name}")
    
    async def get_skill_distribution(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get top skills by verified user count.
        Used for Cabinet Secretary dashboard.
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User)-[:VERIFIED_IN]->(s:Skill)
                RETURN s.name as skill, count(u) as user_count
                ORDER BY user_count DESC
                LIMIT $limit
                """,
                limit=limit
            )
            
            return [
                {"skill": record["skill"], "count": record["user_count"]}
                for record in result
            ]
    
    async def find_skill_holders(
        self,
        skill_name: str,
        verified_only: bool = False
    ) -> List[str]:
        """
        Find all users with a specific skill.
        """
        relationship = "VERIFIED_IN" if verified_only else "CLAIMS|VERIFIED_IN"
        
        with self.driver.session() as session:
            result = session.run(
                f"""
                MATCH (u:User)-[:{relationship}]->(s:Skill {{name: $skill_name}})
                RETURN u.id as user_id
                """,
                skill_name=skill_name
            )
            
            return [record["user_id"] for record in result]
    
    async def init_skills_taxonomy(self):
        """
        Initialize skill taxonomy and prerequisites.
        Should be run once during setup.
        """
        with self.driver.session() as session:
            # Create common skills
            skills = [
                {"name": "Plumbing", "category": "Construction", "complexity": 2},
                {"name": "Electrical Wiring", "category": "Construction", "complexity": 3},
                {"name": "Solar Installation", "category": "Renewable Energy", "complexity": 3},
                {"name": "Carpentry", "category": "Construction", "complexity": 2},
                {"name": "Masonry", "category": "Construction", "complexity": 2},
                {"name": "Welding", "category": "Manufacturing", "complexity": 3},
                {"name": "Automotive Repair", "category": "Automotive", "complexity": 3},
                {"name": "Driving", "category": "Transport", "complexity": 1},
                {"name": "Hairdressing", "category": "Beauty", "complexity": 1},
                {"name": "Tailoring", "category": "Fashion", "complexity": 2},
            ]
            
            for skill in skills:
                session.run(
                    """
                    MERGE (s:Skill {name: $name})
                    SET s.category = $category,
                        s.complexity = $complexity
                    """,
                    **skill
                )
            
            # Create prerequisite relationships
            prerequisites = [
                ("Electrical Wiring", "Solar Installation"),
                ("Driving", "Automotive Repair"),
            ]
            
            for prereq, advanced in prerequisites:
                session.run(
                    """
                    MATCH (s1:Skill {name: $prereq})
                    MATCH (s2:Skill {name: $advanced})
                    MERGE (s1)-[:PREREQUISITE_FOR]->(s2)
                    """,
                    prereq=prereq,
                    advanced=advanced
                )
            
            logger.info("✓ Skills taxonomy initialized")
