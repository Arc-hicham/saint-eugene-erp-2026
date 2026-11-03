# -*- coding: utf-8 -*-
import frappe
from frappe.model.document import Document
from frappe.utils import flt


def recompute_treasury_account_balance(compte_name: str) -> float:
    """Recalcule de manière idempotente le solde actuel d'une Caisse ou Banque."""
    if not compte_name or not frappe.db.exists("SE Compte Tresorerie", compte_name):
        return 0.0

    solde_initial = flt(frappe.db.get_value("SE Compte Tresorerie", compte_name, "solde_initial"))
    enc = flt(
        frappe.db.sql(
            """
            SELECT COALESCE(SUM(montant), 0)
            FROM `tabSE Encaissement`
            WHERE docstatus = 1 AND compte_destination = %s
            """,
            (compte_name,),
        )[0][0]
    )
    dec = flt(
        frappe.db.sql(
            """
            SELECT COALESCE(SUM(montant), 0)
            FROM `tabSE Decaissement`
            WHERE docstatus = 1 AND compte_source = %s
            """,
            (compte_name,),
        )[0][0]
    )
    solde = flt(solde_initial + enc - dec, 2)
    frappe.db.set_value("SE Compte Tresorerie", compte_name, "solde_actuel", solde, update_modified=False)
    return solde


class SECompteTresorerie(Document):
    def validate(self):
        if self.is_new():
            self.solde_actuel = flt(self.solde_initial, 2)
        else:
            enc = flt(
                frappe.db.sql(
                    "SELECT COALESCE(SUM(montant), 0) FROM `tabSE Encaissement` WHERE docstatus=1 AND compte_destination=%s",
                    (self.name,),
                )[0][0]
            )
            dec = flt(
                frappe.db.sql(
                    "SELECT COALESCE(SUM(montant), 0) FROM `tabSE Decaissement` WHERE docstatus=1 AND compte_source=%s",
                    (self.name,),
                )[0][0]
            )
            self.solde_actuel = flt(flt(self.solde_initial) + enc - dec, 2)
