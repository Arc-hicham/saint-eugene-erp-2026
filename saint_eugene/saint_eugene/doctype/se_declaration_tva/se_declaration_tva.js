frappe.ui.form.on("SE Declaration TVA", {
    mois(frm) { frm.trigger("fetch_tva"); },
    precompte_anterieur(frm) { frm.trigger("fetch_tva"); },
    fetch_tva(frm) {
        if (!frm.doc.mois) return;
        frappe.call({
            method: "saint_eugene.api.dashboard.compute_tva_month",
            args: {
                mois: frm.doc.mois,
                precompte_anterieur: flt(frm.doc.precompte_anterieur),
            },
            callback(r) {
                if (r.message) {
                    Object.keys(r.message).forEach((k) => frm.set_value(k, r.message[k]));
                }
            },
        });
    },
});
