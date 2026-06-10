import subprocess
from pathlib import Path


def extract_audio(video_path: str, out_wav: str):
    Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vn",
        "-ac", "1",
        "-ar", "44100",
        out_wav,
    ]
    subprocess.run(cmd, check=True)
