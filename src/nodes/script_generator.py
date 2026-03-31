from ..state import ShortsState

def script_generator(state: ShortsState) -> dict:
    return {'script': state['script'], 'caption': state['caption']}
