import re
import unicodedata
from difflib import SequenceMatcher

from services.edl_service import (
    parse_edl_clip_name,
)


# ============================================================
# NORMALISATION
# ============================================================

def normalize_match_text(value: str) -> str:
    """
    Normalise un texte pour permettre les comparaisons.

    Exemples :
        "À la folie" -> "a la folie"
        "Hide_and_Sneak" -> "hide and sneak"
        "Jean-Pierre" -> "jean pierre"
    """

    value = str(value or "").strip().lower()

    if not value:
        return ""

    # Retirer les accents
    value = unicodedata.normalize(
        "NFKD",
        value,
    )

    value = "".join(
        char
        for char in value
        if not unicodedata.combining(char)
    )

    # Underscores / tirets -> espaces
    value = re.sub(
        r"[_\-–—]+",
        " ",
        value,
    )

    # Ponctuation -> espace
    value = re.sub(
        r"[^a-z0-9\s]",
        " ",
        value,
    )

    # Espaces multiples
    value = re.sub(
        r"\s+",
        " ",
        value,
    ).strip()

    return value


# ============================================================
# SIMILARITÉ TEXTE
# ============================================================

def text_similarity(
    value_a: str,
    value_b: str,
) -> float:
    """
    Retourne un score entre 0 et 1.
    """

    a = normalize_match_text(value_a)
    b = normalize_match_text(value_b)

    if not a or not b:
        return 0.0

    if a == b:
        return 1.0

    # Si un titre est contenu dans l'autre
    if a in b or b in a:
        shorter = min(
            len(a),
            len(b),
        )

        longer = max(
            len(a),
            len(b),
        )

        if longer:
            containment_score = (
                shorter / longer
            )

            # Le containment est généralement
            # un signal assez fort.
            return max(
                0.80,
                containment_score,
            )

    return SequenceMatcher(
        None,
        a,
        b,
    ).ratio()


# ============================================================
# OVERLAP TEMPOREL
# ============================================================

def overlap_seconds(
    a_start: float,
    a_end: float,
    b_start: float,
    b_end: float,
) -> float:

    return max(
        0.0,
        min(a_end, b_end)
        - max(a_start, b_start),
    )


def overlap_ratio(
    a_start: float,
    a_end: float,
    b_start: float,
    b_end: float,
) -> float:
    """
    Ratio du chevauchement par rapport au plus petit segment.

    1.0 = le plus petit segment est entièrement
          compris dans l'autre.
    """

    overlap = overlap_seconds(
        a_start,
        a_end,
        b_start,
        b_end,
    )

    if overlap <= 0:
        return 0.0

    duration_a = max(
        0.0,
        a_end - a_start,
    )

    duration_b = max(
        0.0,
        b_end - b_start,
    )

    shortest = min(
        duration_a,
        duration_b,
    )

    if shortest <= 0:
        return 0.0

    return min(
        1.0,
        overlap / shortest,
    )


# ============================================================
# EXTRACTION DES INFORMATIONS EDL
# ============================================================

def get_edl_identity(
    edl_row: dict,
) -> dict:

    clip_name = str(
        edl_row.get(
            "clip_name",
            "",
        )
        or ""
    ).strip()

    parsed = parse_edl_clip_name(
        clip_name
    )

    title = str(
        parsed.get(
            "title",
            "",
        )
        or ""
    ).strip()

    artist = str(
        parsed.get(
            "artist",
            "",
        )
        or ""
    ).strip()

    return {
        "title": title,
        "artist": artist,
        "clip_name": clip_name,
    }


# ============================================================
# SCORE DE MATCH ACR <-> EDL
# ============================================================

