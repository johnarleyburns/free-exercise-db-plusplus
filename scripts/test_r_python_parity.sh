#!/usr/bin/env bash
set -euo pipefail

# Execute the installed native R package against the same Python-authored
# engine fixtures consumed by the other language implementations. The
# comparator is applied to every expected document; this is not a property
# smoke test and never compares an expected document with itself.
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
out=$(mktemp -d)
lib=$(mktemp -d)
if [[ "${KEEP_R_PARITY_OUTPUT:-0}" == "1" ]]; then
  echo "R parity output: $out" >&2
else
  trap 'rm -rf "$out" "$lib"' EXIT
fi

R CMD INSTALL --library="$lib" "$repo/packages/r/fedbpp" >/dev/null
R_LIBS_USER="$lib${R_LIBS_USER:+:$R_LIBS_USER}" Rscript - "$repo" "$out" <<'RS'
args <- commandArgs(trailingOnly = TRUE)
repo <- normalizePath(args[[1]], mustWork = TRUE)
out <- normalizePath(args[[2]], mustWork = TRUE)
library(fedbpp)

read_doc <- function(path) jsonlite::fromJSON(path, simplifyVector = FALSE,
                                               simplifyDataFrame = FALSE,
                                               simplifyMatrix = FALSE)
emit <- function(path, value) {
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  fedbpp:::.write_json(value, path = path, pretty = TRUE)
}
fixture <- function(...) file.path(repo, "fixtures", "cross-language", ...)
actual <- function(kind, name, suffix = "actual.json")
  file.path(out, kind, name, suffix)

db <- load_database()
relationships <- load_relationships()

# Intent resolution and intent-driven generation.
intent_root <- fixture("intent")
for (name in sort(list.dirs(intent_root, full.names = FALSE, recursive = FALSE))) {
  dir <- file.path(intent_root, name)
  input <- read_workout_intent(file.path(dir, "input.json"), validate = FALSE)
  explicit_target <- if (file.exists(file.path(dir, "target.json")))
    read_doc(file.path(dir, "target.json")) else NULL
  history <- if (file.exists(file.path(dir, "history.json")))
    read_training_history(file.path(dir, "history.json"), validate = FALSE) else NULL
  as_of <- if (identical(name, "history-aware")) "2026-08-25T12:00:00Z" else NULL
  resolved <- resolve_intent(input, db = db, target = explicit_target,
                            relationships = NULL, history = history,
                            as_of = as_of)
  emit(actual("intent", name, "actual-resolution.json"), resolved)
  if (file.exists(file.path(dir, "expected-generation.json"))) {
    generated <- generate_plan_from_intent(
      input, db, target = explicit_target, relationships = NULL,
      history = history, as_of = as_of)
    emit(actual("intent", name, "actual-generation.json"), generated)
  }
}

# Plan evaluation, including database-overrides custom-credit fixtures.
evaluation_root <- fixture("evaluation")
eval_dirs <- c("", sort(list.dirs(evaluation_root, full.names = FALSE,
                                   recursive = FALSE)))
for (name in eval_dirs) {
  dir <- if (nzchar(name)) file.path(evaluation_root, name) else evaluation_root
  input <- read_doc(file.path(dir, "input.json"))
  eval_db <- db
  if (!is.null(input$databaseOverrides$setCredits))
    eval_db$metadata$setCredits <- input$databaseOverrides$setCredits
  result <- evaluate_plan(input$plan, eval_db, input$profile, input$target,
                          relationships)
  emit(if (nzchar(name)) actual("evaluation", name) else
         file.path(out, "evaluation", "actual.json"), result)
}

# History and TrainingState fixtures.
history_root <- fixture("history")
history_dirs <- c("", sort(list.dirs(history_root, full.names = FALSE,
                                     recursive = FALSE)))
for (name in history_dirs) {
  dir <- if (nzchar(name)) file.path(history_root, name) else history_root
  input <- read_doc(file.path(dir, "input.json"))
  history <- if (is.null(input$history))
    read_training_history(file.path(dir, "input.json"), validate = FALSE) else
    input$history
  result <- derive_training_state(
    history, db, as_of = input$asOf, window = input$window %||% "last_28_days",
    relationships = relationships, timezone = input$timezone %||% "UTC")
  emit(if (nzchar(name)) actual("history", name) else
         file.path(out, "history", "actual.json"), result)
}

# Progression root and one-document case fixtures.
progression_root <- fixture("progression")
progression_input <- read_doc(file.path(progression_root, "input.json"))
progression_results <- list()
for (case in progression_input$cases) {
  progression_results[[case$id]] <- apply_progression_policy(
    progression_input$policy, case$prescription, case$state, db = db,
    parameters = progression_input$parameters %||% list())
}
emit(file.path(out, "progression", "actual.json"), progression_results)
for (name in sort(list.dirs(progression_root, full.names = FALSE,
                            recursive = FALSE))) {
  dir <- file.path(progression_root, name)
  input <- read_doc(file.path(dir, "input.json"))
  result <- apply_progression_policy(input$policy, input$prescription,
                                     input$state, db = db,
                                     parameters = input$parameters %||% list())
  emit(actual("progression", name), result)
}

# Production plan generation, including locked and target-maximum cases.
generation_root <- fixture("generation")
generation_dirs <- c("", sort(list.dirs(generation_root, full.names = FALSE,
                                         recursive = FALSE)))
for (name in generation_dirs) {
  dir <- if (nzchar(name)) file.path(generation_root, name) else generation_root
  input <- read_doc(file.path(dir, "input.json"))
  result <- generate_plan(
    input$profile, input$target, db, policy = input$policy,
    training_state = input$trainingState %||% NULL,
    relationships = relationships, current_plan = input$currentPlan %||% NULL,
    requiredExerciseIds = input$requiredExerciseIds %||% character(),
    lockedExerciseIds = input$lockedExerciseIds %||% character(),
    requiredFamilyIds = input$requiredFamilyIds %||% character(),
    additionalExclusions = input$additionalExclusions %||% character(),
    options = input$options %||% list())
  emit(if (nzchar(name)) actual("generation", name) else
         file.path(out, "generation", "actual.json"), result)
}

# Adaptive coaching fixtures.
adaptation_root <- fixture("adaptation")
adaptation_dirs <- c("", sort(list.dirs(adaptation_root, full.names = FALSE,
                                         recursive = FALSE)))
for (name in adaptation_dirs) {
  dir <- if (nzchar(name)) file.path(adaptation_root, name) else adaptation_root
  input <- read_doc(file.path(dir, "input.json"))
  history <- input$history
  result <- adapt_plan(
    input$profile, input$target, input$currentPlan, history, db,
    policy = input$policy, relationships = relationships,
    as_of = input$asOf, options = input$options %||% list())
  emit(if (nzchar(name)) actual("adaptation", name) else
         file.path(out, "adaptation", "actual.json"), result)
}
RS

compare() {
  python3 "$repo/tools/compare_canonical_json.py" "$1" "$2" >/dev/null
}

while IFS= read -r -d '' expected; do
  relative=${expected#"$repo/fixtures/cross-language/"}
  actual_path="$out/${relative/expected/actual}"
  if [[ ! -f "$actual_path" ]]; then
    echo "missing R parity output: $relative -> $actual_path" >&2
    exit 1
  fi
  compare "$expected" "$actual_path"
  echo "R parity ok: $relative"
done < <(find "$repo/fixtures/cross-language" -type f -name 'expected*.json' -print0 | sort -z)

echo "Python↔R canonical parity passed"
