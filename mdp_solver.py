from pathlib import Path
import re
import librosa
import numpy as np


def sec_to_timecode(sec: int) -> str:
    sec = max(0, int(sec))
    return f"{sec // 3600:02d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


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
        score = float(
            np.dot(v_vec, r_vec)
            / ((np.linalg.norm(v_vec) + 1e-9) * r_norm)
        )

        if score > best_score:
            best_score = score
            best_i = i

    detected_start = search_start + best_i * 0.25
    return int(round(detected_start)), best_score


def solve_mdp_timeline(conductor_rows, video_path):
    video_y, sr = librosa.load(video_path, sr=22050, mono=True)
    video_duration = int(librosa.get_duration(y=video_y, sr=sr))

    rows = [r.copy() for r in conductor_rows]

    cursor = 0

    # Phase 1 + 2 : fixed + anchors
    for i, row in enumerate(rows):
        kind = row.get("kind") or row.get("duration_mode") or "anchor"
        title = row.get("title", "")

        row["kind"] = kind
        row["audio_ref"] = find_ref_for_title(title)

        if kind == "fixed":
            duration = int(row.get("duration", 3))
            row["start_sec"] = cursor
            row["end_sec"] = cursor + duration
            row["match_score"] = "fixed"
            cursor = row["end_sec"]

        elif kind == "anchor":
            ref_path = row["audio_ref"]

            if ref_path:
                ref_y, _ = librosa.load(ref_path, sr=sr, mono=True)

                search_start = max(0, cursor - 8)
                search_end = min(video_duration, cursor + 80)

                detected_start, score = match_ref_start(
                    video_y,
                    ref_y,
                    sr,
                    search_start,
                    search_end,
                )

                row["start_sec"] = detected_start
                row["match_score"] = round(score, 3)
                cursor = detected_start
            else:
                row["start_sec"] = cursor
                row["match_score"] = "no_ref"

        elif kind == "dynamic":
            row["start_sec"] = cursor
            row["match_score"] = "dynamic"

    # Phase 3 : reconstruction des fins
    for i, row in enumerate(rows):
        kind = row.get("kind")

        if kind == "fixed":
            duration = int(row.get("duration", 3))
            row["end_sec"] = int(row["start_sec"]) + duration

        else:
            if i < len(rows) - 1:
                row["end_sec"] = int(rows[i + 1]["start_sec"])
            else:
                row["end_sec"] = video_duration

        if row["end_sec"] <= row["start_sec"]:
            row["end_sec"] = row["start_sec"] + 1

        duration = int(row["end_sec"]) - int(row["start_sec"])

        row["time_in"] = sec_to_timecode(row["start_sec"])
        row["time_out"] = sec_to_timecode(row["end_sec"])
        row["duration"] = sec_to_timecode(duration)
        row["source"] = "MDP solver"

    return rows