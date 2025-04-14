from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
from datetime import datetime

class StoreEnum(str, Enum):
    """Enumeration of supported online stores for fashion searching."""
    ZALANDO = "zalando"
    MODIVO = "modivo"
    ASOS = "asos"

class SearchResponse(BaseModel):
    """Response model for the initiate search endpoint."""
    search_id: str
    status: str = "processing"
    estimated_time_seconds: int = 10
    timestamp: str

    class Config:
        json_schema_extra = {
            "example": {
                "search_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "processing",
                "estimated_time_seconds": 10,
                "timestamp": "2023-04-14T19:22:37Z"
            }
        }

class StoreSearchStatus(BaseModel):
    """Status of search in a specific store."""
    name: str
    status: str  # completed, processing, failed
    time_ms: int

class AttributeRecognition(BaseModel):
    """Recognized attribute from image analysis."""
    name: str
    value: str
    confidence: float

class SearchStatusResponse(BaseModel):
    """Response model for the search status endpoint."""
    search_id: str
    status: str  # processing, completed, failed
    elapsed_time_ms: int
    stores_searched: List[StoreSearchStatus]
    attributes_recognized: List[AttributeRecognition]
    result_count: int
    timestamp: str

class ProductAttribute(BaseModel):
    """Attributes of a found product."""
    color: Optional[str] = None
    pattern: Optional[str] = None
    cut: Optional[str] = None
    brand: Optional[str] = None

class ProductAlternative(BaseModel):
    """Alternative version of a found product."""
    color: str
    url: str

class Product(BaseModel):
    """Model representing a found product."""
    title: str
    store: str
    url: str
    similarity_score: float
    attributes: ProductAttribute
    alternatives: List[ProductAlternative] = []

class SearchResultsResponse(BaseModel):
    """Response model for the search results endpoint."""
    search_id: str
    products: List[Product]
    total_results_found: int
    total_time_ms: int 