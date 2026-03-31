from ..state import ShortsState

def voice_generator(state: ShortsState) -> dict:
    return {state['audio_path']}