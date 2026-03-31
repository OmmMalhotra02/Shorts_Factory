from ..state import ShortsState

def media_fetcher(state: ShortsState) -> dict:
    return {state['related_images'], state['related_videos']}