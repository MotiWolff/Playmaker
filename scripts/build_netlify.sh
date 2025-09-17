#!/usr/bin/env bash
set -euo pipefail

# Replace the ${API_BASE_URL} placeholder in ui/js/api.js with the Netlify env value
if [[ -z "${API_BASE_URL:-}" ]]; then
  echo "ERROR: API_BASE_URL env var is required for Netlify build" >&2
  exit 2
fi

# Use perl for safe in-place replacement of the literal ${API_BASE_URL}
perl -0777 -pe "s|\\\$\{API_BASE_URL\}|${API_BASE_URL}|g" -i ui/js/api.js

echo "[netlify] Injected API_BASE_URL=${API_BASE_URL} into ui/js/api.js"


