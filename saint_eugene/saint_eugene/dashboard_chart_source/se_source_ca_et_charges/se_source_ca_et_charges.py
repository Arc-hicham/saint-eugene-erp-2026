# -*- coding: utf-8 -*-
import frappe
from frappe.utils import flt
from saint_eugene.api.budget_engine import get_month_bounds

MOIS_LABELS = ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin", "Juil", "Août", "Sep", "Oct", "Nov", "Déc"]


@frappe.whitelist()
def get(chart_name=None, chart=None, no_cache=None, filters=None, from_date=None, to_date=None, timespan=None, time_interval=None, heatmap_year=None):
    ca_values = []
    charges_values = []

    for m in range(1, 13):
        mois = f"2026-{m:02d}"
        start_d, end_d = get_month_bounds(mois)
        ca = flt(
            frappe.db.sql(
                "SELECT COALESCE(SUM(montant_ht), 0) FROM `tabSE Facture Client` WHERE docstatus=1 AND date_facture BETWEEN %s AND %s",
                (start_d, end_d),
            )[0][0],
            2,
        )
        achats = flt(
            frappe.db.sql(
                "SELECT COALESCE(SUM(montant_ht), 0) FROM `tabSE Facture Fournisseur` WHERE docstatus=1 AND date_facture BETWEEN %s AND %s",
                (start_d, end_d),
            )[0][0]
        )
        chg = flt(
            frappe.db.sql(
                "SELECT COALESCE(SUM(montant_ht), 0) FROM `tabSE Charge et Depense` WHERE docstatus=1 AND date_charge BETWEEN %s AND %s",
                (start_d, end_d),
            )[0][0]
        )
        paie = flt(
            frappe.db.sql(
                "SELECT COALESCE(SUM(salaire_brut), 0) FROM `tabSE Fiche de Paie Mensuelle` WHERE docstatus=1 AND mois=%s",
                (mois,),
            )[0][0]
        )
        ca_values.append(ca)
        charges_values.append(flt(achats + chg + paie, 2))

    return {
        "labels": [f"{lbl} 2026" for lbl in MOIS_LABELS],
        "datasets": [
            {"name": "Chiffre d'Affaires HT (DZD)", "values": ca_values},
            {"name": "Total Charges & Salaires HT (DZD)", "values": charges_values},
        ],
        "type": "bar",
    }
