frappe.ui.form.on("SE Facture Fournisseur", {
    refresh(frm) {
        if (frm.doc.docstatus === 1 && flt(frm.doc.reste_a_payer) > 0) {
            frm.add_custom_button(__("Régler (Décaissement)"), () => {
                frappe.new_doc("SE Decaissement", {
                    type_beneficiaire: "Fournisseur",
                    fournisseur: frm.doc.fournisseur,
                    beneficiaire: frm.doc.fournisseur,
                    facture_liee: frm.doc.name,
                    motif: `Règlement facture ${frm.doc.numero_facture_fournisseur} - ${frm.doc.objet}`,
                    montant: frm.doc.reste_a_payer,
                });
            }, __("Trésorerie"));
        }
    },
    montant_ht(frm) { frm.trigger("recalc"); },
    taux_tva(frm) { frm.trigger("recalc"); },
    recalc(frm) {
        const ht = flt(frm.doc.montant_ht);
        const tva = flt((ht * flt(frm.doc.taux_tva)) / 100.0, 2);
        const ttc = flt(ht + tva, 2);
        frm.set_value("montant_tva", tva);
        frm.set_value("montant_ttc", ttc);
        frm.set_value("reste_a_payer", Math.max(0, flt(ttc - flt(frm.doc.montant_paye), 2)));
    },
});
