from state import ShortsState
import edge_tts
import asyncio
from pathlib import Path
import json
import re
import time

# ---------- ASYNC VOICE ENGINE ----------

async def generate_voice_with_timestamps(script: str, audio_file: Path, subtitle_file: Path):
    communicate = edge_tts.Communicate(script, "en-US-GuyNeural", rate="+5%")
    words = []
    audio_chunks = []

    async for chunk in communicate.stream():
        if chunk['type'] == 'audio':
            audio_chunks.append(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            words.append({
                "word": chunk["text"],
                "start": chunk["offset"] / 10000000,
                "duration": chunk["duration"] / 10000000
            })

    # write audio after collecting all chunks
    with open(audio_file, "wb") as f:
        for chunk in audio_chunks:
            f.write(chunk)

    print(f"Words captured: {len(words)}")

    with open(subtitle_file, "w", encoding="utf-8") as f:
        json.dump(words, f, indent=2)
# ---------- SAFE ASYNC RUNNER ----------

def run_async(coro):
    try:
        loop = asyncio.get_running_loop()
        return asyncio.create_task(coro)
    except RuntimeError:
        return asyncio.run(coro)

# ---------- MAIN NODE ----------

def voice_generator(state: ShortsState) -> dict:
    topic = state['topic']
    script = state['script']

    # sanitize filename
    safe_topic = re.sub(r'[^a-zA-Z0-9_]', '', topic.replace(" ", "_")).lower()

    assets_folder = Path("public/assets") / f"{state['genre']}_{int(time.time())}"
    assets_folder.mkdir(parents=True, exist_ok=True)

    audio_path = assets_folder / f"{safe_topic}.mp3"
    subtitle_path = assets_folder / f"{safe_topic}.json"

    try:
        run_async(generate_voice_with_timestamps(script, audio_path, subtitle_path))
    except Exception as e:
        print(f"Failed to generate audio: {e}")
        return {"audio_path": "", "subtitle_path": ""}

    return {
        'audio_path': str(audio_path),
        'subtitle_path': str(subtitle_path),
        'assets_folder': str(assets_folder)  # ← add this
    }