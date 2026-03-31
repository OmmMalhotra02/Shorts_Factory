from ..state import ShortsState

def publisher(state: ShortsState) -> dict:
    return {state['is_published']}