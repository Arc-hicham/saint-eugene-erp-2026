frappe.ui.form.on("SE Immobilisation", {
    valeur_acquisition(frm) { frm.trigger("recalc"); },
    duree_amortissement(frm) { frm.trigger("recalc"); },
    recalc(frm) {
        const val = flt(frm.doc.valeur_acquisition);
        const dur = cint(frm.doc.duree_amortissement) || 1;
        frm.set_value("dotation_annuelle", flt(val / dur, 2));
    },
});
