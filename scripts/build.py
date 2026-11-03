"""index.html'i üç parçadan kurar: head.html (barındırma katmanı) + page.html (Claude panosundaki sayfanın aynısı) + foot.html."""
from pathlib import Path

here = Path(__file__).resolve().parent
page = (here / "page.html").read_text(encoding="utf-8")
page = page.replace('<meta name="dash-one-writer">', "", 1)
# GitHub sürümünde fiyatlar her hafta otomatik yenilenir: güncelleme notunu buna göre değiştir.
NOTES = {
    "Pano, AgriHub-AI'da her yeni yazı yayımlandığında en son verilerle yenilenir; son veri ayı sayfanın başında yazar.":
        "Fiyatlar her hafta FRED'den otomatik olarak yenilenir; blog bağlantıları, hipotez karnesi ve günlük hayat kartları her yeni AgriHub-AI yazısıyla güncellenir. Son veri ayı sayfanın başında yazar.",
    "The dashboard is refreshed with the latest data whenever a new AgriHub-AI article is published; the latest data month is shown at the top of the page.":
        "Prices are refreshed automatically from FRED every week; article links, the hypothesis scorecard and the everyday-life cards are updated with each new AgriHub-AI article. The latest data month is shown at the top of the page.",
}
for old, new in NOTES.items():
    page = page.replace(old, new)
out = (here / "head.html").read_text(encoding="utf-8") + page + (here / "foot.html").read_text(encoding="utf-8")
(here.parent / "index.html").write_text(out, encoding="utf-8")
print("index.html", len(out.encode()), "bytes")
