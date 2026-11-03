# -*- coding: utf-8 -*-
import frappe
from frappe.utils import flt
from saint_eugene.api.budget_engine import get_month_bounds

MOIS_LABELS = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]


@frappe.whitelist()
def get(chart_name=None, chart=None, no_cache=None, filters=None, from_date=None, to_date=None, timespan=None, time_interval=None, heatmap_year=None):
    solde_ouverture = flt(
        frappe.db.sql("SELECT COALESCE(SUM(solde_initial), 0) FROM `tabSE Compte Tresorerie`")[0][0],
        2,
    )
    treso_cumul = []

    for m in range(1, 13):
        mois = f"2026-{m:02d}"
        _, end_d = get_month_bounds(mois)
        enc = flt(
            frappe.db.sql(
                "SELECT COALESCE(SUM(montant), 0) FROM `tabSE Encaissement` WHERE docstatus=1 AND date_encaissement <= %s",
                (end_d,),
            )[0][0]
        )
        dec = flt(
            frappe.db.sql(
                "SELECT COALESCE(SUM(montant), 0) FROM `tabSE Decaissement` WHERE docstatus=1 AND date_decaissement <= %s",
                (end_d,),
            )[0][0]
        )
        treso_cumul.append(flt(solde_ouverture + enc - dec, 2))

    return {
        "labels": [f"{lbl} 2026" for lbl in MOIS_LABELS],
        "datasets": [
            {"name": "Trésorerie Globale Cumulée (DZD)", "values": treso_cumul},
        ],
        "type": "line",
    }
