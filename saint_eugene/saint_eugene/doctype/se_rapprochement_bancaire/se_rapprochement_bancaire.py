# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from saint_eugene.api.budget_engine import get_month_bounds


@frappe.whitelist()
def get_book_balance_at_month_end(mois: str, compte_bancaire: str) -> float:
    """Calcule le solde comptable théorique (512) à la clôture du mois demandé."""
    _, end_date = get_month_bounds(mois)
    solde_init = flt(frappe.db.get_value("SE Compte Tresorerie", compte_bancaire, "solde_initial"))
    enc = flt(
        frappe.db.sql(
            """
            SELECT COALESCE(SUM(montant), 0)
            FROM `tabSE Encaissement`
            WHERE docstatus = 1 AND compte_destination = %s AND date_encaissement <= %s
            """,
            (compte_bancaire, end_date),
        )[0][0]
    )
    dec = flt(
        frappe.db.sql(
            """
            SELECT COALESCE(SUM(montant), 0)
            FROM `tabSE Decaissement`
            WHERE docstatus = 1 AND compte_source = %s AND date_decaissement <= %s
            """,
            (compte_bancaire, end_date),
        )[0][0]
    )
    return flt(solde_init + enc - dec, 2)


class SERapprochementBancaire(Document):
    def validate(self):
        ajouter = 0.0
        deduire = 0.0
        for row in self.lignes_suspens or []:
            if row.sens == "À ajouter au relevé (+)":
                ajouter += flt(row.montant)
            else:
                deduire += flt(row.montant)

        self.total_a_ajouter = flt(ajouter, 2)
        self.total_a_deduire = flt(deduire, 2)
        self.solde_releve_corrige = flt(
            flt(self.solde_releve_bancaire) + self.total_a_ajouter - self.total_a_deduire,
            2,
        )
        self.ecart_final = flt(self.solde_releve_corrige - flt(self.solde_comptable), 2)

        if self.docstatus == 0:
            self.statut = "Équilibré" if abs(self.ecart_final) < 0.01 else "Avec Écart"

    def before_submit(self):
        if abs(flt(self.ecart_final)) >= 0.01:
            frappe.throw(
                _("Validation refusée : l'état de rapprochement présente encore un écart non justifié de {0} DZD.").format(
                    self.ecart_final
                )
            )

    def on_submit(self):
        self.db_set("statut", "Validé")
        start_date, end_date = get_month_bounds(self.mois)
        frappe.db.sql(
            """
            UPDATE `tabSE Operation Bancaire`
            SET statut_pointage = 'Pointé'
            WHERE compte_bancaire = %s AND date_operation BETWEEN %s AND %s
            """,
            (self.compte_bancaire, start_date, end_date),
        )

    def on_cancel(self):
        self.db_set("statut", "Annulé")
