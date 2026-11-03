frappe.listview_settings["SE Budget Annuel"] = {
    get_indicator(doc) {
        const map = {
            "Objectif Atteint": "green",
            "Conforme": "green",
            "Sous-Performance": "orange",
            "Dépassement": "red",
        };
        const st = doc.statut_budget || "Conforme";
        return [__(st), map[st] || "blue", "statut_budget,=," + st];
    },
};
