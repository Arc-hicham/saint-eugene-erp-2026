# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from saint_eugene.saint_eugene.doctype.se_compte_tresorerie.se_compte_tresorerie import (
    recompute_treasury_account_balance,
)
from saint_eugene.saint_eugene.doctype.se_facture_fournisseur.se_facture_fournisseur import (
    sync_supplier_invoice_payment,
)


class SEDecaissement(Document):
    def validate(self):
        if flt(self.montant) <= 0:
            frappe.throw(_("Le montant du décaissement doit être strictement supérieur à 0 DZD."))

        if self.fournisseur and not self.beneficiaire:
            self.beneficiaire = self.fournisseur

        if self.facture_liee:
            fac = frappe.db.get_value(
                "SE Facture Fournisseur",
                self.facture_liee,
                ["fournisseur", "docstatus", "reste_a_payer"],
                as_dict=True,
            )
            if not fac or fac.docstatus != 1:
                frappe.throw(_("La facture fournisseur liée {0} doit être validée.").format(self.facture_liee))
            if self.docstatus == 0 and flt(self.montant) > flt(fac.reste_a_payer) + 0.01:
                frappe.throw(
                    _("Le montant ({0} DZD) dépasse le reste à payer de la facture ({1} DZD).").format(
                        self.montant, fac.reste_a_payer
                    )
                )

    def before_submit(self):
        if not self.validation_daf:
            frappe.throw(_("Le visa 'Bon à Payer (DAF)' doit être coché avant de valider le décaissement."))

    def on_submit(self):
        self.db_set("statut", "Validé")
        if self.facture_liee:
            sync_supplier_invoice_payment(self.facture_liee)
        recompute_treasury_account_balance(self.compte_source)
        self._create_bank_operation_if_needed()

    def on_cancel(self):
        self.db_set("statut", "Annulé")
        if self.facture_liee:
            sync_supplier_invoice_payment(self.facture_liee)
        recompute_treasury_account_balance(self.compte_source)
        self._delete_linked_bank_operation()

    def _create_bank_operation_if_needed(self):
        type_cpte = frappe.db.get_value("SE Compte Tresorerie", self.compte_source, "type_compte")
        if type_cpte != "Banque":
            return
        type_op = "Chèque Débité" if self.mode_paiement == "Chèque" else "Virement Émis"
        op = frappe.get_doc(
            {
                "doctype": "SE Operation Bancaire",
                "compte_bancaire": self.compte_source,
                "date_operation": self.date_decaissement,
                "libelle": f"Décaissement {self.name} - {self.beneficiaire} ({self.motif})",
                "type_operation": type_op,
                "debit": flt(self.montant, 2),
                "credit": 0.0,
                "statut_pointage": "Non pointé",
                "document_source": f"SE Decaissement:{self.name}",
            }
        )
        op.insert(ignore_permissions=True)

    def _delete_linked_bank_operation(self):
        ops = frappe.get_all(
            "SE Operation Bancaire",
            filters={"document_source": f"SE Decaissement:{self.name}"},
            pluck="name",
        )
        for op_name in ops:
            frappe.delete_doc("SE Operation Bancaire", op_name, ignore_permissions=True)
