from ..state import ShortsState
import edge_tts
import asyncio
from pathlib import Path
import json

async def generate_voice_with_timestamps(script: str, audio_file: Path, subtitle_file: Path):
    communicate = edge_tts.Communicate(script, "en-US-GuyNeural", rate="+10%", pitch="+2Hz")
    words=[]
    
    with open(audio_file, "wb") as f:
        async for chunk in communicate.stream():
            if chunk['type'] == 'audio':
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                words.append({
                    "word": chunk["text"],
                    "start": chunk["offset"] / 10000000,
                    "duration": chunk["duration"] / 10000000
                })
    with open(subtitle_file, "w", encoding="utf-8") as f:
        json.dump(words, f, indent=2)

def voice_generator(state: ShortsState) -> dict:
    topic=state['topic']
    safe_topic = topic.replace(" ", "_").lower()
    script = state['script']

    assets_folder = Path(state['assets_folder'])
    audio_path = assets_folder / f"{safe_topic}.mp3"
    subtitle_path = assets_folder / f"{safe_topic}.json"

    try:
        asyncio.run(generate_voice_with_timestamps(script, audio_path, subtitle_path))
    except Exception as e:
        print(f"Failed to generate audio: {e}")
        return {"audio_path": "", "subtitle_path": ""}

    return {'audio_path': str(audio_path), 'subtitle_path': str(subtitle_path)}