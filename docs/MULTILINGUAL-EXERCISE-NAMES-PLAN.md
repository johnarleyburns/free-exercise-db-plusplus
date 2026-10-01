# Multilingual Exercise Names Plan

## Goal

Add reviewed, locale-specific exercise names and search aliases while preserving
the existing English source names, stable `exerciseId` values, exercise
relationships, and research semantics.

Localized names are presentation and search metadata. They must never replace
`exerciseId` as the identity used by plans, workouts, relationships, exports, or
research joins.

## Single-release locale scope

This release includes the original first- and second-wave languages, plus
research-collaboration languages Dutch and Italian, Hebrew, and Russian:

- `en` — existing canonical language
- `es` — Spanish
- `de` — German
- `zh-Hans` — Simplified Chinese
- `zh-Hant` — Traditional Chinese
- `pt-BR` — Brazilian Portuguese
- `fr` — French
- `ja` — Japanese
- `ko` — Korean
- `hi` — Hindi
- `ar` — Arabic
- `he` — Hebrew
- `ru` — Russian
- `nl` — Dutch
- `it` — Italian

Use BCP-47 locale tags. Do not use a bare `zh`: Chinese script and region
affect the displayed name. `he`, rather than the deprecated `iw`, is the
correct modern locale tag.

The locale list should align with Apple localization and Android per-app
language configuration. Future regional variants can resolve through the base
language, for example `es-MX -> es -> en` and `zh-TW -> zh-Hant -> en`.

## Terminology policy

This is semantic localization, not word-for-word translation. For each
exercise, determine the target-language term from:

1. movement, body position, equipment, grip, angle, and laterality;
2. national sports authorities and federation terminology;
3. university and peer-reviewed exercise-science sources;
4. local equipment manufacturers and established fitness platforms;
5. native-speaking strength or sports-science reviewers.

Dictionaries and machine translation may discover candidates, but must not be
the final authority. Require one authoritative source plus native domain review,
or two independent reputable sources plus native domain review.

For example, `bench press` should use terms actually used in each fitness
community: Spanish `press de banca`, German `Bankdrücken`, and Simplified
Chinese `卧推` or the more specific `杠铃卧推`. The system must not generate
these names by directly translating the English words.

Each localized entry should distinguish:

- preferred display name;
- common aliases;
- regional alternatives;
- accepted English loanwords;
- search-only forms such as Chinese pinyin or transliterations;
- reviewed, provisional, or unresolved status.

Arabic should initially use broadly interoperable Modern Standard Arabic names,
with regional aliases added when evidence supports them. Hebrew and Arabic must
also be tested as right-to-left text. Hindi, Japanese, Korean, Dutch, Italian,
Russian, and Chinese should retain English loanwords where those are the normal
gym terms rather than forcing artificial native wording.

## Source data and generated database

Create a reviewable source catalog:

```text
translations/
  README.md
  locale-manifest.json
  evidence.json
  es.json
  de.json
  zh-Hans.json
  zh-Hant.json
  pt-BR.json
  fr.json
  ja.json
  ko.json
  hi.json
  ar.json
  he.json
  ru.json
  nl.json
  it.json
```

The converter in `src/convert_fedb_to_fedbpp.py` should merge reviewed
translation data into the generated root database. The runtime database remains
self-contained; consumers should not need to download translation sidecars.

Add an optional `localizedNames` field to each exercise:

```json
{
  "localizedNames": {
    "de": {
      "preferred": "Bankdrücken mit Langhantel, mittlerer Griff",
      "aliases": ["Langhantel-Bankdrücken"],
      "sourceRefs": ["de-001"],
      "reviewStatus": "reviewed"
    }
  }
}
```

Add metadata describing `defaultLocale`, `supportedLocales`, fallback behavior,
translation-catalog version, and catalog checksums. Keep translation provenance
in the generated artifact through source references, while retaining full source
details in `translations/evidence.json`.

## Implementation phases

### Phase 1: schema and converter

- Extend `free-exercise-db-plusplus.schema.json` with `localizedNames`.
- Add translation catalog loading and validation to the converter.
- Preserve `source.name`, `exerciseId`, and all existing annotations.
- Add BCP-47 locale validation and deterministic fallback rules.
- Keep the new field optional so older databases remain readable.

### Phase 2: terminology pilot

Review approximately 100 representative exercises in every target locale:

- major compound lifts;
- bodyweight exercises;
- cable and machine movements;
- Olympic and powerlifting exercises;
- grip, angle, unilateral, and equipment variants;
- culturally named or ambiguous exercises.

Use the pilot to establish language-specific naming conventions before
localizing the long tail.

### Phase 3: complete catalog

- Provide a reviewed preferred name for all 927 exercises in all 14 non-English
  locales.
- Add aliases and search-only forms.
- Record source references and review status for every entry.
- Do not classify machine-generated names as reviewed.
- Require explicit exceptions for unresolved names rather than silently hiding
  English fallback.

### Phase 4: Swift and iPhone integration

Update the Swift database model and API to expose:

```swift
exercise.preferredName(locale: Locale)
exercise.aliases(locale: Locale)
database.findExercises(containing: query, locale: Locale)
```

Support Apple locales including `es-ES`, `es-MX`, `zh-Hans`, `zh-Hant`, `pt-BR`,
`he`, `ar`, `ru`, `nl`, and `it`. Use Unicode normalization, locale-aware case
handling, accent-insensitive search, and English fallback.

Add tests for Chinese script selection, Hebrew and Arabic RTL data, aliases,
unknown locales, older databases, and locale fallback. Keep the bundled Swift
database synchronized with the root artifact using
`scripts/test_swift_resources.sh`.

### Phase 5: Kotlin and Android integration

Update the Kotlin model and API to expose equivalent locale-aware methods using
`Locale.forLanguageTag(...)`.

- expose the supported locale list for Android `localeConfig`;
- support Android 13 per-app language selection;
- support older Android versions through the same database fallback behavior;
- keep the database offline and bundled;
- test `zh-Hans`, `zh-Hant`, `he`, `ar`, `ru`, `nl`, and `it` explicitly.

Keep the Kotlin bundled database synchronized using
`scripts/test_kotlin_resources.sh`.

### Phase 6: research and interoperability

Research exports should include:

```json
{
  "exerciseId": "Barbell_Bench_Press_-_Medium_Grip",
  "canonicalName": "Barbell Bench Press - Medium Grip",
  "localizedName": "Bankdrücken mit Langhantel, mittlerer Griff",
  "locale": "de",
  "nameSourceRefs": ["de-001"]
}
```

This makes multilingual research collaboration reproducible without making
localized spelling part of the join key.

## Validation and release work

Add checks that:

- every supported locale is listed in metadata;
- every exercise has a reviewed preferred name in every supported locale;
- every `sourceRef` resolves;
- localized names are Unicode-normalized;
- locale fallback is deterministic;
- aliases are searchable without changing display spelling;
- existing IDs and English source names are unchanged;
- root, Swift, Kotlin, Python, and R artifacts remain compatible;
- reproducible-build checks include translation inputs;
- CI path filters include `translations/**`;
- release checksums and release documentation include the updated artifacts.

The release is complete when the full 927-exercise catalog passes schema,
provenance, fallback, search, Swift resource, Kotlin resource, and existing
cross-language parity tests.
