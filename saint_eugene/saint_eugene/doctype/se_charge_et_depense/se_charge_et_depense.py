# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

SCF_MAP = {
    "Électricité & Gaz (Sonelgaz)": "607100",
    "Eau (SEAAL)": "607200",
    "Internet & Télécom": "626000",
    "Maintenance & Réparations": "615000",
    "Assurances": "616000",
    "Marketing & Commissions OTA": "623000",
    "Honoraires (CAC / Conseil)": "622600",
    "Impôts & Taxes Locales": "645000",
    "Frais Généraux": "628000",
}


class SEChargeetDepense(Document):
    def validate(self):
        if flt(self.montant_ht) <= 0:
            frappe.throw(_("Le Montant HT de la charge doit être supérieur à 0 DZD."))
        self.compte_scf = SCF_MAP.get(self.nature, "628000")
        self.montant_tva = flt(flt(self.montant_ht) * flt(self.taux_tva) / 100.0, 2)
        self.montant_ttc = flt(flt(self.montant_ht) + self.montant_tva, 2)
