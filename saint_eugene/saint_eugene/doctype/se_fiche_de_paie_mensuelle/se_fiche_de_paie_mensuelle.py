# -*- coding: utf-8 -*-
from frappe.model.document import Document
from frappe.utils import flt


def compute_irg_algerie(revenu_imposable: float) -> float:
    """
    Calcule l'IRG mensuel selon le barème progressif algérien en vigueur (LF 2022/2026) :
    - Exonération totale si revenu imposable <= 30 000 DZD
    - Tranches progressives + abattement 40% (min 1 000 DZD, max 1 500 DZD)
    - Décote de lissage pour les revenus entre 30 000 et 35 000 DZD.
    """
    rev = flt(revenu_imposable)
    if rev <= 30_000.0:
        return 0.0

    tranches = [
        (20_000.0, 0.00),
        (40_000.0, 0.23),
        (80_000.0, 0.27),
        (160_000.0, 0.30),
        (320_000.0, 0.33),
        (float("inf"), 0.35),
    ]
    impot_brut = 0.0
    plancher = 0.0
    for plafond, taux in tranches:
        if rev <= plancher:
            break
        base_tranche = min(rev, plafond) - plancher
        impot_brut += base_tranche * taux
        plancher = plafond

    abattement = min(max(impot_brut * 0.40, 1_000.0), 1_500.0)
    irg = max(0.0, impot_brut - abattement)

    if 30_000.0 < rev < 35_000.0:
        irg = irg * (137.0 / 51.0) - (27_925.0 / 8.0)
        irg = max(0.0, irg)

    return flt(irg, 2)


class SEFichedePaieMensuelle(Document):
    def validate(self):
        assiette_cnas = flt(self.salaire_base) + flt(self.primes)
        self.retenue_cnas = flt(assiette_cnas * 0.09, 2)
        self.charges_patronales_cnas = flt(assiette_cnas * 0.26, 2)

        imposable = max(0.0, assiette_cnas - self.retenue_cnas)
        if self.auto_calcul_irg:
            self.retenue_irg = compute_irg_algerie(imposable)

        self.salaire_brut = flt(flt(self.salaire_base) + flt(self.primes) + flt(self.indemnites), 2)
        self.total_retenues = flt(
            self.retenue_cnas + flt(self.retenue_irg) + flt(self.autres_retenues),
            2,
        )
        self.net_a_payer = flt(max(0.0, self.salaire_brut - self.total_retenues), 2)

        if self.docstatus == 0:
            self.statut = "Brouillon"

    def on_submit(self):
        new_st = "Payée" if (self.ref_paiement or "").strip() else "Validée"
        self.db_set("statut", new_st)

    def on_cancel(self):
        self.db_set("statut", "Annulée")
