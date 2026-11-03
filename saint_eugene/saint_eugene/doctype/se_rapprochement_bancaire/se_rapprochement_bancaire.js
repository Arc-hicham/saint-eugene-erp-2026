frappe.ui.form.on("SE Rapprochement Bancaire", {
    setup(frm) {
        frm.set_query("compte_bancaire", () => ({
            filters: { type_compte: "Banque" },
        }));
    },
    mois(frm) { frm.trigger("fetch_book_balance"); },
    compte_bancaire(frm) { frm.trigger("fetch_book_balance"); },
    solde_comptable(frm) { frm.trigger("recalc"); },
    solde_releve_bancaire(frm) { frm.trigger("recalc"); },
    fetch_book_balance(frm) {
        if (!frm.doc.mois || !frm.doc.compte_bancaire) return;
        frappe.call({
            method: "saint_eugene.saint_eugene.doctype.se_rapprochement_bancaire.se_rapprochement_bancaire.get_book_balance_at_month_end",
            args: { mois: frm.doc.mois, compte_bancaire: frm.doc.compte_bancaire },
            callback(r) {
                if (r.message !== undefined) {
                    frm.set_value("solde_comptable", flt(r.message));
                }
            },
        });
    },
    recalc(frm) {
        let add = 0;
        let sub = 0;
        (frm.doc.lignes_suspens || []).forEach((row) => {
            if (row.sens === "À ajouter au relevé (+)") add += flt(row.montant);
            else sub += flt(row.montant);
        });
        const corr = flt(frm.doc.solde_releve_bancaire) + add - sub;
        frm.set_value("total_a_ajouter", flt(add, 2));
        frm.set_value("total_a_deduire", flt(sub, 2));
        frm.set_value("solde_releve_corrige", flt(corr, 2));
        frm.set_value("ecart_final", flt(corr - flt(frm.doc.solde_comptable), 2));
    },
});

frappe.ui.form.on("SE Ligne Rapprochement Bancaire", {
    montant(frm) { frm.trigger("recalc"); },
    sens(frm) { frm.trigger("recalc"); },
    lignes_suspens_remove(frm) { frm.trigger("recalc"); },
});
