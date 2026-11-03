# -*- coding: utf-8 -*-
"""
Endpoints API Whitelistés pour le Tableau de Bord Direction Saint Eugène 2026
et les assistants de calcul côté client (JS).
"""
from __future__ import annotations

import frappe
from frappe.utils import add_days, flt, getdate, nowdate

from saint_eugene.api.budget_engine import get_month_bounds


@frappe.whitelist()
def get_resultat_mensuel(mois: str | None = None) -> dict:
    """
    Number Card Custom KPI : Résultat Net d'Exploitation Mensuel (SCF) en DZD.
    Formule : CA Total HT (Classe 70) - Achats HT (Classe 60) - Charges HT (Classes 61/62) - Masse Salariale Brute (Classe 63).
    Si `mois` n'est pas fourni, utilise le dernier mois de 2026 ayant une activité (ou le mois courant).
    """
    if not mois:
        today = getdate(nowdate())
        default_mois = f"2026-{today.month:02d}" if today.year == 2026 else None
        if default_mois and frappe.db.exists("SE Facture Client", {"docstatus": 1}):
            latest = frappe.db.sql(
                """
                SELECT DATE_FORMAT(MAX(date_facture), '%%Y-%%m')
                FROM `tabSE Facture Client`
                WHERE docstatus = 1
                """
            )
            mois = (latest[0][0] if latest and latest[0][0] else None) or default_mois or "2026-01"
        else:
            mois = "2026-01"

    start_date, end_date = get_month_bounds(mois)

    ca_ht = flt(
        frappe.db.sql(
            """
            SELECT COALESCE(SUM(montant_ht), 0)
            FROM `tabSE Facture Client`
            WHERE docstatus = 1 AND date_facture BETWEEN %s AND %s
            """,
            (start_date, end_date),
        )[0][0]
    )

    achats_ht = flt(
        frappe.db.sql(
            """
            SELECT COALESCE(SUM(montant_ht), 0)
            FROM `tabSE Facture Fournisseur`
            WHERE docstatus = 1 AND date_facture BETWEEN %s AND %s
            """,
            (start_date, end_date),
        )[0][0]
    )

    charges_ht = flt(
        frappe.db.sql(
            """
            SELECT COALESCE(SUM(montant_ht), 0)
            FROM `tabSE Charge et Depense`
            WHERE docstatus = 1 AND date_charge BETWEEN %s AND %s
            """,
            (start_date, end_date),
        )[0][0]
    )

    salaires_bruts = flt(
        frappe.db.sql(
            """
            SELECT COALESCE(SUM(salaire_brut), 0)
            FROM `tabSE Fiche de Paie Mensuelle`
            WHERE docstatus = 1 AND mois = %s
            """,
            (mois,),
        )[0][0]
    )

    resultat = flt(ca_ht - achats_ht - charges_ht - salaires_bruts, 2)
    return {
        "value": resultat,
        "fieldtype": "Currency",
        "mois": mois,
    }


@frappe.whitelist()
def compute_caisse_totals(mois: str, compte_caisse: str) -> dict:
    """Calcule les encaissements et décaissements validés sur une caisse pour un mois donné."""
    start_date, end_date = get_month_bounds(mois)

    enc = flt(
        frappe.db.sql(
            """
            SELECT COALESCE(SUM(montant), 0)
            FROM `tabSE Encaissement`
            WHERE docstatus = 1
              AND compte_destination = %s
              AND date_encaissement BETWEEN %s AND %s
            """,
            (compte_caisse, start_date, end_date),
        )[0][0],
        2,
    )

    dec = flt(
        frappe.db.sql(
            """
            SELECT COALESCE(SUM(montant), 0)
            FROM `tabSE Decaissement`
            WHERE docstatus = 1
              AND compte_source = %s
              AND date_decaissement BETWEEN %s AND %s
            """,
            (compte_caisse, start_date, end_date),
        )[0][0],
        2,
    )

    return {"total_encaissements": enc, "total_decaissements": dec}


