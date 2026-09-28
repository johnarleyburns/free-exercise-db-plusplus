# CLI

Exercise relationship queries added in v1.5:

```bash
fedbpp family Dumbbell_Bench_Press --json
fedbpp family-members bench_press --json
fedbpp related Barbell_Bench_Press_-_Medium_Grip --json
fedbpp compare-exercises Barbell_Bench_Press_-_Medium_Grip Dumbbell_Bench_Press \
  --db free-exercise-db-plusplus.json --json
fedbpp analyze-plan plan.json --db free-exercise-db-plusplus.json \
  --relationships exercise-relationships.json --json
```

`related` means taxonomically related candidate, not recommended substitute.

Install the standalone package with `pip install packages/python`. The command
returns `0` on success and `1` for invalid input, unsupported format, or a
strict conversion loss.

```text
fedbpp validate db database.json
fedbpp validate workout actual.json
fedbpp validate plan plan.json
fedbpp validate target target.json

fedbpp analyze-plan plan.json --db free-exercise-db-plusplus.json --json
fedbpp compare-plans plan-a.json plan-b.json --db db.json --json
fedbpp compare-actual plan.json actual.json --db db.json --json
fedbpp compare-target plan.json target.json --db db.json --json

fedbpp import fhir source.json --output actual.json --report report.json --strict
fedbpp export fhir actual.json --output source.json --report report.json --allow-lossy
fedbpp import healthkit healthkit-envelope.json --output actual.json --strict
fedbpp export healthkit actual.json --output healthkit-envelope.json --strict
fedbpp import health-connect health-connect-envelope.json --output actual.json --strict
fedbpp export health-connect actual.json --output health-connect-envelope.json --strict
fedbpp import garmin-fit fit-envelope.json --output actual.json --strict
fedbpp export garmin-fit actual.json --output fit-envelope.json --strict
fedbpp import garmin-fit activity.fit --binary --output actual.json --strict
fedbpp export garmin-fit actual.json --binary --output activity.fit --strict
fedbpp mapping external fhir Dumbbell_Bench_Press
fedbpp mapping dbpp Dumbbell_Bench_Press --system fhir
```

Health target files are loss-aware JSON envelopes containing a native projection
and an exact `canonicalWorkout` sidecar. They are the portable boundary for the
offline package; a platform host must turn the projection into a Garmin FIT
binary, `HKWorkout`, or `ExerciseSessionRecord` and retain the sidecar with that
native record. Native-only records fail strict import because they cannot carry
all DB++ workout fields.

Conversion documents are written to `--output` (or stdout when omitted). Reports
are deterministic JSON and contain status, loss entries, warnings, and provenance.


## v1.9 CLI

```bash
fedbpp adapt-plan --profile profile.json --target target.json --plan current-plan.json --history history.json --db db.json --as-of 2026-08-25T12:00:00Z --output proposed-plan.json --report adaptive-report.json
```

The report is authoritative. If no proposal exists, `--output` is not created.
