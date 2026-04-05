from state import ShortsState
from dotenv import load_dotenv
import os
from pathlib import Path
from .visual_brain import Visual_Plan
from huggingface_hub import InferenceClient
import io

load_dotenv()

HF_API_KEY = os.getenv("HUGGINGFACEHUB_API_TOKEN")

client = InferenceClient(
    provider="hf-inference",
    api_key=HF_API_KEY,
)

def image_prompt(frame_desc: str, style):
    return f"""
        Vertical format 9:16 aspect ratio.
        Minimal flat vector illustration, educational diagram style.

        Scene description:
        {frame_desc}

        Style:
        - {style.type}
        - background: {style.background}
        - colors: {", ".join(style.color_palette)}

        Rules:
        - no realism
        - no humans
        - no faces
        - clean vector shapes
        - simple geometry
        - no textures
        """

# HuggingFace image generator
def generate_image(prompt: str):
    try:
        image = client.text_to_image(
            prompt,
            model="black-forest-labs/FLUX.1-schnell",
        )
        # convert PIL image to bytes
        img_bytes = io.BytesIO()
        image.save(img_bytes, format="PNG")
        return img_bytes.getvalue()
        
    except Exception as e:
        print(f"❌ HF Exception: {e}")
        return None


def image_generator(state: ShortsState):
    plan: Visual_Plan = state['visual_plan']
    generated_images = {}

    base_folder = Path("public/assets")
    base_folder.mkdir(parents=True, exist_ok=True)

    for scene in plan.scenes:
        generated_images[str(scene.id)] = []

        scene_folder = base_folder / f"scene_{scene.id}"
        scene_folder.mkdir(parents=True, exist_ok=True)

        if not scene.frames:
            raise Exception(f"❌ Scene {scene.id} has no frames")

        for frame in scene.frames:
            prompt = image_prompt(frame.description, plan.style)

            image_bytes = generate_image(prompt)

            # 🔥 HARD FAIL
            if not image_bytes:
                raise Exception(f"❌ Image generation failed for scene {scene.id}, frame {frame.order}")

            try:
                path = scene_folder / f"frame_{frame.order}.png"

                with open(path, "wb") as f:
                    f.write(image_bytes)

                # ✅ verify
                if not path.exists() or path.stat().st_size == 0:
                    raise Exception(f"❌ Image not saved properly: {path}")

                generated_images[str(scene.id)].append(str(path))

                print(f"✅ Saved: {path}")

            except Exception as e:
                raise Exception(f"❌ Save failed scene {scene.id}, frame {frame.order}: {e}")

        # Safety
        if not generated_images[str(scene.id)]:
            raise Exception(f"❌ No images generated for scene {scene.id}")

    print("✅ GENERATED IMAGES:", generated_images)

    return {"generated_images": generated_images}