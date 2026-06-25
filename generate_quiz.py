#!/usr/bin/env python3
"""Generate the Samfunnskunnskap quiz HTML from Word (.docx) question files.

The script reads one .docx file per curriculum topic, where each question is a
single paragraph laid out like this::

    Hva er hovedstaden i Norge?
    A. Bergen
    B. Oslo
    C. Trondheim

The correct answer is the option whose run is **bold**. Parsed questions are
embedded as JSON into ``template.html`` and written out as a self-contained
quiz page.

The quiz offers four modes, all drawing ``--count`` random questions:
    * Utdanning, kompetanse og arbeidsliv  — only that topic's file.
    * Familie, helse og hverdagsliv        — only that topic's file.
    * Norge før og nå                      — only that topic's file.
    * Blandet prøve                        — all three topics mixed together.

Usage:
    python3 generate_quiz.py
    python3 generate_quiz.py --files utanding.docx "familie helse.docx" Norge.docx --count 36
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


# ─── Topics ──────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Topic:
    """One curriculum topic and the .docx file its questions come from."""

    key: str        # stable id shared with the template (DATA key + mode id)
    title: str      # display title (official læreplan heading)
    icon: str       # emoji shown on the mode card
    filename: str   # source .docx


# Order here = display order on the start screen (left-to-right on the website).
TOPICS = [
    Topic("utdanning", "Utdanning, kompetanse og arbeidsliv", "📚", "utanding.docx"),
    Topic("familie", "Familie, helse og hverdagsliv", "👨‍👩‍👧", "familie helse.docx"),
    Topic("norge", "Norge før og nå", "🏔️", "Norge.docx"),
]

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
        sys.exit("ERROR: python-docx is not installed. Run: pip install python-docx")

    if not path.exists():
        logger.warning("'%s' not found, skipping.", path)
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


def render(template: str, topics: list[Topic], data: dict[str, list[Question]], count: int) -> str:
    """Inject question data, the per-quiz count and topic metadata into the template."""
    quiz_data = {key: [q.as_dict() for q in qs] for key, qs in data.items()}
    topics_meta = [{"key": t.key, "title": t.title, "icon": t.icon} for t in topics]
    return (
        template.replace("__QUIZ_DATA__", json.dumps(quiz_data, ensure_ascii=False))
        .replace("__TOPICS_META__", json.dumps(topics_meta, ensure_ascii=False))
        .replace("__COUNT__", str(count))
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--files",
        nargs=len(TOPICS),
        metavar="DOCX",
        default=[t.filename for t in TOPICS],
        help=f"Topic .docx files, in this order: {', '.join(t.key for t in TOPICS)}.",
    )
    parser.add_argument("--template", default=DEFAULT_TEMPLATE, help="HTML template file.")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="HTML file to generate.")
    parser.add_argument("--count", type=int, default=DEFAULT_COUNT,
                        help="Number of random questions drawn per quiz.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")

    template_path = Path(args.template)
    if not template_path.exists():
        sys.exit(f"ERROR: template not found: {template_path}")

    data = {topic.key: parse_docx(Path(name)) for topic, name in zip(TOPICS, args.files)}
    total = sum(len(qs) for qs in data.values())
    for topic in TOPICS:
        logger.info("  ✅ %-32s %3d questions", topic.title, len(data[topic.key]))
    logger.info("  📊 Total: %d questions", total)

    for topic in TOPICS:
        if len(data[topic.key]) < args.count:
            logger.warning("  ⚠️  topic «%s» has %d questions; its quiz will use %d.",
                           topic.title, len(data[topic.key]), len(data[topic.key]))

    html = render(template_path.read_text(encoding="utf-8"), TOPICS, data, args.count)
    Path(args.output).write_text(html, encoding="utf-8")
    logger.info("\n✅ HTML generated: %s", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
