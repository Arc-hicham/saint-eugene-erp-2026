frappe.ui.form.on("SE Charge et Depense", {
    montant_ht(frm) { frm.trigger("recalc"); },
    taux_tva(frm) { frm.trigger("recalc"); },
    recalc(frm) {
        const ht = flt(frm.doc.montant_ht);
        const tva = flt((ht * flt(frm.doc.taux_tva)) / 100.0, 2);
        frm.set_value("montant_tva", tva);
        frm.set_value("montant_ttc", flt(ht + tva, 2));
    },
});
