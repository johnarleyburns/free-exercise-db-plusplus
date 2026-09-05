# Canonical exercise catalog expansion

DB++ keeps the pinned `yuhonas/free-exercise-db` snapshot intact and adds
original, vendor-neutral records in `src/catalog_additions.json`. The manifest
contains canonical IDs, movement patterns, muscle-role annotations, search
aliases, and the vendor catalogs that demonstrated the exercise. It does not
copy vendor descriptions, photographs, trademarks, or product-specific
instructions.

The first expansion was reviewed on 2026-09-05. It adds 54 canonical cable,
functional-trainer, selectorized, and plate-loaded exercises. In particular,
`Cable_Push_Pull` represents the named dual-cable movement in which one handle
is pushed while the other is pulled from a split stance. It is not collapsed
into the existing cable chest press or cable row records.

## How the list was found

The review compared the existing DB++ IDs against current official exercise and
equipment catalogs from Keiser, Hammer Strength/Cybex, Precor, Life Fitness,
and Matrix. We recorded a new canonical record when a label represented a
distinct movement, equipment path, body position, or compound protocol. We
recorded an alias or relationship when a product label only described an
existing movement or a grip, angle, laterality, or resistance variation.

Primary catalog references used for the initial review:

- [Keiser Functional Trainer exercises](https://resources.keiser.com/functional-trainer-exercises)
- [Hammer Strength/Cybex equipment configurator](https://configurator.cybexintl.com/?brand=3&entity=HS-MTS-iso-lateral-high-row)
- [Precor Resolute selectorized strength](https://www.precor.com/en-US/strength/selectorized/resolute)
- [Life Fitness Universal Cable](https://www.lifefitness.com/en-us/catalog/strength-training/cable-machines-functional-trainers/universal-cable)
- [Matrix strength equipment](https://www.matrixfitness.com/us/eng/strength)

Vendor names remain evidence and discovery metadata. They are never canonical
exercise identities, and a product name is not treated as evidence that two
movements are physiologically equivalent.

## Annual update procedure

Run this review once per calendar year, and sooner when a major vendor catalog
changes or an athlete reports a missing gym movement.

1. Record the review date and inspect the current official catalogs listed in
   `src/catalog_additions.json`. Add other major manufacturers or regional gym
   catalogs when they expose a distinct, reproducible movement.
2. Export the current DB++ names and compare them with every catalog label. For
   each label, choose exactly one disposition: existing canonical record,
   alias/facet, vendor overlay, or new canonical record.
3. For each new record, add an original vendor-neutral name, stable ID,
   equipment, force, level, mechanic, movement pattern(s), muscle roles,
   volume eligibility, aliases, and vendor source keys to the manifest.
4. Use original instructions and no copied vendor text or imagery. Keep
   commercial product names in aliases or mapping documentation only.
5. Validate the manifest and regenerate every public artifact:

   ```bash
   python3 -m pip install jsonschema
   curl --fail --location \
     https://raw.githubusercontent.com/yuhonas/free-exercise-db/5197c055b356498944328bd00178b64a5e9f422c/dist/exercises.json \
     --output exercises.json
   python3 src/convert_fedb_to_fedbpp.py exercises.json \
     free-exercise-db-plusplus.json \
     --schema free-exercise-db-plusplus.schema.json \
     --completeness full
   PYTHONPATH=. python3 -m src.relationships.build \
     free-exercise-db-plusplus.json exercise-relationships.json
   ```

6. Review generated `reports/REVIEW.md`, `reports/MAPPING-AUDIT.md`,
   `reports/EVIDENCE-AUDIT.md`, and the relationship report. Confirm that new
   patterns use non-provisional evidence and that all bundled language
   resources match the root database.
7. Run the release checklist, commit the manifest, generator, documentation,
   generated artifacts, and package resources together, then tag the next
   release. The tagged release must pass normal CI before the release workflow
   publishes it.

The weekly upstream build remains responsible for detecting changes in the
open upstream snapshot. It does not replace this annual vendor-catalog review:
vendor catalogs require human semantic deduplication and cannot safely be
treated as a scrape-and-append feed.
