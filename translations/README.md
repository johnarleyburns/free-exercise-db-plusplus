# Localized exercise names

These files are the source catalogs for localized exercise names. The converter
embeds them into `free-exercise-db-plusplus.json` under each exercise's
`localizedNames` field so runtime consumers remain self-contained.

Names are semantic fitness terminology, not mechanical translations. Each entry
must have at least one source reference and a status of `reviewed`, `provisional`,
or `untranslated`.

`untranslated` entries are explicit English fallbacks and do not count as
completed localization coverage. `provisional` entries are usable candidates
from a licensed terminology source or the repository's domain-term rules, but
must not be presented as native-reviewed terminology. Both statuses remain
visible in generated metadata so release review cannot mistake candidate
coverage for native review coverage.

Locale files use BCP-47 tags. The planned release locales are listed in
`locale-manifest.json`.

## Source and attribution

Some provisional names are sourced from the Wger exercise-information API;
those entries retain the `wger-api` source reference and are subject to the
Creative Commons Attribution-ShareAlike 4.0 terms recorded in `evidence.json`.
The remaining provisional candidates are composed from the repository-owned
domain terminology inventory. No external translation service is called by the
build.

The Spanish catalog also includes exact English-name matches from the
[Kinetic Exercises Spanish catalog](https://github.com/kinetic-place/exercises-json)
under its MIT license. These entries use the `es-reference-terminology` source
reference and remain provisional until native fitness review.

## Release policy (2026-11-16)

Non-English exercise names are accepted in releases with their actual review status: `reviewed`, `provisional`, or `untranslated`. Native-speaker review is encouraged but is not a publication prerequisite. Do not relabel provisional translations as reviewed merely to release. Nonempty names, valid IDs, unique aliases, recognized provenance, schema integrity, and localization audit checks remain required. Consumers should use locale → base language → English fallback and preserve canonical IDs independently of the displayed language.

The 11 specialized-muscle additions have provisional preferred names in every supported non-English locale. Their reproducible terminology source is `src/specialized_exercise_names.json`; the catalog builder consumes it without overwriting existing reviewed entries.
