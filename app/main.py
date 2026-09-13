"""
Main FastAPI Application
AI Interior Designer API with simplified endpoints
"""

import os
import logging
import uuid
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.agent import InteriorDesignerAgent
from app.image_generator import ImageGenerator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Interior Designer",
    description="AI-powered interior design using GPT-4 Vision and DALL-E",
    version="1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup directories
UPLOAD_DIR = Path(os.getenv("UPLOAD_FOLDER", "./uploads"))
GENERATED_DIR = Path(os.getenv("GENERATED_FOLDER", "./generated"))

UPLOAD_DIR.mkdir(exist_ok=True)
GENERATED_DIR.mkdir(exist_ok=True)

# Initialize agent
try:
    agent = InteriorDesignerAgent()
    image_generator = ImageGenerator(os.getenv("OPENAI_API_KEY"))
    logger.info("AI Interior Designer Agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize agent: {str(e)}")
    agent = None
    image_generator = None


@app.get("/")
def home():
    """
    Welcome endpoint
    """
    return {
        "name": "AI Interior Designer",
        "version": "1.0",
        "status": "running" if agent else "initialization failed",
        "docs": "Visit /docs for API documentation"
    }


@app.get("/health")
def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy" if agent else "unhealthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/status")
def api_status():
    """
    Get current API status and configuration
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return {
        "service": "AI Interior Designer",
        "status": "running",
        "version": "1.0",
        "vision_model": os.getenv("VISION_MODEL", "gpt-4-vision-preview"),
        "image_gen_model": os.getenv("IMAGE_GEN_MODEL", "dall-e-3"),
        "uploads_folder": str(UPLOAD_DIR),
        "generated_folder": str(GENERATED_DIR)
    }


@app.post("/design")
async def create_design(
    room_photo: UploadFile = File(...),
    room_type: str = Form("bedroom"),
    dimensions: str = Form("unknown"),
    style: str = Form("modern"),
    budget: str = Form("unknown"),
    requirements: str = Form("")
):
    """
    Create an interior design proposal from a room photo.
    
    This endpoint performs the complete design workflow:
    1. Analyzes the room photo using GPT-4 Vision
    2. Generates a comprehensive design brief
    3. Creates a photorealistic visualization with DALL-E
    
    Args:
        room_photo: Room image file (JPEG, PNG, or WebP)
        room_type: Type of room (bedroom, living room, kitchen, etc.)
        dimensions: Room dimensions if known (e.g., "15x20 feet")
        style: Preferred design style (modern, minimalist, traditional, etc.)
        budget: Budget range (e.g., "$5000-$10000")
        requirements: Special requirements or preferences
    
    Returns:
        Dictionary with:
        - success: Boolean indicating success
        - analysis: Room analysis from GPT-4 Vision
        - generated_image: Path to generated design image
        - timestamp: Creation timestamp
    """
    
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Validate file type
        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        if room_photo.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: JPEG, PNG, WebP"
            )
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        extension = Path(room_photo.filename).suffix
        
        # Save uploaded file
        image_path = UPLOAD_DIR / f"{file_id}{extension}"
        
        logger.info(f"Processing room photo: {file_id}{extension}")
        
        file_contents = await room_photo.read()
        with open(image_path, "wb") as buffer:
            buffer.write(file_contents)
        
        logger.info(f"File saved to: {image_path}")
        
        # Step 1: Analyze room
        logger.info("Step 1: Analyzing room with GPT-4 Vision...")
        analysis_result = agent.analyze_room(
            image_path=str(image_path),
            room_type=room_type,
            dimensions=dimensions,
            style=style,
            budget=budget,
            requirements=requirements
        )
        
        if not analysis_result["success"]:
            raise Exception(f"Room analysis failed: {analysis_result.get('error', 'Unknown error')}")
        
        analysis = analysis_result["analysis"]
        logger.info("Room analysis completed")
        
        # Step 2: Generate design brief
        logger.info("Step 2: Generating design brief...")
        brief_result = agent.generate_design_brief(
            room_analysis=analysis,
            room_type=room_type,
            dimensions=dimensions,
            style=style,
            budget=budget,
            requirements=requirements
        )
        
        if not brief_result["success"]:
            raise Exception(f"Design brief generation failed: {brief_result.get('error', 'Unknown error')}")
        
        design_brief = brief_result["brief"]
        logger.info("Design brief generated")
        
        # Step 3: Generate visualization
        logger.info("Step 3: Generating design visualization with DALL-E...")
        
        # Create a refined prompt for DALL-E
        design_prompt = f"""
Create a photorealistic interior design visualization based on this professional design brief.

IMPORTANT DIRECTIVES:
- Preserve the underlying room architecture, proportions, doors and windows
- Do not invent impossible structural changes
- Show realistic furniture, materials, lighting, textures, and proportions
- Maintain realistic architectural details
- Result should look like a professional interior-design visualization

DESIGN BRIEF:
{design_brief}

Create a realistic finished interior that demonstrates the design transformation.
"""
        
        output_path = GENERATED_DIR / f"{file_id}.png"
        
        # Use image generator to create visualization
        image_result = image_generator.generate_design_image_from_prompt(
            prompt=design_prompt,
            output_path=str(output_path)
        )
        
        if not image_result["success"]:
            raise Exception(f"Visualization generation failed: {image_result.get('error', 'Unknown error')}")
        
        logger.info(f"Design visualization generated: {output_path}")
        
        # Return success response
        return {
            "success": True,
            "file_id": file_id,
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "design_brief": design_brief,
            "generated_image": str(output_path),
            "image_url": image_result.get("image_url"),
            "message": "Design created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating design: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error creating design: {str(e)}"
        )


@app.get("/download/{file_id}")
async def download_image(file_id: str):
    """
    Download a generated design image
    
    Args:
        file_id: The file ID from the design creation
    
    Returns:
        Generated design image file
    """
    
    try:
        # Find the file (could be .png, .jpg, etc.)
        image_files = list(GENERATED_DIR.glob(f"{file_id}.*"))
        
        if not image_files:
            raise HTTPException(
                status_code=404,
                detail=f"Generated image not found: {file_id}"
            )
        
        image_path = image_files[0]
        
        return FileResponse(
            path=image_path,
            media_type="image/png",
            filename=f"design_{file_id}.png"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading image: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error downloading image: {str(e)}"
        )


@app.post("/upload")
async def upload_photo(file: UploadFile = File(...)):
    """
    Upload a room photo for later processing
    
    Args:
        file: Room image file
    
    Returns:
        File information and upload path
    """
    
    try:
        # Validate file type
        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: JPEG, PNG, WebP"
            )
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        extension = Path(file.filename).suffix
        
        # Save file
        file_path = UPLOAD_DIR / f"{file_id}{extension}"
        contents = await file.read()
        
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
        
        logger.info(f"Photo uploaded: {file_id}{extension}")
        
        return {
            "success": True,
            "file_id": file_id,
            "filename": file.filename,
            "file_path": str(file_path),
            "file_size": len(contents),
            "message": "Photo uploaded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading photo: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading photo: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting AI Interior Designer on port {port}")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("APP_ENV") == "development"
    )
