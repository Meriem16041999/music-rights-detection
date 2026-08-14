import re
from pathlib import Path
import pandas as pd


def clean_title(x):
    x = str(x).strip()
    x = re.sub(r"\s*-\s*Durée Réelle\s*", "", x, flags=re.I)
    x = re.sub(r"\s+", " ", x)
    return x.strip()


all_rows = []

for xlsx in Path("mdp_data").glob("*.xlsx"):
    xl = pd.ExcelFile(xlsx)

    for sheet in xl.sheet_names:
        sheet_upper = sheet.upper()
        if "DÉROULÉ" not in sheet_upper and "DEROULE" not in sheet_upper:
            continue

        df = pd.read_excel(xlsx, sheet_name=sheet, header=None)

        conductor_type = "Vendredi" if sheet.strip().upper().endswith("V") else "Lundi-Jeudi"

        position = 0

        for row_idx in range(4, len(df)):
            raw_title = str(df.iloc[row_idx, 0]).strip()

            if raw_title.lower() == "nan":
                continue

            if "DURÉE TOTALE" in raw_title.upper():
                continue

            if "AUDIOTEL" in raw_title.upper():
                continue

            if "DURÉE RÉELLE" not in raw_title.upper():
                continue

            title = clean_title(raw_title)
            position += 1

            values = []

            for col_idx in range(1, len(df.columns)):
                try:
                    v = float(df.iloc[row_idx, col_idx])
                    if v > 0:
                        values.append(v)
                except Exception:
                    pass

            if not values:
                continue

            all_rows.append({
                "file": xlsx.name,
                "sheet": sheet,
                "type": conductor_type,
                "position": position,
                "title": title,
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "avg": round(sum(values) / len(values), 1),
                "median": round(pd.Series(values).median(), 1),
            })


stats = pd.DataFrame(all_rows)

stats.to_excel("mdp_stats.xlsx", index=False)

print(stats)
print()
print("Fichier créé : mdp_stats.xlsx")