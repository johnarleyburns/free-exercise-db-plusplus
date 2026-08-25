# CLI

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
fedbpp mapping external fhir Dumbbell_Bench_Press
fedbpp mapping dbpp Dumbbell_Bench_Press --system fhir
```

Conversion documents are written to `--output` (or stdout when omitted). Reports
are deterministic JSON and contain status, loss entries, warnings, and provenance.
