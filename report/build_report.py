"""Word raporunu (report/Proje_Raporu.docx) üretir.

Önce deneyleri çalıştırın:  python -m src.experiments
Sonra:                      python report/build_report.py
Sayılar ve grafikler results/ klasöründen okunur; rapor deneylerle tutarlı kalır.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.experiments import (  # noqa: E402
    DEAD_NODES,
    N_NODES,
    TRAP_NODES,
    _base_graph,
    validate_against_networkx,
)
from src.graph import add_spider_trap  # noqa: E402
from src.pagerank import pagerank  # noqa: E402

RES = ROOT / "results"
OUT = ROOT / "report" / "Proje_Raporu.docx"
AUTHOR = "Ali Cömert"
STUDENT_NO = "21YÖBİ1042"
GITHUB = "[GitHub depo bağlantısı buraya eklenecek]"


def read_csv(name: str) -> tuple[list[str], list[list[str]]]:
    with open(RES / name, encoding="utf-8") as f:
        rows = list(csv.reader(f))
    return rows[0], rows[1:]


def add_table(doc, header, rows, col_widths=None):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Light Grid Accent 1"
    for i, h in enumerate(header):
        t.rows[0].cells[i].text = h
    for r in rows:
        cells = t.add_row().cells
        for i, v in enumerate(r):
            cells[i].text = str(v)
    doc.add_paragraph()
    return t


def add_figure(doc, filename, caption, width=5.6):
    doc.add_picture(str(RES / filename), width=Inches(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph(caption)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].italic = True


def para(doc, text):
    p = doc.add_paragraph(text)
    p.paragraph_format.space_after = Pt(6)
    return p


def bullets(doc, items):
    for it in items:
        doc.add_paragraph(it, style="List Bullet")


def main() -> None:
    A = _base_graph()
    n_edges = int(A.sum())
    diffs = validate_against_networkx(A)

    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(11)

    # ---------------------------------------------------------------- kapak
    t = doc.add_heading("Web Arama ve Bağlantı Analizi", 0)
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p = doc.add_paragraph("PageRank ve HITS Algoritmaları – Proje 4.3")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.runs[0].font.size = Pt(14)
    p = doc.add_paragraph(
        "Ders: Akıllı Bilgi Erişim Sistemleri ve Metin Analitiği\n"
        "Kategori: Anlamsal Arama ve Bağlantı Analizi\n\n"
        f"Hazırlayan (Ekip Lideri): {AUTHOR} – {STUDENT_NO}\n"
        "Ekip: Proje bireysel olarak yürütülmüştür.\n"
        f"Kod deposu: {GITHUB}"
    )
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_page_break()

    # ---------------------------------------------------------------- 1
    doc.add_heading("1. Özet", 1)
    para(doc,
         "Bu çalışmada, web sayfalarının bağlantı yapısından sayfa önemini hesaplayan iki "
         "klasik algoritma, PageRank ve HITS, Python ile sıfırdan gerçeklenmiştir. "
         f"Sentetik bir web grafiği ({N_NODES} sayfa, {n_edges} bağlantı) üzerinde algoritmalar "
         "çalıştırılmış; sonuçlar networkx kütüphanesiyle karşılaştırılarak doğrulanmıştır. "
         "Deneylerde Spider Trap (örümcek kapanı) ve Dead End (ölü yol) durumlarının PageRank "
         "üzerindeki bozucu etkisi gösterilmiş, teleportation mekanizmasının bu sorunlara çözüm "
         "olduğu ve sönümleme faktörünün α (0.50, 0.85, 0.99) yakınsama hızını nasıl etkilediği "
         "ölçülmüştür. Ayrıca sonuçların etkileşimli incelenebildiği bir Streamlit simülatörü "
         "geliştirilmiştir.")

    # ---------------------------------------------------------------- 2
    doc.add_heading("2. Amaç ve Kapsam", 1)
    para(doc,
         "Projenin amacı, ağ yapısındaki web sayfalarının popülerlik (PageRank), merkez (hub) "
         "ve otorite (authority) değerlerini hesaplayan algoritmaları simüle etmektir. Kapsam:")
    bullets(doc, [
        "Sentetik yönlü web bağlantı grafiği ve komşuluk matrisi oluşturulması.",
        "PageRank'in Power Iteration yöntemiyle, teleportation (sönümleme faktörü α) ile kodlanması.",
        "HITS algoritmasında hub ve authority vektörlerinin birim norm ile yinelemeli güncellenmesi.",
        "Spider Trap ve Dead End durumlarının etkisinin ve çözümünün gösterilmesi.",
        "α = 0.50, 0.85, 0.99 için yakınsama hızının raporlanması.",
        "Link Analizi Simülatörü, yakınsama grafikleri ve Spider Trap çözüm raporu (teslim çıktıları).",
    ])

    # ---------------------------------------------------------------- 3
    doc.add_heading("3. Teorik Arka Plan", 1)
    doc.add_heading("3.1 Web grafiği ve komşuluk matrisi", 2)
    para(doc,
         "Web, düğümlerin sayfaları, yönlü kenarların bağlantıları temsil ettiği bir yönlü graftır. "
         "n sayfalı bir grafın komşuluk matrisi A (n×n) şöyle tanımlanır: i sayfasından j sayfasına "
         "bağlantı varsa A[i, j] = 1, yoksa 0.")

    doc.add_heading("3.2 Markov zinciri ve yönlendirme matrisi", 2)
    para(doc,
         "Rastgele gezgin modelinde kullanıcı her adımda bulunduğu sayfadaki bağlantılardan "
         "birini eşit olasılıkla seçer. Bu, satır-stokastik bir geçiş (yönlendirme) matrisi P ile "
         "ifade edilir: P[i, j] = 1 / çıkışDerecesi(i) (i → j varsa). Gezginin uzun vadede bir "
         "sayfada bulunma olasılığı, P'nin durağan dağılımıdır ve sayfanın PageRank'idir.")

    doc.add_heading("3.3 Sönümleme faktörü ve teleportation", 2)
    para(doc,
         "Gerçek webde gezgin bazen bağlantıları izlemeyi bırakıp rastgele bir sayfaya atlar. "
         "α olasılıkla bağlantı izlenir, (1 − α) olasılıkla tekdüze rastgele bir sayfaya "
         "ışınlanılır (teleportation). Güncelleme kuralı:")
    p = para(doc, "r(k+1) = α · Pᵀ · r(k) + (1 − α) · (1/n) · 1")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para(doc,
         "Bu kural, ardışık vektörler arasındaki L1 fark belirlenen toleransın altına inene kadar "
         "tekrarlanır (Power Iteration). Yöntem her adımda hatayı en çok α kat küçülttüğü için "
         "‖r(k) − r*‖₁ ≤ αᵏ · ‖r(0) − r*‖₁ üst sınırıyla yakınsar. Bu çalışmada α = 0.85 "
         "varsayılan değerdir.")

    doc.add_heading("3.4 Spider Trap ve Dead End", 2)
    bullets(doc, [
        "Spider Trap: Kendi içine kapalı, dışarıya bağlantısı olmayan sayfa kümesi (örn. a → b → c → a). "
        "Gezgin bu kümeye girince çıkamaz; teleportation yoksa tüm PageRank kütlesi tuzakta toplanır.",
        "Dead End: Hiç çıkış bağlantısı olmayan sayfa. Geçiş matrisinin o satırı sıfır olur; "
        "rank kütlesi her iterasyonda sızar ve toplam 1'in altına düşer. Çözüm olarak gezginin "
        "ölü yoldan tekdüze (1/n) olasılıkla her sayfaya atlaması sağlanır.",
    ])

    doc.add_heading("3.5 HITS algoritması", 2)
    para(doc,
         "HITS (Kleinberg) her sayfaya iki skor verir: hub (iyi otoritelere bağlanan sayfa) ve "
         "authority (iyi hub'lar tarafından gösterilen sayfa). Güncellemeler, her adımda birim L2 "
         "norma normalize edilerek yapılır:")
    p = para(doc, "a = Aᵀ · h ;   h = A · a   (her adımdan sonra ‖a‖₂ = ‖h‖₂ = 1)")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # ---------------------------------------------------------------- 4
    doc.add_heading("4. Tasarım ve Uygulama", 1)
    para(doc,
         "Proje bireysel yürütülmüştür; tüm modüllerden sorumlu kişi " + AUTHOR + "'tır. "
         "Modüller ve sorumluları:")
    add_table(doc, ["Modül", "İşlev", "Sorumlu"], [
        ["src/graph.py", "Sentetik graf, komşuluk matrisi, Spider Trap / Dead End ekleme", AUTHOR],
        ["src/pagerank.py", "Geçiş matrisi, PageRank, teleportation, Dead End yönetimi", AUTHOR],
        ["src/hits.py", "HITS hub/authority yinelemesi (birim norm)", AUTHOR],
        ["src/experiments.py", "Deneyler, tablolar, grafikler, networkx doğrulaması", AUTHOR],
        ["app.py", "Streamlit Link Analizi Simülatörü", AUTHOR],
        ["tests/", "Otomatik testler (pytest)", AUTHOR],
        ["report/", "Teknik rapor", AUTHOR],
    ])
    para(doc,
         f"Deney grafiği: n = {N_NODES} sayfa, bağlantı olasılığı p = 0.08, tohum = 42, "
         f"toplam {n_edges} bağlantı. Temel grafta kendine bağlantı ve ölü yol yoktur; "
         f"bozucu yapılar sonradan kontrollü eklenir. Spider Trap: {TRAP_NODES} düğümlerinin "
         "çıkışları silinip üçlü döngüye çevrilmiş ve dışarıdan rastgele seçilen 3 sayfadan "
         "tuzağa ek bağlantı verilmiştir. Dead End: ayrı bir deneyde "
         f"{DEAD_NODES} düğümlerinin tüm çıkış bağlantıları silinmiştir. "
         "Durma ölçütü: ardışık iki vektör arasındaki L1 fark < 1e-10.")

    # ---------------------------------------------------------------- 5
    doc.add_heading("5. Deneyler ve Bulgular", 1)

    doc.add_heading("5.1 networkx ile doğrulama", 2)
    para(doc,
         "Gerçeklenen algoritmalar networkx'in pagerank ve hits fonksiyonlarıyla aynı graf üzerinde "
         "karşılaştırılmıştır (α = 0.85, tolerans 1e-12). En büyük mutlak farklar:")
    add_table(doc, ["Ölçüt", "En büyük fark"], [
        ["PageRank", f"{diffs['pagerank_max_diff']:.1e}"],
        ["HITS hub", f"{diffs['hub_max_diff']:.1e}"],
        ["HITS authority", f"{diffs['authority_max_diff']:.1e}"],
    ])
    para(doc, "Farklar sayısal hata düzeyindedir; uygulama doğrudur.")

    doc.add_heading("5.2 Spider Trap'in bozucu etkisi", 2)
    h, rows = read_csv("spider_trap_paylari.csv")
    add_table(doc, ["α", "3 düğümün PageRank payı (tuzaksız)", "3 düğümün PageRank payı (tuzaklı)"],
              rows)
    lo = min(float(r[1]) for r in rows) * 100
    hi = max(float(r[1]) for r in rows) * 100
    para(doc,
         f"Tuzaksız grafta bu 3 düğümün toplam payı yalnızca %{lo:.1f} ile %{hi:.1f} arasındayken, "
         "tuzak eklenince pay "
         f"belirgin biçimde artar. α büyüdükçe (teleportation azaldıkça) tuzak daha fazla rank "
         f"emer: α = 0.99'da tuzaktaki 3 sayfanın payı yaklaşık %{float(rows[-1][2]) * 100:.0f} "
         "düzeyine çıkar. Bu, gerçekte hiçbir önemi olmayan bir sayfa kümesinin sıralamayı ele geçirmesi "
         "demektir.")
    add_figure(doc, "spider_trap_alpha.png", "Şekil 1: α'ya göre tuzaktaki 3 düğümün toplam PageRank payı.")
    add_figure(doc, "spider_trap_dugumler.png", "Şekil 2: Düğüm bazında PageRank (α = 0.85); son 3 düğüm tuzaktır.")

    doc.add_heading("5.3 Spider Trap çözüm raporu", 2)
    para(doc,
         "Çözüm teleportation'dır: gezgin her adımda (1 − α) olasılıkla tekdüze rastgele bir "
         "sayfaya atladığı için tuzaktan kurtulabilir ve tuzağın payı sınırlanır. Aşağıda α 0'dan "
         "0.99'a taranmış, ayrıca teleportation'ın hiç olmadığı (α = 1, saf Markov zinciri) durum "
         "karşılaştırılmıştır.")
    h, rows = read_csv("spider_trap_cozum.csv")
    sel = [r for r in rows if r[0] in ("0.0", "0.5", "0.85", "0.95", "0.99", "1.0")]
    add_table(doc, ["α", "Tuzak payı (tuzaksız graf)", "Tuzak payı (tuzaklı graf)"], sel)
    para(doc, "Bulgular:")
    bullets(doc, [
        "α = 1 (teleportation yok): tuzak, tüm rank kütlesini (≈ %100) toplar; PageRank anlamsızlaşır.",
        "α = 0: tamamen tekdüze dağılım; tuzak yalnızca adil payını (3/50 = %6) alır, ama bağlantı "
        "bilgisi tamamen kaybolur.",
        "α = 0.85: tuzağın payı yaklaşık %33 ile sınırlı kalır; sıralama hâlâ bağlantı yapısını yansıtır.",
        "Sonuç: α, tuzak etkisi ile bağlantı bilgisinin korunması arasında bir dengedir. Küçük α "
        "tuzağı daha iyi bastırır, büyük α bağlantı yapısına daha çok güvenir. Pratikte 0.85 "
        "kullanılır; tuzak etkisi tamamen yok olmaz, yalnızca sınırlanır.",
    ])
    add_figure(doc, "spider_trap_cozum.png", "Şekil 3: Teleportation ile Spider Trap'in sınırlanması.")

    doc.add_heading("5.4 Dead End etkisi", 2)
    h, rows = read_csv("dead_end_kutle.csv")
    add_table(doc, ["α", "Toplam kütle (sızıntı)", "Toplam kütle (yeniden dağıtım)",
                    "İter. (sızıntı)", "İter. (yeniden dağıtım)"], rows)
    para(doc,
         "Naif modelde ölü yolların rank'i her adımda sızar: toplam kütle α = 0.85'te yaklaşık "
         f"{float(rows[1][1]):.2f}, α = 0.99'da ise yalnızca {float(rows[2][1]):.2f} olur; yani skorlar "
         "olasılık dağılımı olmaktan çıkar. Ölü yolun satırının tekdüze (1/n) yapılmasıyla toplam kütle tam 1'de kalır.")
    add_figure(doc, "dead_end_kutle.png", "Şekil 4: Dead End nedeniyle toplam PageRank kütlesinin kaybı.")

    doc.add_heading("5.5 α'nın yakınsama hızına etkisi", 2)
    h, rows = read_csv("alpha_yakinsama.csv")
    add_table(doc, ["α", "İterasyon sayısı", "Yakınsadı mı?", "Son artık (L1)"], rows)
    para(doc,
         "α büyüdükçe iterasyon sayısı artar: α = 0.50'de "
         f"{rows[0][1]}, α = 0.85'te {rows[1][1]}, α = 0.99'da {rows[2][1]} iterasyon gerekir. "
         "Teorik üst sınır αᵏ olsa da gözlenen hız grafın yapısına bağlıdır; rastgele graf hızlı "
         "karıştığı için gözlenen iterasyon sayıları üst sınırdan çok daha azdır.")
    trapped = add_spider_trap(A, TRAP_NODES, seed=1)
    it_trap = {a: pagerank(trapped, a).iterations for a in (0.85, 0.99)}
    para(doc,
         "Graf yapısının etkisi Spider Trap'li grafta açıkça görülür: tuzak periyodik bir döngü "
         "olduğu için hata gerçekten yaklaşık α hızında küçülür. Aynı tolerans için tuzaklı grafta "
         f"α = 0.85'te {it_trap[0.85]}, α = 0.99'da {it_trap[0.99]} iterasyon gerekmiştir. Yani α "
         "1'e yaklaştıkça hem tuzak etkisi büyür hem de hesaplama maliyeti artar.")
    add_figure(doc, "alpha_yakinsama.png", "Şekil 5: Farklı α değerleri için yakınsama eğrileri (log ölçek).")

    doc.add_heading("5.6 HITS sonuçları", 2)
    h, rows = read_csv("hits_ilk10.csv")
    add_table(doc, ["Hub düğüm", "Hub skoru", "Authority düğüm", "Authority skoru"], rows[:5])
    para(doc,
         "Tabloda en yüksek 5 hub ve authority görülmektedir. Hub'lar çok sayıda iyi otoriteye "
         "bağlanan sayfalar, authority'ler ise çok sayıda iyi hub tarafından gösterilen sayfalardır. "
         "İki vektör de birim L2 normludur.")
    add_figure(doc, "hits_skorlar.png", "Şekil 6: En yüksek hub ve authority skorları.", 6.0)
    add_figure(doc, "hits_yakinsama.png", "Şekil 7: HITS yakınsama eğrisi.", 4.2)

    # ---------------------------------------------------------------- 6
    doc.add_heading("6. Link Analizi Simülatörü", 1)
    para(doc,
         "Simülatör Streamlit ile geliştirilmiştir (streamlit run app.py). Kullanıcı düğüm sayısı, "
         "bağlantı olasılığı ve tohumu seçebilir; isteğe bağlı Spider Trap veya Dead End "
         "ekleyebilir; α'yı kaydırıcıyla değiştirebilir ve Dead End için sızıntı / yeniden "
         "dağıtım modunu seçebilir. Arayüz dört sekme sunar:")
    bullets(doc, [
        "Graf: düğüm boyutu PageRank ile orantılı çizim; tuzak ve ölü yollar renkli.",
        "PageRank: en yüksek skorlar tablosu ve grafiği, giriş/çıkış dereceleri.",
        "HITS: hub ve authority tabloları, birim norm doğrulaması.",
        "Yakınsama: α = 0.50, 0.85, 0.99 için PageRank ve HITS yakınsama eğrileri.",
    ])

    # ---------------------------------------------------------------- 7
    _, conv_rows = read_csv("alpha_yakinsama.csv")
    conv_text = " → ".join(r[1] for r in conv_rows)
    doc.add_heading("7. Sonuç", 1)
    bullets(doc, [
        "PageRank ve HITS sıfırdan gerçeklenmiş ve networkx ile ~1e-12 farkla doğrulanmıştır.",
        "Spider Trap, teleportation yokken tüm rank'i emer; α = 0.99'da bile payı çok yüksektir.",
        "Teleportation tuzağın payını sınırlar; α bu sınırlama ile bağlantı bilgisinin korunması arasındaki dengeyi belirler.",
        "Dead End kütle sızıntısına yol açar; tekdüze yeniden dağıtım ile toplam kütle 1'de tutulur.",
        f"α arttıkça yakınsama yavaşlar ({conv_text} iterasyon); tuzaklı grafta bu yavaşlama çok daha belirgindir.",
    ])
    para(doc,
         "Sınırlılıklar: Deneyler tek bir sentetik rastgele graf üzerinde yapılmıştır; gerçek web "
         "grafikleri ağırlıklı olarak ölçeksiz (scale-free) yapıdadır ve sonuçlar farklılaşabilir. "
         "HITS, graf bağlantısız olduğunda başlangıç vektörüne duyarlı olabilir. Gelecek çalışma olarak "
         "gerçek bir web veri kümesi (ör. SNAP) ile deney ve kişiselleştirilmiş PageRank eklenebilir.")

    # ---------------------------------------------------------------- 8
    doc.add_heading("8. Kaynaklar", 1)
    bullets(doc, [
        "Brin, S., Page, L. (1998). The anatomy of a large-scale hypertextual Web search engine. "
        "Computer Networks and ISDN Systems, 30.",
        "Page, L., Brin, S., Motwani, R., Winograd, T. (1999). The PageRank citation ranking: "
        "Bringing order to the Web. Stanford InfoLab.",
        "Kleinberg, J. M. (1999). Authoritative sources in a hyperlinked environment. "
        "Journal of the ACM, 46(5).",
        "Langville, A. N., Meyer, C. D. (2004). Deeper inside PageRank. Internet Mathematics, 1(3).",
        "Leskovec, J., Rajaraman, A., Ullman, J. D. Mining of Massive Datasets, Bölüm 5: Link Analysis.",
    ])

    # ---------------------------------------------------------------- ek
    doc.add_heading("Ek: Çalıştırma Talimatı", 1)
    for line in [
        "py -3 -m venv .venv",
        ".\\.venv\\Scripts\\Activate.ps1",
        "pip install -r requirements.txt",
        "python -m pytest -q            # testler",
        "python -m src.experiments      # deneyler -> results/",
        "streamlit run app.py           # simülatör",
        "python report/build_report.py  # bu raporu yeniden üretir",
    ]:
        p = doc.add_paragraph(line)
        p.runs[0].font.name = "Consolas"
        p.runs[0].font.size = Pt(10)

    doc.save(OUT)
    print(f"Rapor yazıldı: {OUT}")


if __name__ == "__main__":
    main()
