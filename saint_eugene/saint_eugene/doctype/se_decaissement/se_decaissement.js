frappe.ui.form.on("SE Decaissement", {
    setup(frm) {
        frm.set_query("facture_liee", () => {
            const filters = { docstatus: 1, reste_a_payer: [">", 0] };
            if (frm.doc.fournisseur) {
                filters.fournisseur = frm.doc.fournisseur;
            }
            return { filters };
        });
    },
    fournisseur(frm) {
        if (frm.doc.fournisseur) {
            frm.set_value("beneficiaire", frm.doc.fournisseur);
        }
    },
    facture_liee(frm) {
        if (!frm.doc.facture_liee) return;
        frappe.db.get_value(
            "SE Facture Fournisseur",
            frm.doc.facture_liee,
            ["fournisseur", "reste_a_payer", "objet", "numero_facture_fournisseur"],
            (r) => {
                if (r) {
                    frm.set_value("fournisseur", r.fournisseur);
                    frm.set_value("beneficiaire", r.fournisseur);
                    frm.set_value("montant", flt(r.reste_a_payer));
                    if (!frm.doc.motif) {
                        frm.set_value("motif", `Règlement facture ${r.numero_facture_fournisseur} - ${r.objet}`);
                    }
                }
            }
        );
    },
});
