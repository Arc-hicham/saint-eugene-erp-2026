# -*- coding: utf-8 -*-
import frappe
from frappe.utils import flt
from saint_eugene.api.budget_engine import BUDGET_CATEGORIES


@frappe.whitelist()
def get(chart_name=None, chart=None, no_cache=None, filters=None, from_date=None, to_date=None, timespan=None, time_interval=None, heatmap_year=None):
    prevu_vals = []
    realise_vals = []

    for cat in BUDGET_CATEGORIES:
        row = frappe.db.sql(
            """
            SELECT COALESCE(SUM(budget_prevu), 0), COALESCE(SUM(realise), 0)
            FROM `tabSE Budget Annuel`
            WHERE categorie = %s
            """,
            (cat,),
        )[0]
        prevu_vals.append(flt(row[0], 2))
        realise_vals.append(flt(row[1], 2))

    return {
        "labels": list(BUDGET_CATEGORIES),
        "datasets": [
            {"name": "Budget Prévu 2026 (DZD)", "values": prevu_vals},
            {"name": "Réalisé Validé 2026 (DZD)", "values": realise_vals},
        ],
        "type": "bar",
    }
