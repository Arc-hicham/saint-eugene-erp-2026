frappe.ui.form.on("SE Operation Bancaire", {
    setup(frm) {
        frm.set_query("compte_bancaire", () => ({
            filters: { type_compte: "Banque" },
        }));
    },
});
