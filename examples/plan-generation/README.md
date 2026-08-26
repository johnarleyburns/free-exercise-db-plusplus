# Deterministic PLAN generation examples

Run the full-body example from any directory with the installed package:

```bash
fedbpp generate-plan --profile full-body-profile.json --target full-body-target.json \
  --db ../../free-exercise-db-plusplus.json --policy full-body-general-v1 \
  --output generated-plan.json --report generation-report.json
```

The report is generator metadata; `generated-plan.json` is clean canonical
PLAN interchange JSON and can be passed directly to `fedbpp evaluate-plan`.
