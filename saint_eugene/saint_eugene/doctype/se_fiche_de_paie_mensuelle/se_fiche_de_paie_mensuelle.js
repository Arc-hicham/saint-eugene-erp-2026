frappe.ui.form.on("SE Fiche de Paie Mensuelle", {
    salaire_base(frm) { frm.trigger("recalc_preview"); },
    primes(frm) { frm.trigger("recalc_preview"); },
    indemnites(frm) { frm.trigger("recalc_preview"); },
    retenue_irg(frm) { frm.trigger("recalc_preview"); },
    autres_retenues(frm) { frm.trigger("recalc_preview"); },
    recalc_preview(frm) {
        const assiette = flt(frm.doc.salaire_base) + flt(frm.doc.primes);
        const cnas = flt(assiette * 0.09, 2);
        const brut = flt(assiette + flt(frm.doc.indemnites), 2);
        const ret = flt(cnas + flt(frm.doc.retenue_irg) + flt(frm.doc.autres_retenues), 2);
        frm.set_value("retenue_cnas", cnas);
        frm.set_value("charges_patronales_cnas", flt(assiette * 0.26, 2));
        frm.set_value("salaire_brut", brut);
        frm.set_value("total_retenues", ret);
        frm.set_value("net_a_payer", Math.max(0, flt(brut - ret, 2)));
    },
});
