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
