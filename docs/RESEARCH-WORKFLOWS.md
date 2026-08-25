# Research workflows

For a study, create one `TrainingHistory` per opaque subject and run
`analyze_cohort`. The result contains participant-level `subject × period ×
muscle`, `subject × session`, and `subject × session × exercise` rows. Export
the tables with `export_muscle_period_csv`, `export_session_csv`, and
`export_exercise_csv`.

```python
from fedbpp import analyze_cohort, export_muscle_period_csv
cohort = analyze_cohort(subjects, db, period="calendar_week",
                        start="2026-01-01", end="2026-03-26", timezone="UTC")
export_muscle_period_csv(cohort, "subject-week-muscle.csv")
```

Python can read the CSV with `pandas.read_csv`; R can use
`read.csv("subject-week-muscle.csv")`. The library supplies descriptive rows
only. It does not calculate p-values, confidence intervals, effect sizes,
regressions, or statistical conclusions.

Retain `plan_revisions_used`, `plan_ids_used`, and `phase_ids_used` when
exporting rows. Repeated PLAN sessions are occurrence-based, and mixed TARGET
periods are reported explicitly rather than silently averaged.
