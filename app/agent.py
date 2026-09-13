"""
AI Interior Designer Agent
Core agent logic for the design workflow
"""

import os
import base64
import json
import logging
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

from openai import OpenAI
from dotenv import load_dotenv

from app.prompts import (
    SYSTEM_PROMPT,
    VISION_ANALYSIS_PROMPT,
    DESIGN_BRIEF_PROMPT,
    IMAGE_GENERATION_PROMPT
)
from app.image_generator import ImageGenerator

# Load environment variables
load_dotenv()

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
        self.gpt_model = os.getenv("GPT_MODEL", "gpt-4")
        self.image_generator = ImageGenerator(self.api_key)
        self.uploads_folder = Path(os.getenv("UPLOAD_FOLDER", "./uploads"))
        self.uploads_folder.mkdir(exist_ok=True)
        
        logger.info(f"Agent initialized with vision model: {self.vision_model}")
        logger.info(f"Agent initialized with GPT model: {self.gpt_model}")
    
    def analyze_room(
        self,
        image_path: str,
        room_type: str = "",
        dimensions: str = "",
        style: str = "",
        budget: str = "",
        requirements: str = ""
    ) -> Dict:
        """
        Analyze a room using GPT-4 Vision and generate a design proposal
        
        Args:
            image_path: Path to the room image
            room_type: Type of room (bedroom, living room, etc.)
            dimensions: Room dimensions if known
            style: Preferred design style
            budget: Budget range
            requirements: Special requirements
            
        Returns:
            Dictionary with analysis and design proposal
        """
        logger.info(f"Analyzing room image: {image_path}")
        
        try:
            # Verify file exists
            if not os.path.exists(image_path):
                return {
                    "success": False,
                    "error": f"Image file not found: {image_path}"
                }
            
            # Encode image to base64
            image_data = self._encode_image(image_path)
            
            # Build the prompt with user inputs
            prompt = self._build_analysis_prompt(
                room_type, dimensions, style, budget, requirements
            )
            
            logger.info("Sending request to GPT-4 Vision API...")
            
            # Call GPT-4 Vision API
            response = self.client.messages.create(
                model=self.vision_model,
                max_tokens=2000,
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_data,
                                },
                            }
                        ],
                    }
                ],
            )
            
            # Extract response
            analysis_text = response.content[0].text
            
            logger.info("Room analysis completed successfully")
            return {
                "success": True,
                "analysis": analysis_text,
                "model_used": self.vision_model,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing room: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_design_brief(
        self,
        room_analysis: str,
        room_type: str = "",
        dimensions: str = "",
        style: str = "",
        budget: str = "",
        requirements: str = ""
    ) -> Dict:
        """
        Generate a detailed design brief based on room analysis
        
        Args:
            room_analysis: Analysis from analyze_room()
            room_type: Type of room
            dimensions: Room dimensions
            style: Preferred design style
            budget: Budget range
            requirements: Special requirements
            
        Returns:
            Dictionary with design brief
        """
        logger.info("Generating design brief from analysis")
        
        try:
            # Build the design brief prompt
            prompt = f"""
Based on the following room analysis, create a comprehensive interior design brief.

ROOM ANALYSIS:
{room_analysis}

USER REQUIREMENTS:
- Room Type: {room_type or 'Not specified'}
- Dimensions: {dimensions or 'Not specified'}
- Preferred Style: {style or 'Not specified'}
- Budget: {budget or 'Not specified'}
- Requirements: {requirements or 'None specified'}

{DESIGN_BRIEF_PROMPT}
"""
            
            logger.info("Sending request to GPT-4 API for design brief...")
            
            # Call GPT-4 API
            response = self.client.messages.create(
                model=self.gpt_model,
                max_tokens=3000,
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
            )
            
            brief_text = response.content[0].text
            
            logger.info("Design brief generated successfully")
            return {
                "success": True,
                "brief": brief_text,
                "model_used": self.gpt_model,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating design brief: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_design_visualization(self, design_brief: str) -> Dict:
        """
        Generate design visualization image using DALL-E
        
        Args:
            design_brief: Design brief text
            
        Returns:
            Dictionary with generated image URL and metadata
        """
        logger.info("Generating design visualization")
        
        try:
            # Extract key information from design brief for prompt construction
            visualization_prompt = f"""
Based on this interior design brief, create a photorealistic visualization 
of the redesigned room:

{design_brief}

Use the guidelines from the IMAGE_GENERATION_PROMPT to create a professional, 
client-ready visualization.
"""
            
            # Use image generator to create visualization
            result = self.image_generator.generate_design_image_from_brief(
                visualization_prompt
            )
            
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
        room_type: str = "",
        dimensions: str = "",
        style: str = "",
        budget: str = "",
        requirements: str = ""
    ) -> Dict:
        """
        Run the complete design workflow from image to visualization
        
        Args:
            image_path: Path to room image
            room_type: Room type
            dimensions: Room dimensions
            style: Preferred design style
            budget: Budget range
            requirements: Special requirements
            
        Returns:
            Dictionary with complete workflow results
        """
        logger.info("Starting complete design workflow")
        
        workflow_results = {
            "timestamp": datetime.now().isoformat(),
            "image_path": image_path,
            "steps": {}
        }
        
        # Step 1: Analyze room
        logger.info("Step 1: Analyzing room image...")
        analysis_result = self.analyze_room(
            image_path, room_type, dimensions, style, budget, requirements
        )
        workflow_results["steps"]["analysis"] = analysis_result
        
        if not analysis_result["success"]:
            workflow_results["success"] = False
            return workflow_results
        
        # Step 2: Generate design brief
        logger.info("Step 2: Generating design brief...")
        brief_result = self.generate_design_brief(
            analysis_result["analysis"],
            room_type, dimensions, style, budget, requirements
        )
        workflow_results["steps"]["design_brief"] = brief_result
        
        if not brief_result["success"]:
            workflow_results["success"] = False
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
    
    def _build_analysis_prompt(
        self,
        room_type: str,
        dimensions: str,
        style: str,
        budget: str,
        requirements: str
    ) -> str:
        """
        Build the analysis prompt with user inputs
        
        Args:
            room_type: Type of room
            dimensions: Room dimensions
            style: Preferred design style
            budget: Budget range
            requirements: Special requirements
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""
Analyze this room photograph and create an interior design proposal.

User Information:
================
Room Type: {room_type if room_type else 'Not specified'}
Dimensions: {dimensions if dimensions else 'Not specified'}
Preferred Style: {style if style else 'Not specified'}
Budget: {budget if budget else 'Not specified'}
Requirements: {requirements if requirements else 'None specified'}

Please analyze the photograph and provide:

{VISION_ANALYSIS_PROMPT}

Then provide your initial design concept considering:
- The existing architecture and good bones of the space
- The user's stated preferences
- Budget constraints
- Practical improvements that would maximize the space
- A cohesive design direction

Preserve architectural features unless structural changes are explicitly requested.
Make recommendations that are realistic and practical to implement.
"""
        return prompt.strip()
