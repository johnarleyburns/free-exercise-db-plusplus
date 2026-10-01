#!/usr/bin/env python3
"""Build a checked-in exercise-name catalog from domain terminology sources.

This tool is intentionally conservative: names imported from Wger remain
provisional, and names composed from the locale terminology inventory remain
provisional until a native fitness reviewer confirms them. It never labels a
mechanically translated string as reviewed.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "free-exercise-db-plusplus.json"
TRANSLATIONS = ROOT / "translations"


PROFILES: dict[str, dict[str, Any]] = {
    "es": {
        "wgerLanguage": 4,
        "phrases": {
            "barbell bench press": "press de banca con barra",
            "dumbbell bench press": "press de banca con mancuernas",
            "bench press": "press de banca",
            "barbell deadlift": "peso muerto con barra",
            "barbell full squat": "sentadilla completa con barra",
            "barbell squat": "sentadilla con barra",
            "barbell lunge": "zancada con barra",
            "barbell curl": "curl con barra",
            "dumbbell curl": "curl con mancuerna",
            "ab crunch machine": "abdominales en máquina",
            "ab roller": "rueda abdominal",
            "ab rollout": "rueda abdominal",
            "alternate hammer curl": "curl martillo alterno",
            "3/4 sit-up": "abdominales 3/4",
            "sissy squat": "sentadilla sissy",
            "shoulder press": "press de hombros",
            "chest press": "press de pecho",
            "leg press": "prensa de piernas",
            "lat pulldown": "jalón al pecho",
            "pull up": "dominada",
            "pull-up": "dominada",
            "chin up": "dominada supina",
            "chin-up": "dominada supina",
            "push up": "flexión",
            "push-up": "flexión",
            "sit up": "abdominal",
            "sit-up": "abdominal",
            "deadlift": "peso muerto",
            "front raise": "elevación frontal",
            "lateral raise": "elevación lateral",
            "rear delt raise": "elevación posterior de hombros",
            "calf raise": "elevación de talones",
            "leg extension": "extensión de piernas",
            "leg curl": "curl de piernas",
            "triceps extension": "extensión de tríceps",
            "biceps curl": "curl de bíceps",
            "good morning": "buenos días",
            "hip thrust": "empuje de cadera",
            "glute bridge": "puente de glúteos",
            "cable crossover": "cruce de poleas",
            "chest fly": "aperturas de pecho",
            "chest flyes": "aperturas de pecho",
            "reverse fly": "aperturas inversas",
            "barbell row": "remo con barra",
            "dumbbell row": "remo con mancuerna",
            "cable row": "remo en polea",
            "upright row": "remo al mentón",
            "barbell curl": "curl con barra",
            "dumbbell curl": "curl con mancuerna",
            "hammer curl": "curl martillo",
            "skull crusher": "extensión de tríceps tumbado",
            "triceps pushdown": "extensión de tríceps en polea",
            "overhead triceps extension": "extensión de tríceps por encima de la cabeza",
            "box jump": "salto al cajón",
            "jump squat": "sentadilla con salto",
            "walking lunge": "zancada caminando",
            "reverse lunge": "zancada inversa",
            "split squat": "sentadilla dividida",
            "bulgarian split squat": "sentadilla búlgara",
            "front squat": "sentadilla frontal",
            "back squat": "sentadilla trasera",
            "overhead squat": "sentadilla sobre la cabeza",
            "kettlebell swing": "balanceo con pesa rusa",
            "clean and jerk": "cargada y envión",
            "power clean": "cargada de potencia",
            "snatch": "arrancada",
            "shrug": "encogimiento de hombros",
            "side bend": "inclinación lateral",
            "russian twist": "giro ruso",
            "plank": "plancha",
            "crunch": "abdominal",
            "stretch": "estiramiento",
        },
        "words": {
            "barbell": "barra", "dumbbell": "mancuerna", "kettlebell": "pesa rusa",
            "cable": "polea", "machine": "máquina", "band": "banda elástica",
            "bands": "bandas elásticas", "bodyweight": "peso corporal", "bodyweight": "peso corporal",
            "medicine ball": "balón medicinal", "exercise ball": "fitball", "bench": "banco",
            "seated": "sentado", "standing": "de pie", "lying": "tumbado",
            "incline": "inclinado", "decline": "declinado", "close-grip": "agarre cerrado",
            "close grip": "agarre cerrado", "wide-grip": "agarre ancho", "wide grip": "agarre ancho",
            "medium grip": "agarre medio", "alternating": "alterno", "alternate": "alterno",
            "one-arm": "un brazo", "one arm": "un brazo", "two-arm": "dos brazos", "two arm": "dos brazos",
            "reverse": "inverso", "front": "frontal", "rear": "posterior", "side": "lateral",
            "rotation": "rotación", "rotations": "rotaciones", "twist": "giro", "curl": "curl",
            "extension": "extensión", "raise": "elevación", "row": "remo", "press": "press",
            "squat": "sentadilla", "lunge": "zancada", "deadlift": "peso muerto", "flyes": "aperturas",
            "fly": "aperturas", "pullover": "pullover", "pull": "tirón", "push": "empuje",
            "jump": "salto", "jumps": "saltos", "stretch": "estiramiento", "bridge": "puente",
            "clean": "cargada", "jerk": "envión", "snatch": "arrancada", "swing": "balanceo",
            "shrug": "encogimiento", "calf": "pantorrilla", "hip": "cadera", "glute": "glúteo",
            "shoulder": "hombro", "chest": "pecho", "back": "espalda", "leg": "pierna",
            "legs": "piernas", "arm": "brazo", "arms": "brazos", "ab": "abdominal", "abs": "abdominales",
            "with": "con", "from": "desde", "on": "en", "to": "a", "the": "el", "and": "y",
            "kneeling": "de rodillas", "weighted": "con peso", "overhead": "por encima de la cabeza",
            "behind the neck": "tras nuca", "behind the head": "tras la cabeza", "bent over": "inclinado",
            "power": "de potencia", "sled": "trineo", "rope": "cuerda", "split": "dividida",
            "suspended": "suspendido", "double": "doble", "single": "unilateral", "single-leg": "a una pierna",
            "high-to-low": "de alto a bajo", "flat-bench": "banco plano", "floor": "suelo", "hang": "suspensión",
            "bicep": "bíceps", "tricep": "tríceps", "deltoid": "deltoides", "heel touchers": "toques de talón",
            "renegade": "renegado", "jackknife": "navaja", "ez-bar": "barra EZ", "ez bar": "barra EZ",
            "high": "alto", "low": "bajo", "neck": "cuello", "stiff-legged": "con piernas rígidas",
            "pistol": "a una pierna", "off of": "desde", "multiple": "múltiple", "response": "respuesta",
        },
    },
    "de": {
        "wgerLanguage": 1,
        "phrases": {
            "barbell bench press": "Langhantel-Bankdrücken", "dumbbell bench press": "Kurzhantel-Bankdrücken",
            "bench press": "Bankdrücken", "shoulder press": "Schulterdrücken", "chest press": "Brustpresse",
            "leg press": "Beinpresse", "lat pulldown": "Latzug", "pull up": "Klimmzug", "pull-up": "Klimmzug",
            "chin up": "Klimmzug im Untergriff", "chin-up": "Klimmzug im Untergriff", "push up": "Liegestütz",
            "push-up": "Liegestütz", "sit up": "Sit-up", "sit-up": "Sit-up", "deadlift": "Kreuzheben",
            "front raise": "Frontheben", "lateral raise": "Seitheben", "rear delt raise": "vorgebeugtes Seitheben",
            "calf raise": "Wadenheben", "leg extension": "Beinstrecken", "leg curl": "Beinbeugen",
            "triceps extension": "Trizepsstrecken", "biceps curl": "Bizepscurl", "good morning": "Good Morning",
            "hip thrust": "Hip Thrust", "glute bridge": "Glute Bridge", "cable crossover": "Kabelzug über Kreuz",
            "chest fly": "Fliegende", "chest flyes": "Fliegende", "reverse fly": "Reverse Fly",
            "barbell row": "Langhantelrudern", "dumbbell row": "Kurzhantelrudern", "cable row": "Kabelrudern",
            "upright row": "aufrechtes Rudern", "hammer curl": "Hammercurl", "skull crusher": "French Press",
            "triceps pushdown": "Trizepsdrücken am Kabel", "overhead triceps extension": "Trizepsstrecken über Kopf",
            "box jump": "Boxsprung", "jump squat": "Sprungkniebeuge", "walking lunge": "Ausfallschritte im Gehen",
            "reverse lunge": "umgekehrter Ausfallschritt", "split squat": "Split Squat",
            "bulgarian split squat": "Bulgarische Split Squat", "front squat": "Frontkniebeuge",
            "back squat": "Kniebeuge", "overhead squat": "Overhead Squat", "kettlebell swing": "Kettlebell-Swing",
            "clean and jerk": "Umsetzen und Stoßen", "power clean": "Umsetzen", "snatch": "Reißen",
            "shrug": "Shrug", "side bend": "Seitbeugen", "russian twist": "Russian Twist", "plank": "Plank",
            "crunch": "Crunch", "stretch": "Dehnung",
        },
        "words": {
            "barbell": "Langhantel", "dumbbell": "Kurzhantel", "kettlebell": "Kettlebell", "cable": "Kabel",
            "machine": "Maschine", "band": "Band", "bands": "Bänder", "bodyweight": "Körpergewicht",
            "medicine ball": "Medizinball", "exercise ball": "Gymnastikball", "bench": "Bank",
            "seated": "sitzend", "standing": "stehend", "lying": "liegend", "incline": "Schräg",
            "decline": "negativ", "close-grip": "enger Griff", "close grip": "enger Griff",
            "wide-grip": "weiter Griff", "wide grip": "weiter Griff", "medium grip": "mittlerer Griff",
            "alternating": "abwechselnd", "alternate": "abwechselnd", "one-arm": "einarmig", "one arm": "einarmig",
            "two-arm": "beidarmig", "two arm": "beidarmig", "reverse": "umgekehrt", "front": "vorderes",
            "rear": "hinteres", "side": "seitlich", "rotation": "Rotation", "rotations": "Rotationen",
            "twist": "Drehung", "curl": "Curl", "extension": "Strecken", "raise": "Heben", "row": "Rudern",
            "press": "Drücken", "squat": "Kniebeuge", "lunge": "Ausfallschritt", "deadlift": "Kreuzheben",
            "flyes": "Fliegende", "fly": "Fliegende", "pullover": "Pullover", "pull": "Ziehen", "push": "Drücken",
            "jump": "Sprung", "jumps": "Sprünge", "stretch": "Dehnung", "bridge": "Brücke", "clean": "Umsetzen",
            "jerk": "Stoßen", "swing": "Schwingen", "calf": "Wade", "hip": "Hüfte", "glute": "Gesäß",
            "shoulder": "Schulter", "chest": "Brust", "back": "Rücken", "leg": "Bein", "legs": "Beine",
            "arm": "Arm", "arms": "Arme", "ab": "Bauch", "abs": "Bauchmuskeln", "with": "mit", "from": "aus",
            "on": "auf", "to": "zu", "the": "der", "and": "und", "kneeling": "kniend", "weighted": "mit Gewicht",
            "overhead": "über Kopf", "behind the neck": "hinter dem Nacken", "behind the head": "hinter dem Kopf",
            "bent over": "vorgebeugt", "power": "Power", "sled": "Schlitten", "rope": "Seil", "split": "geteilte",
            "suspended": "hängend", "double": "doppelt", "single": "einzeln", "single-leg": "einbeinig",
            "high-to-low": "von oben nach unten", "flat-bench": "Flachbank", "floor": "Boden", "hang": "Hängen",
            "bicep": "Bizeps", "tricep": "Trizeps", "deltoid": "Deltamuskel", "heel touchers": "Fersenberührungen",
            "renegade": "Renegade", "jackknife": "Klappmesser", "ez-bar": "SZ-Stange", "ez bar": "SZ-Stange",
            "high": "hoch", "low": "tief", "neck": "Nacken", "stiff-legged": "mit gestreckten Beinen",
            "pistol": "einbeinig", "off of": "von", "multiple": "mehrfach", "response": "Reaktion",
        },
    },
}


def normalize(value: str) -> str:
    value = value.lower().replace("–", "-").replace("—", "-")
    value = re.sub(r"[()]+", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def load_wger(path: Path | None, language: int) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    result: dict[str, str] = {}
    for exercise in data.get("results", []):
        english = [t["name"] for t in exercise.get("translations", []) if t.get("language") == 2]
        localized = [t["name"] for t in exercise.get("translations", []) if t.get("language") == language]
        for source_name in english:
            if localized and localized[0].strip():
                result[normalize(source_name)] = localized[0].strip()
    return result


def compose(source_name: str, profile: dict[str, Any], locale: str) -> str:
    text = normalize(source_name)
    for source, target in sorted(profile["phrases"].items(), key=lambda item: len(item[0]), reverse=True):
        text = re.sub(rf"\b{re.escape(source)}\b", target, text)
    for source, target in sorted(profile["words"].items(), key=lambda item: len(item[0]), reverse=True):
        text = re.sub(rf"\b{re.escape(source)}\b", target, text)
    text = re.sub(r"\s+", " ", text).strip(" -")
    text = re.sub(r"\s+-\s*", " — ", text)
    if locale == "es":
        # Spanish gym naming normally places the implement after the movement,
        # e.g. "peso muerto con barra", rather than "barra peso muerto".
        suffixes = (("barra", "con barra"), ("mancuerna", "con mancuerna"),
                    ("polea", "en polea"), ("máquina", "en máquina"),
                    ("banda elástica", "con banda elástica"))
        for source, suffix in suffixes:
            if text.startswith(source + " "):
                text = text[len(source) + 1:] + " " + suffix
                break
        text = re.sub(r"^alterno (.+)$", r"\1 alterno", text)
        text = re.sub(r"^agarre (cerrado|ancho|medio) (.+)$", r"\2 con agarre \1", text)
        text = re.sub(r"^smith máquina (.+)$", r"\1 en máquina Smith", text)
        text = re.sub(r"^smith (.+)$", r"\1 en máquina Smith", text)
        text = re.sub(r"^con peso (.+)$", r"\1 con peso", text)
        for modifier in ("inclinado", "declinado", "frontal", "posterior", "inverso", "lateral"):
            text = re.sub(rf"^{modifier} (.+)$", rf"\1 {modifier}", text)
    elif locale == "de":
        text = re.sub(r"^langhantel (.+)$", r"\1 mit Langhantel", text, flags=re.IGNORECASE)
        text = re.sub(r"^kurzhantel (.+)$", r"\1 mit Kurzhanteln", text, flags=re.IGNORECASE)
        text = re.sub(r"^enger griff (.+)$", r"\1 mit engem Griff", text, flags=re.IGNORECASE)
        text = re.sub(r"^weiter griff (.+)$", r"\1 mit weitem Griff", text, flags=re.IGNORECASE)
        text = re.sub(r"^mittlerer griff (.+)$", r"\1 mit mittlerem Griff", text, flags=re.IGNORECASE)
        text = re.sub(r"^abwechselnd (.+)$", r"\1 abwechselnd", text, flags=re.IGNORECASE)
        text = re.sub(r"^smith maschine (.+)$", r"\1 an der Smith-Maschine", text, flags=re.IGNORECASE)
    return text[:1].upper() + text[1:]


def build(locale: str, wger_path: Path | None) -> dict[str, Any]:
    profile = PROFILES[locale]
    db = json.loads(DB_PATH.read_text(encoding="utf-8"))
    wger = load_wger(wger_path, profile["wgerLanguage"])
    entries: dict[str, Any] = {}
    for exercise_id, exercise in db["exercises"].items():
        source_name = exercise["source"]["name"]
        localized = wger.get(normalize(source_name))
        if localized and normalize(localized) != normalize(source_name):
            preferred = localized
            source_refs = ["wger-api"]
        else:
            preferred = compose(source_name, profile, locale)
            source_refs = ["repo-domain-terminology"]
        entries[exercise_id] = {
            "preferred": preferred,
            "aliases": [],
            "sourceRefs": source_refs,
            "reviewStatus": "provisional",
        }

    existing = TRANSLATIONS / f"{locale}.json"
    if existing.exists():
        old = json.loads(existing.read_text(encoding="utf-8"))
        for exercise_id, entry in old.get("exercises", {}).items():
            if entry.get("reviewStatus") == "reviewed":
                entries[exercise_id] = entry
    return {"locale": locale, "exercises": entries}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("locale", choices=sorted(PROFILES))
    parser.add_argument("--wger", type=Path)
    args = parser.parse_args()
    output = TRANSLATIONS / f"{args.locale}.json"
    output.write_text(json.dumps(build(args.locale, args.wger), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {output}")


if __name__ == "__main__":
    main()
