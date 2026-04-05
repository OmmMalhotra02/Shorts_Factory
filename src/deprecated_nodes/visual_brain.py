from state import ShortsState
from pydantic import BaseModel, Field, AliasChoices
from typing import List, Literal, Optional
import os
import json
from langchain_openai import ChatOpenAI

class Frame(BaseModel):
    # Model often uses 'prompt' instead of 'description'
    description: str = Field(validation_alias=AliasChoices('description', 'prompt'))
    order: int

class Objects(BaseModel):
    type: str
    role: str
    color: str
    size: str
    position: str

class Motion(BaseModel):
    type: str
    intensity: str
    direction: str

class Style(BaseModel):
    type: str
    background: str
    color_palette: List[str]
    no_realism: bool
    no_textures: bool

class Scene(BaseModel):
    id: int = Field(validation_alias=AliasChoices('id', 'scene_number'))
    # Catching 'purpose' vs 'goal'
    goal: str = Field(validation_alias=AliasChoices('goal', 'purpose'))
    # Make these optional so a "lazy" model doesn't crash the whole pipeline
    objects: List[Objects] = Field(default_factory=list)
    animation: str = Field(default="none")
    duration: float = Field(validation_alias=AliasChoices('duration', 'duration_seconds'))
    # Motion is the biggest fail point; we default it if missing
    motion: Motion
    frames: List[Frame]
    script_part: Optional[str] = None

class Visual_Plan(BaseModel):
    style: Style
    concept: str
    scenes: List[Scene]

# Eg Visual Plan - 
# {
#   "style": {
#     "type": "minimal_flat_animation",
#     "background": "dark_space",
#     "color_palette": ["yellow", "blue", "white"],
#     "no_realism": true,
#     "no_textures": true
#   },
#   "concept": "Rayleigh scattering causes blue sky",
#   "scenes": [
#     {
#       "id": 1,
#       "goal": "show sunlight reaching earth",
#       "objects": [
#         {"type": "circle", "role": "sun", "color": "yellow"},
#         {"type": "circle", "role": "earth", "color": "blue_green"},
#         {"type": "lines", "role": "sunlight", "color": "white"}
#       ],
#       "animation": "parallel_rays_move_towards_earth",
#       "duration": 3
#     },
#     {
#       "id": 2,
#       "goal": "show atmosphere interaction",
#       "objects": [
#         {"type": "layer", "role": "atmosphere", "color": "light_blue"},
#         {"type": "particles", "role": "gas_molecules"}
#       ],
#       "animation": "light_rays_enter_and_hit_particles",
#       "duration": 4
#     },
#     {
#       "id": 3,
#       "goal": "show scattering",
#       "objects": [
#         {"type": "rays", "role": "light"},
#         {"type": "particles"}
#       ],
#       "animation": "short_wavelength_rays_scatter_in_all_directions",
#       "focus_color": "blue",
#       "duration": 5
#     },
#     {
#       "id": 4,
#       "goal": "final visual outcome",
#       "objects": [
#         {"type": "sky_gradient", "color": "blue"}
#       ],
#       "animation": "sky_fills_with_blue_color",
#       "duration": 3
#     }
#   ]
# }

# class Visual_Plan(BaseModel):
#     style: Style = Field(description="Describes the type of animation, background, color palette, realism and texture")
#     concept: str = Field(description="Main concept behind the video")
#     scenes: List[Scene] = Field(description="Different scenes making the complete video. Each scene contains goal, objects, animations of objects, frames with description and the duration of scene.")

llm = ChatOpenAI(
    model="arcee-ai/trinity-mini:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_KEY")
)

llm_struct_output = llm.with_structured_output(Visual_Plan, method="json_mode")

def visual_brain_1(state: ShortsState):
    script = state['script']
    prompt = f"""
            ROLE:
            You are a visual learning designer who creates simple, clear, animated educational visuals for students (age 8-18).

            GOAL:
            Convert the given script into a structured visual plan for a short educational video.

            SCRIPT:
            {script}

            STYLE RULES:
            - Use minimal flat animation style
            - Use simple shapes (circle, lines, arrows, particles)
            - No real-world imagery
            - No humans, no faces
            - No complex textures
            - Background should be simple (space, gradient, plain)

            SCENE RULES:
            - Each scene must have ONE clear teaching purpose
            - Keep scenes visually simple and focused
            - Each scene must include 2-3 frames showing progression
            - Motion must be simple (zoom, pan, fade)
            - Total video duration should be between 20-40 seconds
            - Each scene duration: 3-6 seconds

            FRAME RULES:
            - Each frame description must be directly usable as an image generation prompt
            - Each frame description must describe EXACTLY what is visible: "A white photon particle traveling in a straight line, then curving around a large black circle representing a black hole, on dark background" NOT "light bending around gravity"
            - Be explicit about:
            - objects
            - colors
            - positions
            - relationships (e.g., rays hitting particles, arrows showing direction)
            - Avoid vague words like "beautiful", "realistic", "cinematic"

            OUTPUT RULES:
            - Strictly follow the JSON schema.
            - The root of your JSON must contain the keys "style", "concept", and "scenes".
            - DO NOT wrap the entire response in a "video_plan" or any output key.
            - Do not add extra text.
            - Inside "style": must be an OBJECT with keys "type", "background", "color_palette", "no_realism", "no_textures".
            - Inside "scenes": each object must use key "id" (NOT "scene_number") and "duration" (NOT "duration_seconds").
            - Inside "frames": each object must have "order" (integer).
            - Strictly follow the Pydantic schema types.
        """

    visual_plan = llm_struct_output.invoke(prompt)
    if len(visual_plan.scenes) == 0:
        raise ValueError("No scenes generated")

    return {'visual_plan': visual_plan}

def visual_brain(state: ShortsState):
    script = state['script']
    
    # We pass the actual JSON schema to the LLM so it sees the field names
    schema_dump = json.dumps(Visual_Plan.model_json_schema(), indent=2)

    llm = ChatOpenAI(
        model="arcee-ai/trinity-large-preview:free",
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_KEY"),
        temperature=0.1 # Lower temperature = better schema adherence
    )
    
    # Using json_mode for reliability with OpenRouter
    llm_struct_output = llm.with_structured_output(Visual_Plan, method="json_mode")

    prompt = f"""
    ROLE: Visual learning designer for students.
    GOAL: Convert script to a structured visual plan.
    
    SCRIPT: {script}

    STRICT SCHEMA REQUIREMENT:
    Your output must match this JSON schema:
    {schema_dump}

    CRITICAL INSTRUCTIONS:
    1. "scenes" MUST contain "goal", "objects", "animation", and "motion".
    2. "motion" MUST be an object with "type", "intensity", and "direction".
    3. Do NOT use names like "purpose" or "scene_number" in your final JSON.
    4. Return ONLY the JSON.
    """

    visual_plan = llm_struct_output.invoke(prompt)
    
    if not visual_plan or len(visual_plan.scenes) == 0:
        raise ValueError("No scenes generated")

    return {'visual_plan': visual_plan}