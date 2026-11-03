# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, now_datetime

from saint_eugene.api.dashboard import compute_caisse_totals


class SECaisseMensuelle(Document):
    def validate(self):
        type_cpte = frappe.db.get_value("SE Compte Tresorerie", self.compte_caisse, "type_compte")
        if type_cpte and type_cpte != "Caisse":
            frappe.throw(_("Le compte sélectionné ({0}) doit être de type 'Caisse'.").format(self.compte_caisse))

        totals = compute_caisse_totals(self.mois, self.compte_caisse)
        self.total_encaissements = flt(totals["total_encaissements"], 2)
        self.total_decaissements = flt(totals["total_decaissements"], 2)
        self.solde_theorique = flt(
            flt(self.solde_initial) + self.total_encaissements - self.total_decaissements,
            2,
        )
        self.ecart = flt(flt(self.solde_physique) - self.solde_theorique, 2)

    def before_submit(self):
        if abs(flt(self.ecart)) >= 0.01 and not (self.justification or "").strip():
            frappe.throw(
                _("Un écart de caisse de {0} DZD a été détecté : une justification écrite est obligatoire avant signature.").format(
                    self.ecart
                )
            )

    def on_submit(self):
        self.db_set(
            {
                "statut_validation": "Validée",
                "valide_par": frappe.session.user,
                "date_validation": now_datetime(),
            }
        )

    def on_cancel(self):
        self.db_set("statut_validation", "Annulée")
