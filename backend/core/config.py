from pydantic_settings import BaseSettings
from typing import List, Optional
from pathlib import Path
import json


class Settings(BaseSettings):
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    # Application
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: str = '["http://localhost:8443","http://localhost:3000","http://localhost:5173","http://127.0.0.1:8443","http://127.0.0.1:5173"]'
    
    # AWS Configuration (India - ap-south-1)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "ap-south-1"
    AWS_S3_BUCKET_NAME: str = "cliniq-documents-mumbai"
    AWS_BEDROCK_MODEL_ID: str = "meta.llama3-70b-instruct-v1:0"
    
    @property
    def cors_origins_list(self) -> List[str]:
        return json.loads(self.CORS_ORIGINS)
    
    class Config:
        env_file = [
            str(Path(__file__).resolve().parent.parent / ".env"),
            ".env"
        ]
        case_sensitive = True


settings = Settings()
