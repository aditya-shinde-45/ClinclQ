from supabase import create_client, Client
from .config import settings
from .mock_db import LocalDatabase
import socket
from urllib.parse import urlparse

local_db = LocalDatabase()
supabase_instance = None

try:
    if settings.SUPABASE_URL and "supabase.co" in settings.SUPABASE_URL:
        host = urlparse(settings.SUPABASE_URL).netloc
        # Test if DNS resolves for the Supabase host
        socket.gethostbyname(host)
        supabase_instance = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )
except Exception:
    supabase_instance = None

# Fallback supabase reference
supabase = supabase_instance if supabase_instance is not None else local_db

def get_db():
    """Dependency for getting database client"""
    if supabase_instance is not None:
        return supabase_instance
    return local_db

