# from state import ShortsState
# import ffmpeg
# from pathlib import Path
# import json
# import re

# def resize_clip(input_path, output_path, duration):
#     ffmpeg.input(input_path, t=duration)\
#     .filter('scale', 1080, 1920, force_original_aspect_ratio='increase')\
#     .filter('crop', 1080, 1920)\
#     .output(output_path, vcodec='libx264')\
#     .run(overwrite_output=True)

# def image_to_clip(input_path, output_path, duration):
#     ffmpeg.input(input_path, loop=1, t=duration)\
#     .filter('scale', 1080, 1920, force_original_aspect_ratio='increase')\
#     .filter('crop', 1080, 1920)\
#     .output(output_path, vcodec='libx264', r=30)\
#     .run(overwrite_output=True)

# def create_concat_file(clip_paths, output_path):
#     with open(output_path, 'w') as f:
#         for clip in clip_paths:
#             f.write(f"file '{Path(clip).resolve()}'\n")
            
# def concat_clips(filelist_path: str, output_path: str):
#     ffmpeg.input(filelist_path, format='concat', safe=0)\
#         .output(output_path, c='copy')\
#         .run(overwrite_output=True)
    
# def safe_text(text):
#     text = text.replace("'", r"\'")
#     text = text.replace(":", r"\:")
#     text = text.replace(",", r"\,")
#     text = text.replace("%", r"\%")
#     return text
    
# # def add_audio_captions(video_path: str, audio_path: str, words: list, output_path: str):
    
#     # build subtitle filter string
#     subtitle_filters = []
#     for word in words:
#         start = word['start']
#         end = start + word['duration']
#         text = safe_text(word['word'])
        
#         filter_str = (
#             f"drawtext=text='{text}'"
#             f":fontsize=60"
#             f":fontcolor=white"
#             f":borderw=3"
#             f":bordercolor=black"
#             f":x=(w-text_w)/2"
#             f":y=(h*3/4)"
#             f":enable='between(t,{start},{end})'"
#         )
#         subtitle_filters.append(filter_str)
    
#     if not subtitle_filters:
#         all_filters = None
#     else:
#         all_filters = ",".join(subtitle_filters)
    
#     video = ffmpeg.input(video_path)
#     audio = ffmpeg.input(audio_path)
    
#     ffmpeg.output(
#         video.video,
#         audio.image,
#         output_path,
#         vcodec='libx264',
#         acodec='aac',
#         vf=all_filters if all_filters else None
#     ).run(overwrite_output=True)

# def add_audio_captions(video_path, audio_path, words, output_path):

#     video = ffmpeg.input(video_path)
#     audio = ffmpeg.input(audio_path)

#     if words:
#         subtitle_filters = []

#         for word in words:
#             start = word['start']
#             end = start + word['duration']
#             text = safe_text(word['word'])

#             filter_str = (
#                 f"drawtext=text='{text}'"
#                 f":fontsize=60"
#                 f":fontcolor=white"
#                 f":borderw=3"
#                 f":bordercolor=black"
#                 f":x=(w-text_w)/2"
#                 f":y=(h*3/4)"
#                 f":enable='between(t,{start},{end})'"
#             )

#             subtitle_filters.append(filter_str)

#         all_filters = ",".join(subtitle_filters)

#         ffmpeg.output(
#             video['v'],
#             audio['a'],
#             output_path,
#             vcodec='libx264',
#             acodec='aac',
#             vf=all_filters
#         ).run(overwrite_output=True)

#     else:
#         # ✅ NO FILTER CASE
#         ffmpeg.output(
#             video['v'],
#             audio['a'],
#             output_path,
#             vcodec='libx264',
#             acodec='aac'
#         ).run(overwrite_output=True)

# def assembler(state: ShortsState) -> dict:

#     # 1. **** resize clip ******

#     # 1 get clips and duration
#     all_media = state['related_videos'] + state['related_images']
#     asset_folder = Path(state['assets_folder'])

#     with open(state['subtitle_path'], 'r') as f:
#         words = json.load(f)

#     if not words:
#         # fallback: just set total duration to sum of clip durations
#         total_duration = len(state['related_videos'] + state['related_images']) * 3  # e.g., 3 sec per clip
#     else:
#         total_duration = words[-1]['start'] + words[-1]['duration']

