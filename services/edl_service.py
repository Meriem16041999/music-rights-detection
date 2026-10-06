import re


def edl_tc_to_seconds(tc: str, fps: float) -> float:
    hh, mm, ss, ff = [
        int(x)
        for x in tc.split(":")
    ]

    return (
        hh * 3600
        + mm * 60
        + ss
        + ff / fps
    )


def parse_edl_text(
    text: str,
    fps: float = 25.0,
    timeline_base_tc: str = "10:00:00:00",
):
    rows = []

    base_sec = edl_tc_to_seconds(
        timeline_base_tc,
        fps,
    )

    pattern = re.compile(
        r"^\s*\d+\s+"
        r"\d+\s+"
        r"(.+?)\s+"
        r"(\d{2}:\d{2}:\d{2}:\d{2})\s+"
        r"(\d{2}:\d{2}:\d{2}:\d{2})\s+"
        r"(\d{2}:\d{2}:\d{2}:\d{2})\s+"
        r"(Muted|Unmuted)\s*$",
        re.MULTILINE,
    )

    for match in pattern.finditer(text):
        clip_name = match.group(1).strip()
        start_tc = match.group(2)
        end_tc = match.group(3)
        duration_tc = match.group(4)
        state = match.group(5)

        start_sec = (
            edl_tc_to_seconds(start_tc, fps)
            - base_sec
        )

        end_sec = (
            edl_tc_to_seconds(end_tc, fps)
            - base_sec
        )

        if end_sec <= start_sec:
            continue

        rows.append({
            "clip_name": clip_name,
            "start_tc": start_tc,
            "end_tc": end_tc,
            "duration_tc": duration_tc,
            "start_sec": start_sec,
            "end_sec": end_sec,
            "duration_sec": end_sec - start_sec,
            "state": state,
        })

    return rows


def parse_edl_clip_name(
    clip_name: str,
) -> dict:

    name = str(
        clip_name or ""
    ).strip()

    name = re.sub(
        r"\.(mp3|wav|m4a|mp4).*$",
        "",
        name,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"_+",
        " ",
        name,
    )

    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned,
    ).strip()

    return {
        "title": cleaned,
        "artist": "",
    }