# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt


class SEOperationBancaire(Document):
    def validate(self):
        if flt(self.debit) < 0 or flt(self.credit) < 0:
            frappe.throw(_("Les montants Débit et Crédit doivent être positifs."))
        if flt(self.debit) == 0 and flt(self.credit) == 0:
            frappe.throw(_("Veuillez renseigner un montant au Débit ou au Crédit."))

        solde_init = flt(frappe.db.get_value("SE Compte Tresorerie", self.compte_bancaire, "solde_initial"))
        cumul = frappe.db.sql(
            """
            SELECT COALESCE(SUM(credit - debit), 0)
            FROM `tabSE Operation Bancaire`
            WHERE compte_bancaire = %s
              AND date_operation <= %s
              AND name != %s
            """,
            (self.compte_bancaire, self.date_operation, self.name or ""),
        )[0][0]
        self.solde_progressif = flt(solde_init + flt(cumul) + flt(self.credit) - flt(self.debit), 2)
