from ..state import ShortsState
import edge_tts
import asyncio
from pathlib import Path
import time

async def generate_voice(script: str, output_file: Path):
    communicate = edge_tts.Communicate(script, "en-US-GuyNeural", rate="+10%",
    pitch="+2Hz")
    await communicate.save(str(output_file))
    return

def voice_generator(state: ShortsState) -> dict:
    topic=state['topic']
    safe_topic = topic.replace(" ", "_").lower()
    script = state['script']

    assets_folder = Path(state['assets_folder'])
    audio_path = assets_folder / f"{safe_topic}.mp3"
    
    try:
        asyncio.run(generate_voice(script, audio_path))
    except Exception as e:
        print(f"Failed to generate audio: {e}")
        return {"audio_path": None}

    return {'audio_path': str(audio_path)}