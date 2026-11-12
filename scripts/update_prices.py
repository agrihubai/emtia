"""14 aylık seriyi indirip data/emtia-fiyatlari.json dosyasını yeniden yazar.

Birincil kaynak FRED (St. Louis Fed). FRED bir seri için yanıt vermezse aynı seri
DBnomics'teki IMF PCPS / BLS aynasından çekilir. Yedek veri ancak elimizdeki eski
veriyle örtüşen aylarda %1'den fazla sapmıyorsa kabul edilir (birim/baz farkına karşı).

Herhangi bir seri iki kaynaktan da inmezse ya da beklenenden az satır gelirse dosyaya
dokunmadan hata verir, böylece yarım veri yayına çıkmaz.

Test: FORCE_FALLBACK=1 ile FRED atlanır, yalnızca yedek yol denenir.
"""
import csv
import io
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

# anahtar: (FRED kodu, DBnomics seri yolu)
SERIES = {
    "wheat": ("PWHEAMTUSDM", "IMF/PCPS/M.W00.PWHEAMT.USD"),
    "maize": ("PMAIZMTUSDM", "IMF/PCPS/M.W00.PMAIZMT.USD"),
    "rice": ("PRICENPQUSDM", "IMF/PCPS/M.W00.PRICENPQ.USD"),
    "soy": ("PSOYBUSDM", "IMF/PCPS/M.W00.PSOYB.USD"),
    "palm": ("PPOILUSDM", "IMF/PCPS/M.W00.PPOIL.USD"),
    "sunoil": ("PSUNOUSDM", "IMF/PCPS/M.W00.PSUNO.USD"),
    "olive": ("POLVOILUSDM", "IMF/PCPS/M.W00.POLVOIL.USD"),
    "sugar": ("PSUGAISAUSDM", "IMF/PCPS/M.W00.PSUGAISA.USD"),
    "arabica": ("PCOFFOTMUSDM", "IMF/PCPS/M.W00.PCOFFOTM.USD"),
    "cocoa": ("PCOCOUSDM", "IMF/PCPS/M.W00.PCOCO.USD"),
    "beef": ("PBEEFUSDM", "IMF/PCPS/M.W00.PBEEF.USD"),
    "salmon": ("PSALMUSDM", "IMF/PCPS/M.W00.PSALM.USD"),
    "fert": ("WPU0652", "BLS/wp/WPU0652"),
    "food": ("PFOODINDEXM", "IMF/PCPS/M.W00.PFOOD.IX"),
}
START = "2015-01-01"
OUT = Path(__file__).resolve().parent.parent / "data" / "emtia-fiyatlari.json"
UA = {"User-Agent": "agrihubai-emtia-updater/1.1"}
MAX_DEV = 0.01  # yedek kaynak için izin verilen en büyük sapma (%1)


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


def fetch_dbnomics(path: str) -> list[dict]:
    data = json.loads(get(f"https://api.db.nomics.world/v22/series/{path}?observations=1&format=json"))
    doc = data["series"]["docs"][0]
    rows = []
    for period, value in zip(doc["period"], doc["value"]):
        if value in (None, "NA") or period < START[:7]:
            continue
        rows.append({"date": period[:7] + "-01", "value": round(float(value), 3)})
    return rows


def matches_old(rows: list[dict], old_rows: dict) -> bool:
    """Yedek veriyi, eski veriyle örtüşen aylarda karşılaştırır."""
    common = [r for r in rows if r["date"] in old_rows and old_rows[r["date"]]]
    if len(common) < 24:
        return False
    worst = max(abs(r["value"] / old_rows[r["date"]] - 1) for r in common)
    print(f"  yedek/eski karşılaştırma: {len(common)} ay, en büyük sapma %{worst * 100:.2f}")
    return worst <= MAX_DEV


def main() -> int:
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else []
    old_by = {}
    for r in old:
        old_by.setdefault(r["series"], {})[r["date"]] = r["value"]
    force_fallback = os.environ.get("FORCE_FALLBACK") == "1"
    out = []
    for key, (fred, dbn) in SERIES.items():
        need = max(100, len(old_by.get(key, {})))
        rows, source = None, None
        if not force_fallback:
            try:
                rows, source = fetch_fred(fred), "FRED"
            except Exception as e:
                print(f"{key}: FRED başarısız ({e}); DBnomics deneniyor", file=sys.stderr)
        if rows is None or len(rows) < need:
            try:
                alt = fetch_dbnomics(dbn)
            except Exception as e:
                print(f"HATA: {key} DBnomics de başarısız ({e})", file=sys.stderr)
                return 1
            if not matches_old(alt, old_by.get(key, {})):
                print(f"HATA: {key} DBnomics verisi eski veriyle uyuşmuyor; kullanılmadı", file=sys.stderr)
                return 1
            rows, source = alt, "DBnomics"
        if len(rows) < need:
            print(f"HATA: {key} {len(rows)} satır; önceki {len(old_by.get(key, {}))}", file=sys.stderr)
            return 1
        out += [{"series": key, **r} for r in rows]
        print(key, source, len(rows), rows[-1]["date"], rows[-1]["value"])
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
