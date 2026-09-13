"""
Prompts for the AI Interior Designer Agent
"""

# Vision Analysis Prompt - Analyze uploaded room photo
VISION_ANALYSIS_PROMPT = """
Analyze this room image and provide a detailed assessment in JSON format with the following:

1. room_type: Type of room (bedroom, living room, kitchen, etc.)
2. current_style: Current design style observed
3. dimensions_estimate: Estimated room dimensions based on visual cues
4. current_furniture: List of furniture items visible
5. current_colors: Primary and secondary colors used
6. lighting_assessment: Current lighting situation
7. space_issues: Any spatial or design issues identified
8. improvement_areas: Key areas that need improvement

Be specific and detailed in your analysis.
"""

# Design Agent Prompt - Generate design brief
DESIGN_BRIEF_PROMPT = """
Based on the room analysis and user requirements, create a comprehensive interior design brief.

Input:
- Room Analysis: {room_analysis}
- User Style Preference: {style_preference}
- Budget Range: {budget}
- Special Requirements: {requirements}

Generate a detailed design brief that includes:

1. Design Concept: Overall design concept and theme
2. Color Palette: Recommended colors with hex codes
3. Furniture Layout: Suggested furniture arrangement
4. Furniture Recommendations: Specific furniture pieces with approximate costs
5. Accessories: Decorative items and accessories
6. Lighting Plan: Lighting recommendations
7. Materials & Finishes: Recommended materials
8. Timeline & Budget Breakdown: Implementation timeline and cost estimates

Provide the response in a structured format that can be used for image generation.
"""

# Image Generation Prompt - Create visualization
IMAGE_GENERATION_PROMPT = """
Create a photorealistic interior design visualization for:

Room Type: {room_type}
Style: {design_style}
Color Scheme: {color_palette}
Key Features: {key_features}
Layout: {furniture_layout}

Generate a high-quality, realistic image showing the complete redesigned room with:
- All recommended furniture
- Proper lighting and shadows
- Accurate color scheme
- Professional interior design aesthetics
- Clear visibility of the space and layout

The image should be suitable for client presentation and show the transformation clearly.
"""

# Design Questions Prompt - Gather requirements
DESIGN_REQUIREMENTS_PROMPT = """
Ask the user these questions to gather interior design requirements:

1. What is your preferred design style? (Modern, Minimalist, Traditional, Industrial, Bohemian, etc.)
2. What is your budget range for this redesign?
3. Do you have any specific furniture pieces you want to keep?
4. Are there any specific functional requirements? (Storage, workspace, entertainment area, etc.)
5. Do you prefer natural light or artificial lighting?
6. Any color preferences or colors to avoid?
7. Are there any space constraints or limitations?
8. What is the primary purpose of this room?

Compile responses into structured requirements for the design agent.
"""