def calculate_acr_edl_match(
    acr: dict,
    edl: dict,
) -> dict:
    """
    Compare une détection ACR avec un événement EDL.

    Score total sur 100 :

        temps       : 45 points
        titre       : 45 points
        artiste     : 10 points

    IMPORTANT :
    le temps seul ne suffit jamais à produire
    un match automatique.
    """

    acr_start = float(
        acr.get(
            "start_sec",
            0,
        )
        or 0
    )

    acr_end = float(
        acr.get(
            "end_sec",
            0,
        )
        or 0
    )

    edl_start = float(
        edl.get(
            "start_sec",
            0,
        )
        or 0
    )

    edl_end = float(
        edl.get(
            "end_sec",
            0,
        )
        or 0
    )

    overlap = overlap_seconds(
        acr_start,
        acr_end,
        edl_start,
        edl_end,
    )

    ratio = overlap_ratio(
        acr_start,
        acr_end,
        edl_start,
        edl_end,
    )

    identity = get_edl_identity(
        edl
    )

    edl_title = identity["title"]
    edl_artist = identity["artist"]

    acr_title = str(
        acr.get(
            "title",
            "",
        )
        or acr.get(
            "acr_title",
            "",
        )
        or ""
    ).strip()

    acr_artist = str(
        acr.get(
            "artist",
            "",
        )
        or acr.get(
            "interprete",
            "",
        )
        or ""
    ).strip()

    title_similarity = text_similarity(
        acr_title,
        edl_title,
    )

    artist_similarity = text_similarity(
        acr_artist,
        edl_artist,
    )

    # -------------------------
    # Score temps : 45
    # -------------------------

    time_score = ratio * 45.0

    # -------------------------
    # Score titre : 45
    # -------------------------

    title_score = (
        title_similarity * 45.0
    )

    # -------------------------
    # Score artiste : 10
    # -------------------------

    artist_score = (
        artist_similarity * 10.0
    )

    total_score = (
        time_score
        + title_score
        + artist_score
    )

    # --------------------------------------------------------
    # Sécurité importante :
    #
    # Deux morceaux qui se chevauchent mais dont les titres
    # sont totalement différents ne doivent PAS être associés.
    # --------------------------------------------------------

    title_compatible = (
        title_similarity >= 0.55
    )

    temporal_compatible = (
        overlap >= 1.0
        and ratio >= 0.20
    )

    automatic_match = (
        temporal_compatible
        and title_compatible
        and total_score >= 60
    )

    return {
        "score": round(
            total_score,
            2,
        ),
        "overlap_seconds": round(
            overlap,
            3,
        ),
        "overlap_ratio": round(
            ratio,
            3,
        ),
        "title_similarity": round(
            title_similarity,
            3,
        ),
        "artist_similarity": round(
            artist_similarity,
            3,
        ),
        "title_compatible":
            title_compatible,
        "temporal_compatible":
            temporal_compatible,
        "automatic_match":
            automatic_match,
        "edl_title":
            edl_title,
        "edl_artist":
            edl_artist,
    }


# ============================================================
# TIME CODE
# ============================================================

def seconds_to_timecode(
    seconds: float,
) -> str:
    """
    Format utilisé actuellement par ta timeline :
    HH:MM:SS
    """

    seconds = max(
        0,
        float(seconds or 0),
    )

    total_seconds = int(
        round(seconds)
    )

    hours = (
        total_seconds // 3600
    )

    minutes = (
        total_seconds % 3600
    ) // 60

    secs = (
        total_seconds % 60
    )

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{secs:02d}"
    )


# ============================================================
# MERGE ACR <-> EDL
# ============================================================

