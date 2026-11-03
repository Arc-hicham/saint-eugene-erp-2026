frappe.listview_settings["SE Fiche de Paie Mensuelle"] = {
    get_indicator(doc) {
        if (doc.statut === "Payée" || doc.statut === "Validée") return [__(doc.statut), "green", "statut,=," + doc.statut];
        if (doc.statut === "Annulée") return [__("Annulé"), "red", "statut,=,Annulée"];
        return [__("Brouillon"), "gray", "statut,=,Brouillon"];
    },
};
