#!/usr/bin/env bash
set -euo pipefail

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
venv_dir=${FEDBPP_VENV_DIR:-"$repo/.venv"}

if [[ ! -x "$venv_dir/bin/python" ]]; then
  python3 -m venv "$venv_dir"
fi

"$venv_dir/bin/python" -m pip install --upgrade pip setuptools wheel
"$venv_dir/bin/python" -m pip install --editable "$repo/packages/python"

echo "fedbpp virtualenv ready: $venv_dir"
echo "activate with: source $venv_dir/bin/activate"
