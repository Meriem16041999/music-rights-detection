import sqlite3
from pathlib import Path
from datetime import datetime, timezone
import re
import unicodedata


 


RIGHTS_MEMORY_DB = Path("rights_memory.sqlite3")

 

def normalize_memory_value(value: str) -> str:
    value = str(
        value or ""
    ).strip()

    value = (
        unicodedata.normalize(
            "NFKD",
            value,
        )
        .encode(
            "ascii",
            "ignore",
        )
        .decode("ascii")
    )

    value = value.upper()

    value = re.sub(
        r"[^A-Z0-9]+",
        " ",
        value,
    )

    return " ".join(
        value.split()
    )
def init_rights_memory():
    with sqlite3.connect(RIGHTS_MEMORY_DB) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rights_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                normalized_title TEXT NOT NULL,
                normalized_artist TEXT NOT NULL DEFAULT '',

                title TEXT NOT NULL,
                artist TEXT DEFAULT '',

                auteur TEXT DEFAULT '',
                compositeur TEXT DEFAULT '',
                interprete TEXT DEFAULT '',

                editeur TEXT DEFAULT '',
                sous_editeur TEXT DEFAULT '',

                label TEXT DEFAULT '',
                distributeur TEXT DEFAULT '',

                code_iswc TEXT DEFAULT '',
                code_isrc TEXT DEFAULT '',

                sacem_url TEXT DEFAULT '',

                source TEXT DEFAULT 'manual',

                created_at TEXT,
                updated_at TEXT,

                UNIQUE(
                    normalized_title,
                    normalized_artist
                )
            )
            """
        )

        conn.commit()


def save_rights_memory(row: dict):
    title = str(
        row.get("title", "")
        or ""
    ).strip()

    artist = str(
        row.get("interprete", "")
        or row.get("artist", "")
        or ""
    ).strip()

    if not title:
        return False

    normalized_title = normalize_memory_value(
    title
)

    normalized_artist = normalize_memory_value(
        artist
    )

    now = datetime.now(
        timezone.utc
    ).isoformat()

    with sqlite3.connect(
        RIGHTS_MEMORY_DB
    ) as conn:

        conn.execute(
            """
            INSERT INTO rights_memory (
                normalized_title,
                normalized_artist,

                title,
                artist,

                auteur,
                compositeur,
                interprete,

                editeur,
                sous_editeur,

                label,
                distributeur,

                code_iswc,
                code_isrc,

                sacem_url,

                source,

                created_at,
                updated_at
            )

            VALUES (
                ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?,
                ?, ?,
                ?,
                ?,
                ?, ?
            )

            ON CONFLICT(
                normalized_title,
                normalized_artist
            )
            DO UPDATE SET
                title = excluded.title,
                artist = excluded.artist,

                auteur = excluded.auteur,
                compositeur = excluded.compositeur,
                interprete = excluded.interprete,

                editeur = excluded.editeur,
                sous_editeur = excluded.sous_editeur,

                label = excluded.label,
                distributeur = excluded.distributeur,

                code_iswc = excluded.code_iswc,
                code_isrc = excluded.code_isrc,

                sacem_url = excluded.sacem_url,

                source = excluded.source,

                updated_at = excluded.updated_at
            """,
            (
                normalized_title,
                normalized_artist,

                title,
                artist,

                row.get("auteur", ""),
                row.get("compositeur", ""),
                row.get("interprete", ""),

                row.get("editeur", ""),
                row.get("sous_editeur", ""),

                row.get("label", ""),
                row.get("distributeur", ""),

                row.get("code_iswc", ""),
                row.get("code_isrc", ""),

                row.get("url_sacem_detail", "")
                or row.get("url_sacem", ""),

                "manual",

                now,
                now,
            ),
        )

        conn.commit()

    return True


def get_rights_memory(
    title: str,
    artist: str = "",
):
    normalized_title = normalize_memory_value(
    title
    )

    normalized_artist = normalize_memory_value(
        artist
    )

    with sqlite3.connect(
        RIGHTS_MEMORY_DB
    ) as conn:

        row = conn.execute(
            """
            SELECT
                title,
                artist,

                auteur,
                compositeur,
                interprete,

                editeur,
                sous_editeur,

                label,
                distributeur,

                code_iswc,
                code_isrc,

                sacem_url,

                source

            FROM rights_memory

            WHERE
                normalized_title = ?
                AND normalized_artist = ?
            """,
            (
                normalized_title,
                normalized_artist,
            ),
        ).fetchone()

    if row is None:
        return None

    return {
        "title": row[0],
        "artist": row[1],

        "auteur": row[2],
        "compositeur": row[3],
        "interprete": row[4],

        "editeur": row[5],
        "sous_editeur": row[6],

        "label": row[7],
        "distributeur": row[8],

        "code_iswc": row[9],
        "code_isrc": row[10],

        "url_sacem_detail": row[11],

        "source_memory": row[12],
    }