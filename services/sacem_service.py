import re
import unicodedata
import sqlite3
from pathlib import Path
import json
import datetime
from datetime import datetime, timezone
import platform
from sacem_agent import SacemAgent
from services.rights_memory_service import (
    get_rights_memory,
)

SACEM_CACHE_DB = Path("sacem_cache.sqlite3")

def clean_title_for_sacem(title: str) -> str:
    title = str(title or "").strip()

    if not title:
        return ""

    # Supprimer tout ce qui est entre parenthèses
    # "À la folie (Rework)" -> "À la folie"
    # "Beautiful People (Stay High)" -> "Beautiful People"
    # "Let's Dance (2018 Remaster)" -> "Let's Dance"
    title = re.sub(
        r"\s*\([^)]*\)",
        " ",
        title,
    )

    # Supprimer aussi les crochets
    # "Titre [Official Audio]" -> "Titre"
    title = re.sub(
        r"\s*\[[^\]]*\]",
        " ",
        title,
    )

    # Supprimer certains suffixes après un tiret
    title = re.sub(
        r"\s*-\s*"
        r"(single version|radio edit|"
        r"album version|remastered.*|"
        r"original version|edit|"
        r"piano version|acoustic|instrumental)"
        r"\s*$",
        "",
        title,
        flags=re.IGNORECASE,
    )

    # Nettoyer les espaces
    title = re.sub(
        r"\s+",
        " ",
        title,
    ).strip()

    return title

 

 
 

