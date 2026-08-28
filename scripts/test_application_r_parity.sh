#!/usr/bin/env bash
set -euo pipefail

# External installed-package consumer for the application contract.
repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
lib=$(mktemp -d)
out=$(mktemp -d)
trap 'rm -rf "$lib" "$out"' EXIT
R CMD INSTALL --library="$lib" "$repo/packages/r/fedbpp" >/dev/null
R_LIBS_USER="$lib${R_LIBS_USER:+:$R_LIBS_USER}" Rscript - "$repo" "$out" <<'RS'
args <- commandArgs(trailingOnly = TRUE)
repo <- normalizePath(args[[1]], mustWork = TRUE)
out <- normalizePath(args[[2]], mustWork = TRUE)
library(fedbpp)
db <- load_database()
relationships <- load_relationships()
root <- file.path(repo, "fixtures", "application-integration")
read_doc <- function(path) jsonlite::fromJSON(path, simplifyVector = FALSE,
                                               simplifyDataFrame = FALSE,
                                               simplifyMatrix = FALSE)
for (name in sort(list.dirs(root, full.names = FALSE, recursive = FALSE))) {
  dir <- file.path(root, name)
  request <- read_doc(file.path(dir, "request.json"))
  actual <- process_training_request(request, db, relationships)
  path <- file.path(out, name, "actual-result.json")
  dir.create(dirname(path), recursive = TRUE, showWarnings = FALSE)
  fedbpp:::.write_json(actual, path = path, pretty = TRUE)
}
RS
while IFS= read -r -d '' expected; do
  relative=${expected#"$repo/fixtures/application-integration/"}
  python3 "$repo/tools/compare_canonical_json.py" "$expected" "$out/${relative%expected-result.json}actual-result.json"
done < <(find "$repo/fixtures/application-integration" -name expected-result.json -print0 | sort -z)
echo "Python↔R application parity passed"
