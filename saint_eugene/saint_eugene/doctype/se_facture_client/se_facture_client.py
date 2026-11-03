# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, cint, date_diff, flt, getdate, nowdate

from saint_eugene.utils.fiscal_dz import (
    compute_droit_timbre_algerie,
    compute_taxe_sejour_algerie,
    get_hotel_settings,
    montant_dzd_en_lettres,
)


def compute_invoice_status_and_overdue(
    docstatus: int,
    montant_ttc: float,
    montant_encaisse: float,
    date_echeance,
) -> tuple[float, int, str]:
    """Détermine (reste_a_encaisser, jours_retard, statut) de manière déterministe."""
    reste = flt(max(0.0, flt(montant_ttc) - flt(montant_encaisse)), 2)
    today = getdate(nowdate())
    echeance = getdate(date_echeance) if date_echeance else today

    if docstatus == 0:
        return reste, 0, "Brouillon"
    if docstatus == 2:
        return reste, 0, "Annulée"

    if reste <= 0.01:
        return 0.0, 0, "Payée"

    retard = max(0, date_diff(today, echeance))
    if retard > 0:
        return reste, retard, "Échue"
    if flt(montant_encaisse) > 0:
        return reste, 0, "Partielle"
    return reste, 0, "Validée"


def sync_customer_invoice_payment(facture_name: str) -> None:
    """Recalcule le total encaissé via SUM SQL sur `SE Encaissement` et met à jour la facture."""
    if not facture_name or not frappe.db.exists("SE Facture Client", facture_name):
        return

    fac = frappe.db.get_value(
        "SE Facture Client",
        facture_name,
        ["docstatus", "montant_ttc", "date_echeance"],
        as_dict=True,
    )
    total_encaisse = flt(
        frappe.db.sql(
            """
            SELECT COALESCE(SUM(montant), 0)
            FROM `tabSE Encaissement`
            WHERE docstatus = 1 AND facture_liee = %s
            """,
            (facture_name,),
        )[0][0],
        2,
    )

    if total_encaisse > flt(fac.montant_ttc) + 0.01:
        frappe.throw(
            _("Le cumul des encaissements ({0} DZD) dépasse le TTC de la facture {1} ({2} DZD).").format(
                total_encaisse, facture_name, fac.montant_ttc
            )
        )

    reste, retard, statut = compute_invoice_status_and_overdue(
        fac.docstatus, fac.montant_ttc, total_encaisse, fac.date_echeance
    )
    frappe.db.set_value(
        "SE Facture Client",
        facture_name,
        {
            "montant_encaisse": total_encaisse,
            "reste_a_encaisser": reste,
            "jours_retard": retard,
            "statut": statut,
        },
    )


@frappe.whitelist()
def preview_invoice_taxes(
    montant_ht: float,
    taux_tva: float,
    nature_prestation: str,
    appliquer_taxe_sejour: int,
    nb_adultes: int,
    nuitees: int,
    mode_paiement_prevu: str,
) -> dict:
    """Calcul temps réel côté serveur appelé par le formulaire JS."""
    cfg = get_hotel_settings()
    ht = flt(montant_ht, 2)
    tva = flt(ht * flt(taux_tva) / 100.0, 2)
    taxe_sej = compute_taxe_sejour_algerie(
        nature_prestation=nature_prestation,
        appliquer=cint(appliquer_taxe_sejour),
        nb_adultes=cint(nb_adultes or 1),
        nuitees=cint(nuitees or 1),
        tarif_unitaire=flt(cfg["taxe_sejour_nuitee_adulte"]),
    )
    sous_total = flt(ht + tva + taxe_sej, 2)
    timbre = compute_droit_timbre_algerie(
        montant_base=sous_total,
        mode_paiement=mode_paiement_prevu,
        activer=cint(cfg["activer_droit_timbre_especes"]),
        plafond=flt(cfg["plafond_droit_timbre"]),
    )
    ttc = flt(sous_total + timbre, 2)
    return {
        "montant_tva": tva,
        "taxe_sejour": taxe_sej,
        "droit_timbre": timbre,
        "montant_ttc": ttc,
        "montant_en_lettres": montant_dzd_en_lettres(ttc),
    }


class SEFactureClient(Document):
    def validate(self):
        if flt(self.montant_ht) <= 0:
            frappe.throw(_("Le Montant HT doit être strictement positif."))

        if self.date_arrivee and self.date_depart:
            diff = date_diff(getdate(self.date_depart), getdate(self.date_arrivee))
            if diff < 0:
                frappe.throw(_("La date de départ ne peut pas être antérieure à la date d'arrivée."))
            self.nuitees = max(1, diff)
        else:
            self.nuitees = max(1, cint(self.nuitees or 1))

        self.nb_adultes = max(1, cint(self.nb_adultes or 1))

        if not self.date_echeance:
            delai = frappe.db.get_value("SE Client", self.client, "delai_paiement_jours")
            delai = 0 if self.type_client == "Passager" else (int(delai) if delai is not None else 30)
            self.date_echeance = add_days(self.date_facture, delai)

        res = preview_invoice_taxes(
            montant_ht=self.montant_ht,
            taux_tva=self.taux_tva,
            nature_prestation=self.nature_prestation,
            appliquer_taxe_sejour=self.appliquer_taxe_sejour,
            nb_adultes=self.nb_adultes,
            nuitees=self.nuitees,
            mode_paiement_prevu=self.mode_paiement_prevu,
        )
        self.montant_tva = res["montant_tva"]
        self.taxe_sejour = res["taxe_sejour"]
        self.droit_timbre = res["droit_timbre"]
        self.montant_ttc = res["montant_ttc"]
        self.montant_en_lettres = res["montant_en_lettres"]
        self.montant_encaisse = flt(self.montant_encaisse, 2)

        reste, retard, statut = compute_invoice_status_and_overdue(
            self.docstatus, self.montant_ttc, self.montant_encaisse, self.date_echeance
        )
        self.reste_a_encaisser = reste
        self.jours_retard = retard
        self.statut = statut

    def on_submit(self):
        reste, retard, statut = compute_invoice_status_and_overdue(
            1, self.montant_ttc, self.montant_encaisse, self.date_echeance
        )
        self.db_set({"reste_a_encaisser": reste, "jours_retard": retard, "statut": statut})

    def before_cancel(self):
        enc_lies = frappe.get_all(
            "SE Encaissement",
            filters={"facture_liee": self.name, "docstatus": 1},
            pluck="name",
        )
        if enc_lies:
            frappe.throw(
                _("Impossible d'annuler cette facture : annulez d'abord les encaissements liés ({0}).").format(
                    ", ".join(enc_lies)
                )
            )

    def on_cancel(self):
        self.db_set({"statut": "Annulée", "jours_retard": 0})
