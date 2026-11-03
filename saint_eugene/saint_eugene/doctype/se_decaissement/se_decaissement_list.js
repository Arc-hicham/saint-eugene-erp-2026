frappe.listview_settings["SE Decaissement"] = {
    get_indicator(doc) {
        if (doc.statut === "Validé") return [__("Validé"), "green", "statut,=,Validé"];
        if (doc.statut === "Annulé") return [__("Annulé"), "red", "statut,=,Annulé"];
        return [__("Brouillon"), "gray", "statut,=,Brouillon"];
    },
};
