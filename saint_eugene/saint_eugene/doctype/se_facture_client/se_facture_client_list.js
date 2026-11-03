frappe.listview_settings["SE Facture Client"] = {
    add_fields: ["statut", "reste_a_encaisser", "jours_retard", "montant_ttc"],
    get_indicator(doc) {
        const colors = {
            "Payée": "green",
            "Validée": "green",
            "Partielle": "orange",
            "Impayée": "red",
            "Échue": "red",
            "Brouillon": "gray",
            "Annulée": "darkgrey",
        };
        const st = doc.statut || "Brouillon";
        return [__(st), colors[st] || "blue", "statut,=," + st];
    },
    formatters: {
        jours_retard(val) {
            if (cint(val) > 0) {
                return `<span class="indicator-pill red">+${val} j</span>`;
            }
            return `<span class="text-muted">0 j</span>`;
        },
    },
};
