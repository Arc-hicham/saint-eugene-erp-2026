# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, flt, getdate, nowdate


class SEEmpruntetDette(Document):
    def validate(self):
        if flt(self.capital_initial) <= 0:
            frappe.throw(_("Le capital initial doit être supérieur à 0 DZD."))
        if flt(self.capital_rembourse) > flt(self.capital_initial):
            frappe.throw(_("Le capital remboursé ne peut pas dépasser le capital initial."))

        self.solde_restant = flt(flt(self.capital_initial) - flt(self.capital_rembourse), 2)
        if self.solde_restant <= 0.01:
            self.statut = "Soldé"
        elif self.prochaine_echeance and date_diff(getdate(nowdate()), getdate(self.prochaine_echeance)) > 0:
            self.statut = "En retard"
        else:
            self.statut = "En cours"
