# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from saint_eugene.saint_eugene.doctype.se_compte_tresorerie.se_compte_tresorerie import (
    recompute_treasury_account_balance,
)
from saint_eugene.saint_eugene.doctype.se_facture_client.se_facture_client import (
    sync_customer_invoice_payment,
)


class SEEncaissement(Document):
    def validate(self):
        if flt(self.montant) <= 0:
            frappe.throw(_("Le montant de l'encaissement doit être strictement supérieur à 0 DZD."))

        if self.mode_paiement == "Chèque":
            if not self.statut_cheque or self.statut_cheque == "N/A":
                self.statut_cheque = "En portefeuille (Non encaissé)"
        else:
            self.statut_cheque = "N/A"

        if self.facture_liee:
            fac = frappe.db.get_value(
                "SE Facture Client",
                self.facture_liee,
                ["client", "docstatus", "reste_a_encaisser"],
                as_dict=True,
            )
            if not fac or fac.docstatus != 1:
                frappe.throw(_("La facture liée {0} doit être validée avant d'être encaissée.").format(self.facture_liee))
            if fac.client != self.client:
                frappe.throw(_("Le client de l'encaissement ({0}) ne correspond pas à celui de la facture ({1}).").format(self.client, fac.client))
            if self.docstatus == 0 and flt(self.montant) > flt(fac.reste_a_encaisser) + 0.01:
                frappe.throw(
                    _("Le montant ({0} DZD) dépasse le reste à encaisser de la facture ({1} DZD).").format(
                        self.montant, fac.reste_a_encaisser
                    )
                )

    def on_submit(self):
        self.db_set("statut", "Validé")
        if self.facture_liee:
            sync_customer_invoice_payment(self.facture_liee)
        recompute_treasury_account_balance(self.compte_destination)
        self._create_bank_operation_if_needed()

    def on_cancel(self):
        self.db_set("statut", "Annulé")
        if self.facture_liee:
            sync_customer_invoice_payment(self.facture_liee)
        recompute_treasury_account_balance(self.compte_destination)
        self._delete_linked_bank_operation()

    def _create_bank_operation_if_needed(self):
        type_cpte = frappe.db.get_value("SE Compte Tresorerie", self.compte_destination, "type_compte")
        if type_cpte != "Banque":
            return
        type_op_map = {
            "Virement": "Virement Reçu",
            "Chèque": "Remise Chèque",
            "TPE": "Encaissement TPE/CIB",
            "Espèces": "Virement Reçu",
        }
        op = frappe.get_doc(
            {
                "doctype": "SE Operation Bancaire",
                "compte_bancaire": self.compte_destination,
                "date_operation": self.date_encaissement,
                "libelle": f"Encaissement {self.name} - {self.client}" + (f" ({self.facture_liee})" if self.facture_liee else ""),
                "type_operation": type_op_map.get(self.mode_paiement, "Virement Reçu"),
                "credit": flt(self.montant, 2),
                "debit": 0.0,
                "statut_pointage": "Non pointé",
                "document_source": f"SE Encaissement:{self.name}",
            }
        )
        op.insert(ignore_permissions=True)

    def _delete_linked_bank_operation(self):
        ops = frappe.get_all(
            "SE Operation Bancaire",
            filters={"document_source": f"SE Encaissement:{self.name}"},
            pluck="name",
        )
        for op_name in ops:
            frappe.delete_doc("SE Operation Bancaire", op_name, ignore_permissions=True)
