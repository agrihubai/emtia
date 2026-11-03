"""index.html'i üç parçadan kurar: head.html (barındırma katmanı) + page.html (Claude panosundaki sayfanın aynısı) + foot.html."""
from pathlib import Path

here = Path(__file__).resolve().parent
page = (here / "page.html").read_text(encoding="utf-8")
page = page.replace('<meta name="dash-one-writer">', "", 1)
out = (here / "head.html").read_text(encoding="utf-8") + page + (here / "foot.html").read_text(encoding="utf-8")
(here.parent / "index.html").write_text(out, encoding="utf-8")
print("index.html", len(out.encode()), "bytes")
