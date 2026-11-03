# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, date_diff, flt, getdate, nowdate


def compute_supplier_invoice_status(
    docstatus: int, montant_ttc: float, montant_paye: float, date_echeance
) -> tuple[float, str]:
    reste = flt(max(0.0, flt(montant_ttc) - flt(montant_paye)), 2)
    today = getdate(nowdate())
    echeance = getdate(date_echeance) if date_echeance else today

    if docstatus == 0:
        return reste, "Brouillon"
    if docstatus == 2:
        return reste, "Annulée"
    if reste <= 0.01:
        return 0.0, "Payée"
    if date_diff(today, echeance) > 0:
        return reste, "Échue"
    if flt(montant_paye) > 0:
        return reste, "Partielle"
    return reste, "Validée"


def sync_supplier_invoice_payment(facture_name: str) -> None:
    if not facture_name or not frappe.db.exists("SE Facture Fournisseur", facture_name):
        return

    fac = frappe.db.get_value(
        "SE Facture Fournisseur",
        facture_name,
        ["docstatus", "montant_ttc", "date_echeance"],
        as_dict=True,
    )
    total_paye = flt(
        frappe.db.sql(
            """
            SELECT COALESCE(SUM(montant), 0)
            FROM `tabSE Decaissement`
            WHERE docstatus = 1 AND facture_liee = %s
            """,
            (facture_name,),
        )[0][0],
        2,
    )

    if total_paye > flt(fac.montant_ttc) + 0.01:
        frappe.throw(
            _("Le cumul des décaissements ({0} DZD) dépasse le TTC de la facture fournisseur {1} ({2} DZD).").format(
                total_paye, facture_name, fac.montant_ttc
            )
        )

    reste, statut = compute_supplier_invoice_status(
        fac.docstatus, fac.montant_ttc, total_paye, fac.date_echeance
    )
    frappe.db.set_value(
        "SE Facture Fournisseur",
        facture_name,
        {
            "montant_paye": total_paye,
            "reste_a_payer": reste,
            "statut": statut,
        },
    )


class SEFactureFournisseur(Document):
    def validate(self):
        if flt(self.montant_ht) <= 0:
            frappe.throw(_("Le Montant HT doit être strictement positif."))
        if not self.date_echeance:
            self.date_echeance = add_days(self.date_facture, 30)

        self.montant_tva = flt(flt(self.montant_ht) * flt(self.taux_tva) / 100.0, 2)
        self.montant_ttc = flt(flt(self.montant_ht) + self.montant_tva, 2)
        self.montant_paye = flt(self.montant_paye, 2)

        reste, statut = compute_supplier_invoice_status(
            self.docstatus, self.montant_ttc, self.montant_paye, self.date_echeance
        )
        self.reste_a_payer = reste
        self.statut = statut

    def on_submit(self):
        reste, statut = compute_supplier_invoice_status(
            1, self.montant_ttc, self.montant_paye, self.date_echeance
        )
        self.db_set({"reste_a_payer": reste, "statut": statut})

    def before_cancel(self):
        dec_lies = frappe.get_all(
            "SE Decaissement",
            filters={"facture_liee": self.name, "docstatus": 1},
            pluck="name",
        )
        if dec_lies:
            frappe.throw(
                _("Impossible d'annuler : annulez d'abord les décaissements liés ({0}).").format(
                    ", ".join(dec_lies)
                )
            )

    def on_cancel(self):
        self.db_set("statut", "Annulée")
