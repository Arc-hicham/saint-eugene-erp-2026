# -*- coding: utf-8 -*-
"""
Moteur d'agrégation Budgétaire & Analytique (Équivalent SQL/ORM des SOMME.SI.ENS Google Sheets)
Croise automatiquement les Factures Clients, Factures Fournisseurs, Fiches de Paie et Charges validées
pour alimenter `SE Budget Annuel` (Exercice 2026 - DZD - Normes SCF).
"""
from __future__ import annotations

import calendar
from datetime import date

import frappe
from frappe.utils import flt, getdate

BUDGET_CATEGORIES = (
    "CA Hébergement",
    "CA Restauration",
    "Salaires",
    "Achats",
    "Charges",
)

REVENUE_CATEGORIES = {"CA Hébergement", "CA Restauration"}


def get_month_bounds(mois: str) -> tuple[str, str]:
    """Retourne ('YYYY-MM-01', 'YYYY-MM-DD') pour un mois au format '2026-MM'."""
    year_str, month_str = mois.split("-")
    year, month = int(year_str), int(month_str)
    last_day = calendar.monthrange(year, month)[1]
    return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last_day:02d}"


def extract_mois_from_doc(doc) -> str | None:
    """Extrait la clé mensuelle 'YYYY-MM' depuis n'importe quel document financier SE."""
    if getattr(doc, "mois", None):
        return str(doc.mois)[:7]

    for date_field in ("date_facture", "date_charge", "date_encaissement", "date_decaissement"):
        val = getattr(doc, date_field, None)
        if val:
            d = getdate(val)
            return f"{d.year:04d}-{d.month:02d}"
    return None


def compute_realise_for_month_category(mois: str, categorie: str) -> float:
    """
    Traduction exacte de SOMME.SI.ENS en requêtes SQL paramétrées Frappe (MariaDB) :
    - CA Hébergement  : SUM(montant_ht) de SE Facture Client (docstatus=1, nature='Hébergement')
    - CA Restauration : SUM(montant_ht) de SE Facture Client (docstatus=1, nature IN ('Restauration', 'Séminaires & Banquets'))
    - Salaires        : SUM(salaire_brut) de SE Fiche de Paie Mensuelle (docstatus=1, mois=mois) [SCF Classe 63]
    - Achats          : SUM(montant_ht) de SE Facture Fournisseur (docstatus=1) [SCF Classe 60]
    - Charges         : SUM(montant_ht) de SE Charge et Depense (docstatus=1) [SCF Classes 61/62/64]
    """
    start_date, end_date = get_month_bounds(mois)

    if categorie == "CA Hébergement":
        res = frappe.db.sql(
            """
            SELECT COALESCE(SUM(montant_ht), 0)
            FROM `tabSE Facture Client`
            WHERE docstatus = 1
              AND nature_prestation = 'Hébergement'
              AND date_facture BETWEEN %s AND %s
            """,
            (start_date, end_date),
        )
        return flt(res[0][0], 2)

    if categorie == "CA Restauration":
        res = frappe.db.sql(
            """
            SELECT COALESCE(SUM(montant_ht), 0)
            FROM `tabSE Facture Client`
            WHERE docstatus = 1
              AND nature_prestation IN ('Restauration', 'Séminaires & Banquets')
              AND date_facture BETWEEN %s AND %s
            """,
            (start_date, end_date),
        )
        return flt(res[0][0], 2)

    if categorie == "Salaires":
        res = frappe.db.sql(
            """
            SELECT COALESCE(SUM(salaire_brut), 0)
            FROM `tabSE Fiche de Paie Mensuelle`
            WHERE docstatus = 1
              AND mois = %s
            """,
            (mois,),
        )
        return flt(res[0][0], 2)

    if categorie == "Achats":
        res = frappe.db.sql(
            """
            SELECT COALESCE(SUM(montant_ht), 0)
            FROM `tabSE Facture Fournisseur`
            WHERE docstatus = 1
              AND date_facture BETWEEN %s AND %s
            """,
            (start_date, end_date),
        )
        return flt(res[0][0], 2)

    if categorie == "Charges":
        res = frappe.db.sql(
            """
            SELECT COALESCE(SUM(montant_ht), 0)
            FROM `tabSE Charge et Depense`
            WHERE docstatus = 1
              AND date_charge BETWEEN %s AND %s
            """,
            (start_date, end_date),
        )
        return flt(res[0][0], 2)

    return 0.0


def evaluate_budget_variance(
    categorie: str, budget_prevu: float, realise: float
) -> tuple[str, float, float, str]:
    """
    Calcule le type de flux, l'écart en DZD, l'écart en % et le statut de pilotage.
    Convention Contrôle de Gestion :
    - ecart_dzd = realise - budget_prevu
    - Pour un Produit (CA) : ecart_dzd >= 0 => Objectif Atteint, sinon Sous-Performance (< -5%) ou Conforme
    - Pour une Charge      : realise > budget_prevu => Dépassement, sinon Conforme
    """
    budget_prevu = flt(budget_prevu, 2)
    realise = flt(realise, 2)
    ecart_dzd = flt(realise - budget_prevu, 2)
    ecart_pct = flt((ecart_dzd / budget_prevu) * 100.0, 2) if budget_prevu else 0.0

    if categorie in REVENUE_CATEGORIES:
        type_flux = "Produit (CA)"
        if realise >= budget_prevu and budget_prevu > 0:
            statut = "Objectif Atteint"
        elif ecart_pct < -5.0:
            statut = "Sous-Performance"
        else:
            statut = "Conforme"
    else:
        type_flux = "Charge (Dépense)"
        if budget_prevu > 0 and realise > budget_prevu:
            statut = "Dépassement"
        else:
            statut = "Conforme"

    return type_flux, ecart_dzd, ecart_pct, statut


@frappe.whitelist()
def refresh_budget_month(mois: str) -> dict:
    """Recalcule toutes les lignes de `SE Budget Annuel` existantes pour un mois donné."""
    budgets = frappe.get_all(
        "SE Budget Annuel",
        filters={"mois": mois},
        fields=["name", "categorie", "budget_prevu"],
    )
    updated = 0
    for row in budgets:
        realise = compute_realise_for_month_category(mois, row.categorie)
        type_flux, ecart_dzd, ecart_pct, statut = evaluate_budget_variance(
            row.categorie, row.budget_prevu, realise
        )
        frappe.db.set_value(
            "SE Budget Annuel",
            row.name,
            {
                "type_flux": type_flux,
                "realise": realise,
                "ecart_dzd": ecart_dzd,
                "ecart_pct": ecart_pct,
                "statut_budget": statut,
            },
            update_modified=False,
        )
        updated += 1
    return {"mois": mois, "lignes_mises_a_jour": updated}


@frappe.whitelist()
def refresh_all_budgets_2026() -> dict:
    """Recalcule l'intégralité du budget 2026 (12 mois x 5 catégories)."""
    months = frappe.get_all("SE Budget Annuel", pluck="mois")
    unique_months = sorted(set(months))
    total = 0
    for m in unique_months:
        res = refresh_budget_month(m)
        total += res["lignes_mises_a_jour"]
    return {"mois_traites": len(unique_months), "lignes_mises_a_jour": total}


def on_financial_doc_change(doc, method: str | None = None) -> None:
    """
    Hook appelé automatiquement via `hooks.py` (doc_events) lors de la validation (on_submit)
    ou de l'annulation (on_cancel) d'une facture, fiche de paie ou charge.
    """
    mois = extract_mois_from_doc(doc)
    if mois:
        refresh_budget_month(mois)
