#!/usr/bin/env python3
"""
Samfunnskunnskap Quiz Generator
================================
Bu script 3 adet .docx dosyasını okur ve bir HTML quiz dosyası oluşturur.

KULLANIM:
    python3 generate_quiz.py

DOSYA FORMATI (docx):
    - Her soru bir paragraf
    - Şıklar: A. ... B. ... C. ...  (aynı paragraf içinde, yeni satırla)
    - Doğru cevap: Bold (kalın) olarak işaretlenmiş şık

PRØVE KURALLARI:
    - Prøve 1  : Dosya 1'in İLK 40 sorusu (sıralı)
    - Prøve 2+ : Tüm dosyalardan RASTGELE 40 soru (her seferinde farklı)
"""

import os, re, json, random, sys
from pathlib import Path

# ─── AYARLAR ────────────────────────────────────────────────────────────────
DOSYA_1 = "familie helse.docx"   # İlk prøve bu dosyadan alınır (ilk 40 soru)
DOSYA_2 = "Norge.docx"
DOSYA_3 = "utanding.docx"
CIKTI    = "samfunnskunnskap_quiz.html"

PROVE_1_KAC_SORU = 36   # Prøve 1'de kaç soru
RASTGELE_KAC     = 36   # Prøve 2+'de kaç rastgele soru

# ─── DOCX PARSER ────────────────────────────────────────────────────────────
def parse_docx(filepath):
    try:
        import docx
    except ImportError:
        print("HATA: python-docx kurulu değil.")
        print("Çalıştır: pip install python-docx")
        sys.exit(1)

    if not Path(filepath).exists():
        print(f"UYARI: '{filepath}' bulunamadı, atlanıyor.")
        return []

    doc = docx.Document(filepath)
    questions = []

    for p in doc.paragraphs:
        text = p.text.strip()
        if not text:
            continue
        # "Spørsmål N" başlıklarını atla
        if re.match(r'^Spørsmål\s+\d+$', text, re.IGNORECASE):
            continue
        # En az bir şık olmalı
        if '\n A.' not in text and '\nA.' not in text:
            continue

        # Soru + şıkları ayır
        parts = re.split(r'\n\s*(?=[A-C]\.)', text)
        if len(parts) < 2:
            continue

        q_text   = parts[0].strip()
        opts_raw = parts[1:]

        # Bold run → doğru cevap
        correct_letter = None
        for run in p.runs:
            if run.bold:
                m = re.match(r'\s*([A-C])\.', run.text)
                if m:
                    correct_letter = m.group(1)
                    break

        if not correct_letter:
            continue

        opts = []
        for opt in opts_raw:
            m = re.match(r'^([A-C])\.\s*(.+)', opt.strip(), re.DOTALL)
            if m:
                opts.append({'letter': m.group(1), 'text': m.group(2).strip()})

        if len(opts) < 2:
            continue

        correct_idx = next((i for i, o in enumerate(opts) if o['letter'] == correct_letter), 0)
        questions.append({
            'q':       q_text,
            'opts':    [o['text'] for o in opts],
            'correct': correct_idx,
        })

    return questions


# ─── ANA FONKSİYON ──────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  Samfunnskunnskap Quiz Generator")
    print("=" * 55)

    print(f"\n📂 Dosyalar okunuyor...")
    f1 = parse_docx(DOSYA_1)
    f2 = parse_docx(DOSYA_2)
    f3 = parse_docx(DOSYA_3)

    total = len(f1) + len(f2) + len(f3)
    print(f"  ✅ {DOSYA_1}: {len(f1)} soru")
    print(f"  ✅ {DOSYA_2}: {len(f2)} soru")
    print(f"  ✅ {DOSYA_3}: {len(f3)} soru")
    print(f"  📊 Toplam: {total} soru")

    prove1_count = min(PROVE_1_KAC_SORU, len(f1))
    random_count = RASTGELE_KAC

    if len(f1) < PROVE_1_KAC_SORU:
        print(f"\n  ⚠️  UYARI: Dosya 1'de {len(f1)} soru var, Prøve 1 için {PROVE_1_KAC_SORU} gerekiyor.")
        print(f"     Prøve 1 sadece {prove1_count} soruyla oluşturulacak.")

    data_json = json.dumps({"f1": f1, "f2": f2, "f3": f3}, ensure_ascii=False)

    html = HTML_TEMPLATE \
        .replace("{DATA_JSON}", data_json) \
        .replace("{PROVE1_COUNT}", str(prove1_count)) \
        .replace("{RANDOM_COUNT}", str(random_count)) \
        .replace("{{", "{") \
        .replace("}}", "}")

    with open(CIKTI, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\n✅ HTML oluşturuldu: {CIKTI}")
    print(f"\n📌 Nasıl çalışır?")
    print(f"   Prøve 1 : Dosya 1'den ilk {prove1_count} soru (sıralı)")
    print(f"   Tilfeldig: Tüm {total} sorudan rastgele {random_count} soru")
    print(f"\n🌐 Tarayıcıda aç: {CIKTI}")
    print("=" * 55)


if __name__ == "__main__":
    main()