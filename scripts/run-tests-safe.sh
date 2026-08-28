#!/usr/bin/env bash

set -euo pipefail

TEST_SITE="${1:-}"

if [[ -z "$TEST_SITE" ]]; then
	printf 'Uso: %s <sitio-desechable> [opciones de run-tests]\n' "$0" >&2
	exit 2
fi

shift

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCH_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
SITE_CONFIG="$BENCH_ROOT/sites/$TEST_SITE/site_config.json"

if [[ ! -f "$SITE_CONFIG" ]]; then
	printf 'No existe la configuración del sitio: %s\n' "$SITE_CONFIG" >&2
	exit 2
fi

if ! jq -e '.restaurant_allow_destructive_tests == true' "$SITE_CONFIG" >/dev/null; then
	printf '%s\n' \
		"Pruebas rechazadas para $TEST_SITE." \
		"ERPNext elimina datos maestros, incluidos todos los registros de Item Price, al inicializar pruebas." \
		"Use un sitio desechable y habilítelo con:" \
		"  bench --site $TEST_SITE set-config restaurant_allow_destructive_tests true" >&2
	exit 3
fi

cd "$BENCH_ROOT"
exec bench --site "$TEST_SITE" run-tests --app restaurant_management "$@"
