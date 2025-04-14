import logging
import os
from typing import List, Dict, Optional, Any
from datetime import datetime
import asyncpg
from asyncpg.pool import Pool

from src.models.search import AttributeRecognition, StoreEnum

logger = logging.getLogger(__name__)

class SearchRepository:
    """Repository for database operations related to searches."""
    
    def __init__(self):
        """Initialize search repository."""
        self.pool = None
        self.db_config = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", "postgres"),
            "database": os.getenv("DB_NAME", "fashiondetector")
        }
    
    async def initialize(self) -> None:
        """Initialize database connection pool."""
        try:
            self.pool = await asyncpg.create_pool(**self.db_config)
            logger.info("Database connection pool initialized")
        except Exception as e:
            logger.error(f"Error initializing database connection pool: {str(e)}")
            # In development mode, we can continue without a database
            logger.warning("Running without database connection")
    
    async def close(self) -> None:
        """Close database connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")
    
    async def save_attribute_recognition(
        self, 
        attribute_name: str, 
        attribute_value: str, 
        search_time_ms: int
    ) -> bool:
        """Save recognized attribute to database.
        
        Args:
            attribute_name: Name of the attribute (color, pattern, cut, brand)
            attribute_value: Value of the recognized attribute
            search_time_ms: Time taken to process in milliseconds
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not self.pool:
            logger.warning("Cannot save attribute recognition: No database connection")
            return False
        
        try:
            async with self.pool.acquire() as conn:
                # Check if attribute exists
                exists = await conn.fetchval(
                    """
                    SELECT id FROM attribute_recognitions 
                    WHERE attribute_name = $1 AND attribute_value = $2
                    """,
                    attribute_name, attribute_value
                )
                
                if exists:
                    # Update counter
                    await conn.execute(
                        """
                        UPDATE attribute_recognitions 
                        SET counter = counter + 1,
                            search_time_ms = (search_time_ms + $3) / 2
                        WHERE id = $1
                        """,
                        exists, search_time_ms
                    )
                else:
                    # Insert new record
                    await conn.execute(
                        """
                        INSERT INTO attribute_recognitions 
                        (attribute_name, attribute_value, counter, search_time_ms)
                        VALUES ($1, $2, 1, $3)
                        """,
                        attribute_name, attribute_value, search_time_ms
                    )
                
                return True
        except Exception as e:
            logger.error(f"Error saving attribute recognition: {str(e)}")
            return False
    
    async def save_store_search(
        self, 
        store_name: str, 
        search_performed: bool, 
        response_time_ms: Optional[int] = None
    ) -> bool:
        """Save store search record to database.
        
        Args:
            store_name: Name of the store that was searched
            search_performed: Whether the search was successfully performed
            response_time_ms: Response time in milliseconds
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not self.pool:
            logger.warning("Cannot save store search: No database connection")
            return False
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO store_searches 
                    (store_name, search_performed, response_time_ms)
                    VALUES ($1, $2, $3)
                    """,
                    store_name, search_performed, response_time_ms
                )
                
                return True
        except Exception as e:
            logger.error(f"Error saving store search: {str(e)}")
            return False
    
    async def save_search_metrics(
        self, 
        total_time_ms: int, 
        analysis_time_ms: Optional[int] = None,
        search_time_ms: Optional[int] = None,
        result_count: int = 0
    ) -> bool:
        """Save search metrics to database.
        
        Args:
            total_time_ms: Total search time in milliseconds
            analysis_time_ms: Time taken for image analysis
            search_time_ms: Time taken for store searching
            result_count: Number of results found
            
        Returns:
            True if saved successfully, False otherwise
        """
        if not self.pool:
            logger.warning("Cannot save search metrics: No database connection")
            return False
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO search_metrics 
                    (total_time_ms, analysis_time_ms, search_time_ms, result_count)
                    VALUES ($1, $2, $3, $4)
                    """,
                    total_time_ms, analysis_time_ms, search_time_ms, result_count
                )
                
                return True
        except Exception as e:
            logger.error(f"Error saving search metrics: {str(e)}")
            return False
    
    async def save_attributes_batch(self, attributes: List[AttributeRecognition], analysis_time_ms: int) -> bool:
        """Save multiple recognized attributes in a batch.
        
        Args:
            attributes: List of recognized attributes
            analysis_time_ms: Time taken for attribute analysis
            
        Returns:
            True if all saved successfully, False otherwise
        """
        if not attributes:
            return True
            
        if not self.pool:
            logger.warning("Cannot save attributes batch: No database connection")
            return False
            
        try:
            async with self.pool.acquire() as conn:
                async with conn.transaction():
                    for attr in attributes:
                        # Divide analysis time evenly among attributes
                        attr_time = analysis_time_ms // len(attributes)
                        
                        await self.save_attribute_recognition(
                            attr.name, 
                            attr.value, 
                            attr_time
                        )
                        
                return True
        except Exception as e:
            logger.error(f"Error saving attributes batch: {str(e)}")
            return False 