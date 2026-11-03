# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, getdate, nowdate


class SEContratetAbonnement(Document):
    def validate(self):
        if getdate(self.date_fin) < getdate(self.date_debut):
            frappe.throw(_("La date de fin du contrat ne peut pas être antérieure à la date de début."))

        if self.statut != "Résilié":
            days_left = date_diff(getdate(self.date_fin), getdate(nowdate()))
            if days_left < 0:
                self.statut = "Expiré"
            elif days_left <= 30:
                self.statut = "À renouveler (< 30j)"
            else:
                self.statut = "Actif"
