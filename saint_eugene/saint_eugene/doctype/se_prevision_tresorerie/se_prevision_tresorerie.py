# -*- coding: utf-8 -*-
from frappe.model.document import Document
from frappe.utils import flt

from saint_eugene.api.dashboard import compute_treasury_forecast


class SEPrevisionTresorerie(Document):
    def validate(self):
        data = compute_treasury_forecast(self.date_prevision)
        for key, val in data.items():
            setattr(self, key, val)

        seuil = flt(self.seuil_alerte_minimum) or 2_500_000.0
        if flt(self.tresorerie_nette_30j) < 0 or flt(self.solde_actuel_total) < seuil * 0.5:
            self.niveau_risque = "Critique"
        elif flt(self.tresorerie_nette_30j) < seuil:
            self.niveau_risque = "Sous Tension"
        else:
            self.niveau_risque = "Sain"
