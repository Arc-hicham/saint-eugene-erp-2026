frappe.listview_settings["SE Facture Fournisseur"] = {
    add_fields: ["statut", "reste_a_payer"],
    get_indicator(doc) {
        const colors = {
            "Payée": "green",
            "Validée": "green",
            "Partielle": "orange",
            "Échue": "red",
            "Brouillon": "gray",
            "Annulée": "darkgrey",
        };
        const st = doc.statut || "Brouillon";
        return [__(st), colors[st] || "blue", "statut,=," + st];
    },
};
