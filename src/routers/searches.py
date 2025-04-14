from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Depends, Path
from typing import List, Optional
from datetime import datetime, timezone
import logging

from src.models.search import StoreEnum, SearchResponse, SearchStatusResponse
from src.services.search_service import SearchService
from src.services.search_state_service import SearchStateService
from src.repositories.search_repository import SearchRepository

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/searches", tags=["searches"])

# Setup service dependencies
async def get_search_service():
    """Dependency injection for search service."""
    # Initialize repository
    repository = SearchRepository()
    await repository.initialize()
    
    # In production, pass actual S3 bucket name
    return SearchService(
        s3_bucket=None,  # None for local development
        repository=repository
    )

@router.post("/", response_model=SearchResponse, status_code=202)
async def create_search(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(...),
    stores: Optional[List[StoreEnum]] = Form(None),
    search_service: SearchService = Depends(get_search_service)
):
    """Initiate a clothing search from an uploaded image.
    
    Args:
        background_tasks: FastAPI background tasks manager
        image: Image file of the clothing to search for (JPEG/PNG)
        stores: Optional list of stores to search in, defaults to all supported stores
        search_service: Injected search service
        
    Returns:
        Search information including the search ID and status
        
    Raises:
        400: Invalid image format or size
        413: Image too large
        429: Rate limit exceeded
        500: Server error
    """
    # Log search request
    client_host = "client_ip_would_be_extracted_from_request"
    logger.info(f"Search request received from {client_host}")
    
    # Validate image
    is_valid, error_message = await search_service.validate_image(image)
    if not is_valid:
        logger.warning(f"Invalid image from {client_host}: {error_message}")
        raise HTTPException(
            status_code=400,
            detail=error_message
        )
    
    # Generate search ID
    search_id = search_service.generate_search_id()
    
    # Use all stores if none specified
    if not stores:
        stores = list(StoreEnum)
    
    # Log stores being searched
    logger.info(f"Search {search_id} initiated for stores: {[store.value for store in stores]}")
    
    # Add task to background
    background_tasks.add_task(
        search_service.process_search,
        image,
        stores,
        search_id
    )
    
    # Return response
    timestamp = search_service.get_timestamp()
    
    return SearchResponse(
        search_id=search_id,
        status="processing",
        estimated_time_seconds=10,
        timestamp=timestamp
    )

@router.get("/{search_id}", response_model=SearchStatusResponse)
async def get_search_status(
    search_id: str = Path(..., title="Search ID", description="Unique identifier for the search"),
    search_service: SearchService = Depends(get_search_service)
):
    """Get the status of a previously initiated search.
    
    Args:
        search_id: Unique identifier for the search
        search_service: Injected search service
        
    Returns:
        Current status of the search
        
    Raises:
        404: Search not found
        500: Server error
    """
    # Get search status
    status = await search_service.get_search_status(search_id)
    
    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Search with ID {search_id} not found"
        )
    
    return status 