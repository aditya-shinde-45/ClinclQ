from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from routers import auth, patients, appointments, analyses, documents, admin

app = FastAPI(
    title="ClinIQ API",
    description="Clinical decision support system API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(appointments.router)
app.include_router(analyses.router)
app.include_router(documents.router)
app.include_router(admin.router)


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "ClinIQ API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with AWS S3, Bedrock and Embeddings operational status"""
    from services.s3_service import s3_service
    from services.bedrock_service import bedrock_service
    from services.embedding_service import embedding_service
    
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "aws": {
            "region": settings.AWS_REGION,
            "s3": {
                "configured": s3_service.is_configured,
                "bucket": s3_service.bucket
            },
            "bedrock": {
                "configured": bedrock_service.is_configured,
                "model_id": bedrock_service.model_id
            },
            "embeddings": {
                "configured": embedding_service.is_configured,
                "model_id": embedding_service.model_id,
                "dimension": embedding_service.dimension
            }
        }
    }


@app.get("/aws/status")
async def aws_status():
    """Dedicated AWS infrastructure status endpoint"""
    from services.s3_service import s3_service
    from services.bedrock_service import bedrock_service
    from services.embedding_service import embedding_service

    return {
        "region": settings.AWS_REGION,
        "s3": {
            "status": "operational" if s3_service.is_configured and s3_service.s3_client else "offline",
            "bucket": s3_service.bucket,
            "encryption": "AES256"
        },
        "bedrock": {
            "status": "operational" if bedrock_service.is_configured and bedrock_service.bedrock_client else "offline",
            "model_id": bedrock_service.model_id,
            "provider": "Meta Llama 3"
        },
        "embeddings": {
            "status": "operational" if embedding_service.is_configured and embedding_service.client else "offline",
            "model_id": embedding_service.model_id,
            "dimension": embedding_service.dimension,
            "provider": "Amazon Titan Embeddings v2"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
