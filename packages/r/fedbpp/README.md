# fedbpp: Free Exercise DB++ research engine

`fedbpp` is the native R implementation of the released DB++ training
semantics. It supports PLAN, ACTUAL, TARGET, TrainingProfile, WorkoutIntent,
TrainingHistory, evaluation, TrainingState, progression, deterministic plan
generation, and advisory adaptation. `jsonlite` is the only required
dependency; tidyverse and data.table are not required.

For application orchestration, use `process_training_request()` with a named
list matching `training-request.schema.json`. The operation is explicit and
returns a stable result envelope; see [the application guide](../../../docs/APPLICATION-INTEGRATION.md)
and `examples/app-integration/r/example.R`.

```r
db <- load_database()                         # bundled resource
w <- read_workout("examples/workouts/basic-barbell-strength.json")
sets <- effective_sets(w, db)       # credits from database metadata
observations <- workout_observations(w)
```

Analyses retain source exercise IDs and annotation confidence. Missing IDs, names, and confidence values remain `NA`; derived tables never mutate source observations.

Run `Rscript tests/test_package.R` from this directory, or install with
`R CMD INSTALL packages/r/fedbpp` and use `load_database()` outside the repo.

All coverage and evaluation paths read `metadata.setCredits`, exclude
`volumeEligible=false`, and apply the named `dbpp-default-volume-v1` counting
policy. Canonical documents stay as lists; research helpers such as
`plan_observations()` and `training_state_observations()` return data.frames.

WorkoutIntent resolution is available without a network service:

```r
intent <- read_workout_intent("fixtures/cross-language/intent/flagship-5day-hypertrophy/input.json")
resolution <- resolve_intent(intent, db)
next_plan <- generate_plan_from_intent(intent, db)
```

See [R-API](../../../docs/R-API.md) for history-aware state, progression,
adaptation, serialization, missingness, provenance, and longitudinal examples.
