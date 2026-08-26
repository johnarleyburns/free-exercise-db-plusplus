# fedbpp: Free Exercise DB++ research integration

This base-R-compatible package provides read-only JSON loaders, Workout 0.2 validation/migration, data-frame helpers, and effective-set/longitudinal analysis. `jsonlite` is the only required dependency; tidyverse is not required.

```r
db <- load_database("free-exercise-db-plusplus.json")
w <- load_workout("examples/workouts/basic-barbell-strength.json")
sets <- effective_sets(w, db)       # credits from database metadata
observations <- workout_observations(w)
```

Analyses retain source exercise IDs and annotation confidence. Missing IDs, names, and confidence values remain `NA`; derived tables never mutate source observations.

Run `Rscript tests/test_package.R` from this directory.

Effective-set helpers read `metadata.setCredits`, exclude `volumeEligible=false`, and apply `dbpp-default-volume-v1` top-level set-type counting. Advanced PLAN/TARGET/adherence parity is not currently claimed.

WorkoutIntent resolution is available without a network service:

```r
intent <- read_workout_intent("fixtures/cross-language/intent/flagship-5day-hypertrophy/input.json")
resolution <- resolve_intent(intent)
```
