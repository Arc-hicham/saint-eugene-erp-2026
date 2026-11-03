frappe.listview_settings["SE Rapprochement Bancaire"] = {
    get_indicator(doc) {
        if (doc.statut === "Validé" || doc.statut === "Équilibré") return [__(doc.statut), "green", "statut,=," + doc.statut];
        if (doc.statut === "Avec Écart") return [__("Avec Écart"), "red", "statut,=,Avec Écart"];
        return [__(doc.statut || "Brouillon"), "gray", "statut,=," + (doc.statut || "Brouillon")];
    },
};
