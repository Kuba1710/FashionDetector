import logging
import asyncio
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import json
import os

from src.models.search import StoreSearchStatus, AttributeRecognition, SearchStatusResponse

logger = logging.getLogger(__name__)

class SearchStatus(str, Enum):
    """Enumeration of search statuses."""
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class SearchStateService:
    """Service for managing the state of search operations."""
    
    def __init__(self, state_dir: str = "temp/search_states"):
        """Initialize search state service.
        
        Args:
            state_dir: Directory for storing search state files
        """
        self.state_dir = state_dir
        os.makedirs(state_dir, exist_ok=True)
    
    async def initialize_search(self, search_id: str, stores: List[str]) -> None:
        """Initialize a new search state.
        
        Args:
            search_id: Unique identifier for the search
            stores: List of stores to search in
        """
        stores_state = [
            {"name": store, "status": SearchStatus.PROCESSING.value, "time_ms": 0}
            for store in stores
        ]
        
        state = {
            "search_id": search_id,
            "status": SearchStatus.PROCESSING.value,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "elapsed_time_ms": 0,
            "stores_searched": stores_state,
            "attributes_recognized": [],
            "result_count": 0
        }
        
        await self._save_state(search_id, state)
        logger.info(f"Initialized state for search {search_id}")
    
    async def update_search_status(self, search_id: str, status: SearchStatus) -> None:
        """Update the overall status of a search.
        
        Args:
            search_id: Unique identifier for the search
            status: New search status
        """
        state = await self._load_state(search_id)
        if not state:
            logger.error(f"Cannot update status for search {search_id}: State not found")
            return
        
        state["status"] = status.value
        
        if status == SearchStatus.COMPLETED or status == SearchStatus.FAILED:
            state["end_time"] = datetime.now().isoformat()
            # Calculate elapsed time
            start_time = datetime.fromisoformat(state["start_time"])
            end_time = datetime.fromisoformat(state["end_time"])
            state["elapsed_time_ms"] = int((end_time - start_time).total_seconds() * 1000)
            
        await self._save_state(search_id, state)
        logger.info(f"Updated status for search {search_id} to {status.value}")
    
    async def update_store_status(self, search_id: str, store: str, status: SearchStatus, time_ms: int = 0) -> None:
        """Update the status of a store search.
        
        Args:
            search_id: Unique identifier for the search
            store: Name of the store
            status: New search status
            time_ms: Time taken for the store search in milliseconds
        """
        state = await self._load_state(search_id)
        if not state:
            logger.error(f"Cannot update store status for search {search_id}: State not found")
            return
        
        for store_state in state["stores_searched"]:
            if store_state["name"] == store:
                store_state["status"] = status.value
                store_state["time_ms"] = time_ms
                break
        
        await self._save_state(search_id, state)
        logger.info(f"Updated status for store {store} in search {search_id} to {status.value}")
    
    async def update_attributes(self, search_id: str, attributes: List[AttributeRecognition]) -> None:
        """Update the recognized attributes for a search.
        
        Args:
            search_id: Unique identifier for the search
            attributes: List of recognized attributes
        """
        state = await self._load_state(search_id)
        if not state:
            logger.error(f"Cannot update attributes for search {search_id}: State not found")
            return
        
        state["attributes_recognized"] = [attr.dict() for attr in attributes]
        
        await self._save_state(search_id, state)
        logger.info(f"Updated attributes for search {search_id}: {len(attributes)} attributes")
    
    async def update_result_count(self, search_id: str, count: int) -> None:
        """Update the number of results found for a search.
        
        Args:
            search_id: Unique identifier for the search
            count: Number of results found
        """
        state = await self._load_state(search_id)
        if not state:
            logger.error(f"Cannot update result count for search {search_id}: State not found")
            return
        
        state["result_count"] = count
        
        await self._save_state(search_id, state)
        logger.info(f"Updated result count for search {search_id}: {count} results")
    
    async def get_search_status(self, search_id: str) -> Optional[SearchStatusResponse]:
        """Get the current status of a search.
        
        Args:
            search_id: Unique identifier for the search
            
        Returns:
            Current search status or None if not found
        """
        state = await self._load_state(search_id)
        if not state:
            logger.error(f"Cannot get status for search {search_id}: State not found")
            return None
        
        # Convert to response model
        stores_searched = [
            StoreSearchStatus(
                name=store["name"],
                status=store["status"],
                time_ms=store["time_ms"]
            )
            for store in state["stores_searched"]
        ]
        
        attributes_recognized = [
            AttributeRecognition(
                name=attr["name"],
                value=attr["value"],
                confidence=attr["confidence"]
            )
            for attr in state["attributes_recognized"]
        ]
        
        return SearchStatusResponse(
            search_id=state["search_id"],
            status=state["status"],
            elapsed_time_ms=state["elapsed_time_ms"],
            stores_searched=stores_searched,
            attributes_recognized=attributes_recognized,
            result_count=state["result_count"],
            timestamp=datetime.now().isoformat()
        )
    
    async def _save_state(self, search_id: str, state: Dict[str, Any]) -> None:
        """Save search state to file.
        
        Args:
            search_id: Unique identifier for the search
            state: Search state data
        """
        filepath = os.path.join(self.state_dir, f"{search_id}.json")
        try:
            async with asyncio.Lock():
                with open(filepath, "w") as f:
                    json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving state for search {search_id}: {str(e)}")
    
    async def _load_state(self, search_id: str) -> Optional[Dict[str, Any]]:
        """Load search state from file.
        
        Args:
            search_id: Unique identifier for the search
            
        Returns:
            Search state data or None if not found
        """
        filepath = os.path.join(self.state_dir, f"{search_id}.json")
        try:
            if not os.path.exists(filepath):
                return None
                
            async with asyncio.Lock():
                with open(filepath, "r") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading state for search {search_id}: {str(e)}")
            return None 