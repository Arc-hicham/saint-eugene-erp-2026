frappe.ui.form.on("SE Performance Hoteliere", {
    onload(frm) {
        if (frm.is_new()) {
            frappe.call({
                method: "saint_eugene.utils.fiscal_dz.get_hotel_settings",
                callback(r) {
                    if (r.message && r.message.capacite_chambres) {
                        frm.set_value("chambres_disponibles", cint(r.message.capacite_chambres));
                    }
                },
            });
        }
    },
    chambres_disponibles(frm) { frm.trigger("recalc"); },
    chambres_vendues(frm) { frm.trigger("recalc"); },
    ca_hebergement(frm) { frm.trigger("recalc"); },
    ca_restaurant(frm) { frm.trigger("recalc"); },
    autres_revenus(frm) { frm.trigger("recalc"); },
    recalc(frm) {
        const dispo = cint(frm.doc.chambres_disponibles) || 1;
        const vendues = cint(frm.doc.chambres_vendues);
        const heb = flt(frm.doc.ca_hebergement);
        frm.set_value("taux_occupation", flt((vendues / dispo) * 100.0, 2));
        frm.set_value("adr", vendues > 0 ? flt(heb / vendues, 2) : 0);
        frm.set_value("revpar", flt(heb / dispo, 2));
        frm.set_value("ca_total_jour", flt(heb + flt(frm.doc.ca_restaurant) + flt(frm.doc.autres_revenus), 2));
    },
});
