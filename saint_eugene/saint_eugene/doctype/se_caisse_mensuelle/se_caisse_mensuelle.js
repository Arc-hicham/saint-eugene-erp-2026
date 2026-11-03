frappe.ui.form.on("SE Caisse Mensuelle", {
    setup(frm) {
        frm.set_query("compte_caisse", () => ({
            filters: { type_compte: "Caisse" },
        }));
    },
    refresh(frm) {
        if (frm.doc.docstatus === 0 && frm.doc.mois && frm.doc.compte_caisse) {
            frm.add_custom_button(__("Actualiser les mouvements du mois"), () => {
                frm.trigger("fetch_movements");
            });
        }
    },
    mois(frm) { frm.trigger("fetch_movements"); },
    compte_caisse(frm) { frm.trigger("fetch_movements"); },
    solde_initial(frm) { frm.trigger("recalc_local"); },
    solde_physique(frm) { frm.trigger("recalc_local"); },
    fetch_movements(frm) {
        if (!frm.doc.mois || !frm.doc.compte_caisse) return;
        frappe.call({
            method: "saint_eugene.api.dashboard.compute_caisse_totals",
            args: { mois: frm.doc.mois, compte_caisse: frm.doc.compte_caisse },
            callback(r) {
                if (r.message) {
                    frm.set_value("total_encaissements", r.message.total_encaissements);
                    frm.set_value("total_decaissements", r.message.total_decaissements);
                    frm.trigger("recalc_local");
                }
            },
        });
    },
    recalc_local(frm) {
        const theo = flt(frm.doc.solde_initial) + flt(frm.doc.total_encaissements) - flt(frm.doc.total_decaissements);
        frm.set_value("solde_theorique", flt(theo, 2));
        frm.set_value("ecart", flt(flt(frm.doc.solde_physique) - theo, 2));
    },
});
