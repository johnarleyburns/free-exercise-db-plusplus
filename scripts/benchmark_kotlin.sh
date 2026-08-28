#!/usr/bin/env bash
set -euo pipefail

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo/packages/kotlin/fedbpp"
start=$(date +%s%N)
./gradlew --no-daemon test --tests com.fedbpp.CanonicalParityTest.generationFixturesMatch --tests com.fedbpp.CanonicalParityTest.historyVariantFixturesMatch >/dev/null
end=$(date +%s%N)
echo "Kotlin bundled generation/history smoke: $(( (end - start) / 1000000 )) ms"
