# -*- coding: utf-8 -*-
"""
MODULE RH & PAIE — Saint Eugène ERP
===================================
Définition des DocTypes RH (JSON compatibles Frappe/ERPNext), données de SIMULATION
(toutes marquées `donnee_simulation = 1`) et utilitaires de sauvegarde sécurisée.

Usage :
    python rh_module.py          -> (re)génère les DocTypes JSON RH + étend SE Employe / SE Fiche de Paie

IMPORTANT — paramètres réglementaires : aucun taux/échéance n'est « inventé ». Les valeurs de
`SE Parametres RH` reprennent le paramétrage déjà présent dans l'ERP (CNAS 9 % / 26 %, barème IRG) ou
sont des valeurs usuelles marquées « À valider » : elles DOIVENT être validées par le responsable RH
et l'expert-comptable avant tout usage réel.
"""
from __future__ import annotations

import json
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
DOCTYPE_DIR = APP_ROOT / "saint_eugene" / "saint_eugene" / "doctype"

MOIS = "\n".join(f"2026-{m:02d}" for m in range(1, 13))
DEPARTEMENTS = "Direction & Administration\nRéception & Hébergement\nRestauration & Cuisine\nÉtages & Housekeeping\nMaintenance & Sécurité"
FONCTIONS = [
    "Directeur d'Exploitation", "Chef Comptable SCF", "Chef de Réception", "Gouvernante Générale",
    "Chef Exécutif Cuisine", "Maître d'Hôtel", "Responsable Technique & CVC", "Réceptionniste Bilingue",
    "Réceptionniste", "Femme de chambre", "Valet de chambre", "Commis de cuisine", "Serveur / Serveuse",
    "Agent de sécurité", "Plongeur", "Autre",
]
TYPES_CONTRAT = "CDI\nCDD\nContrat d'essai\nAutre"
STATUTS_EMPLOYE = "Actif\nCongé\nArrêt maladie\nSuspendu\nSorti"
STATUTS_PAIE = ("Brouillon\nEn préparation\nEn attente de validation\nValidée\nComptabilisée\n"
                "En attente de paiement\nPartiellement payée\nPayée\nAnnulée")
DOCS_RH = ["Carte nationale d'identité", "Extrait de naissance", "Justificatif de résidence",
           "Photo d'identité", "Diplômes", "Attestations"]
DOCS_RH_OBLIGATOIRES = DOCS_RH[:4]

ROLES_PERMISSIONS = [
    {"role": "System Manager", "create": 1, "delete": 1, "email": 1, "export": 1, "print": 1, "read": 1, "report": 1, "share": 1, "write": 1},
    {"role": "Accounts Manager", "create": 1, "delete": 1, "email": 1, "export": 1, "print": 1, "read": 1, "report": 1, "share": 1, "write": 1},
    {"role": "Accounts User", "create": 1, "read": 1, "write": 1, "print": 1, "export": 1, "report": 1},
]

# Doctypes RH (hors extension de SE Employe / SE Fiche de Paie Mensuelle)
RH_DOCTYPES = [
    "SE Contrat RH", "SE Revision Salariale", "SE Declaration CNAS", "SE Conge", "SE Arret Maladie",
    "SE Presence Absence", "SE Accident Travail", "SE Avance Pret", "SE Sortie Personnel",
    "SE Periode Paie", "SE Ecriture RH", "SE Parametres RH",
]
# Doctypes dont le contenu est confidentiel (santé) : exclus de la sauvegarde Google Sheet
RH_CONFIDENTIAL_DOCTYPES = ["SE Arret Maladie", "SE Accident Travail"]
# Champs d'identité sensibles : retirés de la sauvegarde Google Sheet et du seed du script .gs
SENSITIVE_EMPLOYEE_FIELDS = [
    "nin", "n_carte_nationale", "carte_delivree_le", "carte_delivree_par", "carte_expiration",
    "n_assurance", "numero_cnas", "date_naissance", "lieu_naissance", "adresse", "telephone",
    "telephone_2", "email", "urgence_nom", "urgence_tel", "rib_ccp",
]


def F(name, ftype, label, **kw):
    d = {"fieldname": name, "fieldtype": ftype, "label": label}
    d.update(kw)
    return d


def SIM():
    return F("donnee_simulation", "Check", "Donnée de simulation (fictive)", default="0")


