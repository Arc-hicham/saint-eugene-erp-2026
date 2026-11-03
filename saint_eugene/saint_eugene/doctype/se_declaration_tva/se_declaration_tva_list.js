frappe.listview_settings["SE Declaration TVA"] = {
    get_indicator(doc) {
        if (doc.statut === "Payée" || doc.statut === "Crédit Reporté") return [__(doc.statut), "green", "statut,=," + doc.statut];
        if (doc.statut === "Déclarée (G50)") return [__("À payer (G50)"), "orange", "statut,=,Déclarée (G50)"];
        return [__(doc.statut || "Brouillon"), "gray", "statut,=," + (doc.statut || "Brouillon")];
    },
};
