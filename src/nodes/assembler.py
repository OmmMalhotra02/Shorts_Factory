import subprocess
import json
from pathlib import Path

def assembler(state) -> dict:
    clips = state["rendered_clips"]
    audio_path = state["audio_path"]

    output_base = Path(state['assets_folder'])
    output_base.mkdir(parents=True, exist_ok=True)
    final_output = output_base / "final_output.mp4"

    # step 1 — handle single or multiple clips
    if len(clips) == 1:
        video_input = clips[0]
    else:
        concat_file = output_base / "all_clips.txt"
        with open(concat_file, "w") as f:
            for clip in clips:
                abs_path = Path(clip).resolve().as_posix()
                f.write(f"file '{abs_path}'\n")

        merged = output_base / "merged.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_file), "-c", "copy", str(merged)
        ], capture_output=True, text=True)
        video_input = str(merged)

    # step 2 — attach audio
    result = subprocess.run([
        "ffmpeg", "-y",
        "-i", video_input,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(final_output)
    ], capture_output=True, text=True)

    if result.returncode != 0:
        print(result.stderr)
        raise Exception("FFmpeg audio merge failed")

    # step 3 — burn captions from script directly

    return {"video_path": str(final_output)}