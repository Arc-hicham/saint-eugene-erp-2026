frappe.ui.form.on("SE Facture Client", {
    refresh(frm) {
        if (frm.doc.docstatus === 1 && flt(frm.doc.reste_a_encaisser) > 0) {
            frm.add_custom_button(__("Enregistrer un Encaissement"), () => {
                frappe.new_doc("SE Encaissement", {
                    client: frm.doc.client,
                    facture_liee: frm.doc.name,
                    montant: frm.doc.reste_a_encaisser,
                    mode_paiement: frm.doc.mode_paiement_prevu || "Virement",
                });
            }, __("Trésorerie"));
        }
    },
    montant_ht(frm) { frm.trigger("recalc_taxes"); },
    taux_tva(frm) { frm.trigger("recalc_taxes"); },
    nature_prestation(frm) { frm.trigger("recalc_taxes"); },
    appliquer_taxe_sejour(frm) { frm.trigger("recalc_taxes"); },
    nb_adultes(frm) { frm.trigger("recalc_taxes"); },
    date_arrivee(frm) { frm.trigger("update_nuitees"); },
    date_depart(frm) { frm.trigger("update_nuitees"); },
    mode_paiement_prevu(frm) { frm.trigger("recalc_taxes"); },
    update_nuitees(frm) {
        if (frm.doc.date_arrivee && frm.doc.date_depart) {
            const diff = frappe.datetime.get_day_diff(frm.doc.date_depart, frm.doc.date_arrivee);
            if (diff >= 0) {
                frm.set_value("nuitees", Math.max(1, diff));
            }
        }
        frm.trigger("recalc_taxes");
    },
    recalc_taxes(frm) {
        if (!frm.doc.montant_ht) return;
        frappe.call({
            method: "saint_eugene.saint_eugene.doctype.se_facture_client.se_facture_client.preview_invoice_taxes",
            args: {
                montant_ht: flt(frm.doc.montant_ht),
                taux_tva: flt(frm.doc.taux_tva),
                nature_prestation: frm.doc.nature_prestation || "Hébergement",
                appliquer_taxe_sejour: cint(frm.doc.appliquer_taxe_sejour),
                nb_adultes: cint(frm.doc.nb_adultes || 1),
                nuitees: cint(frm.doc.nuitees || 1),
                mode_paiement_prevu: frm.doc.mode_paiement_prevu || "Virement",
            },
            callback(r) {
                if (r.message) {
                    frm.set_value("montant_tva", r.message.montant_tva);
                    frm.set_value("taxe_sejour", r.message.taxe_sejour);
                    frm.set_value("droit_timbre", r.message.droit_timbre);
                    frm.set_value("montant_ttc", r.message.montant_ttc);
                    frm.set_value("montant_en_lettres", r.message.montant_en_lettres);
                    frm.set_value(
                        "reste_a_encaisser",
                        Math.max(0, flt(r.message.montant_ttc - flt(frm.doc.montant_encaisse), 2))
                    );
                }
            },
        });
    },
});