@frappe.whitelist()
def compute_tva_month(mois: str, precompte_anterieur: float = 0.0) -> dict:
    """Calcule les montants G50 (CA HT, TVA collectée, Droits de Timbre, Taxe de Séjour, TVA déductible) pour un mois."""
    start_date, end_date = get_month_bounds(mois)

    ca_row = frappe.db.sql(
        """
        SELECT
            COALESCE(SUM(montant_ht), 0),
            COALESCE(SUM(montant_tva), 0),
            COALESCE(SUM(droit_timbre), 0),
            COALESCE(SUM(taxe_sejour), 0)
        FROM `tabSE Facture Client`
        WHERE docstatus = 1 AND date_facture BETWEEN %s AND %s
        """,
        (start_date, end_date),
    )[0]

    tva_achats = flt(
        frappe.db.sql(
            """
            SELECT COALESCE(SUM(montant_tva), 0)
            FROM `tabSE Facture Fournisseur`
            WHERE docstatus = 1 AND date_facture BETWEEN %s AND %s
            """,
            (start_date, end_date),
        )[0][0],
        2,
    )

    tva_charges = flt(
        frappe.db.sql(
            """
            SELECT COALESCE(SUM(montant_tva), 0)
            FROM `tabSE Charge et Depense`
            WHERE docstatus = 1 AND date_charge BETWEEN %s AND %s
            """,
            (start_date, end_date),
        )[0][0],
        2,
    )

    ca_ht = flt(ca_row[0], 2)
    tva_collectee = flt(ca_row[1], 2)
    droits_timbre = flt(ca_row[2], 2)
    taxe_sejour = flt(ca_row[3], 2)
    precompte = flt(precompte_anterieur, 2)
    tva_deductible = flt(tva_achats + tva_charges + precompte, 2)
    tva_a_payer = flt(max(0.0, tva_collectee - tva_deductible), 2)
    credit_tva = flt(max(0.0, tva_deductible - tva_collectee), 2)
    total_g50 = flt(tva_a_payer + droits_timbre + taxe_sejour, 2)

    return {
        "ca_ht": ca_ht,
        "tva_collectee": tva_collectee,
        "tva_deductible_achats": tva_achats,
        "tva_deductible_charges": tva_charges,
        "tva_deductible": tva_deductible,
        "tva_a_payer": tva_a_payer,
        "credit_tva": credit_tva,
        "droits_timbre_collectes": droits_timbre,
        "taxe_sejour_collectee": taxe_sejour,
        "total_g50_a_payer": total_g50,
    }


@frappe.whitelist()
def compute_treasury_forecast(date_reference: str | None = None) -> dict:
    """
    Calcule en temps réel la position de trésorerie actuelle (Caisses + Banques)
    et les flux d'encaissements/décaissements attendus à 7j, 30j et 90j.
    """
    ref = getdate(date_reference or nowdate())

    solde_caisses = flt(
        frappe.db.sql(
            "SELECT COALESCE(SUM(solde_actuel), 0) FROM `tabSE Compte Tresorerie` WHERE type_compte = 'Caisse'"
        )[0][0],
        2,
    )
    solde_banques = flt(
        frappe.db.sql(
            "SELECT COALESCE(SUM(solde_actuel), 0) FROM `tabSE Compte Tresorerie` WHERE type_compte = 'Banque'"
        )[0][0],
        2,
    )

    def _expected_inflows(days: int) -> float:
        horizon = add_days(ref, days)
        return flt(
            frappe.db.sql(
                """
                SELECT COALESCE(SUM(reste_a_encaisser), 0)
                FROM `tabSE Facture Client`
                WHERE docstatus = 1
                  AND reste_a_encaisser > 0
                  AND date_echeance <= %s
                """,
                (horizon,),
            )[0][0],
            2,
        )

    def _expected_outflows(days: int) -> float:
        horizon = add_days(ref, days)
        factures_frn = flt(
            frappe.db.sql(
                """
                SELECT COALESCE(SUM(reste_a_payer), 0)
                FROM `tabSE Facture Fournisseur`
                WHERE docstatus = 1
                  AND reste_a_payer > 0
                  AND date_echeance <= %s
                """,
                (horizon,),
            )[0][0]
        )
        contrats = flt(
            frappe.db.sql(
                """
                SELECT COALESCE(SUM(montant_echeance), 0)
                FROM `tabSE Contrat et Abonnement`
                WHERE statut IN ('Actif', 'À renouveler (< 30j)')
                  AND prochaine_echeance BETWEEN %s AND %s
                """,
                (ref, horizon),
            )[0][0]
        )
        emprunts = flt(
            frappe.db.sql(
                """
                SELECT COALESCE(SUM(mensualite), 0)
                FROM `tabSE Emprunt et Dette`
                WHERE statut = 'En cours'
                  AND solde_restant > 0
                  AND prochaine_echeance BETWEEN %s AND %s
                """,
                (ref, horizon),
            )[0][0]
        )
        tva_due = flt(
            frappe.db.sql(
                """
                SELECT COALESCE(SUM(solde_fiscal), 0)
                FROM `tabSE Declaration TVA`
                WHERE docstatus = 1
                  AND solde_fiscal > 0
                  AND date_limite_g50 <= %s
                """,
                (horizon,),
            )[0][0]
        )
        return flt(factures_frn + contrats + emprunts + tva_due, 2)

    enc_7, enc_30, enc_90 = _expected_inflows(7), _expected_inflows(30), _expected_inflows(90)
    dec_7, dec_30, dec_90 = _expected_outflows(7), _expected_outflows(30), _expected_outflows(90)
    total_actuel = flt(solde_caisses + solde_banques, 2)

    return {
        "solde_caisses": solde_caisses,
        "solde_banques": solde_banques,
        "solde_actuel_total": total_actuel,
        "encaissements_prevus_7j": enc_7,
        "encaissements_prevus_30j": enc_30,
        "encaissements_prevus_90j": enc_90,
        "decaissements_prevus_7j": dec_7,
        "decaissements_prevus_30j": dec_30,
        "decaissements_prevus_90j": dec_90,
        "tresorerie_nette_30j": flt(total_actuel + enc_30 - dec_30, 2),
        "tresorerie_nette_90j": flt(total_actuel + enc_90 - dec_90, 2),
    }
