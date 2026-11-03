# -*- coding: utf-8 -*-
from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, date_diff, flt, getdate, nowdate

from saint_eugene.utils.fiscal_dz import (
    compute_droit_timbre_algerie,
    get_hotel_settings,
    montant_dzd_en_lettres,
)
from saint_eugene.utils.invoice_calc import apply_to_frappe_doc


def compute_invoice_status_and_overdue(
    docstatus: int,
    montant_ttc: float,
    montant_encaisse: float,
    date_echeance,
) -> tuple[float, int, str]:
    """Détermine (reste_a_encaisser, jours_retard, statut) de manière déterministe."""
    reste = flt(max(0.0, flt(montant_ttc) - flt(montant_encaisse)), 2)
    today = getdate(nowdate())
    echeance = getdate(date_echeance) if date_echeance else today

    if docstatus == 0:
        return reste, 0, "Brouillon"
    if docstatus == 2:
        return reste, 0, "Annulée"

    if reste <= 0.01:
        return 0.0, 0, "Payée"

    retard = max(0, date_diff(today, echeance))
    if retard > 0:
        return reste, retard, "Échue"
    if flt(montant_encaisse) > 0:
        return reste, 0, "Partielle"
    return reste, 0, "Validée"


def sync_customer_invoice_payment(facture_name: str) -> None:
    """Recalcule le total encaissé via SUM SQL sur `SE Encaissement` et met à jour la facture."""
    if not facture_name or not frappe.db.exists("SE Facture Client", facture_name):
        return

    fac = frappe.db.get_value(
        "SE Facture Client",
        facture_name,
        ["docstatus", "montant_ttc", "date_echeance"],
        as_dict=True,
    )
    total_encaisse = flt(
        frappe.db.sql(
            """
            SELECT COALESCE(SUM(montant), 0)
            FROM `tabSE Encaissement`
            WHERE docstatus = 1 AND facture_liee = %s
            """,
            (facture_name,),
        )[0][0],
        2,
    )

    if total_encaisse > flt(fac.montant_ttc) + 0.01:
        frappe.throw(
            _("Le cumul des encaissements ({0} DZD) dépasse le TTC de la facture {1} ({2} DZD).").format(
                total_encaisse, facture_name, fac.montant_ttc
            )
        )

    reste, retard, statut = compute_invoice_status_and_overdue(
        fac.docstatus, fac.montant_ttc, total_encaisse, fac.date_echeance
    )
    frappe.db.set_value(
        "SE Facture Client",
        facture_name,
        {
            "montant_encaisse": total_encaisse,
            "reste_a_encaisser": reste,
            "jours_retard": retard,
            "statut": statut,
        },
    )


class SEFactureClient(Document):
    def validate(self):
        if not self.date_echeance:
            delai = frappe.db.get_value("SE Client", self.client, "delai_paiement_jours")
            delai = 0 if self.type_client == "Passager" else (int(delai) if delai is not None else 30)
            self.date_echeance = add_days(self.date_facture, delai)

        apply_to_frappe_doc(self)

        self.montant_encaisse = flt(self.montant_encaisse, 2)
        reste, retard, statut = compute_invoice_status_and_overdue(
            self.docstatus, self.montant_ttc, self.montant_encaisse, self.date_echeance
        )
        self.reste_a_encaisser = reste
        self.jours_retard = retard
        self.statut = statut

    def on_submit(self):
        reste, retard, statut = compute_invoice_status_and_overdue(
            1, self.montant_ttc, self.montant_encaisse, self.date_echeance
        )
        self.db_set({"reste_a_encaisser": reste, "jours_retard": retard, "statut": statut})

    def before_cancel(self):
        enc_lies = frappe.get_all(
            "SE Encaissement",
            filters={"facture_liee": self.name, "docstatus": 1},
            pluck="name",
        )
        if enc_lies:
            frappe.throw(
                _("Impossible d'annuler cette facture : annulez d'abord les encaissements liés ({0}).").format(
                    ", ".join(enc_lies)
                )
            )

    def on_cancel(self):
        self.db_set({"statut": "Annulée", "jours_retard": 0})