def normalize_sacem_search_text(value: str) -> str:
    value = str(value or "").strip()

    if not value:
        return ""

    # Beyoncé -> Beyonce
    value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
    )

    # Tous les types de tirets -> espace
    value = re.sub(
        r"[-–—_]+",
        " ",
        value,
    )

    # Ponctuation -> espace
    value = re.sub(
        r"[^A-Za-z0-9\s]",
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
def normalize_cache_value(value: str) -> str:
    value = str(value or "").strip()

    value = (
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
    )

    value = value.upper()
    value = re.sub(r"[^A-Z0-9]+", " ", value)

    return " ".join(value.split())


def build_sacem_cache_key(title: str, artist: str) -> str:
    normalized_title = normalize_cache_value(title)
    normalized_artist = normalize_cache_value(artist)

    return f"{normalized_title}||{normalized_artist}"

def init_sacem_cache():
    with sqlite3.connect(SACEM_CACHE_DB) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sacem_cache (
                cache_key TEXT PRIMARY KEY,
                title_input TEXT NOT NULL,
                artist_input TEXT NOT NULL,
                normalized_title TEXT NOT NULL,
                normalized_artist TEXT NOT NULL,
                status TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )

        conn.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_sacem_cache_title
            ON sacem_cache(normalized_title)
            """
        )

        conn.commit()
def get_sacem_cache(
    title: str,
    artist: str,
):
    cache_key = build_sacem_cache_key(
        title,
        artist,
    )

    with sqlite3.connect(
        SACEM_CACHE_DB
    ) as conn:

        row = conn.execute(
            """
            SELECT status, result_json
            FROM sacem_cache
            WHERE cache_key = ?
            """,
            (cache_key,),
        ).fetchone()

    if row is None:
        return None

    status = str(
        row[0] or ""
    ).strip()

    # Un ancien NOT_FOUND ne doit jamais
    # empêcher une nouvelle recherche
    if status != "found":
        print(
            "SACEM CACHE IGNORED:",
            title,
            artist,
            status,
        )

        return None

    try:
        return json.loads(row[1])

    except Exception:
        return None


def save_sacem_cache(
    title: str,
    artist: str,
    result: dict,
):
    status = str(result.get("status", "")).strip()

    # Ne pas mémoriser les erreurs, blocages ou résultats douteux.
    if status != "found":
        return

    cache_key = build_sacem_cache_key(title, artist)
    normalized_title = normalize_cache_value(title)
    normalized_artist = normalize_cache_value(artist)
    now = datetime.now(timezone.utc).isoformat()

    with sqlite3.connect(SACEM_CACHE_DB) as conn:
        conn.execute(
            """
            INSERT INTO sacem_cache (
                cache_key,
                title_input,
                artist_input,
                normalized_title,
                normalized_artist,
                status,
                result_json,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(cache_key) DO UPDATE SET
                title_input = excluded.title_input,
                artist_input = excluded.artist_input,
                normalized_title = excluded.normalized_title,
                normalized_artist = excluded.normalized_artist,
                status = excluded.status,
                result_json = excluded.result_json,
                updated_at = excluded.updated_at
            """,
            (
                cache_key,
                title,
                artist,
                normalized_title,
                normalized_artist,
                status,
                json.dumps(result, ensure_ascii=False),
                now,
                now,
            ),
        )

        conn.commit()

def get_sacem_surnames(value: str) -> list[str]:
    value = str(value or "").strip()

    if not value:
        return []

    results = []

    people = value.split(";")

    for person in people:
        person = person.strip()
        person = re.sub(
            r"\s*\([^)]*\)\s*$",
            "",
            person,
        ).strip()

        if not person:
            continue

        # Mark Brljak (APRA) -> Mark Brljak
        # Adam Steele (PRS) -> Adam Steele
        person = re.sub(
            r"\s*\([^)]*\)\s*$",
            "",
            person,
        ).strip()

        if not person:
            continue

        # Valeurs ACR non exploitables
        if normalize_cache_value(person) in {
            "",
            "PENDING",
            "UNKNOWN",
            "NONE",
            "N A",
            "NA",
            "TBC",
            "TBD",
        }:
            continue

        words = person.split()

        if not words:
            continue

        # Format ACR :
        # FORRESTER TIM -> FORRESTER
        if person.isupper():
            surname = words[0]

        # Format classique :
        # Tim Forrester -> Forrester
        # Beyoncé -> Beyonce
        else:
            surname = words[-1]

        surname = normalize_sacem_search_text(
            surname
        )

        if (
            surname
            and surname.lower()
            not in {
                x.lower()
                for x in results
            }
        ):
            results.append(surname)

    return results
def normalize_iswc(value: str) -> str:
    """
    T-330.432.259-2
    T3304322592
    -> T3304322592
    """
    value = str(
        value or ""
    ).upper().strip()

    return re.sub(
        r"[^A-Z0-9]",
        "",
        value,
    )

def validate_sacem_against_acr(
    row: dict,
    sacem: dict,
    search_surname: str = "",
) -> tuple[bool, str]:

    # ==========================================
    # 1. ISWC
    # ==========================================

    acr_iswc = normalize_iswc(
        row.get("code_iswc", "")
    )

    sacem_iswc = normalize_iswc(
        sacem.get("iswc", "")
    )

    # Si les deux ont un ISWC,
    # c'est notre vérification prioritaire.
    iswc_conflict = False

    if acr_iswc and sacem_iswc:

        if acr_iswc == sacem_iswc:
            return (
                True,
                "ISWC identique"
            )

        # IMPORTANT :
        # on ne rejette pas immédiatement.
        # On continue la vérification avec
        # les auteurs / compositeurs.
        iswc_conflict = True

        print(
            "SACEM ISWC DIFFERENT:",
            row.get("title"),
            "ACR=",
            row.get("code_iswc"),
            "SACEM=",
            sacem.get("iswc"),
        )

    # ==========================================
    # 2. CREATION DES LISTES DE PERSONNES
    # ==========================================

    acr_people = []

    for field in (
        "auteur",
        "compositeur",
    ):
        value = str(
            row.get(field, "")
            or ""
        )

        acr_people.extend(
            part.strip()
            for part in value.split(";")
            if part.strip()
        )

    sacem_people = []

    sacem_people.extend(
        sacem.get("authors", [])
        or []
    )

    sacem_people.extend(
        sacem.get("composers", [])
        or []
    )
    searched_surname = normalize_cache_value(
    search_surname
    )

    if searched_surname:

        for sacem_name in sacem_people:

            normalized_name = normalize_cache_value(
                sacem_name
            )

            words = set(
                normalized_name.split()
            )

            if searched_surname in words:

                # Vérifier également que ce nom existe
                # réellement dans les données ACR.
                acr_all = normalize_cache_value(
                    " ".join(
                        str(row.get(field, "") or "")
                        for field in (
                            "auteur",
                            "compositeur",
                            "interprete",
                            "artist",
                        )
                    )
                )

                if searched_surname in set(
                    acr_all.split()
                ):
                    return (
                        True,
                        f"nom recherché confirmé par SACEM : "
                        f"{search_surname} / {sacem_name}"
                    )
    # ==========================================
    # 3. SI ACR A DES CREATEURS
    # ==========================================

    if acr_people and sacem_people:

        for acr_name in acr_people:

            acr_normalized = (
                normalize_cache_value(
                    acr_name
                )
            )

            if not acr_normalized:
                continue

            acr_words = set(
                acr_normalized.split()
            )

            for sacem_name in sacem_people:

                sacem_normalized = (
                    normalize_cache_value(
                        sacem_name
                    )
                )

                if not sacem_normalized:
                    continue

                # Correspondance exacte
                if (
                    acr_normalized
                    == sacem_normalized
                ):
                    return (
                        True,
                        f"créateur commun : "
                        f"{acr_name}"
                    )

                # Correspondance partielle :
                # Jack Richard Pierce
                # ↔ Jack PIERCE
                common_words = (
                    acr_words
                    & set(
                        sacem_normalized.split()
                    )
                )

                if len(common_words) >= 2:
                    return (
                        True,
                        f"créateur compatible : "
                        f"{acr_name} / "
                        f"{sacem_name}"
                    )

        # ACR et SACEM ont tous les deux
        # des créateurs mais aucun ne correspond.
        return (
            False,
            "aucun créateur SACEM "
            "ne correspond aux données ACR"
        )

    # ==========================================
    # 4. ACR N'A PAS DE CREATEUR
    #    → ON UTILISE L'ARTISTE
    # ==========================================

    if not acr_people:

        artist = normalize_cache_value(
            row.get("artist", "")
        )

        # On cherche l'artiste dans :
        # auteurs + compositeurs + interprètes SACEM
        sacem_names = []

        sacem_names.extend(
            sacem.get("authors", [])
            or []
        )

        sacem_names.extend(
            sacem.get("composers", [])
            or []
        )

        sacem_names.extend(
            sacem.get("performers", [])
            or []
        )

        if artist:

            artist_words = set(
                artist.split()
            )

            for sacem_name in sacem_names:

                sacem_normalized = (
                    normalize_cache_value(
                        sacem_name
                    )
                )

                if not sacem_normalized:
                    continue

                # Exactement le même nom
                if artist == sacem_normalized:
                    return (
                        True,
                        f"artiste retrouvé dans SACEM : "
                        f"{sacem_name}"
                    )

                # Exemple :
                # Dermot Kennedy
                # ↔ Dermot KENNEDY
                common_words = (
                    artist_words
                    & set(
                        sacem_normalized.split()
                    )
                )

                if len(common_words) >= 2:
                    return (
                        True,
                        f"artiste compatible : "
                        f"{row.get('artist')} / "
                        f"{sacem_name}"
                    )

        # ======================================
        # Recherche titre + artiste très fiable
        # ======================================

        if (
            sacem.get("search_mode")
            == "title_artist"
            and sacem.get(
                "exact_title_match"
            ) is True
            and int(
                sacem.get(
                    "result_count",
                    0
                )
                or 0
            ) == 1
        ):
            return (
                True,
                "résultat unique "
                "avec titre + artiste"
            )

        # Rien ne permet de confirmer
        return (
            False,
            "ACR sans créateur et "
            "résultat SACEM non confirmé"
        )

    # ==========================================
    # 5. ACR A DES CREATEURS
    #    MAIS SACEM N'EN A PAS
    # ==========================================

    if acr_people and not sacem_people:
        return (
            False,
            "SACEM sans créateur "
            "pour confirmer ACR"
        )

    return (
        False,
        "résultat SACEM non confirmé"
    )


def enrich_sacem_sync(
    rows: list,
    progress_callback=None,
) -> list:
    """
    Enrichit les lignes avec les informations SACEM.

    Ordre de recherche :
    1. Titre + nom de famille de l'interprète
    2. Si rien : titre + nom de famille du compositeur
    3. Si toujours rien : "à vérifier"

    Aucune recherche avec le titre seul.
    """

    is_server_linux = (
        platform.system() == "Linux"
    )

    agent = SacemAgent(
        headless=is_server_linux
    )

    enriched = []

    for position, row in enumerate(rows):

        print("ROW =", row)

        # On garde toutes les données ACR existantes.
        new_row = dict(row)

        title = str(
            new_row.get("title", "")
            or ""
        ).strip()

        # ==========================================
        # 1. TITRE VIDE
        # ==========================================

        if not title:
            new_row["statut_sacem"] = "titre vide"

            enriched.append(new_row)

            if progress_callback:
                progress_callback(
                    position + 1,
                    len(rows),
                )

            continue

        # ==========================================
        # 2. TITRES INTERNES À IGNORER
        # ==========================================

        internal_titles = (
            "GENERIQUE",
            "GÉNÉRIQUE",
            "JINGLE",
            "NAPPE",
            "MDP ",
        )

        if title.upper().startswith(
            internal_titles
        ):
            new_row["statut_sacem"] = (
                "ignoré - titre interne"
            )

            enriched.append(new_row)

            if progress_callback:
                progress_callback(
                    position + 1,
                    len(rows),
                )

            continue

        try:

            # ==========================================
            # 3. NETTOYAGE DU TITRE POUR SACEM
            # ==========================================

            sacem_title = clean_title_for_sacem(
                title
            )

            sacem_title = normalize_sacem_search_text(
                sacem_title
            )

            print(
                "SACEM TITLE:",
                repr(title),
                "->",
                repr(sacem_title),
            )

            # ==========================================
            # 4. PRÉPARER LES NOMS DE FAMILLE
            # ==========================================

            interprete_surnames = get_sacem_surnames(
                new_row.get(
                    "interprete",
                    "",
                )
            )

            compositeur_surnames = get_sacem_surnames(
                new_row.get(
                    "compositeur",
                    "",
                )
            )

            print(
                "SACEM INTERPRETE SURNAMES:",
                interprete_surnames,
            )

            print(
                "SACEM COMPOSITEUR SURNAMES:",
                compositeur_surnames,
            )
            memory_artist = str(
                new_row.get("interprete", "")
                or new_row.get("artist", "")
                or ""
            ).strip()

            memory = get_rights_memory(
                title,
                memory_artist,
            )
            if memory is not None:
                print(
                    "RIGHTS MEMORY HIT:",
                    title,
                    memory_artist,
                )

                for field in (
                    "auteur",
                    "compositeur",
                    "interprete",
                    "editeur",
                    "sous_editeur",
                    "label",
                    "distributeur",
                    "code_iswc",
                    "code_isrc",
                    "url_sacem_detail",
                ):
                    value = memory.get(
                        field,
                        "",
                    )

                    if value:
                        new_row[field] = value

                new_row[
                    "statut_sacem"
                ] = "found"

                new_row[
                    "source_sacem"
                ] = "mémoire validée"

                new_row[
                    "sacem_validation"
                ] = "Résultat validé manuellement auparavant"

                new_row[
                    "statut_validation"
                ] = "validated"

                enriched.append(
                    new_row
                )

                if progress_callback:
                    progress_callback(
                        position + 1,
                        len(rows),
                    )

                continue
            # Résultat par défaut
            res = {
                "status": "not_found",
            }

            source_sacem = "sacem"

            # On garde la personne réellement utilisée
            # pour la recherche.
            search_person = ""

            # ==========================================
            # 5. RECHERCHE :
            # TITRE + NOM DE FAMILLE INTERPRÈTE
            # ==========================================

            for surname in interprete_surnames:

                print(
                    "SACEM SEARCH INTERPRETE:",
                    repr(sacem_title),
                    "+",
                    repr(surname),
                )

                # --------------------------------------
                # Cache correspondant exactement
                # à titre + nom recherché
                # --------------------------------------

                cached = get_sacem_cache(
                    sacem_title,
                    surname,
                )

                if cached is not None:

                    print(
                        "SACEM CACHE HIT:",
                        sacem_title,
                        surname,
                    )

                    candidate = cached
                    candidate_source = "cache"

                else:

                    print(
                        "SACEM CACHE MISS:",
                        sacem_title,
                        surname,
                    )

                    try:
                        candidate = agent.search(
                            sacem_title,
                            surname,
                        )
                        
                        print(
                            "SACEM CANDIDATE:",
                            surname,
                            candidate,
                        )
                        candidate_source = "sacem"

                    except Exception as exc:
                        print(
                            "SACEM SEARCH ERROR INTERPRETE:",
                            sacem_title,
                            surname,
                            repr(exc),
                        )

                        # On essaie le nom suivant
                        continue
                # --------------------------------------
                # Rien trouvé :
                # essayer l'interprète suivant
                # --------------------------------------

                if (
                    candidate.get("status")
                    != "found"
                ):
                    continue

                # --------------------------------------
                # Résultat trouvé :
                # validation ACR <-> SACEM
                # --------------------------------------

                valid, reason = (
                validate_sacem_against_acr(
                    new_row,
                    candidate,
                    surname,
                )
            )
                print(
                    "SACEM INTERPRETE VALIDATION:",
                    surname,
                    valid,
                    reason,
                )

                if not valid:
                    continue

                # --------------------------------------
                # Résultat accepté
                # --------------------------------------

                res = candidate
                source_sacem = candidate_source
                search_person = surname

                if candidate_source != "cache":
                    save_sacem_cache(
                        sacem_title,
                        surname,
                        candidate,
                    )

                break

            # ==========================================
            # 6. SI RIEN :
            # TITRE + NOM DE FAMILLE COMPOSITEUR
            # ==========================================

            if res.get("status") != "found":

                for surname in compositeur_surnames:

                    # Évite de refaire exactement
                    # la même recherche.
                    if (
                        surname.lower()
                        in {
                            value.lower()
                            for value
                            in interprete_surnames
                        }
                    ):
                        continue

                    print(
                        "SACEM SEARCH COMPOSITEUR:",
                        repr(sacem_title),
                        "+",
                        repr(surname),
                    )

                    cached = get_sacem_cache(
                        sacem_title,
                        surname,
                    )

                    if cached is not None:

                        print(
                            "SACEM CACHE HIT:",
                            sacem_title,
                            surname,
                        )

                        candidate = cached
                        candidate_source = "cache"

                    else:

                        print(
                            "SACEM CACHE MISS:",
                            sacem_title,
                            surname,
                        )

                        try:
                            candidate = agent.search(
                                sacem_title,
                                surname,
                            )
                            print(
                                "SACEM CANDIDATE:",
                                surname,
                                candidate,
                            )

                            candidate_source = "sacem"

                        except Exception as exc:
                            print(
                                "SACEM SEARCH ERROR COMPOSITEUR:",
                                sacem_title,
                                surname,
                                repr(exc),
                            )

                            continue

                    if (
                        candidate.get("status")
                        != "found"
                    ):
                        continue

                    valid, reason = (
                        validate_sacem_against_acr(
                            new_row,
                            candidate,
                            surname,
                        )
                    )
                    print(
                        "SACEM VALIDATION DETAIL:",
                        "title=",
                        title,
                        "| surname=",
                        surname,
                        "| status=",
                        candidate.get("status"),
                        "| sacem_title=",
                        candidate.get("title"),
                        "| composers=",
                        candidate.get("composers"),
                        "| authors=",
                        candidate.get("authors"),
                        "| iswc=",
                        candidate.get("iswc"),
                        "| valid=",
                        valid,
                        "| reason=",
                        reason,
                    )

                    print(
                        "SACEM COMPOSITEUR VALIDATION:",
                        surname,
                        valid,
                        reason,
                    )

                    if not valid:
                        continue

                    res = candidate
                    source_sacem = candidate_source
                    search_person = surname

                    if candidate_source != "cache":
                        save_sacem_cache(
                            sacem_title,
                            surname,
                            candidate,
                        )

                    break

            # ==========================================
            # 7. SACEM BLOQUÉE
            # ==========================================

            if res.get("status") == "blocked":

                print(
                    "SACEM BLOQUEE"
                )

                new_row[
                    "statut_sacem"
                ] = "blocked"

                new_row[
                    "source_sacem"
                ] = "sacem"

                enriched.append(
                    new_row
                )

                if progress_callback:
                    progress_callback(
                        position + 1,
                        len(rows),
                    )

                # On conserve les lignes restantes.
                for remaining in rows[
                    position + 1:
                ]:
                    enriched.append(
                        dict(remaining)
                    )

                break

            # ==========================================
            # 8. RIEN TROUVÉ / RIEN VALIDÉ
            # ==========================================

            if res.get("status") != "found":

                print(
                    "SACEM NOT FOUND:",
                    title,
                )

                new_row[
                    "statut_sacem"
                ] = "à vérifier"

                new_row[
                    "source_sacem"
                ] = "aucun résultat SACEM"

                new_row[
                    "sacem_validation"
                ] = (
                    "Aucun résultat SACEM validé "
                    "avec l'interprète ou "
                    "le compositeur"
                )

                # IMPORTANT :
                # aucune donnée SACEM ajoutée.
                #
                # Les données ACR restent intactes.

                new_row[
                    "url_sacem_detail"
                ] = ""

                new_row[
                    "url_sacem_candidate"
                ] = ""

                new_row[
                    "url_sacem"
                ] = ""

                enriched.append(
                    new_row
                )

                if progress_callback:
                    progress_callback(
                        position + 1,
                        len(rows),
                    )

                continue

            # ==========================================
            # 9. RÉSULTAT SACEM ACCEPTÉ
            # ==========================================

            print(
                "SACEM RESULT ACCEPTED:",
                res,
            )

            new_row[
                "statut_sacem"
            ] = "found"

            new_row[
                "sacem_validation"
            ] = (
                "Résultat SACEM validé"
            )

            # ==========================================
            # 10. DONNÉES SACEM
            # ==========================================

            sacem_compositeur = "; ".join(
                res.get(
                    "composers",
                    [],
                )
            ).strip()

            sacem_auteur = "; ".join(
                res.get(
                    "authors",
                    [],
                )
            ).strip()

            sacem_editeur = "; ".join(
                res.get(
                    "publishers",
                    [],
                )
            ).strip()

            sacem_sous_editeur = "; ".join(
                res.get(
                    "sub_publishers",
                    [],
                )
            ).strip()

            sacem_interprete = "; ".join(
                res.get(
                    "performers",
                    [],
                )
            ).strip()

            sacem_iswc = str(
                res.get(
                    "iswc",
                    "",
                )
                or ""
            ).strip()

            # ==========================================
            # 11. COMPLÉTER SANS ÉCRASER ACR
            # ==========================================

            if not str(
                new_row.get(
                    "compositeur",
                    "",
                )
            ).strip():
                new_row[
                    "compositeur"
                ] = sacem_compositeur

            if not str(
                new_row.get(
                    "auteur",
                    "",
                )
            ).strip():
                new_row[
                    "auteur"
                ] = sacem_auteur

            # Pour les résultats SACEM :
# on prend en priorité les sous-éditeurs.
# Si aucun sous-éditeur n'existe,
# on utilise l'éditeur SACEM.

            sacem_editor_value = (
                sacem_sous_editeur
                or sacem_editeur
            )

            if sacem_editor_value:
                new_row["editeur"] = (
                    sacem_editor_value
                )

                new_row["sous_editeur"] = (
                    sacem_editor_value
                )

            if not str(
                new_row.get(
                    "code_iswc",
                    "",
                )
            ).strip():
                new_row[
                    "code_iswc"
                ] = sacem_iswc

             

            if not str(
                new_row.get(
                    "interprete",
                    "",
                )
            ).strip():
                new_row[
                    "interprete"
                ] = sacem_interprete

            # ==========================================
            # 12. URL SACEM
            # ==========================================

            new_row[
                "url_sacem_detail"
            ] = res.get(
                "url",
                "",
            )

            new_row[
                "url_sacem_candidate"
            ] = ""

            new_row[
                "url_sacem"
            ] = res.get(
                "search_url",
                "",
            )

            new_row[
                "source_sacem"
            ] = source_sacem

            new_row[
                "sacem_search_person"
            ] = search_person

        # ==========================================
        # 13. ERREUR
        # ==========================================

        except Exception as exc:

            print(
                "SACEM ERROR:",
                repr(exc),
            )

            new_row[
                "statut_sacem"
            ] = "à vérifier"

            new_row[
                "source_sacem"
            ] = "erreur SACEM"

            new_row[
                "sacem_validation"
            ] = (
                f"{type(exc).__name__}: "
                f"{exc}"
            )

        # ==========================================
        # 14. AJOUTER LA LIGNE
        # ==========================================

        enriched.append(
            new_row
        )

        if progress_callback:
            progress_callback(
                position + 1,
                len(rows),
            )

    return enriched