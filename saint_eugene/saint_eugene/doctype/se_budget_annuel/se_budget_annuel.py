# -*- coding: utf-8 -*-
from frappe.model.document import Document
from frappe.utils import flt

from saint_eugene.api.budget_engine import (
    compute_realise_for_month_category,
    evaluate_budget_variance,
)


class SEBudgetAnnuel(Document):
    def validate(self):
        self.budget_prevu = flt(self.budget_prevu, 2)
        self.realise = compute_realise_for_month_category(self.mois, self.categorie)
        type_flux, ecart_dzd, ecart_pct, statut = evaluate_budget_variance(
            self.categorie, self.budget_prevu, self.realise
        )
        self.type_flux = type_flux
        self.ecart_dzd = ecart_dzd
        self.ecart_pct = ecart_pct
        self.statut_budget = statut
