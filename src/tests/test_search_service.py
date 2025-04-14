import pytest
import os
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import UploadFile

from src.services.search_service import SearchService
from src.services.vision_service import VisionService
from src.services.search_state_service import SearchStateService, SearchStatus
from src.services.scraper_service import ScraperService
from src.repositories.search_repository import SearchRepository
from src.models.search import AttributeRecognition, StoreEnum

@pytest.fixture
def mock_vision_service():
    """Create a mock vision service."""
    service = AsyncMock(spec=VisionService)
    
    # Mock analyze_clothing_image method
    service.analyze_clothing_image.return_value = (
        [
            AttributeRecognition(name="color", value="red", confidence=0.95),
            AttributeRecognition(name="pattern", value="solid", confidence=0.87),
            AttributeRecognition(name="cut", value="slim", confidence=0.78),
        ],
        1500  # Analysis time in ms
    )
    
    return service

@pytest.fixture
def mock_state_service():
    """Create a mock state service."""
    service = AsyncMock(spec=SearchStateService)
    return service

@pytest.fixture
def mock_scraper_service():
    """Create a mock scraper service."""
    service = AsyncMock(spec=ScraperService)
    
    # Mock search_store method to return empty products list
    service.search_store.return_value = []
    
    return service

@pytest.fixture
def mock_repository():
    """Create a mock repository."""
    repo = AsyncMock(spec=SearchRepository)
    
    # Mock successful database operations
    repo.save_attribute_recognition.return_value = True
    repo.save_store_search.return_value = True
    repo.save_search_metrics.return_value = True
    repo.save_attributes_batch.return_value = True
    
    return repo

@pytest.fixture
def search_service(mock_vision_service, mock_state_service, mock_scraper_service, mock_repository):
    """Create a SearchService instance with mocked dependencies."""
    return SearchService(
        s3_bucket=None,
        vision_service=mock_vision_service,
        state_service=mock_state_service,
        scraper_service=mock_scraper_service,
        repository=mock_repository
    )

@pytest.fixture
def mock_upload_file():
    """Create a mock UploadFile object."""
    file = AsyncMock(spec=UploadFile)
    file.filename = "test_image.jpg"
    file.content_type = "image/jpeg"
    
    # Mock file.read() to return some bytes
    file.read.return_value = b"mock image data"
    
    return file

class TestSearchService:
    """Test cases for SearchService."""
    
    @pytest.mark.asyncio
    async def test_validate_image_valid(self, search_service, mock_upload_file):
        """Test validate_image with valid image."""
        is_valid, error_message = await search_service.validate_image(mock_upload_file)
        
        assert is_valid is True
        assert error_message == ""
    
    @pytest.mark.asyncio
    async def test_validate_image_invalid_type(self, search_service):
        """Test validate_image with invalid image type."""
        mock_file = AsyncMock(spec=UploadFile)
        mock_file.content_type = "application/pdf"
        
        is_valid, error_message = await search_service.validate_image(mock_file)
        
        assert is_valid is False
        assert "Invalid image format" in error_message
    
    @pytest.mark.asyncio
    async def test_validate_image_too_large(self, search_service, mock_upload_file):
        """Test validate_image with image too large."""
        # Create a mock file with size > 10 MB
        mock_upload_file.read.return_value = b"X" * (11 * 1024 * 1024)
        
        is_valid, error_message = await search_service.validate_image(mock_upload_file)
        
        assert is_valid is False
        assert "Image too large" in error_message
    
    @pytest.mark.asyncio
    async def test_save_image_local(self, search_service, mock_upload_file):
        """Test save_image saving locally."""
        # Patch aiofiles.open to avoid actual file operations
        with patch("aiofiles.open", new_callable=AsyncMock) as mock_open:
            # Create mock context manager
            mock_context = AsyncMock()
            mock_open.return_value.__aenter__.return_value = mock_context
            
            # Call function
            search_id = "test-search-id"
            result = await search_service.save_image(mock_upload_file, search_id)
            
            # Verify result
            assert result == f"temp/{search_id}.jpg"
            mock_open.assert_called_once()
            mock_context.write.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_search_success(self, search_service, mock_upload_file, mock_vision_service, mock_state_service, mock_scraper_service, mock_repository):
        """Test process_search with successful processing."""
        # Setup
        search_id = "test-search-id"
        stores = [StoreEnum.ZALANDO, StoreEnum.ASOS]
        
        # Mock save_image to avoid actual file operations
        search_service.save_image = AsyncMock(return_value="temp/test_image.jpg")
        
        # Call function
        await search_service.process_search(mock_upload_file, stores, search_id)
        
        # Verify state service calls
        mock_state_service.initialize_search.assert_called_once_with(
            search_id, 
            ["zalando", "asos"]
        )
        
        # Verify vision service calls
        mock_vision_service.analyze_clothing_image.assert_called_once()
        
        # Verify scraper service calls
        assert mock_scraper_service.search_store.call_count == 2
        
        # Verify repository calls
        mock_repository.save_attributes_batch.assert_called_once()
        assert mock_repository.save_store_search.call_count == 2
        mock_repository.save_search_metrics.assert_called_once()
        
        # Verify final state update
        mock_state_service.update_search_status.assert_called_with(
            search_id,
            SearchStatus.COMPLETED
        )
    
    @pytest.mark.asyncio
    async def test_process_search_image_save_failure(self, search_service, mock_upload_file, mock_state_service):
        """Test process_search when image save fails."""
        # Setup
        search_id = "test-search-id"
        stores = [StoreEnum.ZALANDO]
        
        # Mock save_image to fail
        search_service.save_image = AsyncMock(return_value=None)
        
        # Call function
        await search_service.process_search(mock_upload_file, stores, search_id)
        
        # Verify failure handling
        mock_state_service.update_search_status.assert_called_with(
            search_id,
            SearchStatus.FAILED
        )
    
    @pytest.mark.asyncio
    async def test_generate_search_id(self, search_service):
        """Test generate_search_id generates a valid UUID."""
        search_id = search_service.generate_search_id()
        
        # Verify UUID format
        assert len(search_id) == 36
        assert search_id.count('-') == 4
    
    @pytest.mark.asyncio
    async def test_get_timestamp(self, search_service):
        """Test get_timestamp returns correct ISO format."""
        timestamp = search_service.get_timestamp()
        
        # Verify timestamp format
        assert 'T' in timestamp
        assert 'Z' in timestamp
        
        # Verify it's parseable as a datetime
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    
    @pytest.mark.asyncio
    async def test_get_search_status(self, search_service, mock_state_service):
        """Test get_search_status delegates to state service."""
        search_id = "test-search-id"
        
        await search_service.get_search_status(search_id)
        
        mock_state_service.get_search_status.assert_called_once_with(search_id) 