from pipeline.graph import workflow

initial_state = {
    "genre": "math_9_12",  # change this to test different channels
    "topic": "",
    "script": "",
    "previous_script": "",
    "caption": "",
    "audio_path": "",
    "subtitle_path": "",
    "video_path": "",
    "is_reviewed": False,
    "review": "",
    "review_type": "none",
    "is_published": False,
    "assets_folder": "",
    "rendered_clips": [],
    "scene_plan": [],
}

result = workflow.invoke(initial_state)

print("\nFINAL STATE:\n")
for k, v in result.items():
    print(f"{k}: {v}")