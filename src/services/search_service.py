import uuid
import logging
from fastapi import UploadFile
from typing import List, Optional, Tuple, Dict, Any
import aiofiles
import os
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

from src.models.search import StoreEnum, AttributeRecognition
from src.services.vision_service import VisionService
from src.services.search_state_service import SearchStateService, SearchStatus
from src.services.scraper_service import ScraperService
from src.repositories.search_repository import SearchRepository

logger = logging.getLogger(__name__)

class SearchService:
    """Service for handling clothing search operations."""
    
    def __init__(self, 
                s3_bucket: str = None, 
                vision_service: Optional[VisionService] = None,
                state_service: Optional[SearchStateService] = None,
                scraper_service: Optional[ScraperService] = None,
                repository: Optional[SearchRepository] = None):
        """Initialize search service.
        
        Args:
            s3_bucket: Name of S3 bucket for storing images
            vision_service: Service for image analysis
            state_service: Service for managing search state
            scraper_service: Service for web scraping
            repository: Repository for database operations
        """
        self.s3_bucket = s3_bucket
        if s3_bucket:
            self.s3_client = boto3.client('s3')
        
        # Create temp directory if it doesn't exist
        os.makedirs("temp", exist_ok=True)
        
        # Initialize dependent services
        self.vision_service = vision_service or VisionService()
        self.state_service = state_service or SearchStateService()
        self.scraper_service = scraper_service or ScraperService()
        self.repository = repository or SearchRepository()
    
    async def validate_image(self, image: UploadFile) -> Tuple[bool, str]:
        """Validate uploaded image file.
        
        Args:
            image: The uploaded image file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check MIME type
        valid_types = ["image/jpeg", "image/png"]
        if image.content_type not in valid_types:
            return False, "Invalid image format. Only JPEG/PNG accepted."
        
        # Check file size (max 10MB)
        try:
            await image.seek(0)
            content = await image.read()
            size_in_mb = len(content) / (1024 * 1024)
            
            await image.seek(0)  # Reset file position for later use
            
            if size_in_mb > 10:
                return False, "Image too large. Maximum size is 10 MB."
            
            return True, ""
        except Exception as e:
            logger.error(f"Error validating image: {str(e)}")
            return False, "Error processing image file."
    
    async def save_image(self, image: UploadFile, search_id: str) -> Optional[str]:
        """Save uploaded image to storage.
        
        Args:
            image: The uploaded image file
            search_id: Unique identifier for the search
            
        Returns:
            URL to the saved image or None if failed
        """
        try:
            # Determine file extension from content type
            ext = "jpg" if image.content_type == "image/jpeg" else "png"
            filename = f"{search_id}.{ext}"
            
            if self.s3_bucket:
                # Save to S3
                await image.seek(0)
                try:
                    self.s3_client.upload_fileobj(
                        image.file, 
                        self.s3_bucket, 
                        f"uploads/{filename}"
                    )
                    return f"https://{self.s3_bucket}.s3.amazonaws.com/uploads/{filename}"
                except ClientError as e:
                    logger.error(f"Error uploading to S3: {str(e)}")
                    return None
            else:
                # Save locally for development
                local_path = f"temp/{filename}"
                await image.seek(0)
                async with aiofiles.open(local_path, 'wb') as out_file:
                    content = await image.read()
                    await out_file.write(content)
                return local_path
                
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}")
            return None
    
    async def process_search(self, image: UploadFile, stores: List[StoreEnum], search_id: str) -> None:
        """Process a clothing search request.
        
        This is a background task that:
        1. Saves the image
        2. Analyzes the image to extract attributes
        3. Initiates searches in the specified stores
        4. Records metrics in the database
        
        Args:
            image: The uploaded image file
            stores: List of stores to search in
            search_id: Unique identifier for the search
        """
        start_time = datetime.now()
        
        try:
            # Initialize search state
            store_names = [store.value for store in stores]
            await self.state_service.initialize_search(search_id, store_names)
            
            # Save the image
            image_url = await self.save_image(image, search_id)
            if not image_url:
                logger.error(f"Failed to save image for search {search_id}")
                await self.state_service.update_search_status(search_id, SearchStatus.FAILED)
                return
            
            # Analyze image with AI model
            attributes, analysis_time_ms = await self.vision_service.analyze_clothing_image(image_url)
            
            # Update search state with recognized attributes
            await self.state_service.update_attributes(search_id, attributes)
            
            # Save attributes to database
            if self.repository:
                await self.repository.save_attributes_batch(attributes, analysis_time_ms)
            
            # Convert attributes to dictionary format for scrapers
            attributes_dict = {attr.name: attr.value for attr in attributes}
            
            # Start store searches in parallel
            start_search_time = datetime.now()
            
            # Search in all stores
            store_results = {}
            total_results = 0
            
            for store in stores:
                store_name = store.value
                
                try:
                    # Update store status to processing
                    await self.state_service.update_store_status(
                        search_id,
                        store_name,
                        SearchStatus.PROCESSING
                    )
                    
                    # Search in store
                    products = await self.scraper_service.search_store(
                        store_name,
                        attributes,
                        search_id
                    )
                    
                    # Store results
                    store_results[store_name] = products
                    total_results += len(products)
                    
                    # Calculate store search time
                    store_search_time_ms = int(
                        (datetime.now() - start_search_time).total_seconds() * 1000
                    )
                    
                    # Update store status to completed
                    await self.state_service.update_store_status(
                        search_id,
                        store_name,
                        SearchStatus.COMPLETED,
                        store_search_time_ms
                    )
                    
                    # Save store search to database
                    if self.repository:
                        await self.repository.save_store_search(
                            store_name,
                            True,  # search_performed
                            store_search_time_ms
                        )
                        
                except Exception as e:
                    logger.error(f"Error searching in store {store_name}: {str(e)}")
                    
                    # Update store status to failed
                    await self.state_service.update_store_status(
                        search_id,
                        store_name,
                        SearchStatus.FAILED
                    )
                    
                    # Save failed store search to database
                    if self.repository:
                        await self.repository.save_store_search(
                            store_name,
                            False,  # search_performed
                            None    # response_time_ms
                        )
            
            # Calculate search time
            search_time_ms = int(
                (datetime.now() - start_search_time).total_seconds() * 1000
            )
            
            # Update result count
            await self.state_service.update_result_count(search_id, total_results)
            
            # Mark search as completed
            await self.state_service.update_search_status(search_id, SearchStatus.COMPLETED)
            
            # Save search metrics to database
            if self.repository:
                total_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                await self.repository.save_search_metrics(
                    total_time_ms=total_time_ms,
                    analysis_time_ms=analysis_time_ms,
                    search_time_ms=search_time_ms,
                    result_count=total_results
                )
            
        except Exception as e:
            logger.error(f"Error processing search {search_id}: {str(e)}")
            await self.state_service.update_search_status(search_id, SearchStatus.FAILED)
    
    def generate_search_id(self) -> str:
        """Generate a unique search identifier.
        
        Returns:
            Unique search ID as string
        """
        return str(uuid.uuid4())
    
    def get_timestamp(self) -> str:
        """Get current timestamp in ISO format.
        
        Returns:
            Current time as ISO-formatted string
        """
        return datetime.now(timezone.utc).isoformat()
    
    async def get_search_status(self, search_id: str):
        """Get current status of a search.
        
        Args:
            search_id: Unique identifier for the search
            
        Returns:
            Search status response
        """
        return await self.state_service.get_search_status(search_id) 