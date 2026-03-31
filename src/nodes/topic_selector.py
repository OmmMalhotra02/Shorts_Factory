from ..state import ShortsState

def topic_selector(state: ShortsState) -> dict:
    return {state['topic']}