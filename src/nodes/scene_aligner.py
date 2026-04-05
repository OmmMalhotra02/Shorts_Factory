from state import ShortsState
from .visual_brain import Visual_Plan

def map_scenes_to_timing(scenes, timings):
    total_scene = len(scenes)
    total_timing = len(timings)

    mapped_scenes = []
    t_idx = 0

    for i, scene in enumerate(scenes):
        remaining_scenes = total_scene - i
        remaining_timings = total_timing - t_idx

        # distribute evenly
        take = max(1, remaining_timings // remaining_scenes)

        chunk = timings[t_idx: t_idx + take]

        duration = sum(t["duration"] for t in chunk)

        # fallback safety
        if duration <= 0:
            duration = 3.0

        scene.duration = round(duration, 2)

        scene.script_part = " ".join([t["text"] for t in chunk])

        mapped_scenes.append(scene)
        t_idx += take

    return mapped_scenes

def scene_duration_aligner(state: ShortsState):
    plan: Visual_Plan = state["visual_plan"]
    timings = state["timed_sentences"]

    updated_scenes = map_scenes_to_timing(plan.scenes, timings)

    plan.scenes = updated_scenes

    return {"visual_plan": plan}