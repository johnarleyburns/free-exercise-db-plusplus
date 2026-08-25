# Longitudinal analysis

v1.4 derives reports from separate PLAN revisions, ACTUAL sessions, optional
TARGET profiles, an explicit period definition, and the DB++ exercise database.
`TrainingHistory` contains only an opaque `subject_id`; it does not require
personal identity data.

```python
from fedbpp import Database, TrainingHistory, analyze_periods, export_muscle_period_csv

history = TrainingHistory("S001", plans=[plan_r1, plan_r2], workouts=actual,
                          targets=[target])
report = analyze_periods(history, Database.load("free-exercise-db-plusplus.json"),
                         period="calendar_week", timezone="America/New_York")
export_muscle_period_csv(report, "subject-week-muscle.csv")
```

Supported periods are `calendar_week`, `rolling_7_days`, `plan_cycle`, `phase`,
and `custom_date_range`. Periods retain native plan cycles and do not silently
turn an eight- or fourteen-day cycle into a week. PLAN-vs-ACTUAL matching is the
existing canonical matcher; longitudinal analysis adds revision activation,
missed-session, unplanned-session, substitution, and aggregation orchestration.

Muscle rows include direct, indirect, stabilizer, and effective planned ranges,
actual totals, adherence, target state, exposure counts, and mapping
completeness. CSV exports are deterministic and pandas is not required.

Missing ACTUAL data is not automatically zero. A missed planned session,
unplanned work, unmapped custom exercise, zero completed sets, and unable-to-
match linkage remain distinguishable in session and coverage outputs.

Non-goals are inferential statistics, causal or hypertrophy claims, fatigue or
injury prediction, recommendations, automatic substitutions, and a canonical
combined workout file.
