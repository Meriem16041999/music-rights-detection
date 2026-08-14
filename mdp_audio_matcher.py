from pathlib import Path
import re
import librosa
import numpy as np


def norm_key(s: str) -> str:
    s = str(s).upper()
    s = s.replace("MDP 2025", "").replace("MDP", "")
    s = re.sub(r"[^A-Z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def find_ref_for_title(title: str, refs_dir="audio_refs") -> str:
    base = Path(refs_dir)
    key = norm_key(title)

    best = ""
    best_score = 0

    for f in base.rglob("*"):
        if not f.is_file():
            continue
        if f.suffix.lower() not in [".wav", ".mp3", ".m4a", ".aif", ".aiff"]:
            continue

        name = norm_key(f.stem)
        score = sum(1 for w in key.split() if w in name)

        if score > best_score:
            best_score = score
            best = str(f)

    return best


def chroma(y, sr):
    hop = int(sr * 0.25)
    return librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop).T


def match_ref_start(video_y, ref_y, sr, search_start, search_end):
    start_sample = int(search_start * sr)
    end_sample = int(search_end * sr)

    zone = video_y[start_sample:end_sample]

    if len(zone) < sr * 3 or len(ref_y) < sr * 3:
        return int(search_start), 0.0

    # On ne compare que le début de la référence
    ref_part = ref_y[: min(len(ref_y), sr * 12)]

    v = chroma(zone, sr)
    r = chroma(ref_part, sr)

    if len(v) <= len(r) or len(r) < 4:
        return int(search_start), 0.0

    r_vec = r.reshape(-1)
    r_norm = np.linalg.norm(r_vec) + 1e-9

    best_score = -1
    best_i = 0

    for i in range(0, len(v) - len(r) + 1):
        v_vec = v[i:i + len(r)].reshape(-1)
        score = float(np.dot(v_vec, r_vec) / ((np.linalg.norm(v_vec) + 1e-9) * r_norm))

        if score > best_score:
            best_score = score
            best_i = i

    detected_start = search_start + best_i * 0.25
    return int(round(detected_start)), best_score


def apply_reference_matching_to_rows(rows, video_path, search_margin=35):
    video_y, sr = librosa.load(video_path, sr=22050, mono=True)

    out = []
    cursor = 0

    for row in rows:
        row = row.copy()
        title = row.get("title", "")

        ref_path = find_ref_for_title(title)
        row["audio_ref"] = ref_path

        kind = row.get("kind", "anchor")

        if kind == "fixed":
            duration = int(row.get("duration_seconds", row.get("duration", 3)))

            row["start_sec"] = cursor
            row["end_sec"] = cursor + duration
            row["match_score"] = "fixed"

            cursor = row["end_sec"]

        elif kind == "anchor":
            ref_y, _ = librosa.load(ref_path, sr=sr, mono=True)

            detected_start, score = match_ref_start(
                video_y,
                ref_y,
                sr,
                max(0, cursor - 5),
                cursor + search_margin,
            )

            row["start_sec"] = detected_start
            row["match_score"] = round(score, 3)

            cursor = detected_start

        elif kind == "dynamic":
            row["start_sec"] = cursor

    # Recalcul no-overlap : chaque titre finit au début du suivant
 


def sec_to_timecode(sec: int) -> str:
    sec = max(0, int(sec))
    return f"{sec // 3600:02d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"