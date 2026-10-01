#!/usr/bin/env python3
"""Audit localized exercise-name catalogs for fallback and composition hazards."""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# ASCII source-token scan is deliberately separate from duplicate detection;
# the latter must also handle scripts such as Devanagari and Han.
TOKEN = re.compile(r"[A-Za-z][A-Za-z'-]*")
SUSPICIOUS = {
    "and", "behind", "from", "head", "machine", "multiple", "neck", "off", "of",
    "release", "response", "run", "single", "standing", "the", "to", "two", "version",
    "with", "without",
}
ALLOWED_LOANWORDS = {
    "arnold", "band", "bench", "cable", "clean", "conan", "curl", "deadlift", "dip", "ez", "fly",
    "good", "grip", "hammer", "hip", "jackknife", "jerk", "kettlebell", "machine", "pallof", "press",
    "pullover", "rocky", "row", "skull", "smith", "snatch", "squat", "stretch", "trx", "twist",
}
DUPLICATE_STOPWORDS = {
    "a", "à", "al", "and", "au", "aux", "avec", "com", "con", "da", "das", "de", "del", "der",
    "des", "die", "do", "dos", "du", "e", "el", "en", "et", "im", "in", "la", "le", "les", "mit",
    "na", "no", "o", "para", "por", "pour", "sur", "the", "um", "und", "un", "una",
    "в", "во", "для", "и", "из", "на", "от", "по", "с", "со",
}


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold())


def words(value: str) -> list[str]:
    """Return whitespace-delimited Unicode words without splitting scripts."""
    result = []
    for raw in re.split(r"[\s/(),]+", value.casefold()):
        cleaned = "".join(
            char for char in raw
            if unicodedata.category(char).startswith("L")
            or unicodedata.category(char).startswith("M")
            or char in "'-’"
        ).strip("'-’")
        if cleaned:
            result.append(cleaned)
    return result


def audit(root: Path) -> tuple[str, int]:
    db = json.loads((root / "free-exercise-db-plusplus.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "translations/locale-manifest.json").read_text(encoding="utf-8"))
    lines = ["# Localized exercise-name audit", "", "This report is generated from the checked-in catalogs.", ""]
    total_flags = 0
    for locale in manifest["supportedLocales"]:
        if locale == "en":
            continue
        catalog = json.loads((root / manifest["catalogs"][locale]).read_text(encoding="utf-8"))
        flags = []
        untranslated = []
        unchanged = []
        counts = {"reviewed": 0, "provisional": 0, "untranslated": 0}
        for exercise_id, entry in catalog["exercises"].items():
            status = entry["reviewStatus"]
            counts[status] += 1
            source = db["exercises"][exercise_id]["source"]["name"]
            if status != "untranslated" and norm(entry["preferred"]) == norm(source):
                unchanged.append((exercise_id, entry["preferred"]))
            if status == "untranslated":
                untranslated.append((exercise_id, entry["preferred"]))
                if norm(entry["preferred"]) != norm(source):
                    flags.append((exercise_id, "untranslated-status-mismatch", entry["preferred"]))
                continue
            source_tokens = {token.casefold() for token in TOKEN.findall(source)}
            residual = []
            for token in TOKEN.findall(entry["preferred"]):
                lowered = token.casefold()
                if lowered in source_tokens and lowered in SUSPICIOUS and lowered not in ALLOWED_LOANWORDS:
                    residual.append(token)
            if residual:
                flags.append((exercise_id, "residual-English:" + ",".join(sorted(set(residual))), entry["preferred"]))
            content_words = [word for word in words(entry["preferred"]) if word not in DUPLICATE_STOPWORDS]
            if len(content_words) != len(set(content_words)) and len(content_words) >= 3:
                flags.append((exercise_id, "duplicate-token", entry["preferred"]))
        total_flags += len(flags)
        lines.append(f"## {locale}")
        lines.append("")
        lines.append(f"Counts: reviewed={counts['reviewed']}, provisional={counts['provisional']}, untranslated={counts['untranslated']}; flags={len(flags)}.")
        lines.append("")
        if flags:
            lines.append("| exerciseId | flag | preferred |")
            lines.append("|---|---|---|")
            for exercise_id, flag, preferred in flags:
                lines.append(f"| `{exercise_id}` | `{flag}` | {preferred.replace('|', '\\|')} |")
            lines.append("")
        else:
            lines.append("No automated fallback/composition flags.")
            lines.append("")
        lines.append(
            f"Unchanged spelling candidates: {len(unchanged)}. "
            "These are explicit international/proper-term candidates, not proof that a native translation is unnecessary."
        )
        lines.append("")
        if unchanged:
            lines.append("| exerciseId | unchanged preferred name |")
            lines.append("|---|---|")
            for exercise_id, preferred in unchanged:
                lines.append(f"| `{exercise_id}` | {preferred.replace('|', '\\|')} |")
            lines.append("")
        lines.append(f"Untranslated fallback entries: {len(untranslated)}. These remain English source names and require target-language review before being called localized.")
        lines.append("")
        if untranslated:
            lines.append("| exerciseId | source fallback |")
            lines.append("|---|---|")
            for exercise_id, preferred in untranslated:
                lines.append(f"| `{exercise_id}` | {preferred.replace('|', '\\|')} |")
            lines.append("")
    lines.insert(3, f"Automated flags: {total_flags}. Flags require human/native review; they are not proof of correctness.")
    return "\n".join(lines) + "\n", total_flags


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "reports/LOCALIZATION-AUDIT.md")
    parser.add_argument("--fail-on-flags", action="store_true")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report, total_flags = audit(ROOT)
    args.output.write_text(report, encoding="utf-8")
    print(args.output)
    if args.fail_on_flags and total_flags:
        raise SystemExit(f"localization audit found {total_flags} automated flags")


if __name__ == "__main__":
    main()
