# -*- coding: utf-8 -*-
"""
Tâches Planifiées Quotidiennes (Frappe Scheduler - Daily Cron)
1. Calcul quotidien des jours de retard sur les factures clients échues (+ statuts fournisseurs & contrats)
2. Génération d'alertes dans Frappe Desk (`Notification Log`) pour :
   - Factures clients échues
   - Chèques en portefeuille non encaissés (> 7 jours)
   - Dépassement de budget (Charges/Achats/Salaires > Budget Prévu)
   - Trésorerie disponible insuffisante (< Seuil critique de sécurité : 2 500 000 DZD)
"""
from __future__ import annotations

import frappe
from frappe.utils import cint, date_diff, flt, fmt_money, getdate, nowdate

from saint_eugene.utils.fiscal_dz import get_hotel_settings


def _get_alert_recipients() -> list[str]:
    """Retourne les utilisateurs destinataires des alertes financières (System Manager / Accounts Manager)."""
    users = frappe.db.sql_list(
        """
        SELECT DISTINCT u.name
        FROM `tabUser` u
        INNER JOIN `tabHas Role` hr ON hr.parent = u.name
        WHERE u.enabled = 1
          AND u.user_type = 'System User'
          AND u.name NOT IN ('Guest')
          AND hr.role IN ('System Manager', 'Accounts Manager')
        """
    )
    return users or ["Administrator"]


def _create_desk_notification(
    recipients: list[str],
    subject: str,
    message: str,
    document_type: str | None = None,
    document_name: str | None = None,
) -> None:
    """Crée une notification cloche dans Frappe Desk (sans doublon le même jour)."""
    today = nowdate()
    for user in recipients:
        already_sent = frappe.db.exists(
            "Notification Log",
            {
                "for_user": user,
                "subject": subject,
                "creation": [">=", f"{today} 00:00:00"],
            },
        )
        if already_sent:
            continue

        notif = frappe.get_doc(
            {
                "doctype": "Notification Log",
                "for_user": user,
                "from_user": "Administrator",
                "type": "Alert",
                "subject": subject,
                "email_content": message,
                "document_type": document_type,
                "document_name": document_name,
            }
        )
        notif.insert(ignore_permissions=True)


def update_overdue_invoices_and_contracts() -> dict:
    """
    Cron quotidien #1 :
    - Calcule `jours_retard` sur toutes les factures clients validées non soldées.
    - Bascule le statut en `Échue` dès que `date_echeance < aujourd'hui` et `reste_a_encaisser > 0`.
    - Met également à jour le statut `Échue` des factures fournisseurs et l'état des contrats.
    """
    today = getdate(nowdate())
    updated_cli = 0

    factures_clients = frappe.get_all(
        "SE Facture Client",
        filters={"docstatus": 1, "reste_a_encaisser": [">", 0]},
        fields=["name", "date_echeance", "montant_encaisse", "reste_a_encaisser", "statut"],
    )

    for fac in factures_clients:
        echeance = getdate(fac.date_echeance)
        retard = max(0, date_diff(today, echeance))
        if retard > 0:
            new_statut = "Échue"
        elif flt(fac.montant_encaisse) > 0:
            new_statut = "Partielle"
        else:
            new_statut = "Validée"

        frappe.db.set_value(
            "SE Facture Client",
            fac.name,
            {"jours_retard": retard, "statut": new_statut},
            update_modified=False,
        )
        updated_cli += 1

    # Factures fournisseurs échues
    factures_frn = frappe.get_all(
        "SE Facture Fournisseur",
        filters={"docstatus": 1, "reste_a_payer": [">", 0]},
        fields=["name", "date_echeance", "montant_paye"],
    )
    for ffrn in factures_frn:
        if date_diff(today, getdate(ffrn.date_echeance)) > 0:
            frappe.db.set_value(
                "SE Facture Fournisseur", ffrn.name, "statut", "Échue", update_modified=False
            )

    # Contrats proches de l'expiration ou expirés (préavis lu depuis SE Parametres Hotel)
    preavis_contrat = cint(get_hotel_settings()["delai_alerte_contrat_jours"]) or 30
    contrats = frappe.get_all(
        "SE Contrat et Abonnement",
        filters={"statut": ["!=", "Résilié"]},
        fields=["name", "date_fin"],
    )
    for ctr in contrats:
        days_left = date_diff(getdate(ctr.date_fin), today)
        if days_left < 0:
            new_st = "Expiré"
        elif days_left <= preavis_contrat:
            new_st = "À renouveler (< 30j)"
        else:
            new_st = "Actif"
        frappe.db.set_value("SE Contrat et Abonnement", ctr.name, "statut", new_st, update_modified=False)

    frappe.db.commit()
    return {"factures_clients_verifiees": updated_cli}


