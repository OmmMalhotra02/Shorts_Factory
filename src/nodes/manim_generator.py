import os
import subprocess
import sys
from pathlib import Path
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

# Initialize LLM
llm = ChatOpenAI(
    model="qwen/qwen3.6-plus:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_KEY")
)

# -----------------------------
# Helper functions
# -----------------------------
def generate_manim_code(topic: str, script: str, genre: str, scene_text) -> str:
    prompt = f"""
    You are an expert Manim animator creating a vertical YouTube Shorts animation.

    TOPIC: {topic}

    SCENE PLAN:
    {scene_text}

    GOAL:
    Convert the scene plan into a clean, smooth, visually engaging animation suitable for Math, Physics, and Chemistry topics.

    SUBJECT-SPECIFIC RULES:
    - Math:
        * Use MathTex for equations and formulas
        * Dynamic graphs: use ValueTracker + always_redraw + TracedPath
        * Highlight terms using color (BLUE = key, RED/ORANGE = motion)
    - Physics:
        * Use Arrow, Line, Dot to represent vectors, forces, trajectories
        * Show motion, collisions, circuits, pulleys as animated primitives
        * Equations like F=ma, v=dx/dt displayed with MathTex
    - Chemistry:
        * Atoms = Dot, Bonds = Line, Reaction arrows = Arrow
        * Animate reaction steps: moving electrons, bond formation/breaking
        * Simple molecules: use Circle+Line groups; complex molecules can be abstracted
        * Chemical equations = MathTex

    STRICT RULES:
    - from manim import *
    - Class: ConceptScene(Scene)
    - Background: WHITE
    - Text color: BLACK
    - Vertical format:
        self.camera.frame_width = 9
        self.camera.frame_height = 16
    - Use only valid arguments (avoid stroke_type or unsupported kwargs)
    - Reuse objects across scenes when possible

    ADDITIONAL FIX RULES:
    - Colors must ONLY be Manim constants: WHITE, BLACK, BLUE, RED, GREEN, ORANGE, YELLOW, GRAY
    - Never pass hex strings or float values as colors
    - Wrong: color=0.5 or color="#FF0000"
    - Correct: color=RED or color=BLUE

    ALLOWED OBJECTS:
    Text, Circle, Arrow, VGroup, Rectangle, Line, Dot, MathTex

    STYLE:
    - Title at top (font_size=48)
    - Explanation text at bottom (font_size>=36)
    - Visuals in center
    - Avoid overlap

    ANIMATION FLOW:
    For each scene:
    1. FadeOut previous text
    2. Show new text
    3. Animate the visual described
    4. Use smooth transitions (Transform/ReplacementTransform preferred over fade)

    DYNAMIC VISUALS:
    - always_redraw() for moving elements
    - TracedPath for graphs and moving points
    - Keep animations flowing, not step-by-step static
    - Reuse objects instead of recreating

    VISUAL RULES:
    - Simple but meaningful visuals
    - Each visual directly represents the scene meaning
    - No icons, no complex graphics
    - Use color meaningfully: BLUE = key terms, RED/ORANGE = motion/actions

    MATH RULE:
    - x-coordinate → cosine
    - y-coordinate → sine

    TIMING:
    - Use self.wait(2-3 seconds) per step
    - Total duration ~45-60 seconds

    IMPORTANT:
    - Never show multiple text blocks together
    - Keep visuals visible while explaining
    - Avoid unnecessary clutter

    OUTPUT:
    Return ONLY Python code. No explanation.
    """
    resp = llm.invoke(prompt)
    return resp.content

def clean_code(code: str) -> str:
    code = code.strip()
    if code.startswith("```"):
        code = code.split("```")[1]
        if code.startswith("python"):
            code = code[6:]
    if "```" in code:
        code = code.split("```")[0]
    return code.strip()

def manim_generator(state) -> dict:
    topic = state['topic']
    script = state['script']
    genre = state['genre']
    scene_plan = state['scene_plan']

    scene_text = "\n".join([
        f"Scene {i+1}:\nText: {s['text']}\nVisual: {s['visual']}"
        for i, s in enumerate(scene_plan)
    ])

    output_dir = Path("outputs/manim")
    output_dir.mkdir(parents=True, exist_ok=True)
    code_file = output_dir / "concept_scene.py"

    code = generate_manim_code(topic, script, genre, scene_text)
    code = clean_code(code)
    print("Generated Manim code preview:\n", code[:500], "...")  # first 500 chars

    max_attempts = 3
    last_error = ""

    for attempt in range(max_attempts):
        if attempt > 0:
            print(f"Attempt {attempt + 1} — asking LLM to fix error...")
            fix_prompt = f"""
            You are a senior Python + Manim debugger.

            Fix the code based on the error.

            ERROR:
            {last_error}

            CODE:
            {code}

            RULES:
            - Fix ONLY the error, do not change structure unnecessarily
            - Ensure valid Manim syntax
            - Scene must render without crash
            Return ONLY corrected code.
            """
            code = clean_code(llm.invoke(fix_prompt).content)

        with open(code_file, "w", encoding="utf-8") as f:
            f.write(code)

        result = subprocess.run([
            sys.executable, "-m", "manim",
            "-ql",
            "--format=mp4",
            "-o", "concept_output",
            "--media_dir", str(output_dir / "media"),
            str(code_file.resolve()),
            "ConceptScene"
        ], capture_output=True, text=True)

        print(f"Return code: {result.returncode}")
        print(f"Last 500 chars stdout: {result.stdout[-500:]}")
        print(f"Searching from: {Path('.').resolve()}")

        if result.returncode == 0:
            break

        last_error = result.stderr[-800:]
        print(f"Attempt {attempt + 1} failed:\n{last_error}")
    else:
        raise Exception(f"Manim failed after {max_attempts} attempts:\n{last_error}")

    # Find the rendered video
    rendered = list((output_dir / "media").rglob("concept_output.mp4"))
    if not rendered:
        rendered = list(Path(".").rglob("ConceptScene.mp4"))

    if not rendered:
        raise Exception("Manim output video not found")

    video_path = str(rendered[0])
    print(f"Manim rendered video: {video_path}")

    return {"rendered_clips": [video_path]}