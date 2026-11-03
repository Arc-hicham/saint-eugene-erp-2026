frappe.listview_settings["SE Contrat et Abonnement"] = {
    get_indicator(doc) {
        if (doc.statut === "Actif") return [__("Actif"), "green", "statut,=,Actif"];
        if (doc.statut === "À renouveler (< 30j)") return [__("À renouveler"), "orange", "statut,=,À renouveler (< 30j)"];
        return [__(doc.statut || "Expiré"), "red", "statut,=," + (doc.statut || "Expiré")];
    },
};
