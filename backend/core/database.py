import json
import socket
from urllib.parse import urlparse
from supabase import create_client, Client
from .config import settings
from .mock_db import LocalDatabase


def deserialize_vector(val):
    """Safely converts serialized PostgREST pgvector string to a Python List[float]."""
    if isinstance(val, str):
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            try:
                return json.loads(val)
            except Exception:
                return [float(x.strip()) for x in val[1:-1].split(",") if x.strip()]
    return val


class VectorDeserializingRequestBuilder:
    """Wraps PostgREST query builders to automatically deserialize pgvector columns into List[float]."""

    def __init__(self, target):
        self._target = target

    def __getattr__(self, name):
        attr = getattr(self._target, name)
        if callable(attr):
            def wrapper(*args, **kwargs):
                res = attr(*args, **kwargs)
                if hasattr(res, "execute"):
                    return VectorDeserializingRequestBuilder(res)
                return res
            return wrapper
        return attr

    def execute(self):
        res = self._target.execute()
        if hasattr(res, "data") and res.data:
            if isinstance(res.data, list):
                for row in res.data:
                    if isinstance(row, dict) and "embedding" in row:
                        row["embedding"] = deserialize_vector(row["embedding"])
            elif isinstance(res.data, dict) and "embedding" in res.data:
                res.data["embedding"] = deserialize_vector(res.data["embedding"])
        return res


class SupabaseClientWrapper:
    """Proxy around Supabase Client to transparently handle pgvector deserialization for vector tables."""

    def __init__(self, client):
        self._client = client

    def table(self, table_name: str):
        builder = self._client.table(table_name)
        if table_name == "patient_record_chunks":
            return VectorDeserializingRequestBuilder(builder)
        return builder

    def from_(self, table_name: str):
        return self.table(table_name)

    def __getattr__(self, name):
        return getattr(self._client, name)


local_db = LocalDatabase()
supabase_instance = None

try:
    if settings.SUPABASE_URL and "supabase.co" in settings.SUPABASE_URL:
        host = urlparse(settings.SUPABASE_URL).netloc
        # Test if DNS resolves for the Supabase host
        socket.gethostbyname(host)
        raw_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY
        )
        supabase_instance = SupabaseClientWrapper(raw_client)
except Exception:
    supabase_instance = None

# Fallback supabase reference
supabase = supabase_instance if supabase_instance is not None else local_db


def get_db():
    """Dependency for getting database client"""
    if supabase_instance is not None:
        return supabase_instance
    return local_db

