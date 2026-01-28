import os
from supabase import create_client, Client
from src.logger import get_logger

logger = get_logger(__name__)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Supabase client singleton
_supabase_client: Client | None = None


def get_supabase() -> Client:
    """Get Supabase client instance"""
    global _supabase_client

    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY environment variables must be set"
            )

        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized")

    return _supabase_client


def init_db():
    """Initialize and verify database connection"""
    logger.info("Verifying Supabase connection...")

    try:
        supabase = get_supabase()
        # Test connection by querying recipes table
        supabase.table("recipes").select("id", count="exact").limit(1).execute()
        logger.info("Supabase connection verified successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {str(e)}")
        raise
