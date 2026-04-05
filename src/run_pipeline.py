from pipeline.graph import workflow
from datetime import datetime

def get_genre_by_day():
    day = datetime.now().weekday()  # 0 = Monday

    schedule = {
        0: "class_6_science",   # Monday
        1: "class_6_geography",     # Tuesday
        2: "class_7_science",    # Wednesday
        3: "class_7_geography", # Thursday
        4: "class_8_geography",    # Friday
        5: "class_8_science",     # Saturday
        6: "fun_facts_science"   # Sunday
    }

    return schedule.get(day, "class_10_science")

initial_state = {
    "genre": get_genre_by_day(),
    "topic": "",
    "script": "",
    "previous_script": "",
    "caption": "",
    "audio_path": "",
    "video_path": "",
    "is_reviewed": False,
    "review": "",
    "review_type": "none",
    "is_published": False,
    "assets_folder": "",
    "subtitle_path": "",
    "visual_plan": {},
    "scenes": [],
    "rendered_clips": [],
    "generated_images": {},
    "timed_sentences": [],
}

result = workflow.invoke(initial_state)

print("\nFINAL STATE:\n")
for k, v in result.items():
    print(f"{k}: {v}")