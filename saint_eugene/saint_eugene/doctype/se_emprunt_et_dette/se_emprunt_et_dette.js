frappe.ui.form.on("SE Emprunt et Dette", {
    capital_initial(frm) { frm.trigger("recalc"); },
    capital_rembourse(frm) { frm.trigger("recalc"); },
    recalc(frm) {
        frm.set_value("solde_restant", Math.max(0, flt(flt(frm.doc.capital_initial) - flt(frm.doc.capital_rembourse), 2)));
    },
});
