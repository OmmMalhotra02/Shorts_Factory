from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pipeline.graph import workflow

def run_pipeline(genre: str):
    print(f"\n Starting pipeline for: {genre}")
    
    initial_state = {
        "genre": genre,
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
        "rendered_clips": []
    }
    
    try:
        workflow.invoke(initial_state)
        print(f"✅ Done: {genre}")
    except Exception as e:
        print(f"❌ Failed {genre}: {e}")

scheduler = BlockingScheduler()

# 4 videos daily — one per channel, spread across day
scheduler.add_job(lambda: run_pipeline("maths_9_12"),     CronTrigger(hour=8,  minute=0))
scheduler.add_job(lambda: run_pipeline("physics_9_12"),   CronTrigger(hour=13, minute=0))

print("Scheduler running — 2 videos daily at 8am, 1pm")
scheduler.start()
