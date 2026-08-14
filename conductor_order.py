import pandas as pd


CONDUCTOR_WEEKDAY = [
    "MDP 2025 GENERIQUE DEBUT",
    "MDP 2025 NAPPE DEBUT",
    "MDP 2025 JINGLE NEUTRE",
    "MDP NAPPE TALK",
    "MDP 2025 JINGLE NEUTRE",
    "MDP 2025 JEU REFLEXION",
    "MDP 2025 NAPPE CHRONO",
    "MDP 2025 JINGLE NEUTRE",
    "MDP 2025 JEU REFLEXION",
    "MDP 2025 NAPPE CHRONO",
    "MDP 2025 JINGLE NEUTRE",
    "MDP 2025 JEU REFLEXION",
    "MDP 2025 NAPPE CHRONO",
    "MDP 2025 JINGLE NEUTRE",
    "MDP 2025 JEU REFLEXION",
    "MDP 2025 NAPPE CHRONO",
    "MDP 2025 JINGLE NEUTRE",
    "MDP 2025 JEU REFLEXION",
    "MDP 2025 NAPPE CHRONO",
    "MDP 2025 JINGLE NEUTRE",
    "MDP 2025 NAPPE FIN NEUTRE",
]

CONDUCTOR_FRIDAY = [
    "MDP 2025 GENERIQUE DEBUT",
    "MDP 2025 NAPPE DEBUT",
    "MDP 2025 JINGLE NEUTRE",
    "MDP NAPPE TALK",
    "MDP 2025 JINGLE NEUTRE",
    "MDP 2025 NAPPE FINALE REFLEXION",
    "MDP 2025 NAPPE CHRONO FINALE",
    "MDP 2025 JINGLE NEUTRE",
    "MDP 2025 NAPPE FINALE REFLEXION",
    "MDP 2025 NAPPE CHRONO FINALE",
    "MDP 2025 JINGLE NEUTRE",
    "MDP 2025 NAPPE FINALE REFLEXION",
    "MDP 2025 NAPPE CHRONO FINALE",
    "MDP 2025 JINGLE NEUTRE",
    "MDP 2025 NAPPE FINALE REFLEXION",
    "MDP 2025 NAPPE CHRONO FINALE",
    "MDP 2025 JINGLE NEUTRE",
    "MDP 2025 NAPPE FINALE REFLEXION",
    "MDP 2025 FIN GAGNANTE",
]


def sec_to_timecode(sec: int) -> str:
    sec = max(0, int(sec))
    return f"{sec // 3600:02d}:{(sec % 3600) // 60:02d}:{sec % 60:02d}"


def fixed_duration(title: str):
    t = str(title).upper()

    if "GENERIQUE DEBUT" in t:
        return 10

    if "JINGLE NEUTRE" in t:
        return 3

    return None


def load_mdp_stats(stats_path="mdp_stats.xlsx"):
    try:
        return pd.read_excel(stats_path)
    except Exception:
        return pd.DataFrame()


def apply_conductor_order(df_occ: pd.DataFrame, conductor_type: str) -> pd.DataFrame:
    acr = df_occ.copy().sort_values(["part", "start_sec"]).reset_index(drop=True)
    conductor = CONDUCTOR_FRIDAY if conductor_type == "Vendredi" else CONDUCTOR_WEEKDAY
    stats = load_mdp_stats()

    rows = []
    cursor = 0

    for i, title in enumerate(conductor):
        position = i + 1

        hist_min = ""
        hist_max = ""
        hist_avg = ""
        hist_median = ""

        if not stats.empty:
            stat_row = stats[
                (stats["type"].astype(str) == conductor_type)
                & (stats["position"].astype(int) == position)
                & (stats["title"].astype(str).str.upper().str.strip() == title.upper().strip())
            ]

            if not stat_row.empty:
                s = stat_row.iloc[0]
                hist_min = s["min"]
                hist_max = s["max"]
                hist_avg = s["avg"]
                hist_median = s["median"]

        fixed = fixed_duration(title)

        if fixed is not None:
            duration = fixed
        elif hist_median != "":
            duration = int(hist_median)
        else:
            duration = 10

        start_sec = cursor
        end_sec = start_sec + duration

        acr_original = ""
        if i < len(acr):
            acr_original = str(acr.loc[i].get("TITRE", ""))

        rows.append({
            "part": "P1",
            "TITRE": title,
            "ARTISTE": "",
            "SOURCE TITLE": acr_original,
            "TIME IN": sec_to_timecode(start_sec),
            "TIME OUT": sec_to_timecode(end_sec),
            "DUREE": sec_to_timecode(duration),
            "MATCH SCORE": "",
            "ACR SCORE": "",
            "start_sec": start_sec,
            "end_sec": end_sec,
            "audio_ref": "",
            "isrc": "",
            "garder": True,
            "ACR TITLE ORIGINAL": acr_original,
            "CONDUCTEUR TITLE": title,
            "DURÉE HIST MIN": hist_min,
            "DURÉE HIST MAX": hist_max,
            "DURÉE HIST AVG": hist_avg,
            "DURÉE HIST MEDIAN": hist_median,
            "CONDUCTEUR WARNING": "",
        })

        cursor = end_sec

    return pd.DataFrame(rows)