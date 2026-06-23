#!/usr/bin/env python3
"""Generate the Samfunnskunnskap quiz HTML from Word (.docx) question files.

The script reads one or more .docx files where each question is a single
paragraph laid out like this::

    Hva er hovedstaden i Norge?
    A. Bergen
    B. Oslo
    C. Trondheim

The correct answer is the option whose run is **bold**. Parsed questions are
embedded as JSON into ``template.html`` and written out as a self-contained
quiz page.

Quiz rules:
    * Prøve 1   : the first N questions of the first file, in order.
    * Tilfeldig : N random questions drawn from all files (shuffled at runtime).

Usage:
    python3 generate_quiz.py
    python3 generate_quiz.py --files a.docx b.docx --prove1-count 40 --output quiz.html
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger("quiz")

# ─── Defaults ────────────────────────────────────────────────────────────────
DEFAULT_FILES = ["familie helse.docx", "Norge.docx", "utanding.docx"]
DEFAULT_TEMPLATE = "template.html"
DEFAULT_OUTPUT = "samfunnskunnskap_quiz.html"
DEFAULT_COUNT = 36

# A correct option is a bold run that starts with "A.", "B." or "C."
_OPTION_LETTER = re.compile(r"\s*([A-C])\.")
_SPLIT_OPTIONS = re.compile(r"\n\s*(?=[A-C]\.)")
_OPTION_BODY = re.compile(r"^([A-C])\.\s*(.+)", re.DOTALL)
_HEADING = re.compile(r"^Spørsmål\s+\d+$", re.IGNORECASE)


@dataclass(frozen=True)
class Question:
    """A single multiple-choice question."""

    q: str
    opts: list[str]
    correct: int  # index into ``opts`` of the correct answer

    def as_dict(self) -> dict:
        return {"q": self.q, "opts": self.opts, "correct": self.correct}


def parse_docx(path: Path) -> list[Question]:
    """Parse a .docx file into a list of :class:`Question`.

    Missing files are skipped with a warning so a partial run still works.
    """
    try:
        import docx  # python-docx
    except ImportError:
        sys.exit("HATA: python-docx kurulu değil. Çalıştır: pip install python-docx")

    if not path.exists():
        logger.warning("'%s' bulunamadı, atlanıyor.", path)
        return []

    questions: list[Question] = []
    for paragraph in docx.Document(str(path)).paragraphs:
        text = paragraph.text.strip()
        if not text or _HEADING.match(text):
            continue
        if "\nA." not in text and "\n A." not in text:
            continue

        parts = _SPLIT_OPTIONS.split(text)
        if len(parts) < 2:
            continue

        # The correct answer is the first bold run starting with a letter.
        correct_letter = next(
            (
                m.group(1)
                for run in paragraph.runs
                if run.bold and (m := _OPTION_LETTER.match(run.text))
            ),
            None,
        )
        if correct_letter is None:
            continue

        options: list[tuple[str, str]] = []
        for raw in parts[1:]:
            if m := _OPTION_BODY.match(raw.strip()):
                options.append((m.group(1), m.group(2).strip()))
        if len(options) < 2:
            continue

        correct_idx = next(
            (i for i, (letter, _) in enumerate(options) if letter == correct_letter),
            0,
        )
        questions.append(
            Question(q=parts[0].strip(), opts=[text for _, text in options], correct=correct_idx)
        )

    return questions


def render(template: str, files: dict[str, list[Question]], prove1: int, random: int) -> str:
    """Inject question data and counts into the template."""
    data = {key: [q.as_dict() for q in qs] for key, qs in files.items()}
    return (
        template.replace("__QUIZ_DATA__", json.dumps(data, ensure_ascii=False))
        .replace("__PROVE1_COUNT__", str(prove1))
        .replace("__RANDOM_COUNT__", str(random))
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--files", nargs="+", default=DEFAULT_FILES,
                        help="Soru kaynağı .docx dosyaları (ilk dosya Prøve 1 için kullanılır).")
    parser.add_argument("--template", default=DEFAULT_TEMPLATE, help="HTML şablon dosyası.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Üretilecek HTML dosyası.")
    parser.add_argument("--prove1-count", type=int, default=DEFAULT_COUNT,
                        help="Prøve 1'deki soru sayısı.")
    parser.add_argument("--random-count", type=int, default=DEFAULT_COUNT,
                        help="Tilfeldig prøve'deki rastgele soru sayısı.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Ayrıntılı log.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")

    template_path = Path(args.template)
    if not template_path.exists():
        sys.exit(f"HATA: şablon bulunamadı: {template_path}")

    files = {f"f{i}": parse_docx(Path(name)) for i, name in enumerate(args.files, start=1)}
    total = sum(len(qs) for qs in files.values())
    for name, (_, qs) in zip(args.files, files.items()):
        logger.info("  ✅ %-22s %3d soru", name, len(qs))
    logger.info("  📊 Toplam: %d soru", total)

    prove1 = min(args.prove1_count, len(files["f1"]))
    if len(files["f1"]) < args.prove1_count:
        logger.warning("  ⚠️  Dosya 1'de %d soru var; Prøve 1 %d soruyla oluşturulacak.",
                       len(files["f1"]), prove1)

    html = render(template_path.read_text(encoding="utf-8"), files, prove1, args.random_count)
    Path(args.output).write_text(html, encoding="utf-8")
    logger.info("\n✅ HTML oluşturuldu: %s", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
