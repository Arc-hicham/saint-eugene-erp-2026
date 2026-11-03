frappe.ui.form.on("SE Budget Annuel", {
    refresh(frm) {
        frm.add_custom_button(__("Synchroniser tout le Budget 2026"), () => {
            frappe.call({
                method: "saint_eugene.api.budget_engine.refresh_all_budgets_2026",
                freeze: true,
                freeze_message: __("Recalcul du Réalisé & des Écarts 2026..."),
                callback(r) {
                    frm.reload_doc();
                    frappe.show_alert({ message: __("Budget 2026 synchronisé avec succès"), indicator: "green" });
                },
            });
        });
    },
});