def run_daily_financial_alerts() -> dict:
    """
    Cron quotidien #2 :
    Génère les 4 familles d'alertes de contrôle de gestion (Frappe Notifications) :
    1. Factures clients échues
    2. Chèques non encaissés
    3. Dépassements budgétaires
    4. Trésorerie insuffisante
    """
    today = getdate(nowdate())
    cfg = get_hotel_settings()
    delai_cheque = cint(cfg["delai_alerte_cheque_jours"]) or 7
    seuil_treso = flt(cfg["seuil_tresorerie_critique"]) or 2_500_000.0
    recipients = _get_alert_recipients()
    alerts_sent = 0

    # 1. Alerte Factures Clients Échues
    factures_echues = frappe.get_all(
        "SE Facture Client",
        filters={"docstatus": 1, "statut": "Échue", "reste_a_encaisser": [">", 0]},
        fields=["name", "client", "reste_a_encaisser", "jours_retard"],
        order_by="jours_retard desc",
    )
    for fac in factures_echues[:10]:
        montant_str = fmt_money(fac.reste_a_encaisser, currency="DZD")
        _create_desk_notification(
            recipients=recipients,
            subject=f"[ALERTE RECOUVREMENT] Facture échue {fac.name} ({fac.jours_retard}j de retard)",
            message=(
                f"La facture client <b>{fac.name}</b> ({fac.client}) présente un impayé échu de "
                f"<b>{montant_str}</b> avec <b>{fac.jours_retard} jours</b> de retard."
            ),
            document_type="SE Facture Client",
            document_name=fac.name,
        )
        alerts_sent += 1

    # 2. Alerte Chèques Non Encaissés (> 7 jours en portefeuille)
    cheques_en_attente = frappe.get_all(
        "SE Encaissement",
        filters={
            "docstatus": 1,
            "mode_paiement": "Chèque",
            "statut_cheque": ["in", ["En portefeuille (Non encaissé)", "Remis en banque"]],
        },
        fields=["name", "client", "montant", "date_encaissement", "ref_paiement", "statut_cheque"],
    )
    for chq in cheques_en_attente:
        age = date_diff(today, getdate(chq.date_encaissement))
        if age >= delai_cheque:
            montant_str = fmt_money(chq.montant, currency="DZD")
            _create_desk_notification(
                recipients=recipients,
                subject=f"[ALERTE CHÈQUE] Chèque {chq.ref_paiement or chq.name} non encaissé ({age}j)",
                message=(
                    f"L'encaissement par chèque <b>{chq.name}</b> ({chq.client}) de <b>{montant_str}</b> "
                    f"est au statut <i>{chq.statut_cheque}</i> depuis {age} jours."
                ),
                document_type="SE Encaissement",
                document_name=chq.name,
            )
            alerts_sent += 1

    # 3. Alerte Dépassement de Budget
    depassements = frappe.get_all(
        "SE Budget Annuel",
        filters={"statut_budget": "Dépassement"},
        fields=["name", "mois", "categorie", "budget_prevu", "realise", "ecart_dzd", "ecart_pct"],
    )
    for dep in depassements:
        ecart_str = fmt_money(dep.ecart_dzd, currency="DZD")
        _create_desk_notification(
            recipients=recipients,
            subject=f"[ALERTE BUDGET] Dépassement {dep.categorie} ({dep.mois}) : +{dep.ecart_pct:.1f}%",
            message=(
                f"Le poste budgétaire <b>{dep.categorie}</b> du mois <b>{dep.mois}</b> dépasse le budget prévu "
                f"de <b>{ecart_str}</b> (+{dep.ecart_pct:.2f}%)."
            ),
            document_type="SE Budget Annuel",
            document_name=dep.name,
        )
        alerts_sent += 1

    # 4. Alerte Trésorerie Insuffisante
    treso_totale = flt(
        frappe.db.sql("SELECT COALESCE(SUM(solde_actuel), 0) FROM `tabSE Compte Tresorerie`")[0][0],
        2,
    )
    if treso_totale < seuil_treso:
        treso_str = fmt_money(treso_totale, currency="DZD")
        seuil_str = fmt_money(seuil_treso, currency="DZD")
        _create_desk_notification(
            recipients=recipients,
            subject=f"[ALERTE TRÉSORERIE CRITIQUE] Solde disponible : {treso_str}",
            message=(
                f"La trésorerie disponible cumulée (Caisses + Banques) est tombée à <b>{treso_str}</b>, "
                f"sous le seuil de sécurité fixé à <b>{seuil_str}</b>."
            ),
            document_type="SE Compte Tresorerie",
        )
        alerts_sent += 1

    frappe.db.commit()
    return {"alertes_generees": alerts_sent, "tresorerie_totale_dzd": treso_totale}
