frappe.ui.form.on("SE Prevision Tresorerie", {
    refresh(frm) {
        frm.add_custom_button(__("Recalculer en temps réel"), () => {
            frappe.call({
                method: "saint_eugene.api.dashboard.compute_treasury_forecast",
                args: { date_reference: frm.doc.date_prevision },
                callback(r) {
                    if (r.message) {
                        Object.keys(r.message).forEach((k) => frm.set_value(k, r.message[k]));
                        frm.save();
                    }
                },
            });
        });
    },
});
