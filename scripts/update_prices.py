"""14 aylık seriyi indirip data/emtia-fiyatlari.json dosyasını yeniden yazar.

Kaynak FRED (St. Louis Fed). FRED aralıklı olarak takılabildiği için (9 Kasım 2026)
her istek kısa zaman aşımı ve artan beklemeyle tekrarlanır; iş akışı da betiği
3 tura kadar yeniden çalıştırır ve perşembe günü yedek koşu yapar.
(DBnomics aynası denendi: değerler birebir ama 2025 ortasında kalmış, yedek olamaz.)

Herhangi bir seri inmezse ya da beklenenden az satır gelirse dosyaya
dokunmadan hata verir, böylece yarım veri yayına çıkmaz.
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
UA = {"User-Agent": "agrihubai-emtia-updater/1.1"}


def get(url: str, waits=(10, 30, 60), timeout=45) -> str:
    """Kısa zaman aşımı + artan bekleme; FRED takılırsa uzun süre asılı kalmasın."""
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(len(waits) + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8")
        except Exception as e:
            if attempt == len(waits):
                raise
            print(f"  deneme {attempt + 1} başarısız ({e}); {waits[attempt]} sn sonra tekrar", file=sys.stderr)
            time.sleep(waits[attempt])


def fetch_fred(code: str) -> list[dict]:
    text = get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={code}&cosd={START}")
    reader = csv.reader(io.StringIO(text))
    header = next(reader)
    if not header or "date" not in header[0].lower():
        raise ValueError(f"{code}: beklenmeyen yanıt")
    rows = []
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
        rows = fetch_fred(code)
        if len(rows) < max(100, old_n.get(key, 0)):
            print(f"HATA: {key} ({code}) {len(rows)} satır; önceki {old_n.get(key, 0)}", file=sys.stderr)
            return 1
        out += [{"series": key, **r} for r in rows]
        print(key, code, len(rows), rows[-1]["date"], rows[-1]["value"])
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
