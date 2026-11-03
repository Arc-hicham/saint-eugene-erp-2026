#!/usr/bin/env bash
# ==============================================================================
# Script d'installation Frappe v15 + Custom App "saint_eugene" (WSL2 / Ubuntu 22.04+)
# Hôtel Saint Eugène 4★ - Alger | Exercice 2026 | Devise : DZD | Normes SCF
# ==============================================================================
set -euo pipefail

BENCH_DIR="${HOME}/frappe-bench-se"
SITE_NAME="sainteugene.localhost"
ADMIN_PASS="${ADMIN_PASS:-SaintEugene2026!}"
DB_ROOT_PASS="${DB_ROOT_PASS:-root}"
APP_SRC_PATH="${1:-$(pwd)}"

echo "=== [1/6] Initialisation du Bench Frappe v15 ==="
if [ ! -d "${BENCH_DIR}" ]; then
    bench init "${BENCH_DIR}" --frappe-branch version-15 --python python3
fi

cd "${BENCH_DIR}"

echo "=== [2/6] Création du site ${SITE_NAME} ==="
if [ ! -d "sites/${SITE_NAME}" ]; then
    bench new-site "${SITE_NAME}" \
        --mariadb-root-password "${DB_ROOT_PASS}" \
        --admin-password "${ADMIN_PASS}"
fi

echo "=== [3/6] Récupération et installation de l'application saint_eugene ==="
if [ ! -d "apps/saint_eugene" ]; then
    bench get-app "${APP_SRC_PATH}"
fi

bench --site "${SITE_NAME}" install-app saint_eugene

echo "=== [4/6] Configuration Algérie (DZD, Langue FR, Fuseau Africa/Algiers) ==="
bench --site "${SITE_NAME}" execute frappe.db.set_single_value --args '["System Settings", "country", "Algeria"]'
bench --site "${SITE_NAME}" execute frappe.db.set_single_value --args '["System Settings", "time_zone", "Africa/Algiers"]'
bench --site "${SITE_NAME}" execute frappe.db.set_single_value --args '["System Settings", "language", "fr"]'
bench --site "${SITE_NAME}" execute frappe.db.set_single_value --args '["System Settings", "currency", "DZD"]'

echo "=== [5/6] Migration des DocTypes, Workspaces & Activation du Scheduler ==="
bench --site "${SITE_NAME}" migrate
bench --site "${SITE_NAME}" enable-scheduler
bench --site "${SITE_NAME}" clear-cache

echo "=== [6/6] Injection des données de simulation 2026 (Hôtel Saint Eugène 4★) ==="
bench --site "${SITE_NAME}" execute saint_eugene.setup_mock_data.run

echo "=============================================================================="
echo " Installation terminée ! Lancez 'cd ${BENCH_DIR} && bench start'"
echo " Accès : http://${SITE_NAME}:8000 (Utilisateur: Administrator / MDP: ${ADMIN_PASS})"
echo "=============================================================================="
