# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt


class SEParametresHotel(Document):
    def validate(self):
        if cint(self.capacite_chambres) <= 0:
            frappe.throw(_("La capacité en chambres doit être supérieure à 0."))
        if flt(self.seuil_tresorerie_critique) < 0:
            frappe.throw(_("Le seuil critique de trésorerie ne peut pas être négatif."))
        frappe.clear_document_cache("SE Parametres Hotel", "SE Parametres Hotel")
