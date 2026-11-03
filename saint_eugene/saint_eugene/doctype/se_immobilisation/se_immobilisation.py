# -*- coding: utf-8 -*-
from datetime import date

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, date_diff, flt, getdate


class SEImmobilisation(Document):
    def validate(self):
        val = flt(self.valeur_acquisition)
        duree = cint(self.duree_amortissement)
        if val <= 0 or duree <= 0:
            frappe.throw(_("La valeur d'acquisition et la durée d'amortissement doivent être strictement positives."))

        self.dotation_annuelle = flt(val / duree, 2)

        # Prorata temporis linéaire SCF arrêté à la clôture de l'exercice 2026 (31/12/2026)
        cloture_2026 = date(2026, 12, 31)
        acq = getdate(self.date_acquisition)
        jours_utilises = max(0, date_diff(cloture_2026, acq))
        annees_ecoulees = jours_utilises / 365.0

        cumul = min(val, flt(self.dotation_annuelle * annees_ecoulees, 2))
        self.amortissements_cumules = cumul
        self.vnc = flt(max(0.0, val - cumul), 2)
        self.statut = "Totalement amorti" if self.vnc <= 0.01 else "En service"
