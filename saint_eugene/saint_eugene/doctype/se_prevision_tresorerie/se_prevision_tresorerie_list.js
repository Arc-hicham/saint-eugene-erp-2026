frappe.listview_settings["SE Prevision Tresorerie"] = {
    get_indicator(doc) {
        if (doc.niveau_risque === "Sain") return [__("Sain"), "green", "niveau_risque,=,Sain"];
        if (doc.niveau_risque === "Sous Tension") return [__("Sous Tension"), "orange", "niveau_risque,=,Sous Tension"];
        return [__("Critique"), "red", "niveau_risque,=,Critique"];
    },
};
