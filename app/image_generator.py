"""
Image Generation Module
Handles creation of interior design visualizations using DALL-E
"""

import os
import requests
import json
from datetime import datetime
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageGenerator:
    """Generate interior design images using OpenAI's DALL-E"""

    def __init__(self, api_key: str = None):
        """
        Initialize the ImageGenerator
        
        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env variable)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("IMAGE_GEN_MODEL", "dall-e-3")
        self.generated_folder = Path(os.getenv("GENERATED_FOLDER", "./generated"))
        self.generated_folder.mkdir(exist_ok=True)
        
    def generate_design_image(self, design_brief: dict) -> dict:
        """
        Generate an interior design image based on design brief
        
        Args:
            design_brief: Dictionary containing design specifications
            
        Returns:
            Dictionary with image URL and metadata
        """
        try:
            # Construct the prompt from design brief
            prompt = self._construct_prompt(design_brief)
            
            logger.info(f"Generating image with prompt: {prompt[:100]}...")
            
            # Call DALL-E API
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "n": 1,
                    "size": "1024x1024",
                    "quality": "hd",
                }
            )
            
            if response.status_code != 200:
                logger.error(f"DALL-E API error: {response.text}")
                return {
                    "success": False,
                    "error": response.json().get("error", {}).get("message", "Unknown error")
                }
            
            response_data = response.json()
            image_url = response_data["data"][0]["url"]
            
            # Save image metadata
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "model": self.model,
                "prompt": prompt,
                "image_url": image_url,
                "design_brief": design_brief
            }
            
            # Save metadata locally
            self._save_metadata(metadata)
            
            logger.info("Image generated successfully")
            return {
                "success": True,
                "image_url": image_url,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _construct_prompt(self, design_brief: dict) -> str:
        """
        Construct a detailed prompt for DALL-E from design brief
        
        Args:
            design_brief: Design specifications
            
        Returns:
            Detailed prompt string
        """
        room_type = design_brief.get("room_type", "living room")
        style = design_brief.get("design_style", "modern")
        colors = design_brief.get("color_palette", "neutral tones")
        furniture = design_brief.get("furniture_recommendations", "contemporary furniture")
        lighting = design_brief.get("lighting", "natural and ambient lighting")
        
        prompt = f"""
        Create a photorealistic, high-quality interior design visualization for a {room_type}.
        
        Design Style: {style}
        Color Palette: {colors}
        Furniture: {furniture}
        Lighting: {lighting}
        
        The image should show:
        - A beautifully designed {room_type} with {style} aesthetic
        - Professional interior design with attention to detail
        - Proper lighting that highlights the space
        - All furniture items arranged in a functional and aesthetically pleasing way
        - The complete room layout visible
        - Realistic materials and textures
        - Professional photography quality
        
        Make this suitable for a client presentation showing the complete room transformation.
        """
        
        return prompt.strip()
    
    def _save_metadata(self, metadata: dict) -> None:
        """
        Save image generation metadata locally
        
        Args:
            metadata: Metadata dictionary to save
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            metadata_file = self.generated_folder / f"metadata_{timestamp}.json"
            
            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Metadata saved to {metadata_file}")
        except Exception as e:
            logger.error(f"Error saving metadata: {str(e)}")
    
    def download_image(self, image_url: str, filename: str = None) -> str:
        """
        Download generated image and save locally
        
        Args:
            image_url: URL of the generated image
            filename: Optional filename (defaults to timestamp)
            
        Returns:
            Path to saved image
        """
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"design_{timestamp}.png"
            
            filepath = self.generated_folder / filename
            
            response = requests.get(image_url)
            if response.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(response.content)
                logger.info(f"Image saved to {filepath}")
                return str(filepath)
            else:
                logger.error(f"Failed to download image: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading image: {str(e)}")
            return None
