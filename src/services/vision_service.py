import os
import logging
import base64
import asyncio
import httpx
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from contextlib import asynccontextmanager

from src.models.search import AttributeRecognition

logger = logging.getLogger(__name__)

class VisionService:
    """Service for image analysis with GPT-4 Vision API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize vision service.
        
        Args:
            api_key: OpenAI API key. If None, reads from environment variable OPENAI_API_KEY
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.api_url = "https://api.openai.com/v1/chat/completions"
        
        if not self.api_key:
            logger.warning("No OpenAI API key provided. Vision analysis will not work.")
    
    async def analyze_clothing_image(self, image_path: str) -> Tuple[List[AttributeRecognition], int]:
        """Analyze clothing image to extract attributes.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (list of recognized attributes, processing time in ms)
        """
        start_time = datetime.now()
        
        if not self.api_key:
            logger.error("Cannot analyze image: No OpenAI API key provided")
            return [], 0
        
        try:
            # Prepare image data
            if image_path.startswith("http"):
                # Image is a URL
                image_data = {"url": image_path}
            else:
                # Image is a local file
                with open(image_path, "rb") as img_file:
                    encoded_image = base64.b64encode(img_file.read()).decode('utf-8')
                    image_data = {"base64": encoded_image}
            
            # Prepare the request payload
            payload = {
                "model": "gpt-4-vision-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Analyze this clothing item and identify the following attributes: color, pattern, cut, brand (if visible). Return only JSON in this format: {\"attributes\": [{\"name\": \"color\", \"value\": \"red\", \"confidence\": 0.95}, ...]}. No additional text."
                            },
                            {
                                "type": "image",
                                "image": image_data
                            }
                        ]
                    }
                ],
                "max_tokens": 300
            }
            
            # Make the API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=headers
                )
                
                response.raise_for_status()
                response_data = response.json()
                
                # Parse the response to extract attributes
                response_text = response_data["choices"][0]["message"]["content"]
                
                # Process the JSON response (would normally use a JSON parser)
                # For this example, we'll simulate attribute extraction
                attributes = self._parse_attributes(response_text)
                
                # Calculate processing time
                processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                
                return attributes, processing_time_ms
                
        except Exception as e:
            logger.error(f"Error analyzing image: {str(e)}")
            processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            return [], processing_time_ms
    
    def _parse_attributes(self, response_text: str) -> List[AttributeRecognition]:
        """Parse attributes from API response.
        
        In a real implementation, this would properly parse the JSON response.
        Here we're simulating the response for the sake of example.
        
        Args:
            response_text: JSON text from GPT-4 Vision API
            
        Returns:
            List of AttributeRecognition objects
        """
        try:
            import json
            data = json.loads(response_text)
            
            attributes = []
            for attr in data.get("attributes", []):
                attributes.append(
                    AttributeRecognition(
                        name=attr.get("name", ""),
                        value=attr.get("value", ""),
                        confidence=attr.get("confidence", 0.0)
                    )
                )
            
            return attributes
        except Exception as e:
            logger.error(f"Error parsing attributes from response: {str(e)}")
            return [] 