def _doctype(name, prefix, title_field, fields, submittable=0):
    slug = name.lower().replace(" ", "_")
    ordered = [F("sb_main", "Section Break", name.replace("SE ", ""))]
    half = max(1, len(fields) // 2)
    for i, f in enumerate(fields):
        if i == half:
            ordered.append(F("cb_main", "Column Break", ""))
        ordered.append(f)
    return {
        "actions": [], "autoname": f"format:{prefix}{{####}}", "creation": "2026-11-04 08:00:00.000000",
        "doctype": "DocType", "engine": "InnoDB", "field_order": [f["fieldname"] for f in ordered],
        "fields": ordered, "index_web_pages_for_search": 0, "is_submittable": submittable, "istable": 0,
        "links": [], "modified": "2026-11-04 08:00:00.000000", "modified_by": "Administrator",
        "module": "Saint Eugene", "name": name, "naming_rule": "Expression", "owner": "Administrator",
        "permissions": ROLES_PERMISSIONS, "sort_field": "modified", "sort_order": "DESC", "states": [],
        "track_changes": 1, "title_field": title_field, "search_fields": title_field,
    }, slug


def build_specs() -> list[tuple[dict, str]]:
    emp = lambda: F("employe", "Link", "Employé (Matricule)", options="SE Employe", reqd=1, in_list_view=1, in_standard_filter=1)
    nom = lambda: F("nom_employe", "Data", "Nom de l'employé", read_only=1, in_list_view=1)
    specs = []

    specs.append(_doctype("SE Contrat RH", "CTR-RH-", "n_contrat", [
        emp(), nom(),
        F("n_contrat", "Data", "N° Contrat", in_list_view=1),
        F("nature_mouvement", "Select", "Nature du mouvement", in_list_view=1, in_standard_filter=1,
          options="Création\nRenouvellement\nAvenant\nChangement de fonction\nChangement de département\nChangement de salaire\nFin de contrat\nDémission\nLicenciement\nDépart à la retraite\nAutre motif de sortie"),
        F("type_contrat", "Select", "Type de contrat", options=TYPES_CONTRAT, in_list_view=1),
        F("date_contrat", "Date", "Date de signature"),
        F("date_debut", "Date", "Date de début"),
        F("date_fin", "Date", "Date de fin (CDD)", in_list_view=1),
        F("salaire_base_contractuel", "Currency", "Salaire de base contractuel (DZD)"),
        F("responsable", "Link", "Responsable hiérarchique", options="SE Employe"),
        F("decision_renouvellement", "Select", "Décision de renouvellement", options="À décider\nRenouveler\nNe pas renouveler\nConvertir en CDI"),
        F("statut_workflow", "Select", "Statut du dossier (workflow)", in_list_view=1, in_standard_filter=1, default="Brouillon",
          options="Brouillon\nEn attente de validation RH\nValidation Direction\nContrat signé\nActif\nClôturé"),
        F("contrat_pdf_ref", "Data", "Réf. contrat PDF (archivage)"),
        F("observation", "Small Text", "Observation"), SIM(),
    ]))

    specs.append(_doctype("SE Revision Salariale", "REV-SAL-", "employe", [
        emp(), nom(),
        F("date_effet", "Date", "Date d'effet", reqd=1, in_list_view=1),
        F("ancien_contractuel", "Currency", "Ancien salaire contractuel"),
        F("nouveau_contractuel", "Currency", "Nouveau salaire contractuel", in_list_view=1),
        F("ancien_declare", "Currency", "Ancien salaire déclaré"),
        F("nouveau_declare", "Currency", "Nouveau salaire déclaré", in_list_view=1),
        F("ecart_dzd", "Currency", "Écart contractuel − déclaré (DA)", read_only=1, in_list_view=1),
        F("ecart_pct", "Percent", "Écart (%)", read_only=1),
        F("motif_revision", "Select", "Motif de révision", options="Embauche\nAugmentation\nChangement de poste\nRégularisation\nAutre"),
        F("motif_ecart", "Small Text", "Justification de l'écart (obligatoire si écart)"),
        F("validation_rh", "Select", "Validation RH", options="En attente\nValidée\nRefusée", default="En attente", in_list_view=1, in_standard_filter=1),
        F("validation_compta", "Select", "Validation comptable", options="En attente\nValidée\nRefusée", default="En attente"),
        SIM(),
    ]))

    specs.append(_doctype("SE Declaration CNAS", "CNAS-DECL-", "periode", [
        F("periode", "Select", "Période (mois)", options=MOIS, reqd=1, in_list_view=1, in_standard_filter=1),
        F("type_declaration", "Select", "Type de déclaration", in_list_view=1, in_standard_filter=1, default="Déclaration périodique des cotisations",
          options="Déclaration périodique des cotisations\nDéclaration annuelle des salaires et des salariés\nDéclaration d'entrée d'un employé\nDéclaration de sortie d'un employé\nDéclaration de modification de situation\nDéclaration liée à un arrêt maladie\nDéclaration liée à un accident du travail\nAutre déclaration applicable"),
        F("n_employeur_cnas", "Data", "N° employeur CNAS"),
        F("agence_cnas", "Data", "Agence CNAS"),
        F("nb_employes", "Int", "Employés déclarés", read_only=1, in_list_view=1),
        F("masse_salariale", "Currency", "Masse salariale déclarée", read_only=1),
        F("total_bases", "Currency", "Total des bases de cotisation", read_only=1, in_list_view=1),
        F("cotisations_salariales", "Currency", "Cotisations salariales", read_only=1),
        F("cotisations_patronales", "Currency", "Cotisations patronales", read_only=1),
        F("total_cotisations", "Currency", "Total des cotisations", read_only=1, in_list_view=1),
        F("date_preparation", "Date", "Date de préparation"),
        F("date_limite", "Date", "Date limite (selon paramètre à valider)"),
        F("date_depot", "Date", "Date de dépôt (preuve requise)"),
        F("ref_declaration", "Data", "Référence de déclaration / accusé"),
        F("date_paiement", "Date", "Date de paiement (preuve requise)"),
        F("ref_paiement", "Data", "Référence de paiement / bordereau"),
        F("statut", "Select", "Statut", in_list_view=1, in_standard_filter=1, default="Non préparée",
          options="Non préparée\nPréparée\nValidée\nDéposée\nPayée\nEn retard"),
        F("justificatif_ref", "Data", "Justificatif archivé (réf. fichier)"),
        F("anomalies", "Small Text", "Anomalies détectées (auto)", read_only=1),
        F("observation", "Small Text", "Observation"), SIM(),
    ]))

    specs.append(_doctype("SE Conge", "CONGE-", "employe", [
        emp(), nom(),
        F("type_conge", "Select", "Type de congé", reqd=1, in_list_view=1, in_standard_filter=1, default="Congé annuel",
          options="Congé annuel\nCongé exceptionnel\nCongé sans solde\nCongé maternité\nCongé paternité\nCongé maladie\nCongé pour événement familial\nAutre congé"),
        F("date_debut", "Date", "Date de début", reqd=1, in_list_view=1),
        F("date_fin", "Date", "Date de fin", reqd=1, in_list_view=1),
        F("nb_jours", "Float", "Nombre de jours (calculé)", read_only=1, in_list_view=1),
        F("motif", "Small Text", "Motif"),
        F("remplacant", "Link", "Remplaçant", options="SE Employe"),
        F("date_demande", "Date", "Date de la demande"),
        F("responsable_validation", "Link", "Responsable de validation", options="SE Employe"),
        F("statut", "Select", "Statut (workflow)", in_list_view=1, in_standard_filter=1, default="Demande",
          options="Demande\nValidé responsable\nValidé RH\nApprouvé\nRefusé\nAnnulé"),
        F("justificatif_ref", "Data", "Justificatif (réf.)"), SIM(),
    ]))

    specs.append(_doctype("SE Arret Maladie", "ARRET-", "employe", [
        emp(), nom(),
        F("date_debut", "Date", "Date de début", reqd=1, in_list_view=1),
        F("date_fin_prevue", "Date", "Date de fin prévue", in_list_view=1),
        F("date_reprise", "Date", "Date de reprise effective"),
        F("nb_jours", "Int", "Nombre de jours (calculé)", read_only=1, in_list_view=1),
        F("date_reception_certificat", "Date", "Date de réception du certificat"),
        F("justificatif_recu", "Check", "Justificatif médical reçu (conservé dans le dossier RH confidentiel)", default="0"),
        F("date_transmission", "Date", "Date de transmission à l'organisme"),
        F("organisme", "Data", "Organisme destinataire", default="CNAS"),
        F("ref_dossier", "Data", "Référence du dossier"),
        F("statut_admin", "Select", "Statut administratif", in_list_view=1, in_standard_filter=1, default="Déclaré par l'employé",
          options="Déclaré par l'employé\nCertificat reçu\nEn attente de contrôle\nValidé RH\nTransmis à l'organisme\nDéclaration effectuée\nEn attente de traitement\nAccepté\nRefusé\nClôturé"),
        F("statut_indemnisation", "Select", "Statut d'indemnisation (si applicable)", options="Non applicable\nEn attente\nIndemnisé\nRefusé"),
        F("observation_admin", "Small Text", "Observation administrative (aucun diagnostic médical)"), SIM(),
    ]))

    specs.append(_doctype("SE Presence Absence", "PRES-", "employe", [
        emp(), nom(),
        F("date", "Date", "Date", reqd=1, in_list_view=1),
        F("type_absence", "Select", "Type", reqd=1, in_list_view=1, in_standard_filter=1, default="Absence injustifiée",
          options="Présent\nAbsence justifiée\nAbsence injustifiée\nRetard\nSortie autorisée\nCongé\nArrêt maladie\nAccident du travail\nAutre"),
        F("horaire_prevu", "Data", "Horaire prévu", default="08:00-17:00"),
        F("heure_arrivee", "Data", "Heure d'arrivée"),
        F("heure_depart", "Data", "Heure de départ"),
        F("retard_minutes", "Int", "Retard (minutes)"),
        F("heures_sup", "Float", "Heures supplémentaires"),
        F("motif", "Data", "Motif"),
        F("justificatif_recu", "Check", "Justificatif reçu", default="0"),
        F("statut", "Select", "Validation du responsable", in_list_view=1, in_standard_filter=1, default="À valider", options="À valider\nValidé\nRefusé"),
        F("retenue_validee", "Check", "Retenue salariale validée (conforme aux règles)", default="0"), SIM(),
    ]))

    specs.append(_doctype("SE Accident Travail", "AT-", "employe", [
        emp(), nom(),
        F("date_accident", "Date", "Date de l'accident", reqd=1, in_list_view=1),
        F("heure_accident", "Data", "Heure"),
        F("lieu", "Data", "Lieu"),
        F("circonstances", "Small Text", "Circonstances (factuelles)"),
        F("date_declaration", "Date", "Date de déclaration", in_list_view=1),
        F("ref_dossier", "Data", "Référence du dossier"),
        F("organisme", "Data", "Organisme destinataire", default="CNAS"),
        F("arret_associe", "Link", "Arrêt de travail associé", options="SE Arret Maladie"),
        F("statut", "Select", "Statut", in_list_view=1, in_standard_filter=1, default="À déclarer",
          options="À déclarer\nDéclaré\nEn instruction\nAccepté\nRefusé\nClôturé"),
        F("date_reprise", "Date", "Date de reprise"),
        F("indemnites", "Currency", "Indemnités éventuelles (DZD)"),
        F("observation", "Small Text", "Observation"), SIM(),
    ]))

    specs.append(_doctype("SE Avance Pret", "AVP-", "employe", [
        emp(), nom(),
        F("type_operation", "Select", "Type", reqd=1, in_list_view=1, in_standard_filter=1, options="Avance sur salaire\nPrêt au personnel"),
        F("date_operation", "Date", "Date", in_list_view=1),
        F("montant_demande", "Currency", "Montant demandé"),
        F("montant_approuve", "Currency", "Montant approuvé"),
        F("montant_verse", "Currency", "Montant versé", in_list_view=1),
        F("mode_paiement", "Select", "Mode de paiement", options="Virement\nChèque\nEspèces"),
        F("ref_paiement", "Data", "Référence de paiement"),
        F("nb_echeances", "Int", "Nombre d'échéances"),
        F("retenue_mensuelle", "Currency", "Retenue mensuelle"),
        F("date_premiere_retenue", "Date", "Mois de 1ʳᵉ retenue (jj/mm)"),
        F("montant_rembourse", "Currency", "Montant remboursé"),
        F("solde_restant", "Currency", "Solde restant (calculé)", read_only=1, in_list_view=1),
        F("base_autorisation", "Data", "Base d'autorisation de la retenue (obligatoire)"),
        F("statut", "Select", "Statut", in_list_view=1, in_standard_filter=1, default="Demandé",
          options="Demandé\nApprouvé\nVersé\nEn cours de remboursement\nSoldé\nAnnulé"), SIM(),
    ]))

    specs.append(_doctype("SE Sortie Personnel", "SORTIE-", "employe", [
        emp(), nom(),
        F("date_depart", "Date", "Date de départ", reqd=1, in_list_view=1),
        F("type_depart", "Select", "Type de départ", in_list_view=1, options="Fin de CDD\nDémission\nLicenciement\nDépart à la retraite\nAutre"),
        F("motif", "Data", "Motif"),
        F("preavis_jours", "Int", "Préavis (jours)"),
        F("dernier_jour_travaille", "Date", "Dernier jour travaillé"),
        F("solde_conges", "Float", "Solde de congés à régulariser (jours)"),
        F("dernier_salaire", "Currency", "Dernier salaire"),
        F("avances_restantes", "Currency", "Avances / prêts restants dus"),
        F("chk_contrat_cloture", "Check", "Contrat clôturé", default="0"),
        F("chk_derniere_paie", "Check", "Dernière paie préparée", default="0"),
        F("chk_conges_regularises", "Check", "Congés régularisés", default="0"),
        F("chk_avances_controlees", "Check", "Avances et prêts contrôlés", default="0"),
        F("chk_documents_remis", "Check", "Documents remis (certificat de travail…)", default="0"),
        F("chk_declaration_sortie", "Check", "Déclaration de sortie effectuée si applicable", default="0"),
        F("chk_acces_desactives", "Check", "Accès informatiques désactivés", default="0"),
        F("chk_materiel_restitue", "Check", "Matériel restitué", default="0"),
        F("chk_dossier_archive", "Check", "Dossier archivé", default="0"),
        F("validation_rh", "Select", "Validation RH", options="En attente\nValidée", default="En attente"),
        F("validation_direction", "Select", "Validation Direction", options="En attente\nValidée", default="En attente"),
        F("statut", "Select", "Statut", in_list_view=1, in_standard_filter=1, default="En cours", options="En cours\nClôturé"), SIM(),
    ]))

    specs.append(_doctype("SE Periode Paie", "PERIODE-", "mois", [
        F("mois", "Select", "Mois", options=MOIS, reqd=1, in_list_view=1, in_standard_filter=1),
        F("departement", "Data", "Département", default="Tous"),
        F("statut_paie", "Select", "Statut de paie", options=STATUTS_PAIE, default="Brouillon", in_list_view=1, in_standard_filter=1),
        F("date_preparation", "Date", "Date de préparation"),
        F("date_validation", "Date", "Date de validation"),
        F("responsable_rh", "Data", "Responsable RH / Paie"),
        F("responsable_compta", "Data", "Responsable comptable"),
        F("nb_bulletins", "Int", "Bulletins", read_only=1, in_list_view=1),
        F("total_brut", "Currency", "Masse salariale brute", read_only=1, in_list_view=1),
        F("total_net", "Currency", "Total net à payer", read_only=1, in_list_view=1),
        F("total_cnas_sal", "Currency", "Cotisations salariales", read_only=1),
        F("total_cnas_pat", "Currency", "Cotisations patronales", read_only=1),
        F("total_irg", "Currency", "IRG", read_only=1),
        F("cout_employeur", "Currency", "Coût employeur", read_only=1),
        F("total_paye", "Currency", "Total payé", read_only=1),
        F("ecriture_generee", "Check", "Écritures comptables générées (anti double comptabilisation)", read_only=1, default="0"), SIM(),
    ]))

    specs.append(_doctype("SE Ecriture RH", "ECR-RH-", "libelle", [
        F("date_ecriture", "Date", "Date", in_list_view=1),
        F("journal", "Data", "Journal", default="OD Paie", in_list_view=1),
        F("periode", "Data", "Période", in_list_view=1),
        F("piece", "Data", "Pièce d'origine"),
        F("origine", "Select", "Origine", options="Paie\nPaiement salaires\nCNAS\nRégularisation", in_standard_filter=1),
        F("compte", "Data", "Compte SCF", in_list_view=1),
        F("libelle", "Data", "Libellé", in_list_view=1),
        F("debit", "Currency", "Débit", in_list_view=1),
        F("credit", "Currency", "Crédit", in_list_view=1), SIM(),
    ]))

    specs.append(_doctype("SE Parametres RH", "PARAM-RH-", "libelle", [
        F("code", "Data", "Code du paramètre", reqd=1, in_list_view=1),
        F("libelle", "Data", "Libellé", in_list_view=1),
        F("categorie", "Select", "Catégorie", options="Cotisations\nPaie\nCongés\nAbsences\nDéclarations\nArrêts maladie\nComptabilité", in_standard_filter=1),
        F("valeur", "Data", "Valeur", reqd=1, in_list_view=1),
        F("unite", "Data", "Unité"),
        F("date_effet", "Date", "Date d'effet (versionnement)", reqd=1, in_list_view=1),
        F("source_reglementaire", "Data", "Source réglementaire documentée"),
        F("statut_validation", "Select", "Validation", options="À valider\nValidé", default="À valider", in_list_view=1, in_standard_filter=1),
        F("valide_par", "Data", "Validé par (RH / expert-comptable)"), SIM(),
    ]))
    return specs


def extend_existing():
    """Étend SE Employe et SE Fiche de Paie Mensuelle (idempotent, conserve les champs existants)."""
    # ---------- SE Employe ----------
    p = DOCTYPE_DIR / "se_employe" / "se_employe.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    have = {f["fieldname"] for f in d["fields"]}
    for f in d["fields"]:
        if f["fieldname"] == "fonction":
            f["fieldtype"] = "Select"
            f["options"] = "\n".join(FONCTIONS)
        if f["fieldname"] == "statut":
            f["options"] = STATUTS_EMPLOYE
        if f["fieldname"] == "salaire_base":
            f["label"] = "Salaire de base mensuel — référence paie (DZD)"
    new = [
        F("sb_a", "Section Break", "A — Informations personnelles & administratives"),
        F("matricule", "Data", "Matricule (MAT) — unique", reqd=1, in_list_view=1),
        F("nom", "Data", "Nom"), F("prenom", "Data", "Prénom"),
        F("sexe", "Select", "Sexe", options="Masculin\nFéminin"),
        F("date_naissance", "Date", "Date de naissance"), F("lieu_naissance", "Data", "Lieu de naissance (commune / wilaya)"),
        F("nationalite", "Data", "Nationalité", default="Algérienne"),
        F("adresse", "Data", "Adresse actuelle"), F("wilaya", "Data", "Wilaya de résidence"),
        F("telephone", "Data", "Téléphone principal"), F("telephone_2", "Data", "Téléphone secondaire"), F("email", "Data", "Email"),
        F("nin", "Data", "NIN (identification nationale) 🔒"),
        F("n_carte_nationale", "Data", "N° carte nationale 🔒"), F("carte_delivree_le", "Date", "Carte délivrée le"),
        F("carte_delivree_par", "Data", "Carte délivrée par"), F("carte_expiration", "Date", "Expiration du document"),
        F("n_assurance", "Data", "N° assurance / affiliation sociale 🔒"), F("agence_cnas", "Data", "Agence CNAS d'affiliation"),
        F("situation_familiale", "Select", "Situation familiale", options="Célibataire\nMarié(e)\nDivorcé(e)\nVeuf(ve)"),
        F("nb_enfants", "Int", "Enfants à charge"),
        F("urgence_nom", "Data", "Personne à contacter en urgence"), F("urgence_tel", "Data", "Téléphone urgence"),
        F("documents_fournis", "Small Text", "Documents fournis (liste, séparés par |)"),
        F("sb_b", "Section Break", "B — Informations professionnelles"),
        F("responsable", "Link", "Responsable hiérarchique", options="SE Employe"),
        F("date_prise_poste", "Date", "Date de prise de poste"),
        F("type_contrat", "Select", "Type de contrat", options=TYPES_CONTRAT, default="CDI", in_list_view=1, in_standard_filter=1),
        F("periode_essai_mois", "Int", "Période d'essai (mois)"), F("date_fin_essai", "Date", "Fin de période d'essai (calculée)", read_only=1),
        F("date_fin_contrat", "Date", "Date de fin du contrat (CDD)"),
        F("horaires", "Data", "Horaires / régime de travail", default="Poste de jour"),
        F("categorie_pro", "Data", "Catégorie professionnelle"), F("qualification", "Data", "Qualification"),
        F("centre_cout", "Data", "Centre de coût"), F("lieu_travail", "Data", "Lieu de travail", default="Hôtel Saint Eugène — Alger"),
        F("observation_rh", "Small Text", "Observation RH"),
        F("sb_c", "Section Break", "C — Contrat & salaire (contractuel ≠ déclaré)"),
        F("salaire_base_contractuel", "Currency", "Salaire de base CONTRACTUEL (DZD)"),
        F("salaire_base_declare", "Currency", "Salaire de base DÉCLARÉ (base de cotisation) (DZD)"),
        F("primes_contractuelles", "Currency", "Primes contractuelles"), F("indemnites_contractuelles", "Currency", "Indemnités (non soumises — à valider)"),
        F("avantages", "Currency", "Avantages en nature"),
        F("salaire_net_estime", "Currency", "Salaire net estimé (calcul)", read_only=1),
        F("cout_employeur_estime", "Currency", "Coût employeur estimé (calcul)", read_only=1),
        F("date_derniere_revision", "Date", "Dernière révision salariale", read_only=1),
        F("solde_initial_conges", "Float", "Solde initial de congés (jours)"),
        F("date_sortie", "Date", "Date de sortie"),
        SIM(),
    ]
    for f in new:
        if f["fieldname"] not in have:
            d["fields"].append(f)
            d["field_order"].append(f["fieldname"])
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # ---------- SE Fiche de Paie Mensuelle ----------
    p = DOCTYPE_DIR / "se_fiche_de_paie_mensuelle" / "se_fiche_de_paie_mensuelle.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    have = {f["fieldname"] for f in d["fields"]}
    for f in d["fields"]:
        if f["fieldname"] == "statut":
            f["options"] = STATUTS_PAIE
    new = [
        F("nb_heures_sup", "Float", "Heures supplémentaires validées (h)"),
        F("montant_heures_sup", "Currency", "Montant heures supplémentaires"),
        F("retenue_absences", "Currency", "Retenue absences validées"),
        F("retenue_avances", "Currency", "Retenue avances / prêts (échéancier validé)"),
        F("base_cotisation", "Currency", "Base de cotisation (salaire déclaré + primes)"),
        F("cout_employeur", "Currency", "Coût total employeur"),
        F("date_paiement", "Date", "Date de paiement"),
        F("comptabilise", "Check", "Comptabilisée (anti double comptabilisation)", read_only=1, default="0"),
    ]
    for f in new:
        if f["fieldname"] not in have:
            d["fields"].append(f)
            d["field_order"].append(f["fieldname"])
    p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_doctypes():
    for dt, slug in build_specs():
        folder = DOCTYPE_DIR / slug
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f"{slug}.json").write_text(json.dumps(dt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        init = folder / "__init__.py"
        if not init.exists():
            init.write_text("", encoding="utf-8")
    extend_existing()


# ============================================================================
#  DONNÉES DE SIMULATION (toutes fictives — `donnee_simulation = 1`)
# ============================================================================
def _irg(rev: float) -> float:
    if rev <= 30000.0:
        return 0.0
    tr = [(20000.0, 0.0), (40000.0, 0.23), (80000.0, 0.27), (160000.0, 0.30), (320000.0, 0.33), (float("inf"), 0.35)]
    brut, plancher = 0.0, 0.0
    for plaf, taux in tr:
        if rev <= plancher:
            break
        brut += (min(rev, plaf) - plancher) * taux
        plancher = plaf
    abat = min(max(brut * 0.40, 1000.0), 1500.0)
    irg = max(0.0, brut - abat)
    if 30000.0 < rev < 35000.0:
        irg = max(0.0, irg * (137.0 / 51.0) - (27925.0 / 8.0))
    return round(irg, 2)


# (id, nom, prénom, sexe, naissance, dept, fonction, type, embauche, fin_contrat, essai_mois, contractuel, declaré, primes, statut, docs_count)
_EMP_EXTRA = {
    "SE-EMP-0009": ("Hamel", "Lilia", "Féminin", "1999-04-12", "Étages & Housekeeping", "Femme de chambre", "CDD", "2026-05-30", "2026-11-29", 0, 42000, 42000, 4200, "Actif", 6),
    "SE-EMP-0010": ("Tabet", "Samir", "Masculin", "1995-09-03", "Étages & Housekeeping", "Valet de chambre", "CDI", "2025-02-01", "", 3, 44000, 44000, 4400, "Actif", 6),
    "SE-EMP-0011": ("Cherif", "Amina", "Féminin", "1998-01-22", "Réception & Hébergement", "Réceptionniste", "CDD", "2026-07-01", "2026-12-31", 0, 52000, 48000, 5200, "Actif", 5),
    "SE-EMP-0012": ("Slimani", "Walid", "Masculin", "2001-06-30", "Restauration & Cuisine", "Commis de cuisine", "CDI", "2026-08-20", "", 3, 46000, 46000, 4600, "Actif", 4),
    "SE-EMP-0013": ("Ouali", "Karima", "Féminin", "1997-11-18", "Restauration & Cuisine", "Serveur / Serveuse", "CDD", "2026-02-12", "2026-11-12", 0, 45000, 45000, 4500, "Actif", 6),
    "SE-EMP-0014": ("Ferhat", "Hakim", "Masculin", "1990-03-09", "Maintenance & Sécurité", "Agent de sécurité", "CDI", "2024-06-01", "", 0, 50000, 50000, 5000, "Actif", 6),
    "SE-EMP-0015": ("Rezgui", "Djamel", "Masculin", "1992-12-05", "Restauration & Cuisine", "Plongeur", "CDD", "2025-10-01", "2026-09-30", 0, 38000, 38000, 3800, "Sorti", 6),
}
_EMP_ORIG_NAMES = {
    "SE-EMP-0001": ("Benali", "Karim", "Masculin", "1982-05-14", "CDI", "2023-03-01"),
    "SE-EMP-0002": ("Mansouri", "Amel", "Féminin", "1985-08-21", "CDI", "2023-03-01"),
    "SE-EMP-0003": ("Khelifi", "Yacine", "Masculin", "1991-02-10", "CDI", "2023-03-01"),
    "SE-EMP-0004": ("Boudiaf", "Nadia", "Féminin", "1987-07-28", "CDI", "2023-03-01"),
    "SE-EMP-0005": ("Zerrouki", "Mourad", "Masculin", "1980-10-02", "CDI", "2023-03-01"),
    "SE-EMP-0006": ("Meziane", "Sofiane", "Masculin", "1993-04-17", "CDI", "2023-03-01"),
    "SE-EMP-0007": ("Hamidi", "Rachid", "Masculin", "1984-12-30", "CDI", "2023-03-01"),
    "SE-EMP-0008": ("Saïdi", "Meriem", "Féminin", "1996-09-09", "CDD", "2023-03-01"),
}
_MISSING = {  # anomalies volontaires de simulation (dossiers incomplets)
    "SE-EMP-0013": {"nin": ""},
    "SE-EMP-0014": {"n_assurance": ""},
}


def _hr_fields(eid: str, e: dict, idx: int) -> dict:
    """Champs RH complémentaires d'un employé (setdefault côté migration)."""
    base = float(e.get("salaire_base") or 0)
    sim = {"donnee_simulation": 1}
    extra = _EMP_EXTRA.get(eid)
    if extra:
        nom, pre, sexe, nais, dept, fct, typ, emb, fin, essai, contr, decl, primes, statut, ndocs = extra
        out = {"nom": nom, "prenom": pre, "sexe": sexe, "date_naissance": nais, "type_contrat": typ, "date_embauche": emb,
               "date_fin_contrat": fin, "periode_essai_mois": essai, "salaire_base_contractuel": contr,
               "salaire_base_declare": decl, "primes_contractuelles": primes, "statut": statut, "departement": dept,
               "fonction": fct, "salaire_base": contr}
    else:
        nom, pre, sexe, nais, typ, emb = _EMP_ORIG_NAMES[eid]
        ndocs = 6 if idx % 3 else 5
        out = {"nom": nom, "prenom": pre, "sexe": sexe, "date_naissance": nais, "type_contrat": typ, "date_embauche": emb,
               "date_fin_contrat": "", "periode_essai_mois": 0, "salaire_base_contractuel": base,
               "salaire_base_declare": base, "primes_contractuelles": round(base * 0.10, 2)}
        if eid == "SE-EMP-0008":
            out["type_contrat"] = "CDD"
            out["date_fin_contrat"] = "2027-02-28"
    out.update({
        "nom_complet": f"{out['prenom']} {out['nom']}",
        "matricule": f"MAT-{int(eid[-4:]):04d}",
        "lieu_naissance": "Alger", "nationalite": "Algérienne", "adresse": f"Cité SIMULATION n°{idx + 1}, Alger", "wilaya": "Alger",
        "telephone": f"0550 00 {idx + 10:02d} {idx + 20:02d}", "email": f"{out['prenom'].lower()}.{out['nom'].lower()}@exemple.invalid",
        "nin": f"999000{int(eid[-4:]):012d}", "n_carte_nationale": f"SIM{int(eid[-4:]):07d}",
        "carte_delivree_le": "2020-01-15", "carte_delivree_par": "Daïra de Bab El Oued (simulation)", "carte_expiration": "2030-01-14",
        "n_assurance": f"99 0000 {int(eid[-4:]):04d} 00", "agence_cnas": "CNAS Alger — Agence simulation",
        "situation_familiale": "Marié(e)" if idx % 2 == 0 else "Célibataire", "nb_enfants": idx % 3,
        "urgence_nom": "Contact SIMULATION", "urgence_tel": "0660 00 00 00",
        "date_prise_poste": out["date_embauche"], "horaires": "Poste de jour", "categorie_pro": "Cat. simulation",
        "qualification": "Qualifié", "centre_cout": out.get("departement") or e.get("departement"), "lieu_travail": "Hôtel Saint Eugène — Alger",
        "indemnites_contractuelles": 6500.0, "avantages": 0.0, "solde_initial_conges": 0.0, "responsable": "SE-EMP-0001" if eid != "SE-EMP-0001" else "",
        "documents_fournis": "|".join(DOCS_RH[:ndocs]), "date_derniere_revision": out["date_embauche"],
    })
    out.update(_MISSING.get(eid, {}))
    out.update(sim)
    return out


def seed_rh(db: dict) -> dict:
    """Insère les données RH de simulation (idempotent : ne remplace jamais des données existantes)."""
    db.setdefault("SE Employe", [])
    employes = {e["name"]: e for e in db["SE Employe"]}
    # ---- employés additionnels ----
    for eid, x in _EMP_EXTRA.items():
        if eid not in employes:
            e = {"name": eid, "nom_complet": f"{x[1]} {x[0]}", "fonction": x[5], "departement": x[4], "salaire_base": float(x[10]),
                 "numero_cnas": f"16 99{int(eid[-4:]):02d} 0000", "mode_paiement_defaut": "Virement", "statut": x[13],
                 "date_embauche": x[7]}
            db["SE Employe"].append(e)
            employes[eid] = e
    for idx, (eid, e) in enumerate(sorted(employes.items())):
        for k, v in _hr_fields(eid, e, idx).items():
            if k in ("nom_complet", "fonction", "departement", "salaire_base", "date_embauche", "statut") and eid not in _EMP_EXTRA:
                continue
            e.setdefault(k, v)
        e["salaire_net_estime"], e["cout_employeur_estime"] = estimate_net_cost(e)

    def put(dt, rows):
        db.setdefault(dt, [])
        existing = {r.get("name") for r in db[dt]}
        for r in rows:
            r.setdefault("donnee_simulation", 1)
            if r["name"] not in existing:
                db[dt].append(r)

    nm = lambda eid: employes[eid]["nom_complet"] if eid in employes else eid
    # ---- paramètres RH (À VALIDER) ----
    P = lambda code, lib, cat, val, unite, src, st="À valider": {
        "name": f"PARAM-RH-{code}-2026-01-01", "code": code, "libelle": lib, "categorie": cat, "valeur": str(val), "unite": unite,
        "date_effet": "2026-01-01", "source_reglementaire": src, "statut_validation": st, "valide_par": ""}
    put("SE Parametres RH", [
        P("taux_cnas_salarial", "Taux cotisation CNAS salariale", "Cotisations", 9, "%", "Paramétrage existant de l'ERP — à confirmer (CNAS)"),
        P("taux_cnas_patronal", "Taux cotisation CNAS patronale", "Cotisations", 26, "%", "Paramétrage existant de l'ERP — à confirmer (CNAS)"),
        P("irg_bareme", "Barème IRG salaires", "Paie", "bareme_erp_2026", "—", "Barème intégré à l'ERP (fiscal) — à valider expert-comptable"),
        P("diviseur_jour_retenue", "Diviseur du salaire pour retenue journalière", "Absences", 30, "jours", "Usage courant — à valider"),
        P("heures_mensuelles", "Heures mensuelles de référence", "Paie", 173.33, "h", "40 h/sem. — à valider"),
        P("majoration_hs", "Coefficient heures supplémentaires", "Paie", 1.5, "×", "À valider selon durée légale / convention"),
        P("conges_jours_par_mois", "Droits à congé annuel par mois travaillé", "Congés", 2.5, "jours", "Règle usuelle — à valider (texte applicable)"),
        P("conges_plafond_annuel", "Plafond annuel de congé", "Congés", 30, "jours", "Règle usuelle — à valider (texte applicable)"),
        P("conges_mode_comptage", "Mode de comptage des congés", "Congés", "calendaires", "—", "calendaires | ouvrables — à valider"),
        P("delai_transmission_arret_jours", "Délai de transmission d'un arrêt maladie", "Arrêts maladie", 2, "jours", "À valider (procédure CNAS en vigueur)"),
        P("delai_declaration_cnas_jours", "Délai de dépôt déclaration CNAS (jours après fin de période)", "Déclarations", 30, "jours", "À valider (échéances CNAS en vigueur)"),
        P("delai_declaration_at_jours", "Délai de déclaration d'un accident du travail", "Déclarations", 2, "jours", "À valider (procédure CNAS en vigueur)"),
        P("seuil_retards_repetes", "Seuil de retards répétés par mois", "Absences", 3, "retards", "Règle interne — à valider"),
        P("compte_charges_personnel", "Compte charges de personnel (rémunérations)", "Comptabilité", "631", "SCF", "Plan SCF — à valider expert-comptable"),
        P("compte_charges_sociales", "Compte charges sociales patronales", "Comptabilité", "635", "SCF", "Plan SCF — à valider expert-comptable"),
        P("compte_personnel_dus", "Compte personnel — rémunérations dues", "Comptabilité", "421", "SCF", "Plan SCF — à valider expert-comptable"),
        P("compte_securite_sociale", "Compte organismes sociaux (CNAS)", "Comptabilité", "431", "SCF", "Plan SCF — à valider expert-comptable"),
        P("compte_irg", "Compte État — IRG retenu à la source", "Comptabilité", "442", "SCF", "Plan SCF — à valider expert-comptable"),
        P("compte_avances", "Compte personnel — avances et prêts", "Comptabilité", "425", "SCF", "Plan SCF — à valider expert-comptable"),
        P("compte_banque", "Compte banque (paiements)", "Comptabilité", "512", "SCF", "Plan SCF — à valider expert-comptable"),
    ])
    # ---- contrats ----
    C = lambda eid, nat, typ, deb, fin, wf, dec="À décider": {
        "name": f"CTR-RH-{eid[-4:]}-{nat[:3].upper()}", "employe": eid, "nom_employe": nm(eid), "n_contrat": f"CT/2026/{eid[-4:]}",
        "nature_mouvement": nat, "type_contrat": typ, "date_contrat": deb, "date_debut": deb, "date_fin": fin,
        "salaire_base_contractuel": employes[eid].get("salaire_base_contractuel"), "responsable": "SE-EMP-0001",
        "decision_renouvellement": dec, "statut_workflow": wf, "observation": "Contrat de simulation"}
    contrats = [C(e, "Création", employes[e].get("type_contrat", "CDI"), employes[e].get("date_embauche", "2023-03-01"),
                  employes[e].get("date_fin_contrat", ""), "Actif") for e in employes if e not in ("SE-EMP-0010",)]
    for c in contrats:
        if c["employe"] == "SE-EMP-0013":
            c["decision_renouvellement"] = "À décider"
        if c["employe"] == "SE-EMP-0009":
            c["statut_workflow"] = "En attente de validation RH"
        if c["employe"] == "SE-EMP-0015":
            c["statut_workflow"] = "Clôturé"
    put("SE Contrat RH", contrats)
    # ---- révisions salariales (versions, jamais rétroactives) ----
    put("SE Revision Salariale", [
        {"name": "REV-SAL-0001", "employe": "SE-EMP-0011", "nom_employe": nm("SE-EMP-0011"), "date_effet": "2026-07-01", "ancien_contractuel": 0.0,
         "nouveau_contractuel": 52000.0, "ancien_declare": 0.0, "nouveau_declare": 48000.0, "ecart_dzd": 4000.0, "ecart_pct": 7.69,
         "motif_revision": "Embauche", "motif_ecart": "", "validation_rh": "En attente", "validation_compta": "En attente"},
        {"name": "REV-SAL-0002", "employe": "SE-EMP-0003", "nom_employe": nm("SE-EMP-0003"), "date_effet": "2026-01-01", "ancien_contractuel": 88000.0,
         "nouveau_contractuel": 92000.0, "ancien_declare": 88000.0, "nouveau_declare": 92000.0, "ecart_dzd": 0.0, "ecart_pct": 0.0,
         "motif_revision": "Augmentation", "motif_ecart": "", "validation_rh": "Validée", "validation_compta": "Validée"},
    ])
    # ---- congés ----
    G = lambda n, eid, typ, d1, d2, j, st: {"name": f"CONGE-{n:04d}", "employe": eid, "nom_employe": nm(eid), "type_conge": typ, "date_debut": d1,
                                            "date_fin": d2, "nb_jours": j, "motif": "Simulation", "date_demande": d1, "statut": st,
                                            "responsable_validation": "SE-EMP-0001"}
    put("SE Conge", [
        G(1, "SE-EMP-0003", "Congé annuel", "2026-08-03", "2026-08-16", 14, "Approuvé"),
        G(2, "SE-EMP-0004", "Congé annuel", "2026-11-02", "2026-11-08", 7, "Approuvé"),
        G(3, "SE-EMP-0006", "Congé annuel", "2026-11-20", "2026-11-26", 7, "Demande"),
        G(4, "SE-EMP-0008", "Congé sans solde", "2026-10-12", "2026-10-14", 3, "Approuvé"),
        G(5, "SE-EMP-0005", "Congé annuel", "2026-09-06", "2026-09-19", 14, "Validé responsable"),
    ])
    # ---- arrêts maladie (aucun diagnostic) ----
    put("SE Arret Maladie", [
        {"name": "ARRET-0001", "employe": "SE-EMP-0007", "nom_employe": nm("SE-EMP-0007"), "date_debut": "2026-11-03", "date_fin_prevue": "2026-11-09",
         "nb_jours": 7, "date_reception_certificat": "", "justificatif_recu": 0, "date_transmission": "", "organisme": "CNAS", "ref_dossier": "",
         "statut_admin": "Déclaré par l'employé", "statut_indemnisation": "Non applicable", "observation_admin": "Certificat à fournir"},
        {"name": "ARRET-0002", "employe": "SE-EMP-0002", "nom_employe": nm("SE-EMP-0002"), "date_debut": "2026-10-20", "date_fin_prevue": "2026-10-26",
         "date_reprise": "2026-10-27", "nb_jours": 7, "date_reception_certificat": "2026-10-21", "justificatif_recu": 1, "date_transmission": "",
         "organisme": "CNAS", "ref_dossier": "", "statut_admin": "Certificat reçu", "statut_indemnisation": "En attente",
         "observation_admin": "À transmettre à la CNAS"},
        {"name": "ARRET-0003", "employe": "SE-EMP-0001", "nom_employe": nm("SE-EMP-0001"), "date_debut": "2026-09-14", "date_fin_prevue": "2026-09-17",
         "date_reprise": "2026-09-18", "nb_jours": 4, "date_reception_certificat": "2026-09-14", "justificatif_recu": 1, "date_transmission": "2026-09-15",
         "organisme": "CNAS", "ref_dossier": "SIM-ARR-0003", "statut_admin": "Clôturé", "statut_indemnisation": "Indemnisé", "observation_admin": "Dossier clôturé"},
    ])
    # ---- présences / absences ----
    A = lambda n, eid, d, typ, mot, just, st="À valider", extra=None: dict({
        "name": f"PRES-{n:04d}", "employe": eid, "nom_employe": nm(eid), "date": d, "type_absence": typ, "motif": mot,
        "justificatif_recu": just, "statut": st, "horaire_prevu": "08:00-17:00", "retenue_validee": 0}, **(extra or {}))
    put("SE Presence Absence", [
        A(1, "SE-EMP-0010", "2026-11-04", "Absence injustifiée", "Non communiqué", 0),
        A(2, "SE-EMP-0011", "2026-10-28", "Retard", "Transport", 0, "Validé", {"retard_minutes": 35, "heure_arrivee": "08:35"}),
        A(3, "SE-EMP-0011", "2026-10-30", "Retard", "Transport", 0, "Validé", {"retard_minutes": 20, "heure_arrivee": "08:20"}),
        A(4, "SE-EMP-0011", "2026-11-02", "Retard", "Transport", 0, "Validé", {"retard_minutes": 25, "heure_arrivee": "08:25"}),
        A(5, "SE-EMP-0013", "2026-10-15", "Absence injustifiée", "Non communiqué", 0, "Validé", {"retenue_validee": 1}),
        A(6, "SE-EMP-0003", "2026-10-22", "Présent", "Heures supplémentaires événement", 1, "Validé", {"heures_sup": 3.0, "heure_arrivee": "08:00", "heure_depart": "20:00"}),
        A(7, "SE-EMP-0012", "2026-10-10", "Absence justifiée", "Rendez-vous administratif", 1, "Validé"),
        A(8, "SE-EMP-0014", "2026-11-03", "Sortie autorisée", "Autorisation responsable", 1, "Validé"),
    ])
    put("SE Accident Travail", [
        {"name": "AT-0001", "employe": "SE-EMP-0005", "nom_employe": nm("SE-EMP-0005"), "date_accident": "2026-10-18", "heure_accident": "14:30",
         "lieu": "Cuisine centrale", "circonstances": "Brûlure légère lors du service (simulation)", "date_declaration": "", "ref_dossier": "",
         "organisme": "CNAS", "statut": "À déclarer", "observation": "Déclaration à effectuer dans le délai réglementaire (à valider)"},
    ])
    put("SE Avance Pret", [
        {"name": "AVP-0001", "employe": "SE-EMP-0008", "nom_employe": nm("SE-EMP-0008"), "type_operation": "Prêt au personnel", "date_operation": "2026-02-01",
         "montant_demande": 120000.0, "montant_approuve": 120000.0, "montant_verse": 120000.0, "mode_paiement": "Virement", "ref_paiement": "VIR-PRET-0001",
         "nb_echeances": 12, "retenue_mensuelle": 10000.0, "date_premiere_retenue": "2026-03-01", "montant_rembourse": 30000.0, "solde_restant": 90000.0,
         "base_autorisation": "Convention de prêt signée (simulation)", "statut": "En cours de remboursement"},
        {"name": "AVP-0002", "employe": "SE-EMP-0006", "nom_employe": nm("SE-EMP-0006"), "type_operation": "Avance sur salaire", "date_operation": "2026-10-20",
         "montant_demande": 30000.0, "montant_approuve": 30000.0, "montant_verse": 30000.0, "mode_paiement": "Espèces", "ref_paiement": "",
         "nb_echeances": 3, "retenue_mensuelle": 10000.0, "date_premiere_retenue": "2026-11-01", "montant_rembourse": 0.0, "solde_restant": 30000.0,
         "base_autorisation": "", "statut": "Versé"},
    ])
    put("SE Sortie Personnel", [
        {"name": "SORTIE-0001", "employe": "SE-EMP-0015", "nom_employe": nm("SE-EMP-0015"), "date_depart": "2026-09-30", "type_depart": "Fin de CDD",
         "motif": "Terme du contrat", "preavis_jours": 0, "dernier_jour_travaille": "2026-09-30", "solde_conges": 4.0, "dernier_salaire": 38000.0,
         "avances_restantes": 0.0, "chk_contrat_cloture": 1, "chk_derniere_paie": 0, "chk_conges_regularises": 0, "chk_avances_controlees": 1,
         "chk_documents_remis": 1, "chk_declaration_sortie": 0, "chk_acces_desactives": 1, "chk_materiel_restitue": 1, "chk_dossier_archive": 0,
         "validation_rh": "En attente", "validation_direction": "En attente", "statut": "En cours"},
    ])
    employes["SE-EMP-0015"].setdefault("date_sortie", "2026-09-30")
    # ---- paie : périodes (janv.–mars 2026 déjà payées), CNAS ----
    fiches = db.get("SE Fiche de Paie Mensuelle", [])
    periodes, cnas = [], []
    for i, mois in enumerate(("2026-01", "2026-02", "2026-03")):
        fm = [f for f in fiches if f.get("mois") == mois]
        if not fm:
            continue
        for f in fm:
            f.setdefault("base_cotisation", round(float(f.get("salaire_base", 0)) + float(f.get("primes", 0)), 2))
            f.setdefault("cout_employeur", round(float(f.get("salaire_brut", 0)) + float(f.get("charges_patronales_cnas", 0)), 2))
            f.setdefault("date_paiement", f"{mois}-28")
            f.setdefault("retenue_avances", 0.0)
            f.setdefault("retenue_absences", 0.0)
            f.setdefault("montant_heures_sup", 0.0)
            f.setdefault("nb_heures_sup", 0.0)
        S = lambda k: round(sum(float(f.get(k) or 0) for f in fm), 2)
        comptabilise = 1 if mois == "2026-01" else 0
        for f in fm:
            f["comptabilise"] = comptabilise
        periodes.append({"name": f"PERIODE-{mois}", "mois": mois, "departement": "Tous", "statut_paie": "Comptabilisée" if comptabilise else "Payée",
                         "date_preparation": f"{mois}-25", "date_validation": f"{mois}-26", "responsable_rh": "Responsable RH (simulation)",
                         "responsable_compta": "Amel Mansouri", "nb_bulletins": len(fm), "total_brut": S("salaire_brut"), "total_net": S("net_a_payer"),
                         "total_cnas_sal": S("retenue_cnas"), "total_cnas_pat": S("charges_patronales_cnas"), "total_irg": S("retenue_irg"),
                         "cout_employeur": S("cout_employeur"), "total_paye": S("net_a_payer"), "ecriture_generee": comptabilise})
        statuts = ["Payée", "Déposée", "Préparée"]
        sal, pat = S("retenue_cnas"), S("charges_patronales_cnas")
        stt = statuts[i]
        cnas.append({"name": f"CNAS-DECL-{mois}", "periode": mois, "type_declaration": "Déclaration périodique des cotisations",
                     "n_employeur_cnas": "SIM-EMP-00000", "agence_cnas": "CNAS Alger (simulation)", "nb_employes": len(fm),
                     "masse_salariale": S("base_cotisation"), "total_bases": S("base_cotisation"), "cotisations_salariales": sal,
                     "cotisations_patronales": pat, "total_cotisations": round(sal + pat, 2), "date_preparation": f"{mois}-26",
                     "date_limite": _end_next_month(mois), "statut": stt,
                     "date_depot": f"{mois}-29" if stt in ("Payée", "Déposée") else "",
                     "ref_declaration": f"SIM-ACC-{mois}" if stt in ("Payée", "Déposée") else "",
                     "date_paiement": f"{mois}-30" if stt == "Payée" else "", "ref_paiement": f"SIM-BDX-{mois}" if stt == "Payée" else "",
                     "anomalies": "", "observation": "Simulation"})
    put("SE Periode Paie", periodes)
    put("SE Declaration CNAS", cnas)
    # ---- écritures comptables de la période comptabilisée (2026-01) ----
    ecr = []
    pj = [p for p in periodes if p["mois"] == "2026-01"]
    if pj:
        p = pj[0]
        fm = [f for f in fiches if f.get("mois") == "2026-01"]
        autres = round(sum(float(f.get("autres_retenues") or 0) for f in fm), 2)
        lines = [("631", "Rémunérations du personnel", p["total_brut"], 0), ("635", "Cotisations patronales CNAS", p["total_cnas_pat"], 0),
                 ("421", "Personnel — rémunérations dues (net)", 0, p["total_net"]),
                 ("431", "CNAS (part salariale + patronale)", 0, round(p["total_cnas_sal"] + p["total_cnas_pat"], 2)),
                 ("442", "IRG retenu à la source", 0, p["total_irg"])]
        if autres:
            lines.append(("425", "Avances / prêts retenus", 0, autres))
        for n, (cpt, lib, d, c) in enumerate(lines, 1):
            ecr.append({"name": f"ECR-RH-2026-01-{n:02d}", "date_ecriture": "2026-01-26", "journal": "OD Paie", "periode": "2026-01",
                        "piece": "PAIE-2026-01-COMPTA", "origine": "Paie", "compte": cpt, "libelle": lib, "debit": d, "credit": c})
    put("SE Ecriture RH", ecr)
    return db


def _end_next_month(mois: str, delai_jours: int = 30) -> str:
    """Date limite indicative = fin de période + délai paramétré (À valider selon procédure CNAS)."""
    import calendar
    from datetime import date, timedelta
    y, m = int(mois[:4]), int(mois[5:7])
    fin = date(y, m, calendar.monthrange(y, m)[1])
    return (fin + timedelta(days=delai_jours)).isoformat()


def estimate_net_cost(e: dict, sal_rate=0.09, pat_rate=0.26) -> tuple[float, float]:
    decl = float(e.get("salaire_base_declare") or e.get("salaire_base_contractuel") or e.get("salaire_base") or 0)
    primes = float(e.get("primes_contractuelles") or 0)
    indem = float(e.get("indemnites_contractuelles") or 0)
    assiette = decl + primes
    cs = round(assiette * sal_rate, 2)
    cp = round(assiette * pat_rate, 2)
    net = round(assiette + indem - cs - _irg(assiette - cs), 2)
    return net, round(assiette + indem + cp, 2)


def ensure_rh(db: dict) -> dict:
    """Migration idempotente d'une base existante vers le module RH."""
    return seed_rh(db)


def sanitize_db_for_backup(db: dict) -> dict:
    """Copie de la base sans donnée de santé ni identifiant sensible (sauvegarde Google Sheet / script .gs)."""
    out = {}
    for dt, rows in db.items():
        if dt in RH_CONFIDENTIAL_DOCTYPES:
            continue
        if dt == "SE Employe":
            out[dt] = [{k: v for k, v in r.items() if k not in SENSITIVE_EMPLOYEE_FIELDS} for r in rows]
        else:
            out[dt] = rows
    return out


if __name__ == "__main__":
    write_doctypes()
    print("OK : DocTypes RH générés et SE Employe / SE Fiche de Paie étendus.")
