# AgriHub-AI Emtia Endeksi / Commodity Index

Dünya tarım ve gıda fiyatları, rafa yansıma süresi ve [AgriHub-AI](https://agrihubai.wordpress.com/) blog hipotezlerinin karnesi.

World farm and food prices, how long they take to reach the shelf, and a scorecard of the AgriHub-AI blog's hypotheses.

**Pano / Dashboard:** https://agrihubai.github.io/emtia/ (İngilizce / English: https://agrihubai.github.io/emtia/#en)

## Nasıl çalışır

- `index.html` — panonun kendisi. `scripts/build.py` ile `scripts/head.html` + `scripts/page.html` + `scripts/foot.html` birleştirilerek oluşturulur.
- `data/emtia-fiyatlari.json` — IMF birincil emtia fiyatları ve ABD gübre üretici fiyat endeksi, FRED üzerinden. **Her pazartesi otomatik güncellenir** (`.github/workflows/fiyat-guncelle.yml`).
- `data/emtia-serileri.json`, `data/hipotez-karnesi.json`, `data/gunluk-hayat.json` — ürün adları ve blog bağlantıları, hipotez karnesi ve "günlük hayatta" kartları. Bunlar her yeni AgriHub-AI yazısından sonra elle güncellenir.

Veri kaynakları: [FRED](https://fred.stlouisfed.org/) (IMF Primary Commodity Prices; BLS WPU0652). Bu sayfa yapay zekâ ile hazırlanmıştır; yatırım tavsiyesi değildir.
