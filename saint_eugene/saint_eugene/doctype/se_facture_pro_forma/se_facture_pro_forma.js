frappe.ui.form.on("SE Facture Pro Forma", {
    refresh(frm) {
        if (!frm.is_new() && frm.doc.statut !== "Facturée") {
            frm.add_custom_button(__("Convertir en Facture Définitive"), () => {
                frappe.model.open_mapped_doc({
                    method: "saint_eugene.saint_eugene.doctype.se_facture_pro_forma.se_facture_pro_forma.make_invoice",
                    frm: frm,
                });
            }, __("Actions"));
        }
    },
    sejours_separes(frm) {
        frm.trigger("trigger_recalc");
    },
    taxe_sejour_incluse(frm) {
        frm.trigger("trigger_recalc");
    },
    appliquer_taxe_sejour(frm) {
        frm.trigger("trigger_recalc");
    },
    date_arrivee(frm) {
        frm.trigger("trigger_recalc");
    },
    date_depart(frm) {
        frm.trigger("trigger_recalc");
    },
    mode_paiement_prevu(frm) {
        frm.trigger("trigger_recalc");
    },
    trigger_recalc(frm) {
        if (!frm.doc.lignes || !frm.doc.lignes.length) return;
        frappe.call({
            method: "saint_eugene.utils.invoice_calc.preview_invoice",
            args: { doc: frm.doc },
            callback(r) {
                if (r.message && r.message.totals) {
                    $.extend(frm.doc, r.message.totals);
                    frm.refresh_fields();
                }
            }
        });
    }
});

frappe.ui.form.on("SE Ligne Facture Client", {
    montant_ttc_saisi(frm, cdt, cdn) { frm.trigger("trigger_recalc"); },
    article(frm, cdt, cdn) { frm.trigger("trigger_recalc"); },
    quantite(frm, cdt, cdn) { frm.trigger("trigger_recalc"); },
    nb_personnes(frm, cdt, cdn) { frm.trigger("trigger_recalc"); },
    sejour_no(frm, cdt, cdn) { frm.trigger("trigger_recalc"); },
    lignes_remove(frm) { frm.trigger("trigger_recalc"); }
});

frappe.ui.form.on("SE Sejour Facture Client", {
    date_arrivee(frm, cdt, cdn) { frm.trigger("trigger_recalc"); },
    date_depart(frm, cdt, cdn) { frm.trigger("trigger_recalc"); },
    sejours_remove(frm) { frm.trigger("trigger_recalc"); }
});
