frappe.listview_settings["SE Operation Bancaire"] = {
    get_indicator(doc) {
        if (doc.statut_pointage === "Pointé") return [__("Pointé"), "green", "statut_pointage,=,Pointé"];
        if (doc.statut_pointage === "En écart") return [__("En écart"), "red", "statut_pointage,=,En écart"];
        return [__("Non pointé"), "orange", "statut_pointage,=,Non pointé"];
    },
};
