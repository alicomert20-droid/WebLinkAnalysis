# Web Link Analysis (Proje 4.3)

Akıllı Bilgi Erişim Sistemleri ve Metin Analitiği dersi proje ödevi.
PageRank ve HITS algoritmalarını Python ile yazıp rastgele bir web grafiği üzerinde Spider Trap, Dead End ve sönümleme faktörü (α) deneyleri yaptım.

Ali Cömert - 21YÖBİ1042

## Kurulum

Python 3.10 veya üstü gerekiyor.

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

PowerShell sanal ortamı açmaya izin vermezse önce şunu çalıştırın:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Çalıştırma

```powershell
python -m pytest -q          # testler
python -m src.experiments    # deneyler, sonuçlar results/ klasörüne kaydedilir
streamlit run app.py         # simülatör
```

## Dosyalar

- `src/graph.py`: rastgele graf oluşturma, Spider Trap ve Dead End ekleme
- `src/pagerank.py`: PageRank ve teleportation
- `src/hits.py`: HITS (hub / authority)
- `src/experiments.py`: deneyler ve grafikler
- `app.py`: Streamlit simülatörü
- `tests/`: testler
- `results/`: deneylerin grafik ve tabloları
- `report/Proje_Raporu.docx`: proje raporu