#     if not all_media:
#         raise ValueError("No media found to assemble video")
#     clip_duration = total_duration / len(all_media)

#     # 2 resize script
#     resized_folder = asset_folder / "resized"
#     resized_folder.mkdir(exist_ok=True)

#     resized_clips = []

#     # handle videos
#     for idx, clip_path in enumerate(state['related_videos']):
#         output_path = resized_folder / f'clip_{idx}.mp4'
#         resize_clip(clip_path, str(output_path), clip_duration)
#         resized_clips.append(str(output_path.resolve()))
    
#     # handle images
#     for idx, img_path in enumerate(state['related_images']):
#         output_path = resized_folder / f"image_{idx}.mp4"
#         image_to_clip(img_path, str(output_path), clip_duration)
#         resized_clips.append(str(output_path.resolve()))
    
#     # 2. ***** create concat file ******
#     filelist_path = asset_folder / "filelist.txt"
#     create_concat_file(resized_clips, filelist_path)

#     # 3. ****** concat clips *******
#     concatenated_path = asset_folder / "concatenated.mp4"
#     concat_clips(str(filelist_path), str(concatenated_path))

#     # 4. ******** add audio and captions *****
#     final_path = asset_folder / "final.mp4"
#     add_audio_captions(
#         str(concatenated_path),
#         state['audio_path'],
#         words,
#         str(final_path)
#     )
            
#     # 4. add_audio_and_captions(video, audio, subtitles, output)
#     return {'video_path': str(final_path)}

import subprocess
from pathlib import Path
import os
import json

def assembler(state):
    clips = state["rendered_clips"]
    audio_path = state["audio_path"]

    output_base = Path("public/final")
    output_base.mkdir(parents=True, exist_ok=True)

    concat_file = output_base / "all_clips.txt"

    # write concat file safely
    with open(concat_file, "w") as f:
        for clip in clips:
            abs_path = Path(clip).resolve().as_posix()
            f.write(f"file '{abs_path}'\n")

    merged_video = output_base / "merged.mp4"

    # Merge clips
    result1 = subprocess.run([
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c", "copy",
        str(merged_video)
    ], capture_output=True, text=True)

    if result1.returncode != 0:
        print(result1.stderr)
        raise Exception("❌ FFmpeg merge failed")

    if not merged_video.exists():
        raise FileNotFoundError(f"🚨 merged.mp4 not created at {merged_video}")

    final_output = output_base / "final_output.mp4"

    # Attach audio
    result2 = subprocess.run([
        "ffmpeg",
        "-y",
        "-i", str(merged_video),
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        str(final_output)
    ], capture_output=True, text=True)

    if result2.returncode != 0:
        print(result2.stderr)
        raise Exception("❌ FFmpeg audio merge failed")

    if not final_output.exists():
        raise FileNotFoundError(f"🚨 final_output.mp4 not created")

    print(f"✅ Final video created at: {final_output}")

    if not state['subtitle_path'] or not Path(state['subtitle_path']).exists():
        print("⚠️ No subtitle file found, skipping captions")
        return {"video_path": str(final_output)}

    with open(state['subtitle_path'], 'r') as f:
        words = json.load(f)

    if not words:
        print("⚠️ Empty subtitle file, skipping captions")
        return {"video_path": str(final_output)}

    # 4. burn captions
    captioned_output = output_base / "final_with_captions.mp4"

    with open(state['subtitle_path'], 'r') as f:
        words = json.load(f)

    subtitle_filters = []
    for word in words:
        start = word['start']
        end = start + word['duration']
        text = word['word'].replace("'", "\u2019")
        filter_str = (
            f"drawtext=text='{text}':fontsize=60:fontcolor=white"
            f":borderw=3:bordercolor=black"
            f":x=(w-text_w)/2:y=(h*3/4)"
            f":enable='between(t,{start},{end})'"
        )
        subtitle_filters.append(filter_str)

    all_filters = ",".join(subtitle_filters)

    result3 = subprocess.run([
        "ffmpeg", "-y",
        "-i", str(final_output),
        "-vf", all_filters,
        "-c:a", "copy",
        str(captioned_output)
    ], capture_output=True, text=True)

    if result3.returncode != 0:
        print(result3.stderr)
        raise Exception("❌ Caption overlay failed")

    return {"video_path": str(captioned_output)}