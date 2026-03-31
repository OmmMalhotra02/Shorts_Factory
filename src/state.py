from typing import TypedDict, Literal

class ShortsState(TypedDict):
    topic: str
    script: str
    previous_script: str
    related_images: list[str]
    related_videos: list[str]
    caption: str
    audio_path: str
    video_path: str
    is_reviewed: bool
    review: str
    review_type: Literal['script', 'media', 'both', 'none']
    is_published: bool