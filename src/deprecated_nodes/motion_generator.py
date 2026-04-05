import subprocess
from pathlib import Path

def apply_motion(input_img, output_video, duration, motion):
    if not Path(input_img).exists():
        raise FileNotFoundError(f"Missing image: {input_img}")
    
    fps = 25
    frames = duration * fps

    zoom = {
        "low": "1.0",
        "medium": "1.1",
        "high": "1.2"
    }.get(motion.intensity, "1.05")

    zoompan = f"zoompan=z='min(zoom+0.0015,{zoom})':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"

    cmd = [
        "ffmpeg",
        "-y",
        "-loglevel", "error",
        "-loop", "1",
        "-i", input_img,
        "-vf", zoompan,
        "-t", str(duration),
        "-r", str(fps),
        "-pix_fmt", "yuv420p",
        output_video
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(result.stderr)
        raise Exception("FFmpeg failed")

    if not Path(output_video).exists():
        raise FileNotFoundError(f"Video not created: {output_video}")

def motion_generator(state):
    generated_images = state["generated_images"]
    print("GENERATED IMAGES:", generated_images)
    plan = state["visual_plan"]

    clips = []
    output_base = Path("public/videos")
    output_base.mkdir(parents=True, exist_ok=True)

    for scene in plan.scenes:
        print(f"Scene {scene.id} images:", generated_images.get(scene.id))
        scene_clips = []

        for i, img_path in enumerate(generated_images[str(scene.id)]):
            out = output_base / f"scene_{scene.id}_frame_{i}.mp4"
            frame_duration = max(0.8, scene.duration / len(scene.frames))

            apply_motion(
                input_img=img_path,
                output_video=str(out),
                duration = frame_duration,
                motion=scene.motion
            )

            scene_clips.append(str(out))

        if not scene_clips:
            raise Exception(f"❌ No clips generated for scene {scene.id}")

        # concat frames into scene clip
        concat_file = output_base / f"scene_{scene.id}_concat.txt"
        with open(concat_file, "w") as f:
            for clip in scene_clips:
                abs_path = Path(clip).resolve().as_posix()
                f.write(f"file '{abs_path}'\n")

        scene_output = output_base / f"scene_{scene.id}.mp4"

        subprocess.run([
            "ffmpeg",
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_file),
            "-c", "copy",
            str(scene_output)
        ])

        clips.append(str(scene_output))

    return {"rendered_clips": clips}