# R research API

`fedbpp` is a native, offline R implementation of the released DB++ training
semantics. It needs only `jsonlite` and does not use Python, reticulate, Java,
network services, tidyverse, or an LLM.

## Installation and resources

```r
install.packages("jsonlite")
# From a checkout: R CMD INSTALL packages/r/fedbpp
library(fedbpp)
db <- load_database()
relationships <- load_relationships()
```

The database and relationship artifact are bundled in `inst/extdata`, so an
installed consumer does not need repository-relative paths. Explicit paths
remain supported by `load_database(path)` and `load_relationships(path)`.

## Canonical flow

```r
intent <- read_workout_intent("intent.json")
resolved <- resolve_intent(intent, db, relationships=relationships)
generated <- generate_plan_from_intent(intent, db, relationships=relationships)
plan <- generated$generation$plan
evaluation <- evaluate_plan(plan, db, resolved$resolvedProfile,
                             resolved$resolvedTarget, relationships)
```

For a stable host-application envelope, construct a named list matching
`training-request.schema.json` and call the explicit facade operation:

```r
request <- list(schemaVersion="0.1.0", requestId="request-1",
                operation="generate_from_intent", intent=intent,
                asOf="2026-08-28T12:00:00Z")
result <- process_training_request(request, db, relationships)
if (result$status %in% c("generated", "generated_with_target_gaps")) {
  plan <- result$plan
} else if (identical(result$status, "needs_clarification")) {
  print(result$missingInformation)
}
```

PLAN, ACTUAL, TARGET, TrainingProfile, WorkoutIntent, and TrainingHistory are
ordinary named lists. Use the corresponding `read_*`/`write_*` functions for
JSON round trips. Serialization uses `simplifyVector=FALSE`, `auto_unbox=FALSE`,
and `null="null"`; arrays remain arrays and missing values are not silently
turned into zero.

## History, progression, and adaptation

```r
history <- read_training_history("history.json")
state <- derive_training_state(history, db,
  as_of="2026-08-28T12:00:00Z", window="last_28_days",
  relationships=relationships)
decisions <- suggest_progression(plan, state,
  policy="double-progression-v1",
  parameters=list(loadIncrement=list(value=2.5, unit="kg")))
proposal <- adapt_plan(resolved$resolvedProfile, resolved$resolvedTarget,
  plan, history, db, relationships=relationships,
  as_of="2026-08-28T12:00:00Z")
```

Adaptation never mutates or activates the input plan. Its proposed revision is
validated and evaluated before it is returned. Active-plan selection uses
offset-aware instants, activation windows, and explicit plan/revision IDs.

The [external R consumer](../examples/app-integration/r/example.R) demonstrates
the same persisted-history flow: `derive_state`, `suggest_progression`, and an
explicit `adapt_plan` request with status handling. It uses named lists and runs
after installing the package into a clean library.

## Research views and reproducibility

`workout_observations()`, `plan_observations()`,
`training_state_observations()`, `muscle_state_observations()`,
`family_state_observations()`, `adherence_observations()`,
`coach_decision_observations()`, and `plan_evaluation_observations()` return
base-R `data.frame`s. They are views, not alternate domain models.

`analysis_provenance()` records the DB schema/converter versions, set-credit
policy, as-of instant, and history window. Timestamps are parsed as instants;
the original strings remain in canonical documents. JSON null, omitted fields,
`NA`, zero, `FALSE`, and empty arrays are distinct at the document boundary.

The engine reads `metadata.setCredits` for direct, indirect, and stabilizer
credits and honors `volumeEligible`. It does not infer substitutions from
family membership: only explicit substitution records count.
