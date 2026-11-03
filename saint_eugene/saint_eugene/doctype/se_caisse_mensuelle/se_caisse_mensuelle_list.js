frappe.listview_settings["SE Caisse Mensuelle"] = {
    add_fields: ["statut_validation", "ecart"],
    get_indicator(doc) {
        if (doc.statut_validation === "Validée" && Math.abs(flt(doc.ecart)) < 0.01) {
            return [__("Validée (Sans écart)"), "green", "statut_validation,=,Validée"];
        }
        if (doc.statut_validation === "Validée") {
            return [__("Validée (Avec écart justifié)"), "orange", "statut_validation,=,Validée"];
        }
        if (doc.statut_validation === "Rejetée") {
            return [__("Rejetée"), "red", "statut_validation,=,Rejetée"];
        }
        if (doc.statut_validation === "En attente signature DAF") {
            return [__("En attente DAF"), "orange", "statut_validation,=,En attente signature DAF"];
        }
        return [__(doc.statut_validation || "Brouillon"), "gray", "statut_validation,=," + (doc.statut_validation || "Brouillon")];
    },
};
