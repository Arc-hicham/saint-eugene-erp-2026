# -*- coding: utf-8 -*-
from frappe.model.document import Document
from frappe.utils import flt

from saint_eugene.api.dashboard import compute_tva_month


def compute_g50_due_date(mois: str) -> str:
    year_s, month_s = mois.split("-")
    year, month = int(year_s), int(month_s)
    if month == 12:
        return f"{year + 1:04d}-01-20"
    return f"{year:04d}-{month + 1:02d}-20"


class SEDeclarationTVA(Document):
    def validate(self):
        self.date_limite_g50 = compute_g50_due_date(self.mois)
        vals = compute_tva_month(self.mois, flt(self.precompte_anterieur))
        self.ca_ht = vals["ca_ht"]
        self.tva_collectee = vals["tva_collectee"]
        self.tva_deductible_achats = vals["tva_deductible_achats"]
        self.tva_deductible_charges = vals["tva_deductible_charges"]
        self.tva_deductible = vals["tva_deductible"]
        self.tva_a_payer = vals["tva_a_payer"]
        self.credit_tva = vals["credit_tva"]
        self.droits_timbre_collectes = vals["droits_timbre_collectes"]
        self.taxe_sejour_collectee = vals["taxe_sejour_collectee"]
        self.total_g50_a_payer = vals["total_g50_a_payer"]

        if self.date_paiement or self.total_g50_a_payer <= 0:
            self.solde_fiscal = 0.0
        else:
            self.solde_fiscal = self.total_g50_a_payer

    def on_submit(self):
        if self.total_g50_a_payer <= 0:
            st = "Crédit Reporté"
            solde = 0.0
        elif self.date_paiement:
            st = "Payée"
            solde = 0.0
        else:
            st = "Déclarée (G50)"
            solde = self.total_g50_a_payer
        self.db_set({"statut": st, "solde_fiscal": solde})

    def on_update_after_submit(self):
        if self.date_paiement:
            self.db_set({"statut": "Payée", "solde_fiscal": 0.0})

    def on_cancel(self):
        self.db_set({"statut": "Annulée", "solde_fiscal": 0.0})
