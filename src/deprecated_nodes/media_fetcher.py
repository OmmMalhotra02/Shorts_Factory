from state import ShortsState
from pydantic import BaseModel
from typing import List
import os
from langchain_openai import ChatOpenAI
import requests
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

class Scene(BaseModel):
    scene: str
    search_query: str

class SceneOutput(BaseModel):
    scenes: List[Scene]

load_dotenv()

llm = ChatOpenAI(
    model="nvidia/nemotron-3-super-120b-a12b:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_KEY")
)
scene_llm = llm.with_structured_output(SceneOutput)

def create_run_folder(genre: str) -> Path:
    timestamp = int(time.time())
    folder = Path(f"public/assets/{genre}_{timestamp}")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "videos").mkdir(exist_ok=True)
    (folder / "images").mkdir(exist_ok=True)
    return folder

def download_file(url: str, path: Path) -> str:
    resp = requests.get(url, stream=True, timeout=30)
    resp.raise_for_status()
    with open(path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return str(path)

def extract_scenes(script: str):
    prompt = f"""
            Break this YouTube Shorts script into 4-6 visual scenes.

            SCRIPT:
            {script}

            Rules:
            - Each scene = one visual moment
            - Keep scenes short
            - Generate a search query for stock footage
            - Queries should describe exactly what the camera sees
            - Include camera angle, lighting, and mood
            - Make queries cinematic, high-quality, and specific
            - Prefer terms like: cinematic, 4k, slow motion, dramatic lighting

            Example:
            "cinematic astronaut floating in space 4k earth glowing slow motion"

            BAD query: "person walking on earth"
            GOOD query: "earth core rotation cross section geology 4k"
            GOOD query: "molten iron earth inner core spinning cinematic"

            Always describe the SCIENCE being shown, not generic human activity.

            Return JSON in this format:
            {{
            "scenes": [
                {{
                "scene": "...",
                "search_query": "..."
                }}
            ]
            }}
            """

    resp = scene_llm.invoke(prompt)
    return resp.scenes

def fetch_pexels_video(query: str):
    url = "https://api.pexels.com/videos/search"
    headers = {"Authorization": os.getenv('PEXELS_KEY')}

    params = {
    "query": query,
    "per_page": 5,
    "orientation": "portrait",  # 9:16 friendly
    "size": "large"
}

    try:
        res = requests.get(url, headers=headers, params=params)
        res.raise_for_status()
        data = res.json()

        for video in data.get("videos", []):
            files = video.get("video_files", [])
            if files:
                for f in files:
                    if f.get("quality") == "sd" or f.get("height", 0) <= 1080:
                        return f.get("link")

    except Exception:
        return None

def fetch_pexels_image(query: str):
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": os.getenv('PEXELS_KEY')}

    params = {
    "query": query,
    "per_page": 5,
    "orientation": "portrait",  # 9:16 friendly
    "size": "large"
}

    try:
        res = requests.get(url, headers=headers, params=params)
        res.raise_for_status()
        data = res.json()

        for photo in data.get("photos", []):
            return photo.get("src", {}).get("original")

    except Exception:
        return None

def fetch_nasa_image(query: str):
    url = "https://images-api.nasa.gov/search"

    params = {
    "query": query,
    "per_page": 5,
    "orientation": "portrait",  # 9:16 friendly
    "size": "large"
    }

    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        data = res.json()

        items = data.get("collection", {}).get("items", [])
        if items:
            links = items[0].get("links", [])
            if links:
                return links[0].get("href")

    except Exception:
        return None    

def media_fetcher(state: ShortsState) -> dict:
    script = state["script"]
    genre = state["genre"]

    scenes = extract_scenes(script)

    run_folder = create_run_folder(genre)
    video_folder = run_folder / "videos"
    image_folder = run_folder / "images"

    video_paths = []
    image_paths = []

    def process_scene(idx_scene):
        idx, s = idx_scene

        query = s.search_query

        video_url = None
        image_url = None
        if genre == "space":
            image_url = fetch_nasa_image(query)
        else:
            video_url = fetch_pexels_video(query)
            image_url = fetch_pexels_image(query)

        results = {"video": None, "image": None}

        if video_url:
            try:
                path = video_folder / f"scene_{idx}.mp4"
                results["video"] = download_file(video_url, path)
            except Exception as e:
                print(f"Failed to download scene_{idx}: {e}")

        if image_url:
            try:
                path = image_folder / f"scene_{idx}.jpg"
                results["image"] = download_file(image_url, path)
            except Exception as e:
                print(f"Failed to download scene_{idx}: {e}")

        return results

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(process_scene, enumerate(scenes)))

    for r in results:
        if r["video"]:
            video_paths.append(r["video"])
        if r["image"]:
            image_paths.append(r["image"])

    return {
    "related_videos": video_paths,
    "related_images": image_paths,
    "assets_folder": str(run_folder)
    }