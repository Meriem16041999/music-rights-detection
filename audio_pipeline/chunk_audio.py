import subprocess
from pathlib import Path


def chunk_audio(wav_path: str, out_dir: str, seconds: int = 12):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-i", wav_path,
        "-f", "segment",
        "-segment_time", str(seconds),
        "-c", "copy",
        f"{out_dir}/chunk_%04d.wav",
    ]
    subprocess.run(cmd, check=True)
