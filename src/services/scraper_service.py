import asyncio
import logging
import os
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import tempfile
import subprocess

from src.models.search import Product, ProductAttribute, ProductAlternative

logger = logging.getLogger(__name__)

class ScraperService:
    """Service for web scraping online fashion stores."""
    
    def __init__(self, scrapy_project_path: Optional[str] = None):
        """Initialize scraper service.
        
        Args:
            scrapy_project_path: Path to Scrapy project
        """
        self.scrapy_project_path = scrapy_project_path or os.path.join(os.getcwd(), 'src', 'scrapers')
        
        # Create scrapers directory if it doesn't exist
        os.makedirs(self.scrapy_project_path, exist_ok=True)
    
    async def search_store(
        self, 
        store: str, 
        attributes: Dict[str, Any],
        search_id: str
    ) -> List[Product]:
        """Search for clothing in a specific store.
        
        Args:
            store: Name of the store to search in
            attributes: Recognized clothing attributes
            search_id: Unique identifier for the search
            
        Returns:
            List of found products
        """
        logger.info(f"Searching store {store} for search {search_id}")
        
        # In a real implementation, this would invoke Scrapy spiders
        # For now, we'll simulate the search results
        await asyncio.sleep(2)  # Simulate network delay
        
        return self._simulate_search_results(store, attributes)
    
    async def search_multiple_stores(
        self, 
        stores: List[str], 
        attributes: Dict[str, Any],
        search_id: str
    ) -> Dict[str, List[Product]]:
        """Search for clothing in multiple stores.
        
        Args:
            stores: List of stores to search in
            attributes: Recognized clothing attributes
            search_id: Unique identifier for the search
            
        Returns:
            Dictionary mapping store names to lists of found products
        """
        logger.info(f"Searching multiple stores ({', '.join(stores)}) for search {search_id}")
        
        tasks = []
        for store in stores:
            tasks.append(self.search_store(store, attributes, search_id))
            
        # Run searches in parallel
        results = await asyncio.gather(*tasks)
        
        return {store: result for store, result in zip(stores, results)}
    
    def _simulate_search_results(self, store: str, attributes: Dict[str, Any]) -> List[Product]:
        """Simulate search results for a store.
        
        In a real implementation, this would be the result of Scrapy scraping.
        
        Args:
            store: Name of the store
            attributes: Recognized clothing attributes
            
        Returns:
            List of simulated products
        """
        # Extract key attributes
        color = next((attr.value for attr in attributes if attr.name == "color"), "unknown")
        pattern = next((attr.value for attr in attributes if attr.name == "pattern"), "solid")
        cut = next((attr.value for attr in attributes if attr.name == "cut"), "regular")
        brand = next((attr.value for attr in attributes if attr.name == "brand"), None)
        
        # Generate simulated products
        products = []
        
        # Number of results based on store
        result_count = {
            "zalando": 3,
            "modivo": 2,
            "asos": 4
        }.get(store, 1)
        
        for i in range(result_count):
            similarity = 0.95 - (i * 0.05)  # Decrease similarity for each result
            
            product_attr = ProductAttribute(
                color=color,
                pattern=pattern,
                cut=cut,
                brand=brand
            )
            
            # Generate some alternative colors
            alternatives = []
            alt_colors = ["blue", "black", "white"] if color != "blue" else ["red", "green", "black"]
            
            for alt_color in alt_colors[:2]:
                alternatives.append(
                    ProductAlternative(
                        color=alt_color,
                        url=f"https://{store}.example.com/product{i}/color/{alt_color}"
                    )
                )
            
            product = Product(
                title=f"{brand or 'Brand'} {color} {pattern} {cut} shirt",
                store=store,
                url=f"https://{store}.example.com/product{i}",
                similarity_score=similarity,
                attributes=product_attr,
                alternatives=alternatives
            )
            
            products.append(product)
        
        return products
    
    def _build_scrapy_command(
        self, 
        store: str, 
        attributes: Dict[str, Any],
        output_file: str
    ) -> List[str]:
        """Build Scrapy command for a specific store.
        
        Args:
            store: Name of the store to search in
            attributes: Recognized clothing attributes
            output_file: Path to output file for scraped data
            
        Returns:
            Scrapy command as list of string arguments
        """
        # Convert attributes to a JSON string for command line
        attributes_json = json.dumps(attributes)
        
        # Build command
        command = [
            "scrapy", "crawl", f"{store}_spider",
            "-a", f"attributes={attributes_json}",
            "-o", output_file
        ]
        
        return command
    
    async def _run_scrapy_spider(self, command: List[str]) -> bool:
        """Run a Scrapy spider as a subprocess.
        
        Args:
            command: Scrapy command as list of string arguments
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Change to Scrapy project directory
            cwd = os.getcwd()
            os.chdir(self.scrapy_project_path)
            
            # Run Scrapy command
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for completion in a separate thread
            loop = asyncio.get_event_loop()
            stdout, stderr = await loop.run_in_executor(
                None, process.communicate
            )
            
            # Change back to original directory
            os.chdir(cwd)
            
            # Check for errors
            if process.returncode != 0:
                logger.error(f"Scrapy error: {stderr.decode()}")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error running Scrapy spider: {str(e)}")
            # Change back to original directory if exception occurs
            os.chdir(cwd)
            return False 