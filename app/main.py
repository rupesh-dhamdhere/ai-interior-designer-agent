"""
Main FastAPI Application
API endpoints for the AI Interior Designer Agent
"""

import os
import logging
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from dotenv import load_dotenv

from app.agent import InteriorDesignerAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Interior Designer Agent",
    description="AI-powered interior design service using vision analysis and generative models",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent
try:
    agent = InteriorDesignerAgent()
    logger.info("Interior Designer Agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize agent: {str(e)}")
    agent = None


@app.get("/")
async def root():
    """Root endpoint - Welcome message"""
    return {
        "message": "Welcome to AI Interior Designer Agent",
        "version": "0.1.0",
        "status": "running" if agent else "initialization failed"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy" if agent else "unhealthy",
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }


@app.post("/upload-room-photo")
async def upload_room_photo(file: UploadFile = File(...)):
    """
    Upload a room photo for analysis
    
    Args:
        file: Room image file
        
    Returns:
        Success status and file information
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Validate file type
        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed. Allowed types: {allowed_types}"
            )
        
        # Save uploaded file
        uploads_folder = Path(os.getenv("UPLOAD_FOLDER", "./uploads"))
        uploads_folder.mkdir(exist_ok=True)
        
        file_path = uploads_folder / file.filename
        contents = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(contents)
        
        logger.info(f"File uploaded successfully: {file.filename}")
        
        return {
            "success": True,
            "filename": file.filename,
            "filepath": str(file_path),
            "file_size": len(contents),
            "message": "Room photo uploaded successfully"
        }
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@app.post("/analyze-room")
async def analyze_room(
    image_path: str = Form(...),
    style_preference: str = Form(...),
    budget: str = Form(...),
    requirements: str = Form(...)
):
    """
    Run complete design workflow: analyze room and generate design
    
    Args:
        image_path: Path to uploaded room image
        style_preference: User's preferred design style
        budget: Budget range for renovation
        requirements: Special requirements and preferences
        
    Returns:
        Complete workflow results with analysis, brief, and visualization
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Verify file exists
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="Image file not found")
        
        # Run complete workflow
        logger.info(f"Starting workflow for image: {image_path}")
        results = agent.run_complete_workflow(
            image_path=image_path,
            style_preference=style_preference,
            budget=budget,
            requirements=requirements
        )
        
        return JSONResponse(content=results)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing room: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error analyzing room: {str(e)}")


@app.post("/generate-analysis")
async def generate_analysis(image_path: str = Form(...)):
    """
    Step 1 only: Analyze room image
    
    Args:
        image_path: Path to room image
        
    Returns:
        Room analysis results
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        if not os.path.exists(image_path):
            raise HTTPException(status_code=404, detail="Image file not found")
        
        results = agent.analyze_room_image(image_path)
        return JSONResponse(content=results)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/generate-brief")
async def generate_brief(
    room_analysis: str = Form(...),
    style_preference: str = Form(...),
    budget: str = Form(...),
    requirements: str = Form(...)
):
    """
    Step 2 only: Generate design brief
    
    Args:
        room_analysis: JSON string of room analysis
        style_preference: User's preferred design style
        budget: Budget range
        requirements: Special requirements
        
    Returns:
        Design brief results
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        import json
        analysis = json.loads(room_analysis)
        
        results = agent.generate_design_brief(
            analysis, style_preference, budget, requirements
        )
        return JSONResponse(content=results)
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in room_analysis")
    except Exception as e:
        logger.error(f"Error generating brief: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.post("/generate-visualization")
async def generate_visualization(design_brief: str = Form(...)):
    """
    Step 3 only: Generate design visualization
    
    Args:
        design_brief: JSON string of design brief
        
    Returns:
        Generated visualization with image URL
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        import json
        brief = json.loads(design_brief)
        
        results = agent.generate_design_visualization(brief)
        return JSONResponse(content=results)
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in design_brief")
    except Exception as e:
        logger.error(f"Error generating visualization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@app.get("/api/status")
async def api_status():
    """Get current API status and configuration"""
    return {
        "service": "AI Interior Designer Agent",
        "status": "running",
        "api_version": "0.1.0",
        "vision_model": os.getenv("VISION_MODEL", "gpt-4-vision-preview"),
        "image_gen_model": os.getenv("IMAGE_GEN_MODEL", "dall-e-3"),
        "uploads_folder": os.getenv("UPLOAD_FOLDER", "./uploads"),
        "generated_folder": os.getenv("GENERATED_FOLDER", "./generated")
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Starting server on port {port}")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("APP_ENV") == "development"
    )
