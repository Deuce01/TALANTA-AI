from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from neo4j import GraphDatabase
import redis.asyncio as aioredis
import boto3
from app.config import settings

# ==================== PostgreSQL ====================

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    echo=settings.DEBUG,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Base class for SQLAlchemy models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    FastAPI dependency for database sessions.
    Usage: db: AsyncSession = Depends(get_db)
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


# ==================== Neo4j ====================

class Neo4jConnection:
    """Singleton Neo4j driver connection"""
    _driver = None
    
    @classmethod
    def get_driver(cls):
        if cls._driver is None:
            cls._driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
            )
        return cls._driver
    
    @classmethod
    def close(cls):
        if cls._driver is not None:
            cls._driver.close()
            cls._driver = None


def get_neo4j():
    """
    FastAPI dependency for Neo4j sessions.
    Usage: neo4j = Depends(get_neo4j)
    """
    driver = Neo4jConnection.get_driver()
    with driver.session() as session:
        yield session


# ==================== Redis ====================

redis_client = None


async def get_redis_client():
    """Get Redis async client"""
    global redis_client
    if redis_client is None:
        redis_client = await aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50,
        )
    return redis_client


async def get_redis():
    """
    FastAPI dependency for Redis.
    Usage: redis = Depends(get_redis)
    """
    return await get_redis_client()


# ==================== S3/MinIO ====================

def get_s3_client():
    """
    Get boto3 S3 client configured for MinIO.
    Usage: s3 = get_s3_client()
    """
    return boto3.client(
        's3',
        endpoint_url=settings.S3_ENDPOINT,
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
        region_name=settings.S3_REGION,
    )


# ==================== Initialization ====================

async def init_databases():
    """Initialize all database connections on startup"""
    # Test PostgreSQL connection
    async with engine.begin() as conn:
        await conn.execute("SELECT 1")
    
    # Test Neo4j connection
    driver = Neo4jConnection.get_driver()
    driver.verify_connectivity()
    
    # Test Redis connection
    redis = await get_redis_client()
    await redis.ping()
    
    # Create S3 bucket if not exists
    s3 = get_s3_client()
    try:
        s3.head_bucket(Bucket=settings.S3_BUCKET_NAME)
    except:
        s3.create_bucket(Bucket=settings.S3_BUCKET_NAME)
    
    print(" Database connections initialized successfully")


async def close_databases():
    """Close all database connections on shutdown"""
    await engine.dispose()
    Neo4jConnection.close()
    
    global redis_client
    if redis_client:
        await redis_client.close()
    
    print("✓ Database connections closed")
