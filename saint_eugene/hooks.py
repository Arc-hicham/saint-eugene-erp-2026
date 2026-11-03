# -*- coding: utf-8 -*-
"""
Configuration centrale Frappe Hooks - Application Saint Eugène (Exercice 2026)
Hôtel Saint Eugène 4★ - Alger (Normes SCF / DZD)
"""

app_name = "saint_eugene"
app_title = "Saint Eugène ERP 2026"
app_publisher = "Contrôle de Gestion - Hôtel Saint Eugène"
app_description = (
    "Mini-ERP Hôtelier 4★ (Comptabilité SCF, Trésorerie DZD, Facturation, Paie & Pilotage Budgétaire 2026)"
)
app_email = "daf@hotel-sainteugene.dz"
app_license = "Proprietary"

# Fixtures exportables/importables lors de bench migrate
fixtures = [
    {"dt": "Workflow", "filters": [["name", "in", ["Validation Caisse Mensuelle SE"]]]},
    {"dt": "Workflow State"},
    {"dt": "Workflow Action Master"},
]

# Événements transverses sur les DocTypes -> Alimentation temps réel du Budget 2026 & TVA
doc_events = {
    "SE Facture Client": {
        "on_submit": "saint_eugene.api.budget_engine.on_financial_doc_change",
        "on_cancel": "saint_eugene.api.budget_engine.on_financial_doc_change",
    },
    "SE Facture Fournisseur": {
        "on_submit": "saint_eugene.api.budget_engine.on_financial_doc_change",
        "on_cancel": "saint_eugene.api.budget_engine.on_financial_doc_change",
    },
    "SE Fiche de Paie Mensuelle": {
        "on_submit": "saint_eugene.api.budget_engine.on_financial_doc_change",
        "on_cancel": "saint_eugene.api.budget_engine.on_financial_doc_change",
    },
    "SE Charge et Depense": {
        "on_submit": "saint_eugene.api.budget_engine.on_financial_doc_change",
        "on_cancel": "saint_eugene.api.budget_engine.on_financial_doc_change",
    },
}

# Tâches planifiées (Cron Frappe Worker / Scheduler)
scheduler_events = {
    "daily": [
        "saint_eugene.tasks.daily.update_overdue_invoices_and_contracts",
        "saint_eugene.tasks.daily.run_daily_financial_alerts",
    ],
}
