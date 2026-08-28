#!/usr/bin/env bash
set -euo pipefail
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
consumer=$(mktemp -d)
library_dir=$(mktemp -d)
trap 'rm -rf "$consumer" "$library_dir"' EXIT
R CMD INSTALL --library="$library_dir" "$repo/packages/r/fedbpp" >/dev/null
cd "$consumer"
REPO_ROOT="$repo" R_LIBS_USER="$library_dir${R_LIBS_USER:+:$R_LIBS_USER}" Rscript - <<'RS'
library(fedbpp)
repo <- Sys.getenv("REPO_ROOT")
db <- load_database()
relationships <- load_relationships()
stopifnot(length(db$exercises) > 800L, length(relationships$families) > 10L)
intent <- read_workout_intent(file.path(repo, "fixtures/cross-language/intent/flagship-5day-hypertrophy/input.json"))
result <- resolve_intent(intent, db = db, relationships = relationships)
stopifnot(result$status == "resolved_with_defaults")
stopifnot(identical(result$environmentPolicy, "commercial-gym-general-v1"))
stopifnot(identical(result$resolvedProfile$availability$preferredDayOffsets, as.integer(c(0, 1, 2, 3, 5))))
generated <- generate_plan_from_intent(intent, db, relationships=relationships)
stopifnot(generated$generation$status %in% c("generated", "generated_with_target_gaps"))
stopifnot(evaluate_plan(generated$generation$plan, db, result$resolvedProfile, result$resolvedTarget, relationships)$summary$satisfiesHardConstraints)
history <- read_training_history(file.path(repo, "fixtures/cross-language/history/input.json"))
state <- derive_training_state(history, db, as_of="2026-08-27T12:00:00-04:00", relationships=relationships)
stopifnot(state$activePlan$revisionId == "r1")
invisible(suggest_progression(generated$generation$plan, state, policy="hold-v1"))
stopifnot(nzchar(write_training_history(history)))
cat("r installed consumer ok\n")
RS
