# Web Link Analysis – Proje 4.3

PageRank ve HITS algoritmalarıyla sentetik web bağlantı grafiği analizi.

## Gereksinimler
- Python 3.10 veya üzeri
- Visual Studio Code
- `requirements.txt` içindeki Python paketleri

## Windows PowerShell ile kurulum

Proje klasöründe terminal açın ve sırayla çalıştırın:

```powershell
py -3 --version
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pytest -q
```

PowerShell sanal ortam etkinleştirmeyi engellerse, yalnızca açık olan terminal oturumu için şu komutu çalıştırın:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

VS Code'da `Ctrl+Shift+P` → `Python: Select Interpreter` → proje içindeki `.venv` yorumlayıcısını seçin.

## Kullanım

```powershell
python -m pytest -q            # otomatik testler
python -m src.experiments      # deneyleri çalıştırır, results/ klasörüne grafik ve tablo yazar
streamlit run app.py           # Link Analizi Simülatörü
python report/build_report.py  # report/Proje_Raporu.docx dosyasını üretir
```

## Proje yapısı

- `src/graph.py`: sentetik web grafikleri, komşuluk matrisi, Spider Trap / Dead End ekleme
- `src/pagerank.py`: PageRank (Power Iteration), teleportation, Dead End yönetimi
- `src/hits.py`: HITS hub/authority (birim L2 norm)
- `src/experiments.py`: deney senaryoları, grafikler ve networkx doğrulaması
- `app.py`: Streamlit Link Analizi Simülatörü
- `tests/`: otomatik testler
- `results/`: üretilen grafik ve tablolar
- `report/`: Word raporu ve raporu üreten betik

## Deneyler

1. **Spider Trap etkisi:** tuzaktaki 3 düğümün PageRank payı (α = 0.50, 0.85, 0.99).
2. **Spider Trap çözümü:** α taraması; teleportation tuzağın payını sınırlar.
3. **Dead End:** rank kütlesi sızıntısı ve tekdüze yeniden dağıtım çözümü.
4. **α ve yakınsama hızı:** α büyüdükçe iterasyon sayısı artar.
5. **HITS:** en yüksek hub ve authority skorları, yakınsama.

Hazırlayan: Ali Cömert (21YÖBİ1042) – bireysel proje.
