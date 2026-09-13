"""
AI Interior Designer Agent
Core agent logic for the design workflow
"""

import os
import base64
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from openai import OpenAI
from app.prompts import (
    VISION_ANALYSIS_PROMPT,
    DESIGN_BRIEF_PROMPT,
    IMAGE_GENERATION_PROMPT,
    DESIGN_REQUIREMENTS_PROMPT
)
from app.image_generator import ImageGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InteriorDesignerAgent:
    """
    AI Interior Designer Agent
    Orchestrates the complete design workflow from image analysis to visualization
    """
    
    def __init__(self):
        """Initialize the agent with OpenAI client"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=self.api_key)
        self.vision_model = os.getenv("VISION_MODEL", "gpt-4-vision-preview")
        self.image_generator = ImageGenerator(self.api_key)
        self.uploads_folder = Path(os.getenv("UPLOAD_FOLDER", "./uploads"))
        self.uploads_folder.mkdir(exist_ok=True)
        
    def analyze_room_image(self, image_path: str) -> Dict:
        """
        Step 1: Analyze uploaded room photo using GPT-4 Vision
        
        Args:
            image_path: Path to the uploaded room image
            
        Returns:
            Dictionary with room analysis
        """
        logger.info(f"Analyzing room image: {image_path}")
        
        try:
            # Encode image to base64
            image_data = self._encode_image(image_path)
            
            # Call GPT-4 Vision API
            response = self.client.messages.create(
                model="gpt-4-vision-preview",
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": VISION_ANALYSIS_PROMPT
                            }
                        ],
                    }
                ],
            )
            
            # Parse response
            analysis_text = response.content[0].text
            analysis = self._parse_json_response(analysis_text)
            
            logger.info("Room analysis completed successfully")
            return {
                "success": True,
                "analysis": analysis,
                "raw_response": analysis_text
            }
            
        except Exception as e:
            logger.error(f"Error analyzing room image: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_design_brief(
        self,
        room_analysis: Dict,
        style_preference: str,
        budget: str,
        requirements: str
    ) -> Dict:
        """
        Step 2: Generate design brief based on analysis and requirements
        
        Args:
            room_analysis: Analysis from Step 1
            style_preference: User's preferred design style
            budget: Budget range
            requirements: Special requirements
            
        Returns:
            Dictionary with design brief
        """
        logger.info("Generating design brief")
        
        try:
            # Format the prompt with provided data
            prompt = DESIGN_BRIEF_PROMPT.format(
                room_analysis=json.dumps(room_analysis, indent=2),
                style_preference=style_preference,
                budget=budget,
                requirements=requirements
            )
            
            # Call GPT API
            response = self.client.messages.create(
                model="gpt-4",
                max_tokens=3000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )
            
            brief_text = response.content[0].text
            brief = self._parse_json_response(brief_text)
            
            logger.info("Design brief generated successfully")
            return {
                "success": True,
                "brief": brief,
                "raw_response": brief_text
            }
            
        except Exception as e:
            logger.error(f"Error generating design brief: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_design_visualization(self, design_brief: Dict) -> Dict:
        """
        Step 3: Generate design visualization image using DALL-E
        
        Args:
            design_brief: Design brief from Step 2
            
        Returns:
            Dictionary with generated image URL and metadata
        """
        logger.info("Generating design visualization")
        
        try:
            result = self.image_generator.generate_design_image(design_brief)
            
            if result["success"]:
                logger.info("Design visualization generated successfully")
                return result
            else:
                logger.error(f"Error generating visualization: {result['error']}")
                return result
                
        except Exception as e:
            logger.error(f"Error in generate_design_visualization: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def run_complete_workflow(
        self,
        image_path: str,
        style_preference: str,
        budget: str,
        requirements: str
    ) -> Dict:
        """
        Run the complete design workflow from image to visualization
        
        Args:
            image_path: Path to room image
            style_preference: User's design style preference
            budget: Budget range
            requirements: Special requirements
            
        Returns:
            Dictionary with complete workflow results
        """
        logger.info("Starting complete design workflow")
        
        workflow_results = {
            "timestamp": datetime.now().isoformat(),
            "steps": {}
        }
        
        # Step 1: Analyze room
        logger.info("Step 1: Analyzing room image...")
        analysis_result = self.analyze_room_image(image_path)
        workflow_results["steps"]["analysis"] = analysis_result
        
        if not analysis_result["success"]:
            return workflow_results
        
        # Step 2: Generate design brief
        logger.info("Step 2: Generating design brief...")
        brief_result = self.generate_design_brief(
            analysis_result["analysis"],
            style_preference,
            budget,
            requirements
        )
        workflow_results["steps"]["design_brief"] = brief_result
        
        if not brief_result["success"]:
            return workflow_results
        
        # Step 3: Generate visualization
        logger.info("Step 3: Generating visualization...")
        visualization_result = self.generate_design_visualization(
            brief_result["brief"]
        )
        workflow_results["steps"]["visualization"] = visualization_result
        
        workflow_results["success"] = visualization_result["success"]
        logger.info("Workflow completed")
        
        return workflow_results
    
    def _encode_image(self, image_path: str) -> str:
        """
        Encode image to base64 for API
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded image string
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _parse_json_response(self, response_text: str) -> Dict:
        """
        Parse JSON from LLM response
        
        Args:
            response_text: Raw response from LLM
            
        Returns:
            Parsed dictionary or original text if parsing fails
        """
        try:
            # Try to extract JSON from response
            import json as json_module
            # Look for JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json_module.loads(json_str)
            else:
                # Return as structured dict if no JSON found
                return {"content": response_text}
        except Exception as e:
            logger.warning(f"Could not parse JSON response: {str(e)}")
            return {"content": response_text}
