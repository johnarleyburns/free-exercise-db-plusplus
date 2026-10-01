#!/usr/bin/env python3
"""Validate localized-name metadata and catalog identity contracts."""
import json
import sys
from pathlib import Path


db = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
metadata = db["metadata"]
localization = metadata["localization"]
assert localization["defaultLocale"] == "en"
assert localization["fallbackPolicy"] == "locale -> base language -> en"
supported = localization["supportedLocales"]
assert "en" in supported
assert len(supported) == len(set(supported))

for locale, catalog in localization["catalogs"].items():
    assert locale in supported
    counts = {"reviewed": 0, "provisional": 0, "untranslated": 0}
    for exercise_id, record in db["exercises"].items():
        entry = record.get("localizedNames", {}).get(locale)
        if entry is None:
            continue
        assert entry["preferred"].strip()
        assert len(entry["aliases"]) == len(set(entry["aliases"]))
        assert entry["sourceRefs"]
        assert entry["reviewStatus"] in counts
        counts[entry["reviewStatus"]] += 1
    assert catalog["entryCount"] == sum(counts.values())
    assert catalog["reviewedCount"] == counts["reviewed"]
    assert catalog["provisionalCount"] == counts["provisional"]
    assert catalog["untranslatedCount"] == counts["untranslated"]

print(
    "localization contract passed:",
    ", ".join(f"{locale}={data['entryCount']}" for locale, data in localization["catalogs"].items()),
)
