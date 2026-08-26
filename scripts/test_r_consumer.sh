#!/usr/bin/env bash
set -euo pipefail
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
consumer=$(mktemp -d)
library_dir=$(mktemp -d)
trap 'rm -rf "$consumer" "$library_dir"' EXIT
R CMD INSTALL --library="$library_dir" "$repo/packages/r/fedbpp" >/dev/null
cd "$consumer"
REPO_ROOT="$repo" R_LIBS_USER="$library_dir" Rscript - <<'RS'
library(fedbpp)
repo <- Sys.getenv("REPO_ROOT")
db <- load_database(file.path(repo, "free-exercise-db-plusplus.json"))
intent <- read_workout_intent(file.path(repo, "fixtures/cross-language/intent/flagship-5day-hypertrophy/input.json"))
result <- resolve_intent(intent, db = db)
stopifnot(result$status == "resolved_with_defaults")
stopifnot(identical(result$environmentPolicy, "commercial-gym-general-v1"))
stopifnot(identical(result$resolvedProfile$availability$preferredDayOffsets, as.integer(c(0, 1, 2, 3, 5))))
cat("r consumer ok\n")
RS