def merge_edl_with_acr(
    acr_rows: list,
    edl_rows: list,
) -> list:
    """
    EDL = référence temporelle.
    ACR = identification / métadonnées.

    Un événement EDL peut être associé à maximum
    une ligne ACR.

    Une ligne ACR peut être utilisée maximum une fois.

    Quand un EDL est fourni :
      - match fiable -> ACRCloud + EDL
      - pas de match -> EDL seul

    Les ACR sans correspondance EDL ne sont PAS
    injectés dans la timeline finale.
    """

    final_rows = []

    used_acr = set()

    # Trier l'EDL chronologiquement
    ordered_edl = sorted(
        edl_rows,
        key=lambda row: float(
            row.get(
                "start_sec",
                0,
            )
            or 0
        ),
    )

    for edl in ordered_edl:

        best_index = None
        best_match = None

        # ----------------------------------------------------
        # Chercher le meilleur ACR pour cet événement EDL
        # ----------------------------------------------------

        for index, acr in enumerate(
            acr_rows
        ):

            if index in used_acr:
                continue

            match = (
                calculate_acr_edl_match(
                    acr,
                    edl,
                )
            )

            # Aucun chevauchement temporel :
            # inutile de continuer.
            if (
                match[
                    "overlap_seconds"
                ]
                <= 0
            ):
                continue

            if (
                best_match is None
                or match["score"]
                > best_match["score"]
            ):
                best_index = index
                best_match = match

        # ====================================================
        # CAS 1 :
        # MATCH ACR + EDL FIABLE
        # ====================================================

        if (
            best_index is not None
            and best_match is not None
            and best_match[
                "automatic_match"
            ]
        ):

            acr = dict(
                acr_rows[
                    best_index
                ]
            )

            used_acr.add(
                best_index
            )

            edl_start = float(
                edl.get(
                    "start_sec",
                    0,
                )
                or 0
            )

            edl_end = float(
                edl.get(
                    "end_sec",
                    0,
                )
                or 0
            )

            # Garder le timing original ACR
            # pour audit/debug.
            acr[
                "acr_start_sec"
            ] = acr.get(
                "start_sec"
            )

            acr[
                "acr_end_sec"
            ] = acr.get(
                "end_sec"
            )

            acr[
                "acr_time_in"
            ] = acr.get(
                "time_in",
                "",
            )

            acr[
                "acr_time_out"
            ] = acr.get(
                "time_out",
                "",
            )

            # -----------------------------------------------
            # L'EDL devient la référence temporelle
            # -----------------------------------------------

            acr[
                "start_sec"
            ] = edl_start

            acr[
                "end_sec"
            ] = edl_end

            acr[
                "time_in"
            ] = seconds_to_timecode(
                edl_start
            )

            acr[
                "time_out"
            ] = seconds_to_timecode(
                edl_end
            )

            acr[
                "duration"
            ] = seconds_to_timecode(
                edl_end
                - edl_start
            )

            # -----------------------------------------------
            # Provenance
            # -----------------------------------------------

            acr[
                "edl_clip_name"
            ] = edl.get(
                "clip_name",
                "",
            )

            acr[
                "edl_title"
            ] = best_match.get(
                "edl_title",
                "",
            )

            acr[
                "edl_artist"
            ] = best_match.get(
                "edl_artist",
                "",
            )

            acr[
                "timing_source"
            ] = "EDL"

            acr[
                "identity_source"
            ] = "ACRCloud"

            acr[
                "source"
            ] = "ACRCloud + EDL"

            # -----------------------------------------------
            # Confiance
            # -----------------------------------------------

            acr[
                "match_confidence"
            ] = best_match[
                "score"
            ]

            acr[
                "match_title_similarity"
            ] = best_match[
                "title_similarity"
            ]

            acr[
                "match_artist_similarity"
            ] = best_match[
                "artist_similarity"
            ]

            acr[
                "match_overlap"
            ] = best_match[
                "overlap_seconds"
            ]

            acr[
                "match_overlap_ratio"
            ] = best_match[
                "overlap_ratio"
            ]

            print(
                "EDL MATCH:",
                edl.get(
                    "clip_name",
                    "",
                ),
                "->",
                acr.get(
                    "title",
                    "",
                ),
                "| score=",
                best_match[
                    "score"
                ],
                "| title=",
                best_match[
                    "title_similarity"
                ],
                "| overlap=",
                best_match[
                    "overlap_seconds"
                ],
            )

            final_rows.append(
                acr
            )

            continue

        # ====================================================
        # CAS 2 :
        # EDL SANS MATCH ACR FIABLE
        # ====================================================

        identity = get_edl_identity(
            edl
        )

        edl_start = float(
            edl.get(
                "start_sec",
                0,
            )
            or 0
        )

        edl_end = float(
            edl.get(
                "end_sec",
                0,
            )
            or 0
        )

        row = {
            "title":
                identity.get(
                    "title",
                    "",
                )
                or edl.get(
                    "clip_name",
                    "",
                ),

            "artist":
                identity.get(
                    "artist",
                    "",
                ),

            "acr_title":
                "",

            "time_in":
                seconds_to_timecode(
                    edl_start
                ),

            "time_out":
                seconds_to_timecode(
                    edl_end
                ),

            "duration":
                seconds_to_timecode(
                    edl_end
                    - edl_start
                ),

            "start_sec":
                edl_start,

            "end_sec":
                edl_end,

            "score":
                "",

            "auteur":
                "",

            "compositeur":
                "",

            "interprete":
                identity.get(
                    "artist",
                    "",
                ),

            "label":
                "",

            "editeur":
                "",

            "sous_editeur":
                "",

            "distributeur":
                "",

            "code_iswc":
                "",

            "code_isrc":
                "",

            "edl_clip_name":
                edl.get(
                    "clip_name",
                    "",
                ),

            "edl_title":
                identity.get(
                    "title",
                    "",
                ),

            "edl_artist":
                identity.get(
                    "artist",
                    "",
                ),

            "timing_source":
                "EDL",

            "identity_source":
                "EDL",

            "source":
                "EDL seul",

            "source_droits":
                "",

            "statut_validation":
                "review",

            "statut_sacem":
                "à vérifier",

            "match_confidence":
                (
                    best_match[
                        "score"
                    ]
                    if best_match
                    else 0
                ),

            "match_title_similarity":
                (
                    best_match[
                        "title_similarity"
                    ]
                    if best_match
                    else 0
                ),

            "match_overlap":
                (
                    best_match[
                        "overlap_seconds"
                    ]
                    if best_match
                    else 0
                ),
        }

        print(
            "EDL ONLY:",
            edl.get(
                "clip_name",
                "",
            ),
            "| parsed title=",
            row["title"],
            "| best score=",
            row[
                "match_confidence"
            ],
        )

        final_rows.append(
            row
        )

    # ========================================================
    # TRI FINAL
    # ========================================================

    final_rows.sort(
        key=lambda row: float(
            row.get(
                "start_sec",
                0,
            )
            or 0
        )
    )

    # Refaire les index
    for index, row in enumerate(
        final_rows
    ):
        row["index"] = index

    return final_rows