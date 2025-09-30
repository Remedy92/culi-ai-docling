#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 3 ]; then
  echo "Usage: $0 <service-url> <docling-key> <path-to-pdf>" >&2
  exit 1
fi

SERVICE_URL="$1"
DOCLING_KEY="$2"
PDF_PATH="$3"

if [ ! -f "$PDF_PATH" ]; then
  echo "File not found: $PDF_PATH" >&2
  exit 1
fi

curl -sS -w '\nHTTP %{http_code}\n' \
  -H "X-Docling-Key: ${DOCLING_KEY}" \
  -F "file=@${PDF_PATH}" \
  "${SERVICE_URL%/}/convert"
