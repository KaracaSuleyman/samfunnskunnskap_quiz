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
DOSYA_1 = "familie_helse_.docx"   # İlk prøve bu dosyadan alınır (ilk 40 soru)
DOSYA_2 = "Norge.docx"
DOSYA_3 = "utanding.docx"
CIKTI    = "samfunnskunnskap_quiz.html"

PROVE_1_KAC_SORU = 40   # Prøve 1'de kaç soru
RASTGELE_KAC     = 40   # Prøve 2+'de kaç rastgele soru

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


# ─── HTML TEMPLATE ───────────────────────────────────────────────────────────
HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="nb">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Samfunnskunnskap Prøve</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:'Segoe UI',Arial,sans-serif;background:#f0f4f8;color:#1a202c}}

  .header{{background:linear-gradient(135deg,#003087,#0052cc);color:#fff;padding:16px 24px;
    display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;
    box-shadow:0 2px 12px rgba(0,0,0,.2)}}
  .header-left h1{{font-size:1.1rem;font-weight:700}}
  .header-left p{{font-size:.75rem;opacity:.85;margin-top:2px}}
  .timer-box{{background:rgba(255,255,255,.15);border:2px solid rgba(255,255,255,.4);
    border-radius:10px;padding:7px 16px;text-align:center;min-width:95px}}
  .timer-label{{font-size:.62rem;opacity:.8;text-transform:uppercase;letter-spacing:1px}}
  .timer-value{{font-size:1.45rem;font-weight:700;font-variant-numeric:tabular-nums}}
  .timer-box.warning{{background:rgba(255,150,0,.3);border-color:#ff9500}}
  .timer-box.danger{{background:rgba(220,38,38,.4);border-color:#ef4444;animation:pulse 1s infinite}}
  @keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.7}}}}
  .prog-wrap{{background:rgba(255,255,255,.2);height:4px;position:absolute;bottom:0;left:0;right:0}}
  .prog-fill{{height:100%;background:#ffd700;transition:width .3s}}

  .main{{max-width:780px;margin:0 auto;padding:22px 16px 90px}}

  /* START */
  .start-screen{{background:#fff;border-radius:16px;padding:36px;text-align:center;
    box-shadow:0 4px 20px rgba(0,0,0,.08);margin-top:28px}}
  .start-screen h2{{font-size:1.7rem;color:#003087;margin-bottom:8px}}
  .subtitle{{color:#64748b;margin-bottom:16px;font-size:.95rem}}
  .mode-grid{{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:24px}}
  .mode-card{{background:#f8fafc;border:2px solid #e2e8f0;border-radius:14px;padding:18px;
    cursor:pointer;transition:all .15s;text-align:left}}
  .mode-card:hover{{border-color:#0052cc;background:#f0f4ff}}
  .mode-card.selected{{border-color:#0052cc;background:#e8f0fe}}
  .mode-icon{{font-size:1.8rem;margin-bottom:8px}}
  .mode-title{{font-weight:700;color:#1e293b;margin-bottom:4px}}
  .mode-desc{{font-size:.78rem;color:#64748b;line-height:1.5}}
  .mode-badge{{display:inline-block;background:#dcfce7;color:#166534;border-radius:20px;
    padding:3px 10px;font-size:.7rem;font-weight:700;margin-top:6px}}
  .btn-start{{background:linear-gradient(135deg,#003087,#0052cc);color:#fff;border:none;
    padding:14px 44px;border-radius:12px;font-size:1rem;font-weight:700;cursor:pointer;
    transition:all .15s;box-shadow:0 4px 14px rgba(0,82,204,.4)}}
  .btn-start:hover{{transform:translateY(-2px)}}
  .btn-start:disabled{{opacity:.4;cursor:not-allowed;transform:none}}
  .stats-info{{color:#64748b;font-size:.82rem;margin-bottom:20px}}

  /* FINISH BAR */
  #finish-bar{{display:none;position:fixed;top:0;left:0;right:0;z-index:200;
    background:linear-gradient(135deg,#16a34a,#22c55e);color:#fff;padding:14px 24px;
    align-items:center;justify-content:space-between;box-shadow:0 4px 16px rgba(0,0,0,.2)}}
  .fb-title{{font-weight:700;font-size:1rem}}
  .fb-sub{{font-size:.8rem;opacity:.9}}
  .btn-finish{{background:#fff;color:#16a34a;border:none;padding:10px 22px;
    border-radius:10px;font-weight:700;font-size:.9rem;cursor:pointer}}

  /* QUIZ */
  .q-nav{{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}}
  .q-counter{{font-size:.82rem;color:#64748b;font-weight:600}}
  .mode-tag{{background:#e0e7ff;color:#3730a3;font-size:.72rem;padding:4px 10px;
    border-radius:20px;font-weight:600}}
  .q-card{{background:#fff;border-radius:16px;padding:26px;
    box-shadow:0 2px 12px rgba(0,0,0,.07);margin-bottom:18px;animation:fadeIn .2s ease}}
  @keyframes fadeIn{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:translateY(0)}}}}
  .q-text{{font-size:1.08rem;font-weight:600;color:#1e293b;line-height:1.55;margin-bottom:20px}}

  .option{{display:flex;align-items:center;gap:12px;padding:13px 15px;border:2px solid #e2e8f0;
    border-radius:10px;margin-bottom:9px;cursor:pointer;transition:all .15s;
    font-size:.93rem;color:#334155}}
  .option:hover{{border-color:#0052cc;background:#f0f4ff}}
  .option.selected{{border-color:#0052cc;background:#e8f0fe;color:#003087;font-weight:600}}
  .option-letter{{width:27px;height:27px;border:2px solid currentColor;border-radius:50%;
    display:flex;align-items:center;justify-content:center;font-size:.75rem;font-weight:700;
    flex-shrink:0;background:#fff}}
  .option.selected .option-letter{{background:#0052cc;color:#fff;border-color:#0052cc}}

  /* RESULT */
  .result-screen{{background:#fff;border-radius:16px;padding:36px;text-align:center;
    box-shadow:0 4px 20px rgba(0,0,0,.08);margin-top:16px;animation:fadeIn .4s ease}}
  .result-score{{width:140px;height:140px;border-radius:50%;display:flex;flex-direction:column;
    align-items:center;justify-content:center;margin:0 auto 20px;font-weight:700}}
  .result-score.pass{{background:linear-gradient(135deg,#16a34a,#22c55e);color:#fff}}
  .result-score.fail{{background:linear-gradient(135deg,#dc2626,#ef4444);color:#fff}}
  .score-num{{font-size:2.5rem;line-height:1}}
  .score-label{{font-size:.72rem;opacity:.85}}
  .result-verdict{{font-size:1.4rem;font-weight:700;margin-bottom:6px}}
  .result-verdict.pass{{color:#16a34a}}
  .result-verdict.fail{{color:#dc2626}}
  .result-detail{{color:#64748b;margin-bottom:20px;font-size:.92rem}}
  .stats-row{{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;margin-bottom:20px}}
  .stat-box{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:12px 16px}}
  .st-val{{font-size:1.25rem;font-weight:700}}
  .st-lbl{{font-size:.65rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px}}
  .btn-action{{border:none;padding:12px 28px;border-radius:12px;font-size:.93rem;font-weight:700;
    cursor:pointer;transition:all .15s;margin:0 4px 10px}}
  .btn-action:hover{{transform:translateY(-2px)}}
  .btn-home{{background:linear-gradient(135deg,#003087,#0052cc);color:#fff}}
  .btn-retry{{background:linear-gradient(135deg,#16a34a,#22c55e);color:#fff}}
  .btn-review{{background:linear-gradient(135deg,#475569,#64748b);color:#fff}}

  .review-section{{margin-top:22px;text-align:left}}
  .review-section h3{{font-size:.92rem;font-weight:700;color:#1e293b;margin-bottom:12px;
    border-bottom:2px solid #e2e8f0;padding-bottom:8px}}
  .review-item{{padding:12px 14px;border-radius:10px;margin-bottom:8px;
    background:#f8fafc;border:1px solid #e2e8f0}}
  .review-item.r-wrong{{background:#fef2f2;border:1px solid #fecaca}}
  .ri-q{{font-weight:600;font-size:.86rem;margin-bottom:5px;color:#1e293b}}
  .ri-a{{font-size:.82rem;color:#475569}}
  .ri-wrong{{color:#dc2626;font-weight:600}}
  .ri-correct{{color:#16a34a;font-weight:600;margin-top:4px;display:block}}

  /* NAV */
  .bottom-nav{{position:fixed;bottom:0;left:0;right:0;background:#fff;padding:10px 20px;
    display:flex;justify-content:space-between;align-items:center;
    box-shadow:0 -2px 16px rgba(0,0,0,.1);z-index:50}}
  .btn-nav{{padding:9px 20px;border-radius:10px;border:2px solid #e2e8f0;background:#fff;
    font-size:.86rem;font-weight:600;cursor:pointer;color:#475569;transition:all .15s}}
  .btn-nav:hover:not(:disabled){{border-color:#0052cc;color:#0052cc}}
  .btn-nav:disabled{{opacity:.3;cursor:not-allowed}}
  .btn-next{{background:linear-gradient(135deg,#003087,#0052cc);color:#fff;border:none;
    padding:11px 24px;border-radius:10px;font-size:.86rem;font-weight:700;cursor:pointer;
    transition:all .15s;box-shadow:0 2px 8px rgba(0,82,204,.3)}}
  .btn-next:hover{{transform:translateY(-1px)}}
  .dots-wrap{{display:flex;gap:4px;flex-wrap:wrap;max-width:300px}}
  .dot{{width:11px;height:11px;border-radius:50%;background:#e2e8f0;cursor:pointer;transition:background .2s}}
  .dot.current{{background:#ffd700;box-shadow:0 0 0 2px #003087}}
  .dot.answered{{background:#0052cc}}

  @media(max-width:520px){{
    .mode-grid{{grid-template-columns:1fr}}
    .dots-wrap{{display:none}}
    .header{{flex-direction:column;gap:8px;text-align:center}}
  }}
</style>
</head>
<body>
<div id="app">

<!-- START -->
<div id="start-view">
  <div class="header">
    <div class="header-left">
      <h1>🇳🇴 Samfunnskunnskap Prøve</h1>
      <p>Kilde: dine egne spørsmålsfiler</p>
    </div>
  </div>
  <div class="main">
    <div class="start-screen">
      <h2>🇳🇴 Velg prøvemodus</h2>
      <p class="subtitle">Velg om du vil starte med Prøve 1 (faste spørsmål) eller ta en tilfeldig blanding</p>
      <p class="stats-info" id="pool-stats">Laster spørsmål...</p>
      <div class="mode-grid">
        <div class="mode-card selected" id="card-prove1" onclick="selectMode('prove1')">
          <div class="mode-icon">📋</div>
          <div class="mode-title">Prøve 1 — Fast</div>
          <div class="mode-desc">De første {PROVE1_COUNT} spørsmålene fra fil 1, i fast rekkefølge. Bra for å lære systematisk.</div>
          <span class="mode-badge">Anbefalt første gang</span>
        </div>
        <div class="mode-card" id="card-random" onclick="selectMode('random')">
          <div class="mode-icon">🎲</div>
          <div class="mode-title">Tilfeldig prøve</div>
          <div class="mode-desc">{RANDOM_COUNT} tilfeldige spørsmål fra alle filer. Shakes og byttes ved hvert forsøk.</div>
          <span class="mode-badge">God for repetisjon</span>
        </div>
      </div>
      <button class="btn-start" id="btn-start" onclick="startQuiz()">▶ Start prøven</button>
    </div>
  </div>
</div>

<!-- QUIZ -->
<div id="quiz-view" style="display:none">
  <div id="finish-bar">
    <div>
      <div class="fb-title">🎉 Alle spørsmål besvart!</div>
      <div class="fb-sub">Du kan avslutte nå eller endre svar.</div>
    </div>
    <button class="btn-finish" onclick="finishQuiz()">✓ Avslutt</button>
  </div>
  <div class="header">
    <div class="header-left">
      <h1>🇳🇴 Samfunnskunnskap</h1>
      <p id="q-mode-label">—</p>
    </div>
    <div class="timer-box" id="timer-box">
      <div class="timer-label">Tid igjen</div>
      <div class="timer-value" id="timer-display">60:00</div>
    </div>
    <div class="prog-wrap"><div class="prog-fill" id="prog-fill" style="width:0%"></div></div>
  </div>
  <div class="main">
    <div class="q-nav">
      <span class="q-counter" id="q-counter">Spørsmål 1 av 40</span>
      <span class="mode-tag" id="mode-tag">—</span>
    </div>
    <div class="q-card">
      <div class="q-text" id="q-text"></div>
      <div id="options-container"></div>
    </div>
  </div>
  <div class="bottom-nav">
    <div class="dots-wrap" id="dots-wrap"></div>
    <div style="display:flex;gap:8px">
      <button class="btn-nav" id="btn-prev" onclick="navigate(-1)" disabled>← Forrige</button>
      <button class="btn-next" id="btn-next">Neste →</button>
    </div>
  </div>
</div>

<!-- RESULT -->
<div id="result-view" style="display:none">
  <div class="header">
    <div class="header-left"><h1>🇳🇴 Resultater</h1><p id="result-mode-label">—</p></div>
  </div>
  <div class="main">
    <div class="result-screen">
      <div class="result-score" id="result-circle">
        <span class="score-num" id="result-num">—</span>
        <span class="score-label" id="result-denom">av 40</span>
      </div>
      <div class="result-verdict" id="result-verdict">—</div>
      <div class="result-detail" id="result-detail">—</div>
      <div class="stats-row">
        <div class="stat-box"><div class="st-val" id="st-c" style="color:#16a34a">—</div><div class="st-lbl">✅ Riktige</div></div>
        <div class="stat-box"><div class="st-val" id="st-w" style="color:#dc2626">—</div><div class="st-lbl">❌ Feil</div></div>
        <div class="stat-box"><div class="st-val" id="st-s">—</div><div class="st-lbl">⏭ Hoppet</div></div>
        <div class="stat-box"><div class="st-val" id="st-t">—</div><div class="st-lbl">⏱ Tid</div></div>
      </div>
      <button class="btn-action btn-home"  onclick="goHome()">🏠 Velg ny prøve</button>
      <button class="btn-action btn-retry" onclick="retryQuiz()">🔄 Prøv igjen</button>
      <button class="btn-action btn-review" onclick="toggleReview()">📋 Se svar</button>
      <div class="review-section" id="review-section" style="display:none">
        <h3>Gjennomgang</h3>
        <div id="review-list"></div>
      </div>
    </div>
  </div>
</div>

</div>

<script>
// ═══════════════════════════════════════════════════
//  SPØRSMÅLSDATA  (auto-generert av generate_quiz.py)
// ═══════════════════════════════════════════════════
const DATA = {DATA_JSON};

const PROVE1_COUNT  = {PROVE1_COUNT};
const RANDOM_COUNT  = {RANDOM_COUNT};
const PASS_THRESHOLD = Math.round((PROVE1_COUNT > RANDOM_COUNT ? PROVE1_COUNT : RANDOM_COUNT) * 0.65);

// ═══════════════════════════════════════════════════
//  LOGIKK
// ═══════════════════════════════════════════════════
let mode      = 'prove1';
let active    = [];
let current   = 0;
let answers   = [];
let timerRef  = null;
let sLeft     = 3600;
let startTime = null;
let reviewOpen = false;
let lastMode  = 'prove1';

// Pool info
const allQ = [...DATA.f1, ...DATA.f2, ...DATA.f3];
document.getElementById('pool-stats').textContent =
  `Totalt ${allQ.length} spørsmål: ${DATA.f1.length} fra fil 1 · ${DATA.f2.length} fra fil 2 · ${DATA.f3.length} fra fil 3`;

function selectMode(m) {{
  mode = m;
  document.getElementById('card-prove1').classList.toggle('selected', m==='prove1');
  document.getElementById('card-random').classList.toggle('selected', m==='random');
}}

function shuffle(arr) {{
  const a = [...arr];
  for (let i=a.length-1;i>0;i--) {{
    const j=Math.floor(Math.random()*(i+1));
    [a[i],a[j]]=[a[j],a[i]];
  }}
  return a;
}}

function shuffleOpts(q) {{
  const idx=[0,1,2].slice(0,q.opts.length);
  for(let i=idx.length-1;i>0;i--) {{
    const j=Math.floor(Math.random()*(i+1));
    [idx[i],idx[j]]=[idx[j],idx[i]];
  }}
  return {{...q, opts:idx.map(i=>q.opts[i]), correct:idx.indexOf(q.correct)}};
}}

function buildActive() {{
  if (mode === 'prove1') {{
    active = DATA.f1.slice(0, PROVE1_COUNT).map(shuffleOpts);
  }} else {{
    active = shuffle(allQ).slice(0, RANDOM_COUNT).map(shuffleOpts);
  }}
}}

function startQuiz() {{
  lastMode = mode;
  buildActive();
  answers  = new Array(active.length).fill(null);
  current  = 0;
  sLeft    = 3600;
  reviewOpen = false;

  const label = mode==='prove1' ? 'Prøve 1 — Fast rekkefølge (fil 1)' : 'Tilfeldig prøve — Alle filer';
  document.getElementById('q-mode-label').textContent   = label;
  document.getElementById('mode-tag').textContent       = mode==='prove1' ? '📋 Prøve 1' : '🎲 Tilfeldig';
  document.getElementById('result-mode-label').textContent = label;

  document.getElementById('start-view').style.display  = 'none';
  document.getElementById('quiz-view').style.display   = 'block';

  buildDots(); renderQ(); updateTimer();
  startTime = Date.now();
  clearInterval(timerRef);
  timerRef = setInterval(()=>{{sLeft--; updateTimer(); if(sLeft<=0){{clearInterval(timerRef);finishQuiz();}}}}, 1000);
}}

function updateTimer() {{
  const m=Math.floor(sLeft/60), s=sLeft%60;
  document.getElementById('timer-display').textContent=`${{String(m).padStart(2,'0')}}:${{String(s).padStart(2,'0')}}`;
  const b=document.getElementById('timer-box'); b.className='timer-box';
  if(sLeft<=300)b.classList.add('danger'); else if(sLeft<=600)b.classList.add('warning');
}}

function renderQ() {{
  const q=active[current];
  document.getElementById('q-counter').textContent=`Spørsmål ${{current+1}} av ${{active.length}}`;
  document.getElementById('q-text').textContent=q.q;
  document.getElementById('prog-fill').style.width=`${{((current+1)/active.length)*100}}%`;

  const L=['A','B','C'], c=document.getElementById('options-container');
  c.innerHTML='';
  q.opts.forEach((opt,i)=>{{
    const div=document.createElement('div');
    div.className='option'+(answers[current]===i?' selected':'');
    div.innerHTML=`<span class="option-letter">${{L[i]}}</span><span>${{opt}}</span>`;
    div.onclick=()=>pick(i);
    c.appendChild(div);
  }});

  document.getElementById('btn-prev').disabled=current===0;
  const bn=document.getElementById('btn-next');
  if(current===active.length-1){{bn.textContent='Avslutt ✓';bn.onclick=()=>finishQuiz();}}
  else{{bn.textContent='Neste →';bn.onclick=()=>navigate(1);}}
  updateDots();
}}

function pick(idx) {{
  answers[current]=idx; renderQ();
  document.getElementById('finish-bar').style.display=answers.every(a=>a!==null)?'flex':'none';
}}

function navigate(d) {{ current=Math.max(0,Math.min(active.length-1,current+d)); renderQ(); }}

function buildDots() {{
  const w=document.getElementById('dots-wrap'); w.innerHTML='';
  active.forEach((_,i)=>{{
    const d=document.createElement('div'); d.className='dot'; d.id=`dot-${{i}}`;
    d.onclick=()=>{{current=i;renderQ();}}; w.appendChild(d);
  }});
}}

function updateDots() {{
  active.forEach((_,i)=>{{
    const d=document.getElementById(`dot-${{i}}`); d.className='dot';
    if(i===current) d.classList.add('current');
    else if(answers[i]!==null) d.classList.add('answered');
  }});
}}

function finishQuiz() {{
  clearInterval(timerRef);
  document.getElementById('finish-bar').style.display='none';
  document.getElementById('quiz-view').style.display='none';
  document.getElementById('result-view').style.display='block';

  const correct = active.filter((q,i)=>answers[i]===q.correct).length;
  const wrong   = active.filter((q,i)=>answers[i]!==null&&answers[i]!==q.correct).length;
  const skipped = answers.filter(a=>a===null).length;
  const pass    = correct >= PASS_THRESHOLD;
  const elapsed = Math.floor((Date.now()-startTime)/1000);

  document.getElementById('result-circle').className=`result-score ${{pass?'pass':'fail'}}`;
  document.getElementById('result-num').textContent=correct;
  document.getElementById('result-denom').textContent=`av ${{active.length}}`;
  document.getElementById('result-verdict').className=`result-verdict ${{pass?'pass':'fail'}}`;
  document.getElementById('result-verdict').textContent=pass?'🎉 Bestått!':'😔 Ikke bestått';
  document.getElementById('result-detail').textContent=pass
    ?`Gratulerer! Du fikk ${{correct}} av ${{active.length}} — grensen er ${{PASS_THRESHOLD}}.`
    :`Du fikk ${{correct}} av ${{active.length}}. Du trenger minst ${{PASS_THRESHOLD}} for å bestå.`;
  document.getElementById('st-c').textContent=correct;
  document.getElementById('st-w').textContent=wrong;
  document.getElementById('st-s').textContent=skipped;
  document.getElementById('st-t').textContent=`${{Math.floor(elapsed/60)}}:${{String(elapsed%60).padStart(2,'0')}}`;

  buildReview();
}}

function buildReview() {{
  const L=['A','B','C'], list=document.getElementById('review-list'); list.innerHTML='';
  active.forEach((q,i)=>{{
    const sk=answers[i]===null;
    const div=document.createElement('div');
    div.className='review-item';
    const answerText = sk
      ? '⏭ Hoppet over'
      : `${{L[answers[i]]}}. ${{q.opts[answers[i]]}}`;
    div.innerHTML=`<div class="ri-q">${{i+1}}. ${{q.q}}</div>
      <div class="ri-a">${{answerText}}</div>`;
    list.appendChild(div);
  }});
}}

function toggleReview() {{
  reviewOpen=!reviewOpen;
  document.getElementById('review-section').style.display=reviewOpen?'block':'none';
}}

function goHome() {{
  clearInterval(timerRef);
  document.getElementById('result-view').style.display='none';
  document.getElementById('start-view').style.display='block';
}}

function retryQuiz() {{
  mode=lastMode; startQuiz();
}}
</script>
</body>
</html>
"""


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