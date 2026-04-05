from typing import TypedDict, Literal

class ShortsState(TypedDict):
    genre: str
    topic: str
    script: str
    previous_script: str
    caption: str
    audio_path: str
    subtitle_path: str
    video_path: str
    is_reviewed: bool
    review: str
    review_type: Literal['script', 'media', 'both', 'none']
    is_published: bool
    assets_folder: str
    rendered_clips: list[str]
    scene_plan: list[dict]