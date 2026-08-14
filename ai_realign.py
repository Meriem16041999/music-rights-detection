import os
import json
import pandas as pd
from openai import OpenAI
from conductor_order import CONDUCTOR_WEEKDAY, CONDUCTOR_FRIDAY

from dotenv import load_dotenv
load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def ai_realign_with_conductor(df_occ: pd.DataFrame, conductor_type: str) -> pd.DataFrame:
    conductor = CONDUCTOR_FRIDAY if conductor_type == "Vendredi" else CONDUCTOR_WEEKDAY

    rows = []
    for i, r in df_occ.sort_values("start_sec").reset_index(drop=True).iterrows():
        rows.append({
            "index": i,
            "acr_title": str(r.get("TITRE", "")),
            "time_in": str(r.get("TIME IN", "")),
            "time_out": str(r.get("TIME OUT", "")),
            "duration": str(r.get("DUREE", "")),
            "source_title": str(r.get("SOURCE TITLE", "")),
        })

    prompt = f"""
Tu aides à corriger une déclaration musicale d'une émission MDP.

Règles :
- Respecte l'ordre du conducteur.
- Ne change pas les timings sauf si la ligne est manifestement incohérente.
- Utilise les détections ACR comme indices de transitions.
- Si ACR a sorti trop ou pas assez de lignes, indique-le dans warning.
- Retourne uniquement le JSON demandé.

Conducteur attendu :
{json.dumps(conductor, ensure_ascii=False, indent=2)}

Détections ACR agrégées :
{json.dumps(rows, ensure_ascii=False, indent=2)}
"""

    schema = {
        "name": "mdp_realign",
        "schema": {
            "type": "object",
            "properties": {
                "rows": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "index": {"type": "integer"},
                            "title": {"type": "string"},
                            "time_in": {"type": "string"},
                            "time_out": {"type": "string"},
                            "warning": {"type": "string"},
                        },
                        "required": ["index", "title", "time_in", "time_out", "warning"],
                        "additionalProperties": False,
                    },
                }
            },
            "required": ["rows"],
            "additionalProperties": False,
        },
        "strict": True,
    }

    response = client.responses.create(
        model="gpt-5.5",
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": schema["name"],
                "schema": schema["schema"],
                "strict": True,
            }
        },
    )

    data = json.loads(response.output_text)

    out = df_occ.copy().sort_values("start_sec").reset_index(drop=True)
    out["AI WARNING"] = ""

    for item in data["rows"]:
        i = item["index"]
        if i < len(out):
            out.at[i, "SOURCE TITLE"] = out.at[i, "TITRE"]
            out.at[i, "TITRE"] = item["title"]
            out.at[i, "TIME IN"] = item["time_in"]
            out.at[i, "TIME OUT"] = item["time_out"]
            out.at[i, "AI WARNING"] = item["warning"]

    return out