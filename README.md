# 🇳🇴 Samfunnskunnskap Prøve

[![Build apps](https://github.com/KaracaSuleyman/samfunnskunnskap_quiz/actions/workflows/build.yml/badge.svg)](https://github.com/KaracaSuleyman/samfunnskunnskap_quiz/actions/workflows/build.yml)

A desktop quiz app for preparing for the Norwegian **samfunnskunnskap** (social studies) test. One single file — no installation, no internet, no browser needed. Just double-click and start.

---

## ✨ Features

- 📋 **Prøve 1 — Fast:** The first 36 questions from the first file, in fixed order. Great for studying systematically.
- 🎲 **Tilfeldig prøve:** 36 random questions from all files, reshuffled every time. Ideal for revision.
- ⏱️ Timed exam mode (warns you as time runs low).
- ✅ Instant scoring and a results screen.
- 📦 **Fully offline** — the questions are embedded inside the app; no extra files to carry around.

---

## ⬇️ Download & Run

Download the latest build from the [**Releases**](https://github.com/KaracaSuleyman/samfunnskunnskap_quiz/releases) page — no GitHub account needed, and the files never expire.

### 🪟 Windows
1. Download **`SamfunnskunnskapQuiz.exe`**.
2. Double-click it.
3. If you see *"Windows protected your PC"* on first launch: **More info → Run anyway**. (Normal, since the app is unsigned.)

### 🍎 macOS
1. Download **`SamfunnskunnskapQuiz-macOS.zip`** and unzip it → **`SamfunnskunnskapQuiz.app`**.
2. On first launch, **right-click → Open** (Gatekeeper asks once because the app is unsigned).

---

## 🛠️ Build it yourself (for developers)

[GitHub Actions](.github/workflows/build.yml) builds the Windows `.exe` and macOS `.app` and attaches them to a **GitHub Release** whenever a version tag is pushed:

```bash
git tag v1.0.0
git push origin v1.0.0
```

To build locally instead:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# macOS (.app)
pyinstaller --noconfirm --windowed \
  --name SamfunnskunnskapQuiz \
  --add-data "samfunnskunnskap_quiz.html:." app.py

# Windows (.exe) — use ";" instead of ":" as the separator
pyinstaller --noconfirm --windowed --onefile \
  --name SamfunnskunnskapQuiz \
  --add-data "samfunnskunnskap_quiz.html;." app.py
```

The output lands in the `dist/` folder.

> ℹ️ You can't build a Windows `.exe` on macOS (or vice versa). Use GitHub Actions for both platforms.

---

## 🔄 Regenerate the quiz from the `.docx` sources

The questions live in Word files; `generate_quiz.py` parses them and injects the
data into `template.html` to produce `samfunnskunnskap_quiz.html`. The correct
answer of each question is the option marked **bold** in the document.

```bash
pip install -r requirements-dev.txt   # python-docx
python3 generate_quiz.py              # uses the default files & counts
python3 generate_quiz.py --help       # files, output, question counts, ...
```

---

## 📁 Project structure

| File | Description |
|------|-------------|
| `*.docx` | **Source of truth** — the question texts (correct answer = bold option). |
| [`generate_quiz.py`](generate_quiz.py) | Parses the `.docx` files and renders the quiz HTML from the template. |
| [`template.html`](template.html) | HTML/CSS/JS shell with `__QUIZ_DATA__` / count placeholders. |
| [`samfunnskunnskap_quiz.html`](samfunnskunnskap_quiz.html) | **Generated** self-contained quiz (questions embedded as JSON). |
| [`app.py`](app.py) | A tiny [pywebview](https://pywebview.flowrl.com/) wrapper that opens the quiz in a window. |
| [`requirements.txt`](requirements.txt) | App/runtime deps: `pywebview` + `pyinstaller`. |
| [`requirements-dev.txt`](requirements-dev.txt) | Tooling dep for regenerating the quiz: `python-docx`. |
| [`.github/workflows/build.yml`](.github/workflows/build.yml) | CI that automates the Windows + macOS builds. |

---

Made by **Suleyman Karaca** · 2026
