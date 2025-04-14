from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from dotenv import load_dotenv

from src.routers.searches import router as searches_router
from src.middleware.rate_limiter import RateLimiter
from src.repositories.search_repository import SearchRepository

# Load environment variables from .env file if it exists
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize application
app = FastAPI(
    title="FashionDetector API",
    description="API for detecting clothing items from images and searching online stores",
    version="1.0.0",
    openapi_tags=[
        {"name": "searches", "description": "Operations for searching clothing items from images"}
    ]
)

# Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiter middleware
app.add_middleware(
    RateLimiter,
    anonymous_limit=int(os.getenv("ANONYMOUS_RATE_LIMIT", "10")),
    authenticated_limit=int(os.getenv("AUTHENTICATED_RATE_LIMIT", "100"))
)

# Include routers
app.include_router(searches_router, prefix="/api")

@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "name": "FashionDetector API",
        "version": "1.0.0",
        "description": "API for detecting clothing items from images and searching online stores"
    }

@app.on_event("startup")
async def startup():
    """Initialize services on application startup."""
    logger.info("Starting up FashionDetector API")
    
    # Initialize database
    repository = SearchRepository()
    await repository.initialize()
    
    # Create required directories
    os.makedirs("temp", exist_ok=True)
    os.makedirs("temp/search_states", exist_ok=True)
    
    logger.info("FashionDetector API startup complete")

@app.on_event("shutdown")
async def shutdown():
    """Clean up resources on application shutdown."""
    logger.info("Shutting down FashionDetector API")
    
    # Close database connections
    repository = SearchRepository()
    await repository.close()
    
    logger.info("FashionDetector API shutdown complete")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True) 