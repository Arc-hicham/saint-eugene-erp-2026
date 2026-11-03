# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, flt

from saint_eugene.utils.fiscal_dz import get_hotel_settings


class SEPerformanceHoteliere(Document):
    def validate(self):
        if not self.chambres_disponibles:
            self.chambres_disponibles = cint(get_hotel_settings()["capacite_chambres"])

        dispo = cint(self.chambres_disponibles)
        vendues = cint(self.chambres_vendues)
        if dispo <= 0:
            frappe.throw(_("Le nombre de chambres disponibles doit être strictement supérieur à 0."))
        if vendues < 0 or vendues > dispo:
            frappe.throw(_("Les chambres vendues ({0}) doivent être comprises entre 0 et {1}.").format(vendues, dispo))

        ca_heb = flt(self.ca_hebergement, 2)
        self.taux_occupation = flt((vendues / dispo) * 100.0, 2)
        self.adr = flt(ca_heb / vendues, 2) if vendues > 0 else 0.0
        self.revpar = flt(ca_heb / dispo, 2)
        self.ca_total_jour = flt(ca_heb + flt(self.ca_restaurant) + flt(self.autres_revenus), 2)
