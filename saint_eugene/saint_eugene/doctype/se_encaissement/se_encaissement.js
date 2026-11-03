frappe.ui.form.on("SE Encaissement", {
    setup(frm) {
        frm.set_query("facture_liee", () => {
            const filters = { docstatus: 1, reste_a_encaisser: [">", 0] };
            if (frm.doc.client) {
                filters.client = frm.doc.client;
            }
            return { filters };
        });
    },
    facture_liee(frm) {
        if (!frm.doc.facture_liee) return;
        frappe.db.get_value(
            "SE Facture Client",
            frm.doc.facture_liee,
            ["client", "reste_a_encaisser", "mode_paiement_prevu"],
            (r) => {
                if (r) {
                    if (!frm.doc.client) frm.set_value("client", r.client);
                    frm.set_value("montant", flt(r.reste_a_encaisser));
                }
            }
        );
    },
});
