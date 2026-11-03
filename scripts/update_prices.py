"""FRED'den 14 aylık seriyi indirip data/emtia-fiyatlari.json dosyasını yeniden yazar.

Herhangi bir seri inmezse ya da beklenenden az satır gelirse dosyaya dokunmadan hata verir,
böylece yarım veri yayına çıkmaz.
"""
import csv
import io
import json
import sys
import time
import urllib.request
from pathlib import Path

SERIES = {
    "wheat": "PWHEAMTUSDM", "maize": "PMAIZMTUSDM", "rice": "PRICENPQUSDM", "soy": "PSOYBUSDM",
    "palm": "PPOILUSDM", "sunoil": "PSUNOUSDM", "olive": "POLVOILUSDM", "sugar": "PSUGAISAUSDM",
    "arabica": "PCOFFOTMUSDM", "cocoa": "PCOCOUSDM", "beef": "PBEEFUSDM", "salmon": "PSALMUSDM",
    "fert": "WPU0652", "food": "PFOODINDEXM",
}
START = "2015-01-01"
OUT = Path(__file__).resolve().parent.parent / "data" / "emtia-fiyatlari.json"


def fetch(code: str) -> list[dict]:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={code}&cosd={START}"
    req = urllib.request.Request(url, headers={"User-Agent": "agrihubai-emtia-updater/1.0"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                text = r.read().decode("utf-8")
            break
        except Exception:
            if attempt == 2:
                raise
            time.sleep(5)
    rows = []
    reader = csv.reader(io.StringIO(text))
    header = next(reader)
    if not header or "date" not in header[0].lower():
        raise ValueError(f"{code}: beklenmeyen yanıt")
    for date, value in reader:
        if value in ("", "."):
            continue
        rows.append({"date": date[:7] + "-01", "value": round(float(value), 3)})
    return rows


def main() -> int:
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
    old_n = {}
    for r in old:
        old_n[r["series"]] = old_n.get(r["series"], 0) + 1
    out = []
    for key, code in SERIES.items():
        rows = fetch(code)
        if len(rows) < max(100, old_n.get(key, 0)):
            print(f"HATA: {key} ({code}) {len(rows)} satır; önceki {old_n.get(key, 0)}", file=sys.stderr)
            return 1
        out += [{"series": key, **r} for r in rows]
        print(key, code, len(rows), rows[-1]["date"], rows[-1]["value"])
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
