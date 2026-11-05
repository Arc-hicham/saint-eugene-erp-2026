# -*- coding: utf-8 -*-
"""
Serveur Local Instantané "Saint Eugène ERP 2026" (Windows / Python natif + SQLite)
Permet de lancer et utiliser immédiatement l'application Hôtel Saint Eugène 4★ (Alger)
sur http://localhost:8080 sans attendre l'installation de WSL2 / Docker.

Charge dynamiquement :
- Les 22 schémas JSON officiels des DocTypes (`saint_eugene/saint_eugene/doctype/*/*.json`)
- Le moteur fiscal algérien (`fiscal_dz.py` : Droit de timbre espèces, Taxe de séjour 4★, Arrêté en lettres DZD, CNAS 9%/26%, IRG)
- Les 10 Number Cards, les 4 Graphiques 2026, les 4 Alertes Contrôle de Gestion, et les impressions PDF SCF.
"""
from __future__ import annotations

import json
import sys
import types
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent
LOGO_BASE64_URI = "data:image/png;base64,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"
DOCTYPE_DIR = APP_ROOT / "saint_eugene" / "saint_eugene" / "doctype"
DB_FILE = APP_ROOT / "saint_eugene_2026_data.json"

# Shim léger de `frappe` pour importer directement `fiscal_dz.py` et le barème IRG/CNAS en Python natif
if "frappe" not in sys.modules:
    frappe_stub = types.ModuleType("frappe")
    frappe_stub.whitelist = lambda *a, **kw: (lambda fn: fn)
    frappe_stub._ = lambda s: s
    frappe_utils = types.ModuleType("frappe.utils")
    frappe_utils.flt = lambda x, p=None: round(float(x or 0), p) if p is not None else float(x or 0)
    frappe_utils.cint = lambda x: int(float(x or 0))
    sys.modules["frappe"] = frappe_stub
    sys.modules["frappe.utils"] = frappe_utils

sys.path.insert(0, str(APP_ROOT))
from saint_eugene.utils.fiscal_dz import (  # noqa: E402
    DEFAULT_SETTINGS,
    compute_droit_timbre_algerie,
    compute_taxe_sejour_algerie,
    montant_dzd_en_lettres,
)
from saint_eugene.utils.invoice_calc import (
    ARTICLE_CATEGORY,
    ROOM_TYPES,
    SERVICES,
    compute_invoice_dict,
)


def compute_irg_algerie(revenu_imposable: float) -> float:
    rev = float(revenu_imposable or 0)
    if rev <= 30_000.0:
        return 0.0
    tranches = [
        (20_000.0, 0.00),
        (40_000.0, 0.23),
        (80_000.0, 0.27),
        (160_000.0, 0.30),
        (320_000.0, 0.33),
        (float("inf"), 0.35),
    ]
    impot_brut = 0.0
    plancher = 0.0
    for plafond, taux in tranches:
        if rev <= plancher:
            break
        impot_brut += (min(rev, plafond) - plancher) * taux
        plancher = plafond
    abattement = min(max(impot_brut * 0.40, 1_000.0), 1_500.0)
    irg = max(0.0, impot_brut - abattement)
    if 30_000.0 < rev < 35_000.0:
        irg = max(0.0, irg * (137.0 / 51.0) - (27_925.0 / 8.0))
    return round(irg, 2)


def load_doctype_schemas() -> dict[str, dict]:
    schemas = {}
    for folder in sorted(DOCTYPE_DIR.iterdir()):
        if not folder.is_dir():
            continue
        jf = folder / f"{folder.name}.json"
        if jf.exists():
            data = json.loads(jf.read_text(encoding="utf-8"))
            schemas[data["name"]] = data
    return schemas


import rh_module
rh_module.write_doctypes()
rh_module.extend_existing()
SCHEMAS = load_doctype_schemas()


def build_initial_seed_db() -> dict:
    """Construit la base de données initiale 2026 de l'Hôtel Saint Eugène 4★ à Alger."""
    db: dict[str, list[dict]] = {dt: [] for dt in SCHEMAS}
    db["SE Parametres Hotel"] = [dict(DEFAULT_SETTINGS, name="SE Parametres Hotel")]

    db["SE Compte Tresorerie"] = [
        {"name": "Caisse Principale Hôtel", "nom_compte": "Caisse Principale Hôtel", "type_compte": "Caisse", "compte_scf": "531000", "banque": "—", "solde_initial": 850000.0, "solde_actuel": 850000.0},
        {"name": "Caisse Réception & Restaurant", "nom_compte": "Caisse Réception & Restaurant", "type_compte": "Caisse", "compte_scf": "532000", "banque": "—", "solde_initial": 320000.0, "solde_actuel": 320000.0},
        {"name": "BNA Agence Bologhine - DZD", "nom_compte": "BNA Agence Bologhine - DZD", "type_compte": "Banque", "compte_scf": "512100", "banque": "BNA", "numero_compte_rib": "00100614030001458921", "solde_initial": 14500000.0, "solde_actuel": 14500000.0},
        {"name": "BEA Alger Centre - DZD", "nom_compte": "BEA Alger Centre - DZD", "type_compte": "Banque", "compte_scf": "512200", "banque": "BEA", "numero_compte_rib": "00200012020008874105", "solde_initial": 8200000.0, "solde_actuel": 8200000.0},
        {"name": "CPA Bab El Oued - DZD", "nom_compte": "CPA Bab El Oued - DZD", "type_compte": "Banque", "compte_scf": "512300", "banque": "CPA", "numero_compte_rib": "00400108401005593214", "solde_initial": 4100000.0, "solde_actuel": 4100000.0},
    ]

    db["SE Client"] = [
        {"name": "SONATRACH - Direction Générale Hydra", "nom_client": "SONATRACH - Direction Générale Hydra", "type_client": "Corporate", "delai_paiement_jours": 30, "nif": "000016001245871", "nis": "0998160100452", "rc": "16/00-0012458B00", "article_imposition": "16120145879", "telephone": "+213 23 48 30 00", "adresse": "Djenane El Malik, Hydra, Alger"},
        {"name": "Air Algérie - Direction des Opérations", "nom_client": "Air Algérie - Direction des Opérations", "type_client": "Corporate", "delai_paiement_jours": 45, "nif": "000016001874512", "rc": "16/00-0021547B00", "telephone": "+213 21 98 63 63", "adresse": "1 Place Maurice Audin, Alger Centre"},
        {"name": "ATM Mobilis - Direction Régionale Alger", "nom_client": "ATM Mobilis - Direction Régionale Alger", "type_client": "Corporate", "delai_paiement_jours": 30, "nif": "000316096514203", "rc": "16/00-0965142B03", "telephone": "+213 23 92 10 00", "adresse": "Quartier d'Affaires Bab Ezzouar, Alger"},
        {"name": "COSIDER Groupe Spa", "nom_client": "COSIDER Groupe Spa", "type_client": "Corporate", "delai_paiement_jours": 30, "nif": "000016004512398", "rc": "16/00-0045123B00", "telephone": "+213 23 53 40 40", "adresse": "Route de Dar El Beïda, Alger"},
        {"name": "Touring Club d'Algérie (Agence)", "nom_client": "Touring Club d'Algérie (Agence)", "type_client": "Agence", "delai_paiement_jours": 15, "nif": "000116007891204", "rc": "16/00-0078912B01", "telephone": "+213 21 73 42 15", "adresse": "Rue Hassiba Ben Bouali, Alger"},
        {"name": "Client Passager Comptoir (Walk-in)", "nom_client": "Client Passager Comptoir (Walk-in)", "type_client": "Passager", "delai_paiement_jours": 0, "nif": "—", "telephone": "—", "adresse": "Réception Hôtel Saint Eugène, Alger"},
    ]

    db["SE Fournisseur"] = [
        {"name": "Sarl El Djazaïr Food & Beverage Pro", "nom_fournisseur": "Sarl El Djazaïr Food & Beverage Pro", "categorie": "Alimentation & Boissons (F&B)", "nif": "001216088451209", "rc": "16/00-0884512B12", "rib": "00100614030009988776", "telephone": "+213 23 81 12 45"},
        {"name": "SONELGAZ - Direction Distribution Bologhine", "nom_fournisseur": "SONELGAZ - Direction Distribution Bologhine", "categorie": "Énergie & Eau (Sonelgaz/SEAAL)", "nif": "000016000112233", "telephone": "3303"},
        {"name": "SEAAL - Eau et Assainissement d'Alger", "nom_fournisseur": "SEAAL - Eau et Assainissement d'Alger", "categorie": "Énergie & Eau (Sonelgaz/SEAAL)", "nif": "000616000445566", "telephone": "1594"},
        {"name": "Algérie Télécom Entreprises (Fibre Pro)", "nom_fournisseur": "Algérie Télécom Entreprises (Fibre Pro)", "categorie": "Télécom & IT", "nif": "000216000778899", "telephone": "+213 21 82 38 38"},
        {"name": "Blanchisserie Hôtelière de la Baie Spa", "nom_fournisseur": "Blanchisserie Hôtelière de la Baie Spa", "categorie": "Produits d'Accueil & Linge", "nif": "001516077412365", "rib": "00400108401007741236"},
        {"name": "Eurl Maghreb Ascenseurs & Climatisation CVC", "nom_fournisseur": "Eurl Maghreb Ascenseurs & Climatisation CVC", "categorie": "Maintenance & Technique", "nif": "001416055321478", "rib": "00200012020005532147"},
    ]

    employes = [
        ("SE-EMP-0001", "Karim Benali", "Directeur d'Exploitation", "Direction & Administration", 185000.0, "16 8401 2291"),
        ("SE-EMP-0002", "Amel Mansouri", "Chef Comptable SCF", "Direction & Administration", 125000.0, "16 8902 4410"),
        ("SE-EMP-0003", "Yacine Khelifi", "Chef de Réception", "Réception & Hébergement", 92000.0, "16 9104 3382"),
        ("SE-EMP-0004", "Nadia Boudiaf", "Gouvernante Générale", "Étages & Housekeeping", 85000.0, "16 8705 1129"),
        ("SE-EMP-0005", "Mourad Zerrouki", "Chef Exécutif Cuisine", "Restauration & Cuisine", 135000.0, "16 8209 7741"),
        ("SE-EMP-0006", "Sofiane Meziane", "Maître d'Hôtel", "Restauration & Cuisine", 78000.0, "16 9301 5560"),
        ("SE-EMP-0007", "Rachid Hamidi", "Responsable Technique & CVC", "Maintenance & Sécurité", 88000.0, "16 8603 9982"),
        ("SE-EMP-0008", "Meriem Saïdi", "Réceptionniste Bilingue", "Réception & Hébergement", 58000.0, "16 9807 6614"),
    ]
    for eid, nom, fct, dept, base, cnas_num in employes:
        db["SE Employe"].append(
            {"name": eid, "nom_complet": nom, "fonction": fct, "departement": dept, "salaire_base": base, "numero_cnas": cnas_num, "date_embauche": "2023-03-01", "mode_paiement_defaut": "Virement", "statut": "Actif"}
        )
        for mois in ("2026-01", "2026-02", "2026-03"):
            primes = round(base * 0.10, 2)
            indem = 6500.0
            assiette = base + primes
            cnas_sal = round(assiette * 0.09, 2)
            cnas_pat = round(assiette * 0.26, 2)
            irg = compute_irg_algerie(assiette - cnas_sal)
            brut = round(assiette + indem, 2)
            tot_ret = round(cnas_sal + irg, 2)
            net = round(brut - tot_ret, 2)
            db["SE Fiche de Paie Mensuelle"].append(
                {
                    "name": f"PAIE-{mois}-{eid}",
                    "mois": mois,
                    "employe": eid,
                    "nom_employe": nom,
                    "fonction": fct,
                    "departement": dept,
                    "salaire_base": base,
                    "primes": primes,
                    "indemnites": indem,
                    "salaire_brut": brut,
                    "charges_patronales_cnas": cnas_pat,
                    "retenue_cnas": cnas_sal,
                    "retenue_irg": irg,
                    "autres_retenues": 0.0,
                    "total_retenues": tot_ret,
                    "net_a_payer": net,
                    "mode_paiement": "Virement",
                    "ref_paiement": f"VIR-PAIE-{mois}-{eid}",
                    "statut": "Payée",
                    "docstatus": 1,
                }
            )

    # Budget Annuel 2026
    saison_coef = {1: 0.90, 2: 0.95, 3: 0.85, 4: 1.00, 5: 1.10, 6: 1.20, 7: 1.25, 8: 1.20, 9: 1.15, 10: 1.10, 11: 1.00, 12: 1.05}
    bases = {"CA Hébergement": 6800000.0, "CA Restauration": 2600000.0, "Salaires": 1050000.0, "Achats": 1450000.0, "Charges": 750000.0}
    for m in range(1, 13):
        mois = f"2026-{m:02d}"
        coef = saison_coef[m]
        for cat, bval in bases.items():
            prevu = round(bval * (coef if "CA" in cat or cat == "Achats" else 1.0), -3)
            db["SE Budget Annuel"].append(
                {
                    "name": f"BUD-{mois}-{cat}",
                    "mois": mois,
                    "categorie": cat,
                    "type_flux": "Produit (CA)" if "CA" in cat else "Charge (Dépense)",
                    "budget_prevu": prevu,
                    "realise": 0.0,
                    "ecart_dzd": 0.0,
                    "ecart_pct": 0.0,
                    "statut_budget": "Conforme",
                }
            )

    # Factures Clients & Factures Pro Forma & Encaissements
    factures_seed = [
        {
            "name": "FAC-CLI-2026-00001",
            "date_facture": "2026-01-12",
            "date_echeance": "2026-02-11",
            "client": "SONATRACH - Direction Générale Hydra",
            "type_client": "Corporate",
            "ref_reservation": "SE-RES-2026-001",
            "mode_paiement_prevu": "Virement",
            "sejours_separes": 0,
            "taxe_sejour_incluse": 1,
            "appliquer_taxe_sejour": 1,
            "date_arrivee": "2026-01-05",
            "date_depart": "2026-01-12",
            "statut": "Validée",
            "docstatus": 1,
            "sejours": [
                {"sejour_no": 1, "description": "Séjour Délégation Direction Hydra", "date_arrivee": "2026-01-05", "date_depart": "2026-01-12", "nuitees": 7, "nb_personnes": 12}
            ],
            "lignes": [
                {"sejour_no": 1, "article": "Single", "quantite": 8, "nb_jours": 7, "nb_personnes": 8, "montant_ttc_saisi": 2400000.0},
                {"sejour_no": 1, "article": "Suite Deluxe", "quantite": 2, "nb_jours": 7, "nb_personnes": 4, "montant_ttc_saisi": 1400000.0},
                {"sejour_no": 1, "article": "Dîner", "quantite": 40, "nb_jours": 1, "nb_personnes": 0, "montant_ttc_saisi": 400000.0},
            ],
            "enc": ("ENC-2026-00001", "2026-01-28", "FULL", "Virement", "BNA Agence Bologhine - DZD", "VIR-SNT-2601")
        },
        {
            "name": "FAC-CLI-2026-00002",
            "date_facture": "2026-01-20",
            "date_echeance": "2026-01-20",
            "client": "Client Passager Comptoir (Walk-in)",
            "type_client": "Passager",
            "ref_reservation": "SE-RES-2026-002",
            "mode_paiement_prevu": "Espèces",
            "sejours_separes": 0,
            "taxe_sejour_incluse": 1,
            "appliquer_taxe_sejour": 1,
            "date_arrivee": "2026-01-18",
            "date_depart": "2026-01-20",
            "statut": "Validée",
            "docstatus": 1,
            "sejours": [
                {"sejour_no": 1, "description": "Séjour Famille Passager", "date_arrivee": "2026-01-18", "date_depart": "2026-01-20", "nuitees": 2, "nb_personnes": 4}
            ],
            "lignes": [
                {"sejour_no": 1, "article": "Double", "quantite": 2, "nb_jours": 2, "nb_personnes": 4, "montant_ttc_saisi": 285000.0},
            ],
            "enc": ("ENC-2026-00002", "2026-01-20", "FULL", "Espèces", "Caisse Principale Hôtel", "CAISSE-JAN-01")
        },
        {
            "name": "FAC-CLI-2026-00003",
            "date_facture": "2026-01-25",
            "date_echeance": "2026-02-24",
            "client": "ATM Mobilis - Direction Régionale Alger",
            "type_client": "Corporate",
            "ref_reservation": "SE-RES-2026-003",
            "mode_paiement_prevu": "Virement",
            "sejours_separes": 0,
            "taxe_sejour_incluse": 1,
            "appliquer_taxe_sejour": 0,
            "statut": "Validée",
            "docstatus": 1,
            "lignes": [
                {"sejour_no": 1, "article": "Déjeuner", "quantite": 70, "nb_jours": 1, "nb_personnes": 0, "montant_ttc_saisi": 1750000.0},
                {"sejour_no": 1, "article": "Coffee Break", "quantite": 70, "nb_jours": 1, "nb_personnes": 0, "montant_ttc_saisi": 700000.0},
            ],
            "enc": ("ENC-2026-00003", "2026-02-10", "FULL", "Virement", "BEA Alger Centre - DZD", "VIR-MOB-2602")
        },
        {
            "name": "FAC-CLI-2026-00004",
            "date_facture": "2026-02-14",
            "date_echeance": "2026-12-15",
            "client": "COSIDER Groupe Spa",
            "type_client": "Corporate",
            "ref_reservation": "SE-RES-2026-004",
            "mode_paiement_prevu": "Chèque",
            "sejours_separes": 1,
            "taxe_sejour_incluse": 1,
            "appliquer_taxe_sejour": 1,
            "statut": "Validée",
            "docstatus": 1,
            "sejours": [
                {"sejour_no": 1, "description": "Séjour Direction Alger", "date_arrivee": "2026-02-10", "date_depart": "2026-02-12", "nuitees": 2, "nb_personnes": 4},
                {"sejour_no": 2, "description": "Séjour Équipe Chantier Port", "date_arrivee": "2026-02-12", "date_depart": "2026-02-14", "nuitees": 2, "nb_personnes": 6}
            ],
            "lignes": [
                {"sejour_no": 1, "article": "Suite Deluxe", "quantite": 2, "nb_jours": 2, "nb_personnes": 4, "montant_ttc_saisi": 2100000.0},
                {"sejour_no": 2, "article": "Twin", "quantite": 3, "nb_jours": 2, "nb_personnes": 6, "montant_ttc_saisi": 2800000.0},
            ],
            "enc": ("ENC-2026-00004", "2026-02-22", 2500000.0, "Chèque", "BNA Agence Bologhine - DZD", "CHQ-COS-884120")
        },
        {
            "name": "FAC-CLI-2026-00005",
            "date_facture": "2026-02-20",
            "date_echeance": "2026-03-07",
            "client": "Touring Club d'Algérie (Agence)",
            "type_client": "Agence",
            "ref_reservation": "SE-RES-2026-005",
            "mode_paiement_prevu": "TPE",
            "sejours_separes": 0,
            "taxe_sejour_incluse": 1,
            "appliquer_taxe_sejour": 0,
            "statut": "Validée",
            "docstatus": 1,
            "lignes": [
                {"sejour_no": 1, "article": "Déjeuner", "quantite": 50, "nb_jours": 1, "nb_personnes": 0, "montant_ttc_saisi": 1850000.0},
                {"sejour_no": 1, "article": "Dîner", "quantite": 30, "nb_jours": 1, "nb_personnes": 0, "montant_ttc_saisi": 900000.0},
            ],
            "enc": ("ENC-2026-00005", "2026-02-26", "FULL", "TPE", "CPA Bab El Oued - DZD", "TPE-CIB-9921")
        },
        {
            "name": "FAC-CLI-2026-00006",
            "date_facture": "2026-03-05",
            "date_echeance": "2026-04-19",
            "client": "Air Algérie - Direction des Opérations",
            "type_client": "Corporate",
            "ref_reservation": "SE-RES-2026-006",
            "mode_paiement_prevu": "Virement",
            "sejours_separes": 0,
            "taxe_sejour_incluse": 1,
            "appliquer_taxe_sejour": 1,
            "date_arrivee": "2026-03-01",
            "date_depart": "2026-03-05",
            "statut": "Validée",
            "docstatus": 1,
            "sejours": [
                {"sejour_no": 1, "description": "Séjour Équipage Pilotes & PNC", "date_arrivee": "2026-03-01", "date_depart": "2026-03-05", "nuitees": 4, "nb_personnes": 15}
            ],
            "lignes": [
                {"sejour_no": 1, "article": "Single", "quantite": 15, "nb_jours": 4, "nb_personnes": 15, "montant_ttc_saisi": 3850000.0},
            ],
            "enc": None
        },
        {
            "name": "FAC-CLI-2026-00007",
            "date_facture": "2026-03-18",
            "date_echeance": "2026-12-28",
            "client": "SONATRACH - Direction Générale Hydra",
            "type_client": "Corporate",
            "ref_reservation": "SE-RES-2026-007",
            "mode_paiement_prevu": "Virement",
            "sejours_separes": 0,
            "taxe_sejour_incluse": 1,
            "appliquer_taxe_sejour": 0,
            "statut": "Validée",
            "docstatus": 1,
            "lignes": [
                {"sejour_no": 1, "article": "Location de salle", "quantite": 3, "nb_jours": 3, "nb_personnes": 0, "montant_ttc_saisi": 1800000.0},
                {"sejour_no": 1, "article": "Coffee Break", "quantite": 120, "nb_jours": 1, "nb_personnes": 0, "montant_ttc_saisi": 1100000.0},
            ],
            "enc": None
        },
    ]

    for fdoc in factures_seed:
        enc_info = fdoc.pop("enc", None)
        compute_invoice_dict(fdoc, DEFAULT_SETTINGS)
        fdoc["montant_encaisse"] = 0.0
        fdoc["reste_a_encaisser"] = fdoc["montant_ttc"]
        fdoc["statut"] = "Validée"
        fdoc["jours_retard"] = 0
        db["SE Facture Client"].append(fdoc)
        if enc_info:
            ename, denc, mnt_raw, emode, ecpte, eref = enc_info
            emnt = fdoc["montant_ttc"] if mnt_raw == "FULL" else float(mnt_raw)
            db["SE Encaissement"].append(
                {
                    "name": ename,
                    "date_encaissement": denc,
                    "client": fdoc["client"],
                    "facture_liee": fdoc["name"],
                    "montant": emnt,
                    "mode_paiement": emode,
                    "compte_destination": ecpte,
                    "ref_paiement": eref,
                    "statut_cheque": "En portefeuille (Non encaissé)" if emode == "Chèque" else "N/A",
                    "statut": "Validé",
                    "docstatus": 1,
                }
            )

    proforma_seed = [
        {
            "name": "PRO-2026-00001",
            "date_facture": "2026-11-04",
            "date_validite": "2026-11-25",
            "client": "SONATRACH - Direction Générale Hydra",
            "type_client": "Corporate",
            "ref_devis": "DEV-2026-001",
            "mode_paiement_prevu": "Virement",
            "sejours_separes": 1,
            "taxe_sejour_incluse": 1,
            "appliquer_taxe_sejour": 1,
            "statut": "Pro Forma",
            "conditions_reglement": "Acompte 50% à la confirmation, solde à réception de facture par virement bancaire BNA.",
            "notes_proforma": "Séminaire Stratégique Direction Générale & hébergement exécutif 4 étoiles.",
            "docstatus": 0,
            "sejours": [
                {"sejour_no": 1, "description": "Séjour Comité de Direction", "date_arrivee": "2026-11-15", "date_depart": "2026-11-18", "nuitees": 3, "nb_personnes": 5},
                {"sejour_no": 2, "description": "Séjour Cadres & Intervenants", "date_arrivee": "2026-11-15", "date_depart": "2026-11-18", "nuitees": 3, "nb_personnes": 5}
            ],
            "lignes": [
                {"sejour_no": 1, "article": "Suite Saint Eugène", "quantite": 2, "nb_jours": 3, "nb_personnes": 2, "montant_ttc_saisi": 540000.0},
                {"sejour_no": 1, "article": "Suite Deluxe", "quantite": 3, "nb_jours": 3, "nb_personnes": 3, "montant_ttc_saisi": 630000.0},
                {"sejour_no": 2, "article": "Double", "quantite": 5, "nb_jours": 3, "nb_personnes": 5, "montant_ttc_saisi": 720000.0},
                {"sejour_no": 1, "article": "Location de salle", "quantite": 3, "nb_jours": 3, "nb_personnes": 0, "montant_ttc_saisi": 450000.0},
                {"sejour_no": 1, "article": "Coffee Break", "quantite": 30, "nb_jours": 3, "nb_personnes": 0, "montant_ttc_saisi": 180000.0},
                {"sejour_no": 1, "article": "Déjeuner", "quantite": 30, "nb_jours": 3, "nb_personnes": 0, "montant_ttc_saisi": 360000.0},
            ]
        },
        {
            "name": "PRO-2026-00002",
            "date_facture": "2026-11-03",
            "date_validite": "2026-11-30",
            "client": "Air Algérie - Direction des Opérations",
            "type_client": "Corporate",
            "ref_devis": "DEV-2026-002",
            "mode_paiement_prevu": "Virement",
            "sejours_separes": 0,
            "taxe_sejour_incluse": 1,
            "appliquer_taxe_sejour": 1,
            "date_arrivee": "2026-12-01",
            "date_depart": "2026-12-05",
            "statut": "Confirmée",
            "conditions_reglement": "Règlement sous 30 jours fin de mois après vérification des bons de commande.",
            "notes_proforma": "Hébergement équipage escale Alger - Décembre 2026.",
            "docstatus": 0,
            "sejours": [
                {"sejour_no": 1, "description": "Séjour Équipage Rotation Internationale", "date_arrivee": "2026-12-01", "date_depart": "2026-12-05", "nuitees": 4, "nb_personnes": 6}
            ],
            "lignes": [
                {"sejour_no": 1, "article": "Twin", "quantite": 6, "nb_jours": 4, "nb_personnes": 6, "montant_ttc_saisi": 960000.0},
                {"sejour_no": 1, "article": "Dîner", "quantite": 24, "nb_jours": 1, "nb_personnes": 0, "montant_ttc_saisi": 216000.0},
            ]
        }
    ]
    for pdoc in proforma_seed:
        compute_invoice_dict(pdoc, DEFAULT_SETTINGS)
        db.setdefault("SE Facture Pro Forma", []).append(pdoc)

    # Factures Fournisseurs & Décaissements
    frn_seed = [
        ("FAC-FRN-2026-00001", "FF-2026-0101", "Sarl El Djazaïr Food & Beverage Pro", "2026-01-10", "2026-02-10", "Approvisionnement viandes, poissons frais & épicerie fine Restaurant", 1320000.0, ("DEC-2026-00001", "2026-01-29", 1570800.0, "Virement", "BNA Agence Bologhine - DZD", "VIR-FRN-0101")),
        ("FAC-FRN-2026-00002", "FF-2026-0204", "Blanchisserie Hôtelière de la Baie Spa", "2026-02-12", "2026-03-12", "Traitement & repassage linge chambres 4★ - Février 2026", 640000.0, ("DEC-2026-00002", "2026-02-25", 400000.0, "Chèque", "BNA Agence Bologhine - DZD", "CHQ-BNA-45012")),
        ("FAC-FRN-2026-00003", "FF-2026-0309", "Sarl El Djazaïr Food & Beverage Pro", "2026-03-08", "2026-04-08", "Denrées alimentaires & boissons - Banquets Mars 2026", 1280000.0, None),
    ]
    for ffname, num_ff, frn, dfac, dech, obj, ht, dec in frn_seed:
        tva = round(ht * 0.19, 2)
        ttc = round(ht + tva, 2)
        db["SE Facture Fournisseur"].append(
            {
                "name": ffname,
                "numero_facture_fournisseur": num_ff,
                "fournisseur": frn,
                "date_facture": dfac,
                "date_echeance": dech,
                "objet": obj,
                "montant_ht": ht,
                "taux_tva": 19.0,
                "montant_tva": tva,
                "montant_ttc": ttc,
                "montant_paye": 0.0,
                "reste_a_payer": ttc,
                "statut": "Validée",
                "docstatus": 1,
            }
        )
        if dec:
            dname, ddec, dmnt, dmode, dcpte, dref = dec
            db["SE Decaissement"].append(
                {
                    "name": dname,
                    "date_decaissement": ddec,
                    "type_beneficiaire": "Fournisseur",
                    "fournisseur": frn,
                    "beneficiaire": frn,
                    "facture_liee": ffname,
                    "motif": obj,
                    "montant": dmnt,
                    "mode_paiement": dmode,
                    "compte_source": dcpte,
                    "ref_paiement": dref,
                    "validation_daf": 1,
                    "statut": "Validé",
                    "docstatus": 1,
                }
            )

    db["SE Decaissement"].append(
        {
            "name": "DEC-2026-00003",
            "date_decaissement": "2026-01-22",
            "type_beneficiaire": "Autre Bénéficiaire",
            "fournisseur": "",
            "beneficiaire": "Régie Achats Urgents Cuisine & Réception",
            "facture_liee": "",
            "motif": "Fleurs hall, courses fraîches marché & fournitures accueil",
            "montant": 145000.0,
            "mode_paiement": "Espèces",
            "compte_source": "Caisse Principale Hôtel",
            "ref_paiement": "BON-CAISSE-2601-01",
            "validation_daf": 1,
            "statut": "Validé",
            "docstatus": 1,
        }
    )

    charges_seed = [
        ("CHG-2026-00001", "2026-01-27", "Électricité & Gaz (Sonelgaz)", "607100", "Technique & Maintenance", "SONELGAZ - Direction Distribution Bologhine", 420000.0),
        ("CHG-2026-00002", "2026-01-28", "Eau (SEAAL)", "607200", "Hébergement", "SEAAL - Eau et Assainissement d'Alger", 165000.0),
        ("CHG-2026-00003", "2026-02-26", "Internet & Télécom", "626000", "Administration Générale", "Algérie Télécom Entreprises (Fibre Pro)", 95000.0),
        ("CHG-2026-00004", "2026-02-27", "Électricité & Gaz (Sonelgaz)", "607100", "Technique & Maintenance", "SONELGAZ - Direction Distribution Bologhine", 440000.0),
        ("CHG-2026-00005", "2026-03-19", "Maintenance & Réparations", "615000", "Technique & Maintenance", "Eurl Maghreb Ascenseurs & Climatisation CVC", 520000.0),
        ("CHG-2026-00006", "2026-03-26", "Électricité & Gaz (Sonelgaz)", "607100", "Technique & Maintenance", "SONELGAZ - Direction Distribution Bologhine", 390000.0),
    ]
    for cname, dchg, nat, cscf, dept, frn, ht in charges_seed:
        tva = round(ht * 0.19, 2)
        db["SE Charge et Depense"].append(
            {
                "name": cname,
                "date_charge": dchg,
                "nature": nat,
                "compte_scf": cscf,
                "departement": dept,
                "fournisseur": frn,
                "description": f"Charge d'exploitation {nat} ({dchg[:7]})",
                "montant_ht": ht,
                "taux_tva": 19.0,
                "montant_tva": tva,
                "montant_ttc": round(ht + tva, 2),
                "docstatus": 1,
            }
        )

    perf_samples = [
        ("2026-01-15", 30, 540000.0, 385000.0, 65000.0),
        ("2026-02-15", 33, 610500.0, 420000.0, 80000.0),
        ("2026-03-15", 29, 522000.0, 360000.0, 95000.0),
        ("2026-04-15", 35, 665000.0, 460000.0, 110000.0),
        ("2026-05-15", 38, 741000.0, 510000.0, 140000.0),
        ("2026-06-15", 40, 800000.0, 560000.0, 150000.0),
    ]
    for d_jour, vendues, ca_h, ca_r, autres in perf_samples:
        db["SE Performance Hoteliere"].append(
            {
                "name": f"PERF-{d_jour}",
                "date_jour": d_jour,
                "chambres_disponibles": 45,
                "chambres_vendues": vendues,
                "taux_occupation": round((vendues / 45.0) * 100.0, 2),
                "adr": round(ca_h / vendues, 2),
                "revpar": round(ca_h / 45.0, 2),
                "ca_hebergement": ca_h,
                "ca_restaurant": ca_r,
                "autres_revenus": autres,
                "ca_total_jour": round(ca_h + ca_r + autres, 2),
            }
        )

    db["SE Immobilisation"] = [
        {"name": "IMMO-2026-0001", "nom_immobilisation": "Groupe Électrogène Insonorisé 400 kVA", "categorie": "Bâtiment & Agencements (213)", "date_acquisition": "2024-06-01", "duree_amortissement": 10, "valeur_acquisition": 9800000.0, "dotation_annuelle": 980000.0, "amortissements_cumules": 2533972.60, "vnc": 7266027.40, "statut": "En service"},
        {"name": "IMMO-2026-0002", "nom_immobilisation": "Équipements Cuisine Inox & Chambres Froides", "categorie": "Équipements Cuisine & Froid (215)", "date_acquisition": "2025-01-15", "duree_amortissement": 8, "valeur_acquisition": 6500000.0, "dotation_annuelle": 812500.0, "amortissements_cumules": 1591438.36, "vnc": 4908561.64, "statut": "En service"},
        {"name": "IMMO-2026-0003", "nom_immobilisation": "Rénovation Literie King Size (42 Chambres Vue Mer)", "categorie": "Mobilier & Literie Chambres (2184)", "date_acquisition": "2025-11-01", "duree_amortissement": 5, "valeur_acquisition": 5400000.0, "dotation_annuelle": 1080000.0, "amortissements_cumules": 1257534.25, "vnc": 4142465.75, "statut": "En service"},
        {"name": "IMMO-2026-0004", "nom_immobilisation": "Serveurs Locaux & Terminaux TPE/PMS", "categorie": "Matériel Informatique & PMS (2183)", "date_acquisition": "2026-01-05", "duree_amortissement": 3, "valeur_acquisition": 1450000.0, "dotation_annuelle": 483333.33, "amortissements_cumules": 476712.33, "vnc": 973287.67, "statut": "En service"},
    ]

    db["SE Emprunt et Dette"] = [
        {"name": "EMP-BNC-2026-001", "organisme": "CPA Direction Grandes Entreprises Alger", "type_emprunt": "Crédit d'Investissement Hôtelier Bonifié", "taux_interet_annuel": 3.5, "prochaine_echeance": "2026-11-30", "statut": "En cours", "capital_initial": 45000000.0, "mensualite": 825000.0, "capital_rembourse": 11250000.0, "interets_payes": 1840000.0, "solde_restant": 33750000.0}
    ]

    db["SE Contrat et Abonnement"] = [
        {"name": "CTR-2026-0001", "fournisseur": "Eurl Maghreb Ascenseurs & Climatisation CVC", "type_contrat": "Maintenance Ascenseurs", "date_debut": "2026-01-01", "date_fin": "2026-12-31", "statut": "Actif", "montant_echeance": 95000.0, "frequence": "Mensuelle", "prochaine_echeance": "2026-11-15"},
        {"name": "CTR-2026-0002", "fournisseur": "Algérie Télécom Entreprises (Fibre Pro)", "type_contrat": "Internet Fibre Dédiée", "date_debut": "2026-01-01", "date_fin": "2026-11-20", "statut": "À renouveler (< 30j)", "montant_echeance": 95000.0, "frequence": "Mensuelle", "prochaine_echeance": "2026-11-20"},
    ]

    recompute_all_links(db)

    # Caisse mensuelle & Rapprochement & G50 basés sur les totaux calculés
    enc_caisse_jan = sum(x["montant"] for x in db["SE Encaissement"] if x["compte_destination"] == "Caisse Principale Hôtel" and x["date_encaissement"].startswith("2026-01"))
    dec_caisse_jan = sum(x["montant"] for x in db["SE Decaissement"] if x["compte_source"] == "Caisse Principale Hôtel" and x["date_decaissement"].startswith("2026-01"))
    theo_jan = round(850000.0 + enc_caisse_jan - dec_caisse_jan, 2)
    db["SE Caisse Mensuelle"] = [
        {
            "name": "CAISSE-2026-01-Caisse Principale Hôtel",
            "mois": "2026-01",
            "compte_caisse": "Caisse Principale Hôtel",
            "solde_initial": 850000.0,
            "total_encaissements": enc_caisse_jan,
            "total_decaissements": dec_caisse_jan,
            "solde_theorique": theo_jan,
            "solde_physique": theo_jan,
            "ecart": 0.0,
            "justification": "Inventaire contradictoire conforme au centime près.",
            "statut_validation": "Validée",
            "valide_par": "Administrator (DAF)",
            "date_validation": "2026-01-31 18:30:00",
            "docstatus": 1,
        }
    ]

    for mois_g50, dt_pay in (("2026-01", "2026-02-18"), ("2026-02", ""), ("2026-03", "")):
        ca_ht = sum(x["montant_ht"] for x in db["SE Facture Client"] if x["date_facture"].startswith(mois_g50))
        tva_col = sum(x["montant_tva"] for x in db["SE Facture Client"] if x["date_facture"].startswith(mois_g50))
        timbre_col = sum(x.get("droit_timbre", 0) for x in db["SE Facture Client"] if x["date_facture"].startswith(mois_g50))
        ts_col = sum(x.get("taxe_sejour", 0) for x in db["SE Facture Client"] if x["date_facture"].startswith(mois_g50))
        tva_ach = sum(x["montant_tva"] for x in db["SE Facture Fournisseur"] if x["date_facture"].startswith(mois_g50))
        tva_chg = sum(x["montant_tva"] for x in db["SE Charge et Depense"] if x["date_charge"].startswith(mois_g50))
        tva_ded = round(tva_ach + tva_chg, 2)
        tva_pay = round(max(0.0, tva_col - tva_ded), 2)
        cred = round(max(0.0, tva_ded - tva_col), 2)
        tot_g50 = round(tva_pay + timbre_col + ts_col, 2)
        m_num = int(mois_g50.split("-")[1])
        db["SE Declaration TVA"].append(
            {
                "name": f"G50-TVA-{mois_g50}",
                "mois": mois_g50,
                "date_limite_g50": f"2026-{m_num+1:02d}-20",
                "precompte_anterieur": 0.0,
                "ca_ht": round(ca_ht, 2),
                "tva_collectee": round(tva_col, 2),
                "tva_deductible_achats": round(tva_ach, 2),
                "tva_deductible_charges": round(tva_chg, 2),
                "tva_deductible": tva_ded,
                "tva_a_payer": tva_pay,
                "credit_tva": cred,
                "droits_timbre_collectes": round(timbre_col, 2),
                "taxe_sejour_collectee": round(ts_col, 2),
                "total_g50_a_payer": tot_g50,
                "date_paiement": dt_pay,
                "solde_fiscal": 0.0 if dt_pay else tot_g50,
                "statut": "Payée" if dt_pay else "Déclarée (G50)",
                "docstatus": 1,
            }
        )

    db["SE Rapprochement Bancaire"] = [
        {
            "name": "RAPP-2026-01-BNA Agence Bologhine - DZD",
            "mois": "2026-01",
            "compte_bancaire": "BNA Agence Bologhine - DZD",
            "solde_comptable": 17540800.0,
            "solde_releve_bancaire": 17660800.0,
            "total_a_ajouter": 0.0,
            "total_a_deduire": 120000.0,
            "solde_releve_corrige": 17540800.0,
            "ecart_final": 0.0,
            "statut": "Validé",
            "docstatus": 1,
        }
    ]

    recompute_all_links(db)
    rh_module.seed_rh(db)
    return db


def recompute_all_links(db: dict) -> None:
    """Exécute tous les recalculs automatiques (Factures, Comptes Trésorerie, Opérations Bancaires, Budget 2026, Prévisions)."""
    today_str = "2026-11-03"

    cfg = (db.get("SE Parametres Hotel") or [DEFAULT_SETTINGS])[0]

    # 1. Factures Clients (Calcul complet lignes & séjours)
    for fac in db.get("SE Facture Client", []):
        compute_invoice_dict(fac, cfg)
        ttc = float(fac.get("montant_ttc") or 0)
        enc_sum = round(
            sum(
                float(e.get("montant") or 0)
                for e in db.get("SE Encaissement", [])
                if e.get("facture_liee") == fac["name"] and e.get("statut") != "Annulé"
            ),
            2,
        )
        reste = round(max(0.0, ttc - enc_sum), 2)
        fac["montant_encaisse"] = enc_sum
        fac["reste_a_encaisser"] = reste
        ech = fac.get("date_echeance") or today_str
        if reste <= 0.01:
            fac["statut"] = "Payée"
            fac["jours_retard"] = 0
        elif ech < today_str:
            fac["statut"] = "Échue"
            from datetime import date
            d1 = date.fromisoformat(today_str)
            d2 = date.fromisoformat(ech)
            fac["jours_retard"] = max(0, (d1 - d2).days)
        elif enc_sum > 0:
            fac["statut"] = "Partielle"
            fac["jours_retard"] = 0
        else:
            fac["statut"] = "Validée"
            fac["jours_retard"] = 0

    # 1bis. Factures Pro Forma
    for pro in db.get("SE Facture Pro Forma", []):
        compute_invoice_dict(pro, cfg)
        if not pro.get("statut") or pro.get("statut") not in ("Validée", "Non validée"):
            pro["statut"] = "Non validée"

    # 2. Factures Fournisseurs
    for ff in db["SE Facture Fournisseur"]:
        ht = float(ff.get("montant_ht") or 0)
        tva_r = float(ff.get("taux_tva") or 19)
        tva = round(ht * tva_r / 100.0, 2)
        ttc = round(ht + tva, 2)
        ff["montant_tva"] = tva
        ff["montant_ttc"] = ttc
        pay_sum = round(
            sum(
                float(d.get("montant") or 0)
                for d in db["SE Decaissement"]
                if d.get("facture_liee") == ff["name"] and d.get("statut") != "Annulé"
            ),
            2,
        )
        reste = round(max(0.0, ttc - pay_sum), 2)
        ff["montant_paye"] = pay_sum
        ff["reste_a_payer"] = reste
        ech = ff.get("date_echeance") or today_str
        if reste <= 0.01:
            ff["statut"] = "Payée"
        elif ech < today_str:
            ff["statut"] = "Échue"
        elif pay_sum > 0:
            ff["statut"] = "Partielle"
        else:
            ff["statut"] = "Validée"

    # 3. Comptes de Trésorerie & Opérations Bancaires
    db["SE Operation Bancaire"] = []
    op_idx = 1
    for cpte in db["SE Compte Tresorerie"]:
        cname = cpte["nom_compte"]
        init = float(cpte.get("solde_initial") or 0)
        enc_c = sum(float(e.get("montant") or 0) for e in db["SE Encaissement"] if e.get("compte_destination") == cname)
        dec_c = sum(float(d.get("montant") or 0) for d in db["SE Decaissement"] if d.get("compte_source") == cname)
        cpte["solde_actuel"] = round(init + enc_c - dec_c, 2)

        if cpte.get("type_compte") == "Banque":
            running = init
            for e in db["SE Encaissement"]:
                if e.get("compte_destination") == cname:
                    running = round(running + float(e["montant"]), 2)
                    db["SE Operation Bancaire"].append(
                        {
                            "name": f"OPB-2026-{op_idx:05d}",
                            "compte_bancaire": cname,
                            "banque": cpte.get("banque", ""),
                            "date_operation": e["date_encaissement"],
                            "libelle": f"Encaissement {e['name']} - {e['client']}",
                            "type_operation": "Virement Reçu" if e["mode_paiement"] == "Virement" else "Remise Chèque",
                            "debit": 0.0,
                            "credit": float(e["montant"]),
                            "solde_progressif": running,
                            "statut_pointage": "Pointé" if e["date_encaissement"].startswith("2026-01") else "Non pointé",
                        }
                    )
                    op_idx += 1
            for d in db["SE Decaissement"]:
                if d.get("compte_source") == cname:
                    running = round(running - float(d["montant"]), 2)
                    db["SE Operation Bancaire"].append(
                        {
                            "name": f"OPB-2026-{op_idx:05d}",
                            "compte_bancaire": cname,
                            "banque": cpte.get("banque", ""),
                            "date_operation": d["date_decaissement"],
                            "libelle": f"Décaissement {d['name']} - {d['beneficiaire']}",
                            "type_operation": "Virement Émis" if d["mode_paiement"] == "Virement" else "Chèque Débité",
                            "debit": float(d["montant"]),
                            "credit": 0.0,
                            "solde_progressif": running,
                            "statut_pointage": "Pointé" if d["date_decaissement"].startswith("2026-01") else "Non pointé",
                        }
                    )
                    op_idx += 1

    # 4. Budget Annuel 2026 (SOMME.SI.ENS automatique)
    for b in db["SE Budget Annuel"]:
        mois = b["mois"]
        cat = b["categorie"]
        if cat == "CA Hébergement":
            real = sum(float(x["montant_ht"]) for x in db["SE Facture Client"] if x["date_facture"].startswith(mois) and x["nature_prestation"] == "Hébergement")
        elif cat == "CA Restauration":
            real = sum(float(x["montant_ht"]) for x in db["SE Facture Client"] if x["date_facture"].startswith(mois) and x["nature_prestation"] in ("Restauration", "Séminaires & Banquets"))
        elif cat == "Salaires":
            real = sum(float(x["salaire_brut"]) for x in db["SE Fiche de Paie Mensuelle"] if x["mois"] == mois)
        elif cat == "Achats":
            real = sum(float(x["montant_ht"]) for x in db["SE Facture Fournisseur"] if x["date_facture"].startswith(mois))
        elif cat == "Charges":
            real = sum(float(x["montant_ht"]) for x in db["SE Charge et Depense"] if x["date_charge"].startswith(mois))
        else:
            real = 0.0

        prevu = float(b.get("budget_prevu") or 0)
        real = round(real, 2)
        ecart = round(real - prevu, 2)
        pct = round((ecart / prevu) * 100.0, 2) if prevu else 0.0
        b["realise"] = real
        b["ecart_dzd"] = ecart
        b["ecart_pct"] = pct
        if "CA" in cat:
            b["statut_budget"] = "Objectif Atteint" if (real >= prevu and real > 0) else ("Sous-Performance" if (real > 0 and pct < -5) else "Conforme")
        else:
            b["statut_budget"] = "Dépassement" if (real > prevu and prevu > 0) else "Conforme"

    # 5. Prévision de Trésorerie
    solde_caisses = round(sum(x["solde_actuel"] for x in db["SE Compte Tresorerie"] if x["type_compte"] == "Caisse"), 2)
    solde_banques = round(sum(x["solde_actuel"] for x in db["SE Compte Tresorerie"] if x["type_compte"] == "Banque"), 2)
    tot_treso = round(solde_caisses + solde_banques, 2)
    creances = round(sum(x["reste_a_encaisser"] for x in db["SE Facture Client"] if x["reste_a_encaisser"] > 0), 2)
    dettes = round(sum(x["reste_a_payer"] for x in db["SE Facture Fournisseur"] if x["reste_a_payer"] > 0), 2)
    tva_due = round(sum(x["solde_fiscal"] for x in db["SE Declaration TVA"] if x.get("solde_fiscal", 0) > 0), 2)
    dec_30 = round(dettes + tva_due + 825000.0 + 190000.0, 2)
    db["SE Prevision Tresorerie"] = [
        {
            "name": "PREV-TRESO-2026-11-03",
            "date_prevision": "2026-11-03",
            "seuil_alerte_minimum": 2500000.0,
            "solde_caisses": solde_caisses,
            "solde_banques": solde_banques,
            "solde_actuel_total": tot_treso,
            "encaissements_prevus_7j": round(creances * 0.35, 2),
            "encaissements_prevus_30j": round(creances * 0.75, 2),
            "encaissements_prevus_90j": creances,
            "decaissements_prevus_7j": round(dettes * 0.5, 2),
            "decaissements_prevus_30j": dec_30,
            "decaissements_prevus_90j": round(dec_30 + 1650000.0, 2),
            "tresorerie_nette_30j": round(tot_treso + creances * 0.75 - dec_30, 2),
            "tresorerie_nette_90j": round(tot_treso + creances - (dec_30 + 1650000.0), 2),
            "niveau_risque": "Sain",
        }
    ]


def get_db() -> dict:
    if DB_FILE.exists():
        try:
            db = json.loads(DB_FILE.read_text(encoding="utf-8"))
            rh_module.seed_rh(db)
            return db
        except Exception:
            pass
    db = build_initial_seed_db()
    save_db(db)
    return db


def save_db(db: dict) -> None:
    recompute_all_links(db)
    DB_FILE.write_text(json.dumps(db, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def compute_dashboard_payload(db: dict) -> dict:
    ca_total = round(sum(float(x["montant_ht"]) for x in db["SE Facture Client"]), 2)
    ca_heb = round(sum(float(x["montant_ht"]) for x in db["SE Facture Client"] if x["nature_prestation"] == "Hébergement"), 2)
    ca_rest = round(sum(float(x["montant_ht"]) for x in db["SE Facture Client"] if x["nature_prestation"] in ("Restauration", "Séminaires & Banquets")), 2)
    enc_tot = round(sum(float(x["montant"]) for x in db["SE Encaissement"]), 2)
    dec_tot = round(sum(float(x["montant"]) for x in db["SE Decaissement"]), 2)
    creances = round(sum(float(x["reste_a_encaisser"]) for x in db["SE Facture Client"]), 2)
    dettes = round(sum(float(x["reste_a_payer"]) for x in db["SE Facture Fournisseur"]), 2)
    treso = round(sum(float(x["solde_actuel"]) for x in db["SE Compte Tresorerie"]), 2)
    tva_due = round(sum(float(x.get("solde_fiscal") or 0) for x in db["SE Declaration TVA"]), 2)

    achats_tot = sum(float(x["montant_ht"]) for x in db["SE Facture Fournisseur"])
    charges_tot = sum(float(x["montant_ht"]) for x in db["SE Charge et Depense"])
    salaires_tot = sum(float(x["salaire_brut"]) for x in db["SE Fiche de Paie Mensuelle"])
    resultat_cumul = round(ca_total - achats_tot - charges_tot - salaires_tot, 2)

    # Alertes Contrôle de Gestion
    alerts = []
    for fac in db["SE Facture Client"]:
        if fac.get("statut") == "Échue":
            alerts.append(
                {
                    "level": "red",
                    "title": f"Facture Échue : {fac['name']} ({fac['client']})",
                    "detail": f"Reste à encaisser : {fac['reste_a_encaisser']:,.2f} DZD — Retard : +{fac['jours_retard']} jours",
                    "doctype": "SE Facture Client",
                    "docname": fac["name"],
                }
            )
    for enc in db["SE Encaissement"]:
        if enc.get("mode_paiement") == "Chèque" and enc.get("statut_cheque") == "En portefeuille (Non encaissé)":
            alerts.append(
                {
                    "level": "orange",
                    "title": f"Chèque non encaissé : {enc.get('ref_paiement') or enc['name']}",
                    "detail": f"{enc['client']} — {enc['montant']:,.2f} DZD en portefeuille (> 7 jours)",
                    "doctype": "SE Encaissement",
                    "docname": enc["name"],
                }
            )
    for b in db["SE Budget Annuel"]:
        if b.get("statut_budget") == "Dépassement":
            alerts.append(
                {
                    "level": "red",
                    "title": f"Dépassement Budget : {b['categorie']} ({b['mois']})",
                    "detail": f"Réalisé {b['realise']:,.2f} DZD vs Prévu {b['budget_prevu']:,.2f} DZD (+{b['ecart_pct']}%)",
                    "doctype": "SE Budget Annuel",
                    "docname": b["name"],
                }
            )

    # Séries Graphiques T1-T2 2026
    mois_list = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"]
    ca_mensuel = []
    chg_mensuel = []
    for m in mois_list:
        ca_m = sum(float(x["montant_ht"]) for x in db["SE Facture Client"] if x["date_facture"].startswith(m))
        ac_m = sum(float(x["montant_ht"]) for x in db["SE Facture Fournisseur"] if x["date_facture"].startswith(m))
        ch_m = sum(float(x["montant_ht"]) for x in db["SE Charge et Depense"] if x["date_charge"].startswith(m))
        sa_m = sum(float(x["salaire_brut"]) for x in db["SE Fiche de Paie Mensuelle"] if x["mois"] == m)
        ca_mensuel.append(round(ca_m, 2))
        chg_mensuel.append(round(ac_m + ch_m + sa_m, 2))

    cats = ["CA Hébergement", "CA Restauration", "Salaires", "Achats", "Charges"]
    bud_prevu_t1 = [round(sum(x["budget_prevu"] for x in db["SE Budget Annuel"] if x["categorie"] == c and x["mois"] <= "2026-03"), 2) for c in cats]
    bud_real_t1 = [round(sum(x["realise"] for x in db["SE Budget Annuel"] if x["categorie"] == c and x["mois"] <= "2026-03"), 2) for c in cats]

    return {
        "kpis": [
            {"label": "CA Total HT (DZD)", "value": ca_total, "color": "#16a34a", "doctype": "SE Facture Client"},
            {"label": "CA Hébergement HT", "value": ca_heb, "color": "#2563eb", "doctype": "SE Facture Client"},
            {"label": "CA Restauration & Banquets", "value": ca_rest, "color": "#0891b2", "doctype": "SE Facture Client"},
            {"label": "Encaissements Validés", "value": enc_tot, "color": "#15803d", "doctype": "SE Encaissement"},
            {"label": "Décaissements Validés", "value": dec_tot, "color": "#ea580c", "doctype": "SE Decaissement"},
            {"label": "Créances Clients", "value": creances, "color": "#dc2626", "doctype": "SE Facture Client"},
            {"label": "Dettes Fournisseurs", "value": dettes, "color": "#d97706", "doctype": "SE Facture Fournisseur"},
            {"label": "Trésorerie Disponible", "value": treso, "color": "#0d9488", "doctype": "SE Compte Tresorerie"},
            {"label": "Solde G50 à Payer (DZD)", "value": tva_due, "color": "#7c3aed", "doctype": "SE Declaration TVA"},
            {"label": "Résultat Exploitation SCF", "value": resultat_cumul, "color": "#1d4ed8", "doctype": "SE Budget Annuel"},
        ],
        "alerts": alerts,
        "charts": {
            "ca_charges": {"labels": ["Jan 26", "Fév 26", "Mar 26", "Avr 26", "Mai 26", "Juin 26"], "ca": ca_mensuel, "charges": chg_mensuel},
            "budget_t1": {"labels": cats, "prevu": bud_prevu_t1, "realise": bud_real_t1},
            "occupation": {
                "labels": [x["date_jour"][:7] for x in db["SE Performance Hoteliere"]],
                "taux": [x["taux_occupation"] for x in db["SE Performance Hoteliere"]],
                "revpar": [x["revpar"] for x in db["SE Performance Hoteliere"]],
            },
        },
    }


HTML_INDEX = r"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Saint Eugène ERP 2026 — Direction Financière & Contrôle de Gestion (4★ Alger)</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
<script src="/rh_module.js"></script>
<style>
  :root {
    --bg: #f1f5f9;
    --card: #ffffff;
    --navy: #0f172a;
    --navy-light: #1e293b;
    --gold: #d97706;
    --text: #1e293b;
    --muted: #64748b;
    --border: #e2e8f0;
    --green: #16a34a;
    --orange: #ea580c;
    --red: #dc2626;
  }
  * { box-sizing: border-box; }
  body { margin: 0; font-family: 'Inter', 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); display: flex; height: 100vh; overflow: hidden; }
  /* Sidebar Frappe Desk */
  .sidebar { width: 270px; background: var(--navy); color: #f8fafc; display: flex; flex-direction: column; border-right: 1px solid #334155; flex-shrink: 0; }
  .brand { padding: 18px 20px; border-bottom: 1px solid #1e293b; }
  .brand h1 { margin: 0; font-size: 16px; font-weight: 700; letter-spacing: 0.3px; display: flex; align-items: center; gap: 8px; }
  .brand .stars { color: #fbbf24; font-size: 13px; }
  .brand small { color: #94a3b8; font-size: 11.5px; display: block; margin-top: 3px; }
  .nav-scroll { flex: 1; overflow-y: auto; padding: 10px 12px; }
  .nav-group { font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.8px; color: #94a3b8; margin: 14px 8px 6px; font-weight: 600; }
  .nav-btn { width: 100%; text-align: left; background: transparent; border: none; color: #cbd5e1; padding: 8px 11px; border-radius: 6px; font-size: 13px; cursor: pointer; display: flex; align-items: center; justify-content: space-between; transition: 0.15s; }
  .nav-btn:hover { background: rgba(255,255,255,0.07); color: #fff; }
  .nav-btn.active { background: #b45309; color: #fff; font-weight: 600; }
  /* Main Area */
  .main { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
  .topbar { height: 58px; background: #fff; border-bottom: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; padding: 0 24px; flex-shrink: 0; }
  .topbar-title { font-size: 16px; font-weight: 700; color: var(--navy); display: flex; align-items: center; gap: 10px; }
  .badge-scf { background: #fef3c7; color: #92400e; border: 1px solid #fcd34d; font-size: 11px; padding: 3px 8px; border-radius: 999px; font-weight: 600; }
  .topbar-actions { display: flex; align-items: center; gap: 10px; }
  .btn { padding: 7px 14px; border-radius: 6px; font-size: 12.5px; font-weight: 600; cursor: pointer; border: 1px solid var(--border); background: #fff; color: var(--text); transition: 0.15s; }
  .btn:hover { background: #f8fafc; }
  .btn-primary { background: var(--navy); color: #fff; border-color: var(--navy); }
  .btn-primary:hover { background: #1e293b; }
  .btn-gold { background: #b45309; color: #fff; border-color: #b45309; }
  .btn-gold:hover { background: #92400e; }
  .content { flex: 1; overflow-y: auto; padding: 22px 26px; }
  /* KPI Grid */
  .kpi-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-bottom: 22px; }
  .kpi-card { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; cursor: pointer; transition: transform 0.12s, box-shadow 0.12s; border-top: 4px solid #2563eb; }
  .kpi-card:hover { transform: translateY(-2px); box-shadow: 0 6px 16px rgba(15,23,42,0.07); }
  .kpi-label { font-size: 11.5px; color: var(--muted); font-weight: 600; text-transform: uppercase; margin-bottom: 6px; }
  .kpi-val { font-size: 17.5px; font-weight: 800; color: var(--navy); }
  /* Alerts Banner */
  .alerts-panel { background: #fff; border: 1px solid var(--border); border-radius: 10px; padding: 14px 18px; margin-bottom: 22px; }
  .alerts-panel h3 { margin: 0 0 10px 0; font-size: 13.5px; color: var(--navy); display: flex; align-items: center; gap: 8px; }
  .alert-item { display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; border-radius: 6px; margin-bottom: 6px; font-size: 12.5px; cursor: pointer; }
  .alert-item.red { background: #fef2f2; border-left: 4px solid var(--red); color: #991b1b; }
  .alert-item.orange { background: #fff7ed; border-left: 4px solid var(--orange); color: #9a3412; }
  /* Charts */
  .chart-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 18px; margin-bottom: 24px; }
  .chart-box { background: #fff; border: 1px solid var(--border); border-radius: 10px; padding: 16px; }
  .chart-box h4 { margin: 0 0 12px 0; font-size: 13.5px; color: var(--navy); }
  /* Table ListView */
  .table-card { background: #fff; border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
  .table-toolbar { padding: 14px 18px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; gap: 12px; }
  .search-input { padding: 7px 12px; border: 1px solid var(--border); border-radius: 6px; font-size: 13px; width: 280px; }
  table.frappe-list { width: 100%; border-collapse: collapse; font-size: 12.8px; }
  table.frappe-list th { background: #f8fafc; color: #475569; text-align: left; padding: 10px 14px; font-size: 11.5px; text-transform: uppercase; border-bottom: 1px solid var(--border); }
  table.frappe-list td { padding: 10px 14px; border-bottom: 1px solid #f1f5f9; }
  table.frappe-list tr:hover td { background: #f8fafc; cursor: pointer; }
  .pill { display: inline-block; padding: 3px 9px; border-radius: 999px; font-size: 11px; font-weight: 700; }
  .pill.green { background: #dcfce7; color: #166534; }
  .pill.orange { background: #ffedd5; color: #9a3412; }
  .pill.red { background: #fee2e2; color: #991b1b; }
  .pill.gray { background: #f1f5f9; color: #475569; }
  /* Modal Form & Print */
  .modal-backdrop { position: fixed; inset: 0; background: rgba(15,23,42,0.55); display: none; align-items: center; justify-content: center; z-index: 100; padding: 20px; }
  .modal-backdrop.open { display: flex; }
  .modal { background: #fff; border-radius: 12px; width: 100%; max-width: 1060px; max-height: 90vh; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.25); }
  .modal-hdr { padding: 16px 22px; background: var(--navy); color: #fff; display: flex; justify-content: space-between; align-items: center; }
  .modal-hdr h3 { margin: 0; font-size: 15px; }
  .modal-body { padding: 20px 24px; overflow-y: auto; flex: 1; }
  .form-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
  .form-group { display: flex; flex-direction: column; gap: 4px; }
  .form-group.full { grid-column: span 2; }
  .form-group label { font-size: 11.5px; font-weight: 600; color: #475569; }
  .form-group input, .form-group select, .form-group textarea { padding: 8px 10px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 13px; }
  .form-group input[readonly], .form-group textarea[readonly] { background: #f1f5f9; color: #334155; font-weight: 600; }
  .modal-ftr { padding: 12px 22px; border-top: 1px solid var(--border); background: #f8fafc; display: flex; justify-content: space-between; align-items: center; }
</style>
</head>
<body>

<aside class="sidebar">
  <div class="brand">
    <h1>HÔTEL SAINT EUGÈNE <span class="stars">★★★★</span></h1>
    <small>Mini-ERP Frappe • Exercice 2026 (DZD / SCF)</small>
  </div>
  <div class="nav-scroll" id="sidebarNav"></div>
</aside>

<section class="main">
  <header class="topbar">
    <div class="topbar-title">
      <span id="viewTitle">Direction Saint Eugène 2026</span>
      <span class="badge-scf">Normes SCF Algérie • DZD</span>
    </div>
    <div class="topbar-actions">
      <button class="btn" onclick="showWorkspace()">Tableau de Bord 2026</button>
      <button class="btn btn-gold" onclick="openNewDoc('SE Facture Client')">+ Nouvelle Facture Client</button>
      <button class="btn" style="border-color:#38bdf8;background:#0284c7;color:#fff;" onclick="openNewDoc('SE Facture Pro Forma')">+ Nouvelle Pro Forma</button>
      <button class="btn btn-primary" onclick="openNewDoc('SE Encaissement')">+ Nouvel Encaissement</button>
    </div>
  </header>

  <div class="content" id="mainContent"></div>
</section>

<div class="modal-backdrop" id="deleteConfirmModal" style="z-index:9999;">
  <div class="modal" style="max-width:480px;text-align:left;border-top:4px solid #dc2626;">
    <div class="modal-hdr" style="background:#0f172a;">
      <h3 style="color:#f87171;display:flex;align-items:center;gap:8px;">⚠️ Confirmation de Suppression</h3>
      <button class="btn" style="padding:3px 9px;" onclick="closeDeleteConfirmModal()">✕</button>
    </div>
    <div class="modal-body" style="padding:18px 20px;">
      <p style="font-size:13.5px;color:#1e293b;line-height:1.5;margin:0 0 14px 0;font-weight:600;">
        Êtes-vous sûr de vouloir supprimer cet élément ? Cette action peut être irréversible.
      </p>
      <div id="deleteDocDetails" style="font-size:12px;background:#f8fafc;border:1px solid #e2e8f0;padding:10px 12px;border-radius:6px;margin-bottom:12px;color:#475569;"></div>
      <div id="deleteWarningBlock" style="display:none;background:#fef2f2;border:1px solid #fecaca;color:#991b1b;padding:10px 12px;border-radius:6px;font-size:12px;line-height:1.45;margin-bottom:8px;"></div>
    </div>
    <div class="modal-ftr" style="display:flex;justify-content:flex-end;gap:10px;padding:12px 20px;background:#f8fafc;">
      <button type="button" class="btn" style="padding:6px 14px;" onclick="closeDeleteConfirmModal()">Annuler</button>
      <button type="button" id="btnConfirmDelete" class="btn" style="background:#dc2626;color:#fff;border:none;font-weight:700;padding:6px 18px;" onclick="executeDeleteDoc()">Supprimer</button>
    </div>
  </div>
</div>

<div class="modal-backdrop" id="docModal">
  <div class="modal">
    <div class="modal-hdr">
      <h3 id="modalTitle">Document</h3>
      <button class="btn" style="padding:3px 9px;" onclick="closeModal()">✕</button>
    </div>
    <div class="modal-body" id="modalBody"></div>
    <div class="modal-ftr" id="modalFooter"></div>
  </div>
</div>

<script>
var APP_STATE = { schemas: {}, db: {}, dashboard: {} };
window.APP_STATE = APP_STATE;
let CURRENT_DOCTYPE = null;
let CURRENT_DOC = null;

const NAV_GROUPS = [
  {
    title: "Pilotage Direction",
    items: [
      { label: "📊 Direction Saint Eugène 2026", action: "workspace" },
      { label: "⚙️ Paramètres Hôtel & Fiscalité 4★", doctype: "SE Parametres Hotel" }
    ]
  },
  {
    title: "Facturation & Exploitation",
    items: [
      { label: "🧾 Factures Clients (SCF 70)", doctype: "SE Facture Client" },
      { label: "📋 Factures Pro Forma", doctype: "SE Facture Pro Forma" },
      { label: "🏨 Performance Hôtelière (45 ch.)", doctype: "SE Performance Hoteliere" },
      { label: "📥 Factures Fournisseurs (SCF 60)", doctype: "SE Facture Fournisseur" },
      { label: "⚡ Charges & Dépenses (61/62)", doctype: "SE Charge et Depense" },
      { label: "🏢 Clients (Corporate / Agences)", doctype: "SE Client" },
      { label: "🚚 Fournisseurs", doctype: "SE Fournisseur" }
    ]
  },
  {
    title: "Trésorerie, Caisses & Banques",
    items: [
      { label: "💰 Encaissements Clients", doctype: "SE Encaissement" },
      { label: "💸 Décaissements", doctype: "SE Decaissement" },
      { label: "🔐 Caisse Mensuelle (PV + Workflow)", doctype: "SE Caisse Mensuelle" },
      { label: "🏦 Opérations Bancaires (512)", doctype: "SE Operation Bancaire" },
      { label: "⚖️ Rapprochement Bancaire", doctype: "SE Rapprochement Bancaire" },
      { label: "📈 Prévisions Trésorerie (7/30/90j)", doctype: "SE Prevision Tresorerie" },
      { label: "💳 Comptes Caisses & Banques", doctype: "SE Compte Tresorerie" }
    ]
  },
  {
    title: "👥 Ressources Humaines & Paie",
    items: [
      { label: "📊 Tableau de Bord RH", action: "rh_dashboard" },
      { label: "🪪 Collaborateurs Hôtel", action: "rh_employees" },
      { label: "⚡ Centre de Paie & Bulletins", action: "rh_payroll" },
      { label: "🏛️ Déclarations CNAS & Congés", action: "rh_cnas" }
    ]
  },
  {
    title: "Fiscalité G50 & Patrimoine",
    items: [
      { label: "🏛️ Déclarations TVA (G50)", doctype: "SE Declaration TVA" },
      { label: "🎯 Budget Annuel 2026", doctype: "SE Budget Annuel" },
      { label: "🏗️ Immobilisations & VNC (Cl. 2)", doctype: "SE Immobilisation" },
      { label: "🏦 Emprunts & Dettes (Cl. 16)", doctype: "SE Emprunt et Dette" },
      { label: "📑 Contrats & Abonnements", doctype: "SE Contrat et Abonnement" }
    ]
  }
];

function fmtDZD(val) {
  const n = Number(val || 0);
  return n.toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " DZD";
}

function pillClass(st) {
  if (!st) return "gray";
  const green = ["Payée", "Validée", "Validé", "Pointé", "Équilibré", "Conforme", "Objectif Atteint", "Sain", "Actif", "En service", "Crédit Reporté"];
  const orange = ["Partielle", "Non pointé", "Sous-Performance", "Sous Tension", "En attente signature DAF", "À renouveler (< 30j)", "Déclarée (G50)", "Non validée"];
  const red = ["Impayée", "Échue", "Dépassement", "Critique", "Avec Écart", "Rejetée", "Expiré", "En retard", "Annulée", "Annulé"];
  if (green.includes(st)) return "green";
  if (orange.includes(st)) return "orange";
  if (red.includes(st)) return "red";
  return "gray";
}

async function loadState() {
  const res = await fetch("/api/state");
  APP_STATE = await res.json();
  window.APP_STATE = APP_STATE;
  renderSidebar();
}

function getNavLabel(doctype) {
  for (const g of NAV_GROUPS) {
    for (const item of g.items) {
      if (item.doctype === doctype) return item.label;
    }
  }
  return doctype;
}

function renderSidebar(activeKey = "workspace") {
  const nav = document.getElementById("sidebarNav");
  let html = "";
  NAV_GROUPS.forEach(g => {
    html += `<div class="nav-group">${g.title}</div>`;
    g.items.forEach(item => {
      const key = item.doctype || "workspace";
      let count = "";
      if (item.action === "rh_employees" && APP_STATE.db && APP_STATE.db["SE Employe"]) {
        count = APP_STATE.db["SE Employe"].length;
      } else if (item.action === "rh_payroll" && APP_STATE.db && APP_STATE.db["SE Fiche de Paie Mensuelle"]) {
        count = APP_STATE.db["SE Fiche de Paie Mensuelle"].length;
      } else if (item.doctype && APP_STATE.db && APP_STATE.db[item.doctype]) {
        count = APP_STATE.db[item.doctype].length;
      }
      const active = activeKey === key ? "active" : "";
      let fn = "showWorkspace()";
      if (item.action && item.action.startsWith("rh_")) {
        const sub = item.action.replace("rh_", "");
        fn = `window.showRhModule('${sub}')`;
      } else if (item.doctype) {
        fn = `showList('${item.doctype}')`;
      }
      html += `<button class="nav-btn ${active}" onclick="${fn}">
        <span>${item.label}</span>
        ${count !== "" ? `<span style="font-size:11px;opacity:0.75;">${count}</span>` : ""}
      </button>`;
    });
  });
  nav.innerHTML = html;
}

function showWorkspace() {
  CURRENT_DOCTYPE = null;
  renderSidebar("workspace");
  document.getElementById("viewTitle").textContent = "Direction Saint Eugène 2026 — Tableau de Bord Exécutif";
  const d = APP_STATE.dashboard;

  let kpiHtml = d.kpis.map(k => `
    <div class="kpi-card" style="border-top-color:${k.color}" onclick="showList('${k.doctype}')">
      <div class="kpi-label">${k.label}</div>
      <div class="kpi-val">${fmtDZD(k.value)}</div>
    </div>
  `).join("");

  let alertsHtml = d.alerts.map(a => `
    <div class="alert-item ${a.level}" onclick="openDoc('${a.doctype}', '${a.docname}')">
      <div><b>${a.title}</b> — ${a.detail}</div>
      <span class="pill ${a.level}">Action requise →</span>
    </div>
  `).join("");

  document.getElementById("mainContent").innerHTML = `
    <div class="alerts-panel">
      <h3>🔔 Alertes Automatiques Contrôle de Gestion (${d.alerts.length} actives)</h3>
      ${alertsHtml || '<div style="color:var(--green);font-size:13px;">Aucune alerte critique en attente.</div>'}
    </div>
    <div class="kpi-grid">${kpiHtml}</div>
    <div class="chart-grid">
      <div class="chart-box"><h4>Évolution Mensuelle du CA HT vs Charges & Salaires (DZD)</h4><canvas id="chCaCharges" height="130"></canvas></div>
      <div class="chart-box"><h4>Pilotage Budgétaire 2026 — Prévu vs Réalisé (Cumul T1 DZD)</h4><canvas id="chBudget" height="130"></canvas></div>
      <div class="chart-box"><h4>Taux d'Occupation Mensuel Moyen (%) — Capacité 45 Chambres</h4><canvas id="chOcc" height="130"></canvas></div>
      <div class="chart-box"><h4>RevPAR Mensuel Moyen (Revenu par Chambre Disponible en DZD)</h4><canvas id="chRevpar" height="130"></canvas></div>
    </div>
  `;

  new Chart(document.getElementById("chCaCharges"), {
    type: "bar",
    data: {
      labels: d.charts.ca_charges.labels,
      datasets: [
        { label: "CA HT (DZD)", data: d.charts.ca_charges.ca, backgroundColor: "#16a34a" },
        { label: "Total Charges & Salaires HT (DZD)", data: d.charts.ca_charges.charges, backgroundColor: "#dc2626" }
      ]
    }
  });

  new Chart(document.getElementById("chBudget"), {
    type: "bar",
    data: {
      labels: d.charts.budget_t1.labels,
      datasets: [
        { label: "Budget Prévu T1 (DZD)", data: d.charts.budget_t1.prevu, backgroundColor: "#94a3b8" },
        { label: "Réalisé Comptable Validé T1 (DZD)", data: d.charts.budget_t1.realise, backgroundColor: "#2563eb" }
      ]
    }
  });

  new Chart(document.getElementById("chOcc"), {
    type: "line",
    data: {
      labels: d.charts.occupation.labels,
      datasets: [{ label: "Taux d'Occupation (%)", data: d.charts.occupation.taux, borderColor: "#7c3aed", backgroundColor: "rgba(124,58,237,0.12)", fill: true, tension: 0.3 }]
    }
  });

  new Chart(document.getElementById("chRevpar"), {
    type: "line",
    data: {
      labels: d.charts.occupation.labels,
      datasets: [{ label: "RevPAR (DZD)", data: d.charts.occupation.revpar, borderColor: "#0d9488", backgroundColor: "rgba(13,148,136,0.12)", fill: true, tension: 0.3 }]
    }
  });
}

function showList(doctype, search = "") {
  if (doctype === "SE Parametres Hotel") {
    openDoc("SE Parametres Hotel", "SE Parametres Hotel");
    return;
  }
  CURRENT_DOCTYPE = doctype;
  renderSidebar(doctype);
  const schema = APP_STATE.schemas[doctype];
  const rows = APP_STATE.db[doctype] || [];
  const labelTitle = getNavLabel(doctype);
  document.getElementById("viewTitle").textContent = `${labelTitle} (${rows.length} enregistrements)`;

  const listFields = schema.fields.filter(f => f.in_list_view && !["Section Break", "Column Break", "Table"].includes(f.fieldtype)).slice(0, 6);

  const filtered = rows.filter(r => !search || JSON.stringify(r).toLowerCase().includes(search.toLowerCase()));

  let thHtml = `<th>Référence (ID)</th>` + listFields.map(f => `<th>${f.label}</th>`).join("") + `<th style="text-align:center;width:48px;">Action</th>`;
  let trHtml = filtered.map(r => {
    let tds = `<td><b>${r.name}</b></td>`;
    listFields.forEach(f => {
      let val = r[f.fieldname];
      if (f.fieldname === "client" && (doctype === "SE Facture Client" || doctype === "SE Facture Pro Forma")) {
        tds += `<td>${formatClientBadge(val, APP_STATE ? APP_STATE.db : {})}</td>`;
      } else if (f.fieldtype === "Currency") {
        tds += `<td style="text-align:right;font-variant-numeric:tabular-nums;">${fmtDZD(val)}</td>`;
      } else if (f.fieldtype === "Percent") {
        tds += `<td>${Number(val || 0).toFixed(2)} %</td>`;
      } else if (["statut", "statut_validation", "statut_pointage", "statut_budget", "niveau_risque"].includes(f.fieldname)) {
        tds += `<td><span class="pill ${pillClass(val)}">${val || "—"}</span></td>`;
      } else if (f.fieldname === "jours_retard") {
        tds += `<td>${Number(val) > 0 ? `<span class="pill red">+${val} j</span>` : `<span style="color:#94a3b8">0 j</span>`}</td>`;
      } else {
        tds += `<td>${val ?? "—"}</td>`;
      }
    });
    tds += `<td style="text-align:center;" onclick="event.stopPropagation();">
      <button type="button" class="btn" style="padding:2px 6px;color:#991b1b;background:#fee2e2;border:1px solid #fecaca;border-radius:4px;font-size:11px;cursor:pointer;" title="Supprimer cet élément" onclick="triggerDeleteDoc('${doctype}', '${r.name.replace(/'/g, "\\'")}')">🗑️</button>
    </td>`;
    return `<tr onclick="openDoc('${doctype}', '${r.name.replace(/'/g, "\\'")}')">${tds}</tr>`;
  }).join("");

  document.getElementById("mainContent").innerHTML = `
    <div class="table-card">
      <div class="table-toolbar">
        <input class="search-input" placeholder="Rechercher dans ${labelTitle}..." value="${search}" oninput="showList('${doctype}', this.value)">
        <button class="btn btn-primary" onclick="openNewDoc('${doctype}')">+ Nouveau (${labelTitle})</button>
      </div>
      <table class="frappe-list">
        <thead><tr>${thHtml}</tr></thead>
        <tbody>${trHtml || `<tr><td colspan="8" style="text-align:center;padding:24px;color:#64748b;">Aucun enregistrement</td></tr>`}</tbody>
      </table>
    </div>
  `;
}

function openDoc(doctype, name) {
  const rows = APP_STATE.db[doctype] || [];
  const doc = rows.find(r => r.name === name) || rows[0];
  if (!doc) return;
  renderDocModal(doctype, JSON.parse(JSON.stringify(doc)), false);
}

function openNewDoc(doctype) {
  const schema = APP_STATE.schemas[doctype];
  const doc = { name: `${doctype.replace(/\s+/g, "-")}-${Date.now().toString().slice(-4)}` };
  schema.fields.forEach(f => {
    if (f.default) {
      doc[f.fieldname] = f.default === "Today" ? "2026-11-03" : f.default;
    }
  });
  renderDocModal(doctype, doc, true);
}


// --- CLIENT HELPERS & MOTEUR DE FACTURATION 4★ ---
function getClientObject(clientKey, dbSrc) {
  const list = (dbSrc && dbSrc["SE Client"]) || (typeof DB !== "undefined" && DB["SE Client"]) || (typeof APP_STATE !== "undefined" && APP_STATE.db && APP_STATE.db["SE Client"]) || [];
  if (!clientKey) return null;
  return list.find(c => c.name === clientKey || c.nom_client === clientKey || c.ref_societe === clientKey) || null;
}

function formatClientDisplay(clientKey, dbSrc) {
  const cli = getClientObject(clientKey, dbSrc);
  if (!cli) return clientKey || "—";
  const nom = cli.nom_client || cli.name;
  const ref = cli.ref_societe || (cli.name && cli.name.startsWith("CLI-") ? cli.name : "");
  if (nom && ref && nom !== ref) {
    return `${nom} (${ref})`;
  }
  return nom || clientKey || "—";
}

function formatClientBadge(clientKey, dbSrc) {
  const cli = getClientObject(clientKey, dbSrc);
  if (!cli) return `<b>${clientKey || "—"}</b>`;
  const nom = cli.nom_client || cli.name;
  const ref = cli.ref_societe || (cli.name && cli.name.startsWith("CLI-") ? cli.name : "");
  if (nom && ref && nom !== ref) {
    return `<div><b style="color:#0f172a;">${nom}</b> <span style="font-size:11px;color:#0284c7;background:#e0f2fe;padding:2px 7px;border-radius:4px;font-weight:700;margin-left:4px;">${ref}</span></div>`;
  }
  return `<b style="color:#0f172a;">${nom}</b>`;
}

const ROOM_TYPES = [
  "Single Standard [SGL-STD]",
  "Single Vue Mer [SGL-MER]",
  "Double Standard [DBL-STD]",
  "Double Vue Mer [DBL-MER]",
  "Chambre Twin [TWIN]",
  "Chambre Triple [TRP]",
  "Suite Deluxe [SDL]",
  "Suite Saint Eugène [SSE]",
  "Single",
  "Double",
  "Twin",
  "Triple",
  "Suite Deluxe",
  "Suite Saint Eugène"
];
const SERVICES = ["Dîner", "Déjeuner", "Coffee Break", "Location de salle"];

function getArticleCategory(article) {
  if (ROOM_TYPES.includes(article)) return "Hébergement";
  if (article === "Location de salle") return "Séminaires & Banquets";
  return "Restauration";
}


function formatDzdInWords(montant) {
  const val = Math.abs(Number(montant) || 0);
  const dinars = Math.floor(val);
  const centimes = Math.round((val - dinars) * 100);
  const units = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf",
    "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf"];
  const tens = ["", "", "vingt", "trente", "quarante", "cinquante", "soixante", "soixante-dix", "quatre-vingts", "quatre-vingt-dix"];
  function convertUnder100(n) {
    if (n < 20) return units[n];
    const t = Math.floor(n / 10);
    const u = n % 10;
    if (t === 7) return u === 1 ? "soixante et onze" : ("soixante-" + units[10 + u]);
    if (t === 8) return u === 0 ? "quatre-vingts" : ("quatre-vingt-" + units[u]);
    if (t === 9) return "quatre-vingt-" + units[10 + u];
    if (u === 1) return tens[t] + " et un";
    return u === 0 ? tens[t] : (tens[t] + "-" + units[u]);
  }
  function convertUnder1000(n) {
    if (n === 0) return "";
    const h = Math.floor(n / 100);
    const r = n % 100;
    let res = "";
    if (h === 1) res = "cent";
    else if (h > 1) res = units[h] + " cent" + (r === 0 ? "s" : "");
    if (r > 0) res = res ? (res + " " + convertUnder100(r)) : convertUnder100(r);
    return res;
  }
  function intToFrench(n) {
    if (n === 0) return "zéro";
    let res = "";
    const milliards = Math.floor(n / 1000000000);
    let rem = n % 1000000000;
    const millions = Math.floor(rem / 1000000);
    rem = rem % 1000000;
    const mille = Math.floor(rem / 1000);
    rem = rem % 1000;
    if (milliards > 0) res += convertUnder1000(milliards) + " milliard" + (milliards > 1 ? "s" : "") + " ";
    if (millions > 0) res += convertUnder1000(millions) + " million" + (millions > 1 ? "s" : "") + " ";
    if (mille === 1) res += "mille ";
    else if (mille > 1) res += convertUnder1000(mille) + " mille ";
    if (rem > 0) res += convertUnder1000(rem);
    return res.trim();
  }
  const dinarsTxt = intToFrench(dinars);
  const capDinars = dinarsTxt.charAt(0).toUpperCase() + dinarsTxt.slice(1);
  const dev = dinars <= 1 ? "Dinar Algérien" : "Dinars Algériens";
  let phrase = capDinars + " " + dev;
  if (centimes > 0) phrase += " et " + intToFrench(centimes) + " " + (centimes === 1 ? "Centime" : "Centimes");
  return phrase;
}

function computeInvoiceDocClient(doc, cfg) {
  cfg = cfg || {};
  const tarifTs = Number(cfg.taxe_sejour_nuitee_adulte || 500);
  const incluse = doc.taxe_sejour_incluse !== undefined ? Number(doc.taxe_sejour_incluse) : 1;
  const appliquerTs = doc.appliquer_taxe_sejour !== undefined ? Number(doc.appliquer_taxe_sejour) : 1;

  if (!doc.sejours || !doc.sejours.length) {
    doc.sejours = [{
      sejour_no: 1,
      description: "Séjour Principal",
      date_arrivee: doc.date_arrivee || "2026-11-04",
      date_depart: doc.date_depart || "2026-11-07",
      nuitees: 3,
      nb_personnes: 1,
      taxe_sejour: 0,
      total_ttc_sejour: 0
    }];
  }

  // 1. Calcul des séjours : nuitees, nb_personnes, taxe_sejour calculée séparément par séjour
  let totTs = 0;
  let totNuitees = 0;
  let totAdultes = 0;

  doc.sejours.forEach((s, idx) => {
    s.sejour_no = s.sejour_no || (idx + 1);
    if (s.date_arrivee && s.date_depart) {
      const d1 = new Date(s.date_arrivee);
      const d2 = new Date(s.date_depart);
      const diff = Math.round((d2 - d1) / (1000 * 3600 * 24));
      s.nuitees = diff > 0 ? diff : 1;
    } else {
      s.nuitees = Math.max(1, parseInt(s.nuitees || 1, 10));
    }
    s.nb_personnes = Math.max(1, parseInt(s.nb_personnes || 1, 10));

    // Formule exigée : Nombre de personnes × Nombre de nuitées × Tarif (500 DZD)
    const tsSej = appliquerTs ? Math.round(s.nb_personnes * s.nuitees * tarifTs * 100) / 100 : 0;
    s.taxe_sejour = tsSej;
    s.total_ttc_sejour = 0;

    totTs += tsSej;
    totNuitees += s.nuitees;
    totAdultes += s.nb_personnes;
  });

  totTs = Math.round(totTs * 100) / 100;

  if (!doc.lignes || !doc.lignes.length) {
    doc.lignes = [{
      sejour_no: 1,
      article: "Double",
      type_ligne: "Hébergement",
      prix_unitaire_ttc: 15000,
      quantite: 1,
      nb_jours: doc.sejours[0].nuitees || 3,
      montant_ttc_saisi: 45000,
      taux_tva: 9,
      montant_ht: 0,
      montant_tva: 0,
      total_ligne_ttc: 45000
    }];
  }

  // 2. Calcul des lignes : Formule "Prix unitaire × Quantité × Nuitées"
  let totTtcHeb = 0;
  let totTtcSrv = 0;
  const categories = new Set();

  doc.lignes.forEach((ln) => {
    ln.article = ln.article || "Double";
    const cat = getArticleCategory(ln.article);
    const isRoom = cat === "Hébergement";
    categories.add(cat);
    ln.type_ligne = cat;

    const no = parseInt(ln.sejour_no || 1, 10);
    const sej = doc.sejours.find(s => s.sejour_no === no) || doc.sejours[0];
    ln.sejour_no = sej ? sej.sejour_no : 1;

    const qty = Math.max(1, parseInt(ln.quantite || 1, 10));
    ln.quantite = qty;

    let jours = parseInt(ln.nb_jours || 0, 10);
    if (jours <= 0) {
      jours = isRoom ? (sej ? sej.nuitees : 1) : 1;
    }
    ln.nb_jours = jours;

    const taux = isRoom ? 9.0 : 19.0;
    ln.taux_tva = taux;

    // Calcul Total = Prix unitaire × Quantité × Nuitées
    let pu = parseFloat(ln.prix_unitaire_ttc || 0) || 0;
    let ttcSaisi = parseFloat(ln.montant_ttc_saisi || 0) || 0;

    if (pu > 0 && ttcSaisi === 0) {
      ttcSaisi = Math.round((pu * qty * jours) * 100) / 100;
    } else if (ttcSaisi > 0 && pu === 0) {
      pu = (qty * jours > 0) ? Math.round((ttcSaisi / (qty * jours)) * 100) / 100 : 0;
    } else if (pu > 0 && ttcSaisi > 0) {
      ttcSaisi = Math.round((pu * qty * jours) * 100) / 100;
    } else {
      pu = isRoom ? 15000 : 2500;
      ttcSaisi = Math.round((pu * qty * jours) * 100) / 100;
    }

    ln.prix_unitaire_ttc = pu;
    ln.montant_ttc_saisi = ttcSaisi;
    ln.total_ligne_ttc = ttcSaisi;

    if (isRoom) {
      totTtcHeb += ttcSaisi;
    } else {
      totTtcSrv += ttcSaisi;
    }

    if (sej) {
      sej.total_ttc_sejour = Math.round((sej.total_ttc_sejour + ttcSaisi) * 100) / 100;
    }
  });

  // Si la taxe de séjour n'est pas incluse, elle s'ajoute au total de chaque séjour
  if (!incluse && appliquerTs) {
    doc.sejours.forEach(s => {
      s.total_ttc_sejour = Math.round((s.total_ttc_sejour + (s.taxe_sejour || 0)) * 100) / 100;
    });
  }

  // 3. Ventilation fiscale HT et TVA
  const totalTtcSaisi = Math.round((totTtcHeb + totTtcSrv) * 100) / 100;
  let ttcHebHorsTs = totTtcHeb;
  let totalTtc = totalTtcSaisi;

  if (incluse) {
    ttcHebHorsTs = Math.max(0, Math.round((totTtcHeb - totTs) * 100) / 100);
    totalTtc = totalTtcSaisi;
  } else {
    ttcHebHorsTs = totTtcHeb;
    totalTtc = Math.round((totalTtcSaisi + totTs) * 100) / 100;
  }

  const htHeb = Math.round((ttcHebHorsTs / 1.09) * 100) / 100;
  const tvaHeb = Math.round((ttcHebHorsTs - htHeb) * 100) / 100;

  const htSrv = Math.round((totTtcSrv / 1.19) * 100) / 100;
  const tvaSrv = Math.round((totTtcSrv - htSrv) * 100) / 100;

  // Répartition analytique par ligne
  doc.lignes.forEach(ln => {
    const isRoom = ln.type_ligne === "Hébergement";
    const lnTtc = ln.montant_ttc_saisi || 0;
    const taux = ln.taux_tva || (isRoom ? 9 : 19);
    if (isRoom && totTtcHeb > 0) {
      const ratio = lnTtc / totTtcHeb;
      ln.montant_ht = Math.round(htHeb * ratio * 100) / 100;
      ln.montant_tva = Math.round(tvaHeb * ratio * 100) / 100;
      ln.taxe_sejour = appliquerTs ? Math.round(totTs * ratio * 100) / 100 : 0;
    } else {
      ln.montant_ht = Math.round((lnTtc / (1 + taux / 100)) * 100) / 100;
      ln.montant_tva = Math.round((lnTtc - ln.montant_ht) * 100) / 100;
      ln.taxe_sejour = 0;
    }
  });

  const totalHt = Math.round((htHeb + htSrv) * 100) / 100;
  const totalTva = Math.round((tvaHeb + tvaSrv) * 100) / 100;

  // 4. Droit de timbre fiscal : calculé APRÈS sur le total TTC espèces, puis ajouté
  let timbre = 0;
  if (doc.mode_paiement_prevu === "Espèces") {
    timbre = Math.min(10000, Math.max(100, Math.round(totalTtc * 0.01)));
  }
  const net = Math.round((totalTtc + timbre) * 100) / 100;

  doc.montant_ht = totalHt;
  doc.montant_tva = totalTva;
  doc.taxe_sejour = totTs;
  doc.total_ttc_saisi = totalTtcSaisi;
  doc.droit_timbre = timbre;
  doc.montant_ttc = net;
  doc.ht_hebergement = htHeb;
  doc.ht_services = htSrv;
  doc.nb_adultes = totAdultes;
  doc.nuitees = totNuitees;
  doc.detail_tva = `TVA 9% (Hébergement) : ${fmtDZD(tvaHeb)} | TVA 19% (Services) : ${fmtDZD(tvaSrv)}`;
  doc.montant_en_lettres = formatDzdInWords(net);

  const enc = Number(doc.montant_encaisse || 0);
  doc.reste_a_encaisser = Math.max(0, Math.round((net - enc) * 100) / 100);
}

function renderInvoiceStaysRows(doc) {
  return doc.sejours.map((s, idx) => `
    <tr id="inv_stay_row_${idx}" style="border-bottom:1px solid #e2e8f0;background:${idx % 2 === 0 ? '#fff' : '#f8fafc'};">
      <td style="padding:6px 8px;font-weight:700;">#${s.sejour_no || (idx + 1)}</td>
      <td style="padding:6px 8px;">
        <input type="text" id="inv_stay_desc_${idx}" style="width:100%;padding:4px 6px;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;" value="${s.description || ''}" placeholder="Ex: Séjour Principal" oninput="CURRENT_DOC.sejours[${idx}].description=this.value;">
      </td>
      <td style="padding:6px 8px;">
        <input type="date" id="inv_stay_arr_${idx}" style="padding:4px 6px;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;" value="${s.date_arrivee || ''}" onchange="onInvoiceStayDateChange(${idx}, 'date_arrivee', this.value);">
      </td>
      <td style="padding:6px 8px;">
        <input type="date" id="inv_stay_dep_${idx}" style="padding:4px 6px;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;" value="${s.date_depart || ''}" onchange="onInvoiceStayDateChange(${idx}, 'date_depart', this.value);">
      </td>
      <td style="padding:6px 8px;text-align:center;">
        <input type="number" min="1" id="inv_stay_nuits_${idx}" style="width:55px;padding:4px;text-align:center;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;font-weight:700;" value="${s.nuitees || 1}" onfocus="this.select()" oninput="onInvoiceStayFieldInput(${idx}, 'nuitees', this.value);">
      </td>
      <td style="padding:6px 8px;text-align:center;">
        <input type="number" min="1" id="inv_stay_pers_${idx}" style="width:55px;padding:4px;text-align:center;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;font-weight:700;color:#0369a1;" value="${s.nb_personnes || 1}" onfocus="this.select()" oninput="onInvoiceStayFieldInput(${idx}, 'nb_personnes', this.value);" title="Nombre de personnes pour ce séjour (taxe de séjour = personnes × nuits × 500 DZD)">
      </td>
      <td id="inv_stay_ts_${idx}" style="padding:6px 8px;text-align:right;color:#0369a1;font-weight:700;font-variant-numeric:tabular-nums;">
        ${fmtDZD(s.taxe_sejour || 0)}
      </td>
      <td id="inv_stay_total_${idx}" style="padding:6px 8px;text-align:right;font-weight:700;color:#0f172a;font-variant-numeric:tabular-nums;">
        ${fmtDZD(s.total_ttc_sejour || 0)}
      </td>
      ${doc.sejours_separes ? `
      <td style="padding:6px 8px;text-align:center;">
        <button type="button" class="btn" style="padding:2px 6px;color:#dc2626;" onclick="removeInvoiceStay(${idx})" title="Supprimer ce séjour">✕</button>
      </td>` : ''}
    </tr>
  `).join("");
}

function onInvoiceArticleChange(idx, newArticle) {
  if (!CURRENT_DOC || !CURRENT_DOC.lignes || !CURRENT_DOC.lignes[idx]) return;
  const ln = CURRENT_DOC.lignes[idx];
  ln.article = newArticle;
  const isRoom = ROOM_TYPES.includes(newArticle);
  if (!isRoom) {
    ln.nb_jours = 1;
  }
  onInvoiceFormUpdate();
}

function onInvoiceStayDateChange(idx, field, val) {
  if (!CURRENT_DOC || !CURRENT_DOC.sejours || !CURRENT_DOC.sejours[idx]) return;
  CURRENT_DOC.sejours[idx][field] = val;
  const s = CURRENT_DOC.sejours[idx];
  if (s.date_arrivee && s.date_depart) {
    const d1 = new Date(s.date_arrivee);
    const d2 = new Date(s.date_depart);
    const diff = Math.round((d2 - d1) / (1000 * 3600 * 24));
    s.nuitees = diff > 0 ? diff : 1;
    CURRENT_DOC.lignes.forEach((ln) => {
      if (ln.sejour_no === s.sejour_no && ROOM_TYPES.includes(ln.article)) {
        ln.nb_jours = s.nuitees;
        if (ln.prix_unitaire_ttc > 0) {
          ln.montant_ttc_saisi = Math.round(ln.prix_unitaire_ttc * (ln.quantite || 1) * ln.nb_jours * 100) / 100;
        }
      }
    });
  }
  onInvoiceFormUpdate();
}

function onInvoiceStayFieldInput(idx, field, rawVal) {
  if (!CURRENT_DOC || !CURRENT_DOC.sejours || !CURRENT_DOC.sejours[idx]) return;
  const s = CURRENT_DOC.sejours[idx];
  const num = Math.max(1, parseInt(rawVal || 1, 10));
  s[field] = num;

  if (field === "nuitees") {
    CURRENT_DOC.lignes.forEach((ln) => {
      if (ln.sejour_no === s.sejour_no && ROOM_TYPES.includes(ln.article)) {
        ln.nb_jours = num;
        if (ln.prix_unitaire_ttc > 0) {
          ln.montant_ttc_saisi = Math.round(ln.prix_unitaire_ttc * (ln.quantite || 1) * ln.nb_jours * 100) / 100;
        }
      }
    });
  }

  const dbSrc = (typeof APP_STATE !== "undefined" && APP_STATE.db) ? APP_STATE.db : (typeof DB !== "undefined" ? DB : {});
  const cfg = (dbSrc["SE Parametres Hotel"] && dbSrc["SE Parametres Hotel"][0]) || {};
  computeInvoiceDocClient(CURRENT_DOC, cfg);

  const elTs = document.getElementById(`inv_stay_ts_${idx}`);
  if (elTs) elTs.textContent = fmtDZD(s.taxe_sejour || 0);

  (CURRENT_DOC.sejours || []).forEach((st, sIdx) => {
    const elStayTotal = document.getElementById(`inv_stay_total_${sIdx}`);
    if (elStayTotal) elStayTotal.textContent = fmtDZD(st.total_ttc_sejour || 0);
  });

  const elCard = document.getElementById("inv_totals_card");
  if (elCard) elCard.innerHTML = renderInvoiceTotalsCard(CURRENT_DOC);
}

function onInvoiceLineCalcInput(idx, triggerField, rawVal) {
  if (!CURRENT_DOC || !CURRENT_DOC.lignes || !CURRENT_DOC.lignes[idx]) return;
  const ln = CURRENT_DOC.lignes[idx];

  if (triggerField === "pu") {
    const pu = parseFloat(rawVal || 0) || 0;
    ln.prix_unitaire_ttc = pu;
    const qty = Math.max(1, parseInt(ln.quantite || 1, 10));
    const nuits = Math.max(1, parseInt(ln.nb_jours || 1, 10));
    ln.montant_ttc_saisi = Math.round((pu * qty * nuits) * 100) / 100;
    const elTtc = document.getElementById(`inv_ttc_saisi_${idx}`);
    if (elTtc) elTtc.value = ln.montant_ttc_saisi || "";
  } else if (triggerField === "qty") {
    const qty = Math.max(1, parseInt(rawVal || 1, 10));
    ln.quantite = qty;
    const pu = parseFloat(ln.prix_unitaire_ttc || 0) || 0;
    const nuits = Math.max(1, parseInt(ln.nb_jours || 1, 10));
    if (pu > 0) {
      ln.montant_ttc_saisi = Math.round((pu * qty * nuits) * 100) / 100;
      const elTtc = document.getElementById(`inv_ttc_saisi_${idx}`);
      if (elTtc) elTtc.value = ln.montant_ttc_saisi || "";
    } else if (ln.montant_ttc_saisi > 0) {
      ln.prix_unitaire_ttc = Math.round((ln.montant_ttc_saisi / (qty * nuits)) * 100) / 100;
      const elPu = document.getElementById(`inv_pu_${idx}`);
      if (elPu) elPu.value = ln.prix_unitaire_ttc || "";
    }
  } else if (triggerField === "nuits") {
    const nuits = Math.max(1, parseInt(rawVal || 1, 10));
    ln.nb_jours = nuits;
    const pu = parseFloat(ln.prix_unitaire_ttc || 0) || 0;
    const qty = Math.max(1, parseInt(ln.quantite || 1, 10));
    if (pu > 0) {
      ln.montant_ttc_saisi = Math.round((pu * qty * nuits) * 100) / 100;
      const elTtc = document.getElementById(`inv_ttc_saisi_${idx}`);
      if (elTtc) elTtc.value = ln.montant_ttc_saisi || "";
    } else if (ln.montant_ttc_saisi > 0) {
      ln.prix_unitaire_ttc = Math.round((ln.montant_ttc_saisi / (qty * nuits)) * 100) / 100;
      const elPu = document.getElementById(`inv_pu_${idx}`);
      if (elPu) elPu.value = ln.prix_unitaire_ttc || "";
    }
  } else if (triggerField === "total_ttc") {
    const ttc = parseFloat(rawVal || 0) || 0;
    ln.montant_ttc_saisi = ttc;
    const qty = Math.max(1, parseInt(ln.quantite || 1, 10));
    const nuits = Math.max(1, parseInt(ln.nb_jours || 1, 10));
    ln.prix_unitaire_ttc = (qty * nuits > 0) ? Math.round((ttc / (qty * nuits)) * 100) / 100 : 0;
    const elPu = document.getElementById(`inv_pu_${idx}`);
    if (elPu) elPu.value = ln.prix_unitaire_ttc || "";
  }

  const dbSrc = (typeof APP_STATE !== "undefined" && APP_STATE.db) ? APP_STATE.db : (typeof DB !== "undefined" ? DB : {});
  const cfg = (dbSrc["SE Parametres Hotel"] && dbSrc["SE Parametres Hotel"][0]) || {};
  computeInvoiceDocClient(CURRENT_DOC, cfg);

  const elHt = document.getElementById(`inv_ht_${idx}`);
  if (elHt) elHt.textContent = fmtDZD(ln.montant_ht || 0);

  const elTva = document.getElementById(`inv_tva_${idx}`);
  if (elTva) elTva.textContent = `${ln.taux_tva || 9}%`;

  (CURRENT_DOC.sejours || []).forEach((st, sIdx) => {
    const elStayTotal = document.getElementById(`inv_stay_total_${sIdx}`);
    if (elStayTotal) elStayTotal.textContent = fmtDZD(st.total_ttc_sejour || 0);
  });

  const elCard = document.getElementById("inv_totals_card");
  if (elCard) elCard.innerHTML = renderInvoiceTotalsCard(CURRENT_DOC);
}

function renderInvoiceLinesRows(doc) {
  return doc.lignes.map((ln, idx) => `
    <tr style="border-bottom:1px solid #e2e8f0;background:${idx % 2 === 0 ? '#fff' : '#f8fafc'};">
      ${doc.sejours_separes ? `
      <td style="padding:6px;">
        <select style="width:100%;padding:4px;border:1px solid #cbd5e1;border-radius:4px;font-size:11.5px;" onchange="CURRENT_DOC.lignes[${idx}].sejour_no=parseInt(this.value); onInvoiceFormUpdate();">
          ${doc.sejours.map(s => `<option value="${s.sejour_no}" ${s.sejour_no === ln.sejour_no ? "selected" : ""}>Séjour #${s.sejour_no}</option>`).join("")}
        </select>
      </td>` : ''}
      <td style="padding:6px;">
        <select style="width:100%;padding:5px 6px;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;font-weight:600;" onchange="onInvoiceArticleChange(${idx}, this.value);">
                    <optgroup label="🛏️ Catégories Officielles Chambres 4★ (TVA 9%)">
            ${[
              "Single Standard [SGL-STD]",
              "Single Vue Mer [SGL-MER]",
              "Double Standard [DBL-STD]",
              "Double Vue Mer [DBL-MER]",
              "Chambre Twin [TWIN]",
              "Chambre Triple [TRP]",
              "Suite Deluxe [SDL]",
              "Suite Saint Eugène [SSE]"
            ].map(r => `<option value="${r}" ${r === ln.article ? "selected" : ""}>${r}</option>`).join("")}
          </optgroup>
          <optgroup label="🛏️ Catégories Standards & Historiques (TVA 9%)">
            ${["Single", "Double", "Twin", "Triple"].map(r => `<option value="${r}" ${r === ln.article ? "selected" : ""}>${r}</option>`).join("")}
          </optgroup>
          <optgroup label="🍽️ Services & Événements (TVA 19%)">
            ${SERVICES.map(s => `<option value="${s}" ${s === ln.article ? "selected" : ""}>${s}</option>`).join("")}
          </optgroup>
        </select>
      </td>
      <td style="padding:6px;text-align:right;">
        <input type="number" step="any" id="inv_pu_${idx}" style="width:110px;padding:5px 6px;text-align:right;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;font-weight:600;" value="${ln.prix_unitaire_ttc !== undefined && ln.prix_unitaire_ttc !== null ? ln.prix_unitaire_ttc : ''}" placeholder="0" onfocus="this.select()" oninput="onInvoiceLineCalcInput(${idx}, 'pu', this.value);">
      </td>
      <td style="padding:6px;text-align:center;">
        <input type="number" min="1" id="inv_qty_${idx}" style="width:55px;padding:5px 4px;text-align:center;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;font-weight:600;" value="${ln.quantite || 1}" onfocus="this.select()" oninput="onInvoiceLineCalcInput(${idx}, 'qty', this.value);" title="Nombre de chambres ou de prestations">
      </td>
      <td style="padding:6px;text-align:center;">
        <input type="number" min="1" id="inv_nuits_${idx}" style="width:55px;padding:5px 4px;text-align:center;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;font-weight:600;" value="${ln.nb_jours || 1}" onfocus="this.select()" oninput="onInvoiceLineCalcInput(${idx}, 'nuits', this.value);" title="Nombre de nuitées pour cette chambre">
      </td>
      <td style="padding:6px;text-align:right;">
        <input type="number" step="any" id="inv_ttc_saisi_${idx}" style="width:130px;padding:5px 8px;text-align:right;border:2px solid #b45309;background:#fffbeb;font-weight:700;color:#92400e;border-radius:4px;font-size:13px;" value="${ln.montant_ttc_saisi !== undefined && ln.montant_ttc_saisi !== null ? ln.montant_ttc_saisi : ''}" placeholder="0" onfocus="this.select()" oninput="onInvoiceLineCalcInput(${idx}, 'total_ttc', this.value);" title="Total TTC = P.U. × Quantité × Nuitées">
      </td>
      <td id="inv_ht_${idx}" style="padding:6px;text-align:right;color:#334155;font-variant-numeric:tabular-nums;">${fmtDZD(ln.montant_ht || 0)}</td>
      <td id="inv_tva_${idx}" style="padding:6px;text-align:center;font-size:11px;color:#64748b;">${ln.taux_tva || 9}%</td>
      <td style="padding:6px;">
        <textarea rows="1" placeholder="Observations chambre (ex: VIP, lit sup, vue mer...)" oninput="CURRENT_DOC.lignes[${idx}].observation=this.value; CURRENT_DOC.lignes[${idx}].obs=this.value; CURRENT_DOC.lignes[${idx}].remarque=this.value;" style="width:100%;box-sizing:border-box;padding:4px 6px;border:1px solid #cbd5e1;border-radius:4px;font-size:11.5px;resize:vertical;min-height:30px;line-height:1.3;font-family:inherit;">${ln.observation || ln.obs || ln.remarque || ''}</textarea>
      </td>
      <td style="padding:6px;text-align:center;">
        <button type="button" class="btn" style="padding:2px 6px;color:#dc2626;" onclick="removeInvoiceLine(${idx})" title="Supprimer la ligne">✕</button>
      </td>
    </tr>
  `).join("");
}

function renderInvoiceTotalsCard(doc) {
  const isEsp = (doc.mode_paiement_prevu === "Espèces");
  return `
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:14px;">
      <div style="flex:1;min-width:280px;">
        <div style="font-weight:700;font-size:12.5px;color:#0f172a;margin-bottom:6px;">📊 Ventilation Fiscale & Arrêté Légal (Algérie SCF)</div>
        <div style="font-size:11.5px;color:#475569;margin-bottom:4px;"><b>Détail TVA :</b> ${doc.detail_tva || 'N/A'}</div>
        <div style="font-size:11.5px;color:#475569;margin-bottom:4px;"><b>Hébergement 4★ :</b> ${doc.nuitees || 0} nuitée(s) | ${doc.nb_adultes || 0} personne(s) | Taxe : 500 DZD / nuitée / pers. (Calculée par séjour)</div>
        <div style="background:#fff;border-left:3px solid #b45309;padding:8px 10px;border-radius:4px;font-size:12px;color:#1e293b;margin-top:8px;">
          Arrêtée la présente facture à la somme de :<br>
          <b>« ${doc.montant_en_lettres || ''} »</b>
        </div>
      </div>
      <div style="width:100%;max-width:380px;">
        <table style="width:100%;border-collapse:collapse;font-size:12.5px;">
          <tr><td style="padding:4px 0;color:#475569;">Total HT (Hébergement + Services)</td><td style="padding:4px 0;text-align:right;font-weight:600;">${fmtDZD(doc.montant_ht)}</td></tr>
          <tr><td style="padding:4px 0;color:#475569;">TVA Hébergement (9%)</td><td style="padding:4px 0;text-align:right;">${fmtDZD(doc.lignes.filter(l => l.taux_tva === 9).reduce((a, b) => a + (b.montant_tva || 0), 0))}</td></tr>
          <tr><td style="padding:4px 0;color:#475569;">TVA Services & Restauration (19%)</td><td style="padding:4px 0;text-align:right;">${fmtDZD(doc.lignes.filter(l => l.taux_tva === 19).reduce((a, b) => a + (b.montant_tva || 0), 0))}</td></tr>
          <tr><td style="padding:4px 0;color:#0369a1;font-weight:600;">Taxe de Séjour 4★ (500 DZD × pers. × nuits par séjour)</td><td style="padding:4px 0;text-align:right;font-weight:600;color:#0369a1;">${fmtDZD(doc.taxe_sejour)}</td></tr>
          <tr style="border-top:1px solid #cbd5e1;"><td style="padding:5px 0;font-weight:700;color:#1e293b;">Total TTC Chambres & Services</td><td style="padding:5px 0;text-align:right;font-weight:700;color:#1e293b;">${fmtDZD(doc.total_ttc_saisi || doc.montant_ttc)}</td></tr>
          <tr>
            <td style="padding:4px 0;color:${isEsp ? '#b45309' : '#64748b'};font-weight:${isEsp ? '700' : 'normal'};">
              Droit de Timbre Fiscal ${isEsp ? '(Espèces - En sus)' : '(Exonéré hors espèces)'}
            </td>
            <td style="padding:4px 0;text-align:right;color:${isEsp ? '#b45309' : '#64748b'};font-weight:${isEsp ? '700' : 'normal'};">
              ${fmtDZD(doc.droit_timbre)}
            </td>
          </tr>
          <tr style="background:#0f172a;color:#fff;font-weight:700;font-size:13.5px;">
            <td style="padding:8px 10px;border-radius:4px 0 0 4px;">NET À PAYER TTC (DZD)</td>
            <td style="padding:8px 10px;text-align:right;border-radius:0 4px 4px 0;color:#fbbf24;">${fmtDZD(doc.montant_ttc)}</td>
          </tr>
          ${CURRENT_DOCTYPE === "SE Facture Client" ? `
          <tr><td style="padding:4px 0;color:#16a34a;font-weight:600;">Montant Encaissé</td><td style="padding:4px 0;text-align:right;color:#16a34a;font-weight:600;">${fmtDZD(doc.montant_encaisse || 0)}</td></tr>
          <tr><td style="padding:4px 0;color:#dc2626;font-weight:700;">Reste à Encaisser</td><td style="padding:4px 0;text-align:right;color:#dc2626;font-weight:700;">${fmtDZD(doc.reste_a_encaisser || doc.montant_ttc)}</td></tr>
          ` : ''}
        </table>
      </div>
    </div>
  `;
}

function onInvoiceFormUpdate() {
  const dbSrc = (typeof APP_STATE !== "undefined" && APP_STATE.db) ? APP_STATE.db : (typeof DB !== "undefined" ? DB : {});
  const cfg = (dbSrc["SE Parametres Hotel"] && dbSrc["SE Parametres Hotel"][0]) || {};
  computeInvoiceDocClient(CURRENT_DOC, cfg);
  document.getElementById("inv_stays_tbody").innerHTML = renderInvoiceStaysRows(CURRENT_DOC);
  document.getElementById("inv_lines_tbody").innerHTML = renderInvoiceLinesRows(CURRENT_DOC);
  document.getElementById("inv_totals_card").innerHTML = renderInvoiceTotalsCard(CURRENT_DOC);
}

function onInvoiceClientChange(clientKey) {
  CURRENT_DOC.client = clientKey;
  const dbSrc = (typeof APP_STATE !== "undefined" && APP_STATE.db) ? APP_STATE.db : (typeof DB !== "undefined" ? DB : {});
  const cli = getClientObject(clientKey, dbSrc);
  if (cli) {
    CURRENT_DOC.type_client = cli.type_client || "Corporate";
    CURRENT_DOC.nom_client = cli.nom_client || cli.name;
    CURRENT_DOC.ref_societe = cli.ref_societe || cli.name;
    const elType = document.getElementById("inv_type_client");
    if (elType) elType.value = CURRENT_DOC.type_client;
    const elNom = document.getElementById("inv_nom_client");
    if (elNom) elNom.value = CURRENT_DOC.nom_client;
    const elRef = document.getElementById("inv_ref_client");
    if (elRef) elRef.value = CURRENT_DOC.ref_societe;
  }
}

function addInvoiceStay() {
  const nextNo = (CURRENT_DOC.sejours.length ? Math.max(...CURRENT_DOC.sejours.map(s => s.sejour_no || 0)) : 0) + 1;
  CURRENT_DOC.sejours.push({
    sejour_no: nextNo,
    description: `Séjour #${nextNo}`,
    date_arrivee: CURRENT_DOC.date_facture || "2026-11-04",
    date_depart: "2026-11-07",
    nuitees: 3,
    nb_personnes: 1,
    taxe_sejour: 0,
    total_ttc_sejour: 0
  });
  onInvoiceFormUpdate();
}

function removeInvoiceStay(idx) {
  if (CURRENT_DOC.sejours.length <= 1) {
    alert("Une facture doit comporter au moins un séjour.");
    return;
  }
  CURRENT_DOC.sejours.splice(idx, 1);
  onInvoiceFormUpdate();
}

function addInvoiceLine() {
  const stay1 = (CURRENT_DOC.sejours && CURRENT_DOC.sejours[0]) ? CURRENT_DOC.sejours[0].sejour_no : 1;
  const nuitsStay1 = (CURRENT_DOC.sejours && CURRENT_DOC.sejours[0]) ? CURRENT_DOC.sejours[0].nuitees : 3;
  CURRENT_DOC.lignes.push({
    sejour_no: stay1,
    article: "Double",
    type_ligne: "Hébergement",
    prix_unitaire_ttc: 15000,
    quantite: 1,
    nb_jours: nuitsStay1 || 3,
    montant_ttc_saisi: 15000 * 1 * (nuitsStay1 || 3),
    taux_tva: 9,
    montant_ht: 0,
    montant_tva: 0,
    total_ligne_ttc: 15000 * 1 * (nuitsStay1 || 3)
  });
  onInvoiceFormUpdate();
}

function removeInvoiceLine(idx) {
  if (CURRENT_DOC.lignes.length <= 1) {
    alert("Une facture doit comporter au moins une prestation.");
    return;
  }
  CURRENT_DOC.lignes.splice(idx, 1);
  onInvoiceFormUpdate();
}

function renderInvoiceModal(doctype, doc, isNew) {
  CURRENT_DOCTYPE = doctype;
  CURRENT_DOC = doc;
  const isProforma = (doctype === "SE Facture Pro Forma");
  document.getElementById("modalTitle").textContent = `${isNew ? "Nouvelle" : doc.name} — ${isProforma ? "Facture Pro Forma" : "Facture Client (SCF 70)"}`;

  const dbSrc = (typeof APP_STATE !== "undefined" && APP_STATE.db) ? APP_STATE.db : (typeof DB !== "undefined" ? DB : {});
  const cfg = (dbSrc["SE Parametres Hotel"] && dbSrc["SE Parametres Hotel"][0]) || {};
  computeInvoiceDocClient(doc, cfg);

  const clients = dbSrc["SE Client"] || [];
  const cli = getClientObject(doc.client, dbSrc) || (clients.length ? clients[0] : null);
  if (!doc.client && cli) {
    doc.client = cli.name;
    doc.type_client = cli.type_client || "Corporate";
    doc.nom_client = cli.nom_client || cli.name;
    doc.ref_societe = cli.ref_societe || cli.name;
  }

  const clientOptions = clients.map(c => {
    const nom = c.nom_client || c.name;
    const ref = c.ref_societe || (c.name && c.name.startsWith("CLI-") ? c.name : "");
    const label = (ref && ref !== nom) ? `${nom} — [${ref}] (${c.type_client || 'Corporate'})` : `${nom} (${c.type_client || 'Corporate'})`;
    const isSel = (doc.client === c.name || doc.client === c.nom_client || doc.client === c.ref_societe);
    return `<option value="${c.name}" ${isSel ? "selected" : ""}>${label}</option>`;
  }).join("");

  let html = `
  <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:14px;margin-bottom:16px;">
    <div style="font-weight:700;font-size:13px;color:#1e293b;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;">
      <span>📌 Informations Client & Modalités de Règlement</span>
      <span class="pill ${isProforma ? 'blue' : 'green'}">${isProforma ? 'Devis Pro Forma' : 'Facture Client Officielle'}</span>
    </div>
    <div class="form-grid" style="grid-template-columns:repeat(3, 1fr);gap:12px;">
      <div class="form-group" style="grid-column:span 2;">
        <label>Sélectionner le Client (Nom ou Référence Société) *</label>
        <select id="inv_client" onchange="onInvoiceClientChange(this.value)">
          <option value="">— Sélectionner un client —</option>
          ${clientOptions}
        </select>
      </div>
      <div class="form-group">
        <label>Type Client</label>
        <input type="text" id="inv_type_client" value="${doc.type_client || (cli ? cli.type_client : 'Corporate')}" readonly style="background:#f1f5f9;font-weight:700;">
      </div>
      <div class="form-group" style="grid-column:span 2;">
        <label>Nom / Raison Sociale</label>
        <input type="text" id="inv_nom_client" value="${cli ? (cli.nom_client || cli.name) : (doc.client || '')}" readonly style="background:#f1f5f9;font-weight:700;color:#0f172a;">
      </div>
      <div class="form-group">
        <label>Référence Société</label>
        <input type="text" id="inv_ref_client" value="${cli ? (cli.ref_societe || cli.name) : ''}" readonly style="background:#f1f5f9;font-weight:700;color:#0284c7;">
      </div>
      <div class="form-group">
        <label>Date de Facturation</label>
        <input type="date" id="inv_date_facture" value="${doc.date_facture || '2026-11-04'}" onchange="CURRENT_DOC.date_facture=this.value">
      </div>
      <div class="form-group">
        <label>${isProforma ? 'Date de Validité' : "Date d'Échéance"}</label>
        <input type="date" id="inv_date_echeance" value="${doc.date_echeance || doc.date_validite || '2026-11-25'}" onchange="CURRENT_DOC.date_echeance=this.value; CURRENT_DOC.date_validite=this.value;">
      </div>
      ${isProforma ? `
      <div class="form-group">
        <label>Statut Pro Forma *</label>
        <select id="inv_statut" onchange="CURRENT_DOC.statut=this.value;">
          <option value="Non validée" ${doc.statut === "Non validée" || !doc.statut ? "selected" : ""}>Non validée</option>
          <option value="Validée" ${doc.statut === "Validée" ? "selected" : ""}>Validée</option>
        </select>
      </div>` : ''}
      <div class="form-group">
        <label>N° Bon de Commande (BC) / Réf. Commande</label>
        <input type="text" id="inv_bon_commande" placeholder="Ex: BC-2026/045 ou Réf Client..." value="${doc.bon_commande || doc.num_bon_commande || ''}" onchange="CURRENT_DOC.bon_commande=this.value; CURRENT_DOC.num_bon_commande=this.value;">
      </div>
      <div class="form-group">
        <label>Mode de Paiement Prévu *</label>
        <select id="inv_mode_paiement" onchange="CURRENT_DOC.mode_paiement_prevu=this.value; onInvoiceFormUpdate();">
          <option value="Virement" ${doc.mode_paiement_prevu === "Virement" ? "selected" : ""}>Virement Bancaire (Sans timbre)</option>
          <option value="Chèque" ${doc.mode_paiement_prevu === "Chèque" ? "selected" : ""}>Chèque Bancaire (Sans timbre)</option>
          <option value="Espèces" ${doc.mode_paiement_prevu === "Espèces" ? "selected" : ""}>Espèces (Droit de timbre fiscal 1% en sus)</option>
          <option value="TPE" ${doc.mode_paiement_prevu === "TPE" ? "selected" : ""}>TPE / Carte CIB / Edahabia (Sans timbre)</option>
        </select>
      </div>
      <div class="form-group" style="grid-column:span 3;display:flex;flex-direction:row;gap:20px;margin-top:6px;background:#fff;padding:10px 14px;border:1px solid #cbd5e1;border-radius:6px;flex-wrap:wrap;">
        <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:12px;font-weight:600;">
          <input type="checkbox" id="inv_ts_incluse" ${doc.taxe_sejour_incluse ? "checked" : ""} onchange="CURRENT_DOC.taxe_sejour_incluse = this.checked ? 1 : 0; onInvoiceFormUpdate();">
          🏷️ Taxe de séjour 4★ (500 DZD) incluse dans le montant TTC saisi
        </label>
        <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:12px;font-weight:600;">
          <input type="checkbox" id="inv_app_ts" ${doc.appliquer_taxe_sejour ? "checked" : ""} onchange="CURRENT_DOC.appliquer_taxe_sejour = this.checked ? 1 : 0; onInvoiceFormUpdate();">
          🛎️ Appliquer la taxe de séjour (Hébergement)
        </label>
        <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:12px;font-weight:600;">
          <input type="checkbox" id="inv_sej_separes" ${doc.sejours_separes ? "checked" : ""} onchange="CURRENT_DOC.sejours_separes = this.checked ? 1 : 0; renderInvoiceModal(CURRENT_DOCTYPE, CURRENT_DOC, CURRENT_IS_NEW);">
          📅 Plusieurs séjours distincts (Dates et personnes indépendantes)
        </label>
      </div>
    </div>
  </div>

  <!-- SÉJOURS & TAXE DE SÉJOUR -->
  <div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:14px;margin-bottom:16px;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
      <div>
        <span style="font-weight:700;font-size:13px;color:#0f172a;">📅 Périodes de Séjour & Taxe de Séjour 4★</span>
        <div style="font-size:11px;color:#64748b;margin-top:2px;">La taxe de séjour est calculée par séjour : <b>Nombre de personnes × Nuitées × 500 DZD</b> (sans cumul ni doublon).</div>
      </div>
      ${doc.sejours_separes ? `<button class="btn btn-gold" type="button" style="font-size:11.5px;padding:4px 10px;" onclick="addInvoiceStay()">+ Ajouter un séjour séparé</button>` : ''}
    </div>
    <div style="overflow-x:auto;">
      <table style="width:100%;border-collapse:collapse;font-size:12px;">
        <thead>
          <tr style="background:#f1f5f9;border-bottom:2px solid #cbd5e1;text-align:left;">
            <th style="padding:6px 8px;width:35px;">N°</th>
            <th style="padding:6px 8px;">Désignation Séjour</th>
            <th style="padding:6px 8px;width:125px;">Date Arrivée</th>
            <th style="padding:6px 8px;width:125px;">Date Départ</th>
            <th style="padding:6px 8px;width:70px;text-align:center;">Nuitées</th>
            <th style="padding:6px 8px;width:70px;text-align:center;color:#0369a1;">Personnes</th>
            <th style="padding:6px 8px;width:120px;text-align:right;color:#0369a1;">Taxe Séjour (500 DZD)</th>
            <th style="padding:6px 8px;width:130px;text-align:right;">Total TTC Séjour</th>
            ${doc.sejours_separes ? `<th style="padding:6px 8px;width:35px;text-align:center;"></th>` : ''}
          </tr>
        </thead>
        <tbody id="inv_stays_tbody">
          ${renderInvoiceStaysRows(doc)}
        </tbody>
      </table>
    </div>
  </div>

  <!-- TARIFICATION DES CHAMBRES & PRESTATIONS -->
  <div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:14px;margin-bottom:16px;">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px;">
      <div>
        <span style="font-weight:700;font-size:13px;color:#0f172a;">🛎️ Tarification des Chambres & Services (Formule : Prix unitaire × Quantité × Nuitées)</span>
        <div style="font-size:11px;color:#64748b;margin-top:2px;">Indiquez le Prix unitaire, le nombre de chambres (Quantité) et les nuitées : le système calcule automatiquement le Total et ventile HT et TVA.</div>
      </div>
      <button class="btn btn-primary" type="button" style="font-size:11.5px;padding:4px 10px;" onclick="addInvoiceLine()">+ Ajouter une chambre / service</button>
    </div>
    <div style="overflow-x:auto;">
      <table style="width:100%;border-collapse:collapse;font-size:12px;">
        <thead>
          <tr style="background:#0f172a;color:#fff;text-align:left;">
            ${doc.sejours_separes ? `<th style="padding:7px;width:85px;">Séjour</th>` : ''}
            <th style="padding:7px;min-width:180px;">Type de Chambre ou Prestation</th>
            <th style="padding:7px;width:120px;text-align:right;background:#0369a1;">Prix unitaire TTC *</th>
            <th style="padding:7px;width:65px;text-align:center;background:#0369a1;">Qté (Ch.) *</th>
            <th style="padding:7px;width:65px;text-align:center;background:#0369a1;">Nuitées *</th>
            <th style="padding:7px;width:140px;text-align:right;background:#b45309;">Total TTC Saisi / Calculé *</th>
            <th style="padding:7px;width:95px;text-align:right;">Base HT</th>
            <th style="padding:7px;width:55px;text-align:center;">TVA</th>
            <th style="padding:7px;min-width:140px;">Observations (Chambre)</th>
            <th style="padding:7px;width:35px;text-align:center;"></th>
          </tr>
        </thead>
        <tbody id="inv_lines_tbody">
          ${renderInvoiceLinesRows(doc)}
        </tbody>
      </table>
    </div>
  </div>

  <!-- RÉCAPITULATIF FISCAL & TIMBRE -->
  <div id="inv_totals_card" style="background:#f8fafc;border:2px solid #b45309;border-radius:8px;padding:14px;margin-bottom:14px;">
    ${renderInvoiceTotalsCard(doc)}
  </div>
  `;

  document.getElementById("modalBody").innerHTML = html;

  let ftrHtml = `<div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;">`;
  if (!isNew) {
    ftrHtml += `<button type="button" class="btn" style="background:#fee2e2;color:#991b1b;border:1px solid #fecaca;font-weight:600;padding:6px 12px;margin-right:6px;" onclick="triggerDeleteDoc('${doctype}', '${doc.name.replace(/'/g, "\\'")}')">🗑️ Supprimer</button>`;
    if (typeof openPrintPreview === "function") {
      ftrHtml += `<button class="btn btn-gold" onclick="openPrintPreview('${doctype}', '${doc.name.replace(/'/g, "\\'")}')">🖨️ Imprimer / Aperçu PDF Officiel SCF</button> `;
    }
  }
  if (isProforma && !isNew) {
    ftrHtml += `<button class="btn btn-primary" onclick="convertProformaToInvoice()">🔄 Convertir en Facture Définitive (SCF 70)</button> `;
  }
  if (!isProforma && !isNew && Number(doc.reste_a_encaisser) > 0 && typeof quickReceiptFromInvoice === "function") {
    ftrHtml += `<button class="btn" onclick="quickReceiptFromInvoice()">💰 Enregistrer un Encaissement</button>`;
  }
  ftrHtml += `</div><div>
    <button class="btn" onclick="closeModal()">Fermer</button>
    <button class="btn btn-primary" onclick="saveInvoiceDoc()">💾 Enregistrer & Sauvegarder</button>
  </div>`;
  document.getElementById("modalFooter").innerHTML = ftrHtml;
  document.getElementById("docModal").classList.add("open");
}


async function saveInvoiceDoc() {
  const bcInput = document.getElementById("inv_bon_commande");
  if (bcInput) {
    CURRENT_DOC.bon_commande = bcInput.value.trim();
    CURRENT_DOC.num_bon_commande = bcInput.value.trim();
  }
  const dbSrc = (typeof APP_STATE !== "undefined" && APP_STATE.db) ? APP_STATE.db : (typeof DB !== "undefined" ? DB : {});
  const cfg = (dbSrc["SE Parametres Hotel"] && dbSrc["SE Parametres Hotel"][0]) || {};
  computeInvoiceDocClient(CURRENT_DOC, cfg);

  if (typeof saveCurrentDoc === "function") {
    await saveCurrentDoc(CURRENT_IS_NEW);
  }
}

function convertProformaToInvoice() {
  if (confirm("Voulez-vous convertir cette Facture Pro Forma en Facture Client Définitive (SCF 70) ?")) {
    const pro = CURRENT_DOC;
    pro.statut = "Convertie en Facture";
    const dbSrc = (typeof APP_STATE !== "undefined" && APP_STATE.db) ? APP_STATE.db : (typeof DB !== "undefined" ? DB : {});
    const count = (dbSrc["SE Facture Client"] || []).length + 1;
    const newName = `FAC-CLI-2026-000${count < 10 ? '0' + count : count}`;
    
    const newInvoice = JSON.parse(JSON.stringify(pro));
    newInvoice.name = newName;
    newInvoice.ref_reservation = pro.ref_devis || pro.name;
    newInvoice.statut = "Validée";
    newInvoice.docstatus = 1;
    delete newInvoice.date_validite;
    delete newInvoice.ref_devis;
    newInvoice.date_echeance = "2026-11-25";
    
    renderInvoiceModal("SE Facture Client", newInvoice, true);
  }
}

function renderDocModal(doctype, doc, isNew) {
  CURRENT_DOCTYPE = doctype;
  CURRENT_DOC = doc;
  CURRENT_IS_NEW = !!isNew;
  if (doctype === "SE Facture Client" || doctype === "SE Facture Pro Forma") {
    renderInvoiceModal(doctype, doc, isNew);
    return;
  }
  const schema = APP_STATE.schemas[doctype];
  document.getElementById("modalTitle").textContent = `${isNew ? "Nouveau" : doc.name} — ${getNavLabel(doctype)}`;

  let formHtml = `<div class="form-grid">`;
  schema.fields.forEach(f => {
    if (["Section Break", "Column Break", "Table"].includes(f.fieldtype) || f.fieldname === "naming_series" || f.fieldname === "amended_from") return;
    const val = doc[f.fieldname] ?? "";
    const ro = f.read_only ? "readonly" : "";
    const full = f.fieldtype === "Small Text" ? "full" : "";

    let inputEl = "";
    if (f.fieldtype === "Select") {
      const opts = (f.options || "").split("\n");
      inputEl = `<select id="fld_${f.fieldname}" ${ro ? "disabled" : ""} onchange="onFieldChange('${f.fieldname}', this.value)">
        ${opts.map(o => `<option value="${o}" ${o === String(val) ? "selected" : ""}>${o}</option>`).join("")}
      </select>`;
    } else if (f.fieldtype === "Link" && APP_STATE.db[f.options]) {
      const targets = APP_STATE.db[f.options];
      inputEl = `<select id="fld_${f.fieldname}" onchange="onFieldChange('${f.fieldname}', this.value)">
        <option value="">— Sélectionner —</option>
        ${targets.map(t => `<option value="${t.name}" ${t.name === String(val) ? "selected" : ""}>${t.name} ${t.nom_complet ? " - " + t.nom_complet : ""}</option>`).join("")}
      </select>`;
    } else if (f.fieldtype === "Small Text") {
      inputEl = `<textarea id="fld_${f.fieldname}" rows="2" ${ro} oninput="onFieldChange('${f.fieldname}', this.value)">${val}</textarea>`;
    } else {
      const type = ["Currency", "Percent", "Int"].includes(f.fieldtype) ? "number" : (f.fieldtype === "Date" ? "date" : "text");
      inputEl = `<input type="${type}" step="any" id="fld_${f.fieldname}" value="${val}" ${ro} oninput="onFieldChange('${f.fieldname}', this.value)">`;
    }

    formHtml += `<div class="form-group ${full}">
      <label>${f.label} ${f.read_only ? "🔒" : ""}</label>
      ${inputEl}
    </div>`;
  });
  formHtml += `</div>`;
  document.getElementById("modalBody").innerHTML = formHtml;

  const printable = ["SE Facture Client", "SE Caisse Mensuelle", "SE Fiche de Paie Mensuelle", "SE Declaration TVA"].includes(doctype);
  let ftrHtml = `<div style="display:flex;gap:6px;align-items:center;">`;
  if (!isNew) {
    ftrHtml += `<button type="button" class="btn" style="background:#fee2e2;color:#991b1b;border:1px solid #fecaca;font-weight:600;padding:6px 12px;margin-right:6px;" onclick="triggerDeleteDoc('${doctype}', '${doc.name.replace(/'/g, "\\'")}')">🗑️ Supprimer</button>`;
  }
  if (printable && !isNew) {
    ftrHtml += `<button class="btn btn-gold" onclick="openPrintPreview('${doctype}', '${doc.name.replace(/'/g, "\\'")}')">🖨️ Imprimer / Aperçu PDF Officiel SCF</button> `;
  }
  if (doctype === "SE Facture Client" && !isNew && Number(doc.reste_a_encaisser) > 0) {
    ftrHtml += `<button class="btn" onclick="quickReceiptFromInvoice()">💰 Enregistrer un Encaissement</button>`;
  }
  ftrHtml += `</div><div>
    <button class="btn" onclick="closeModal()">Fermer</button>
    <button class="btn btn-primary" onclick="saveCurrentDoc(${isNew})">💾 Enregistrer & Recalculer (SCF)</button>
  </div>`;
  document.getElementById("modalFooter").innerHTML = ftrHtml;
  document.getElementById("docModal").classList.add("open");
}

function onFieldChange(fieldname, value) {
  CURRENT_DOC[fieldname] = value;
}

function quickReceiptFromInvoice() {
  const inv = CURRENT_DOC;
  closeModal();
  renderDocModal("SE Encaissement", {
    name: `ENC-2026-0000${(APP_STATE.db["SE Encaissement"].length + 1)}`,
    date_encaissement: "2026-11-03",
    client: inv.client,
    facture_liee: inv.name,
    montant: inv.reste_a_encaisser,
    mode_paiement: inv.mode_paiement_prevu || "Virement",
    compte_destination: inv.mode_paiement_prevu === "Espèces" ? "Caisse Principale Hôtel" : "BNA Agence Bologhine - DZD",
    ref_paiement: `REG-${inv.name}`,
    statut: "Validé"
  }, true);
}

async function saveCurrentDoc(isNew) {
  const res = await fetch("/api/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doctype: CURRENT_DOCTYPE, doc: CURRENT_DOC, is_new: isNew })
  });
  APP_STATE = await res.json();
  window.APP_STATE = APP_STATE;
  closeModal();
  if (CURRENT_DOCTYPE === "SE Parametres Hotel") showWorkspace();
  else showList(CURRENT_DOCTYPE);
}

function openPrintPreview(doctype, name) {
  window.open(`/print?doctype=${encodeURIComponent(doctype)}&name=${encodeURIComponent(name)}`, "_blank");
}


let PENDING_DELETE_DOCTYPE = null;
let PENDING_DELETE_NAME = null;

function checkDeleteIntegrity(doctype, docName) {
  const db = APP_STATE.db || {};
  if (doctype === "SE Client") {
    const facs = (db["SE Facture Client"] || []).filter(f => f.client === docName || f.nom_client === docName || f.ref_societe === docName);
    if (facs.length > 0) {
      return {
        blocked: true,
        message: `⚠️ <b>Suppression bloquée pour conformité comptable SCF :</b> Ce client est lié à <b>${facs.length} facture(s) enregistrée(s)</b> (ex: ${facs[0].name}). La suppression directe briserait le lettrage des comptes tiers (SCF 411). Veuillez plutôt archiver ou désactiver ce client.`
      };
    }
  } else if (doctype === "SE Facture Client") {
    const encs = (db["SE Encaissement"] || []).filter(e => e.facture_liee === docName && e.statut !== "Annulé");
    if (encs.length > 0) {
      return {
        blocked: true,
        message: `⚠️ <b>Suppression bloquée :</b> Cette facture est rattachée à <b>${encs.length} encaissement(s) comptabilisé(s)</b> (ex: ${encs[0].name}). Supprimez ou annulez d'abord les encaissements pour préserver les écritures de trésorerie (SCF 512/530).`
      };
    }
  } else if (doctype === "SE Fournisseur") {
    const facs = (db["SE Facture Fournisseur"] || []).filter(f => f.fournisseur === docName);
    if (facs.length > 0) {
      return {
        blocked: true,
        message: `⚠️ <b>Suppression bloquée :</b> Ce fournisseur possède <b>${facs.length} facture(s) d'achat</b> (ex: ${facs[0].name}). La suppression directe compromettrait la déclaration de TVA déductible (G50).`
      };
    }
  } else if (doctype === "SE Facture Fournisseur") {
    const decs = (db["SE Decaissement"] || []).filter(d => d.facture_liee === docName && d.statut !== "Annulé");
    if (decs.length > 0) {
      return {
        blocked: true,
        message: `⚠️ <b>Suppression bloquée :</b> Cette facture fournisseur est associée à <b>${decs.length} décaissement(s)</b>. Supprimez d'abord les règlements correspondants.`
      };
    }
  } else if (doctype === "SE Employe") {
    const paies = (db["SE Fiche de Paie Mensuelle"] || []).filter(p => p.employe === docName);
    if (paies.length > 0) {
      return {
        blocked: true,
        message: `⚠️ <b>Suppression déconseillée pour conformité CNAS :</b> Cet employé possède <b>${paies.length} bulletin(s) de paie</b>. Pour préserver l'historique social et les déclarations DAS/CNAS, il est recommandé de renseigner sa <b>Date de sortie</b> et la situation <b>'Sorti'</b>.`
      };
    }
  } else if (doctype === "SE Compte Tresorerie") {
    return {
      blocked: true,
      message: `⚠️ <b>Compte réservé :</b> Les comptes de trésorerie officiels (CPA, BNA, Caisses) sont indispensables à la comptabilité générale.`
    };
  }
  return { blocked: false, message: "" };
}

function triggerDeleteDoc(doctype, docName) {
  PENDING_DELETE_DOCTYPE = doctype;
  PENDING_DELETE_NAME = docName;
  const detailsEl = document.getElementById("deleteDocDetails");
  const warnEl = document.getElementById("deleteWarningBlock");
  const btnEl = document.getElementById("btnConfirmDelete");
  if (detailsEl) {
    detailsEl.innerHTML = `<b>Élément sélectionné :</b> ${docName} <span style="color:#64748b;">(${getNavLabel(doctype)})</span>`;
  }
  const check = checkDeleteIntegrity(doctype, docName);
  if (check.blocked) {
    warnEl.style.display = "block";
    warnEl.innerHTML = check.message;
    btnEl.disabled = true;
    btnEl.style.opacity = "0.45";
    btnEl.style.cursor = "not-allowed";
    btnEl.title = "Action bloquée pour protéger l'intégrité comptable";
  } else {
    warnEl.style.display = "none";
    warnEl.innerHTML = "";
    btnEl.disabled = false;
    btnEl.style.opacity = "1";
    btnEl.style.cursor = "pointer";
    btnEl.title = "";
  }
  document.getElementById("deleteConfirmModal").classList.add("open");
}

function closeDeleteConfirmModal() {
  document.getElementById("deleteConfirmModal").classList.remove("open");
  PENDING_DELETE_DOCTYPE = null;
  PENDING_DELETE_NAME = null;
}

async function executeDeleteDoc() {
  if (!PENDING_DELETE_DOCTYPE || !PENDING_DELETE_NAME) return;
  const dt = PENDING_DELETE_DOCTYPE;
  const name = PENDING_DELETE_NAME;
  closeDeleteConfirmModal();
  closeModal();
  const res = await fetch("/api/delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doctype: dt, name: name })
  });
  APP_STATE = await res.json();
  window.APP_STATE = APP_STATE;
  if (dt === "SE Parametres Hotel") showWorkspace();
  else showList(dt);
  alert(`L'élément ${name} a été supprimé avec succès.`);
}

function closeModal() {
  document.getElementById("docModal").classList.remove("open");
}

loadState().then(() => showWorkspace());
</script>
</body>
</html>
"""


def render_print_html(db: dict, doctype: str, name: str) -> str:
    rows = db.get(doctype, [])
    doc = next((r for r in rows if r["name"] == name), None)
    if not doc:
        return "<h3>Document introuvable</h3>"
    cfg = db["SE Parametres Hotel"][0]

    if doctype in ("SE Facture Client", "SE Facture Pro Forma"):
        is_pro = (doctype == "SE Facture Pro Forma")
        cli = next((c for c in db.get("SE Client", []) if c.get("name") == doc.get("client") or c.get("nom_client") == doc.get("client") or c.get("ref_societe") == doc.get("client")), {})
        nom_client = cli.get("nom_client") or doc.get("client") or "Client Divers"
        ref_societe = cli.get("ref_societe") or cli.get("name") or doc.get("client") or "—" 
        sejours = doc.get("sejours") or []
        lignes = doc.get("lignes") or []
        
        stays_rows = ""
        if sejours:
            for s in sejours:
                pers = s.get('nb_personnes', 1)
                nuits = s.get('nuitees', 1)
                ts = s.get('taxe_sejour') if s.get('taxe_sejour') is not None else (float(pers) * float(nuits) * 500)
                stays_rows += f"""<tr>
                  <td style="padding:7px;border-bottom:1px solid #e2e8f0;"><b>Séjour #{s.get('sejour_no', 1)}</b> — {s.get('description', '')}</td>
                  <td style="padding:7px;border-bottom:1px solid #e2e8f0;text-align:center;">{s.get('date_arrivee', '')}</td>
                  <td style="padding:7px;border-bottom:1px solid #e2e8f0;text-align:center;">{s.get('date_depart', '')}</td>
                  <td style="padding:7px;border-bottom:1px solid #e2e8f0;text-align:center;font-weight:bold;">{nuits} nuit(s)</td>
                  <td style="padding:7px;border-bottom:1px solid #e2e8f0;text-align:center;font-weight:bold;">{pers} pers.</td>
                  <td style="padding:7px;border-bottom:1px solid #e2e8f0;text-align:right;color:#0369a1;font-weight:bold;">{float(ts):,.2f} DZD</td>
                  <td style="padding:7px;border-bottom:1px solid #e2e8f0;text-align:right;font-weight:bold;">{float(s.get('total_ttc_sejour') or 0):,.2f} DZD</td>
                </tr>"""

        lines_rows = ""
        for ln in lignes:
            qty = float(ln.get('quantite', 1) or 1)
            nuits = float(ln.get('nb_jours', 1) or 1)
            tot_ttc = float(ln.get('total_ligne_ttc') or 0)
            pu = float(ln.get('prix_unitaire_ttc') or (tot_ttc / max(1.0, qty * nuits)))
            lines_rows += f"""<tr>
              <td style="padding:8px;border-bottom:1px solid #e2e8f0;">
                <b>{ln.get('article', 'Prestation')}</b> ({ln.get('type_ligne', 'Hébergement')})
                {f'<span style="font-size:11px;color:#64748b;">[Séjour #{ln.get("sejour_no", 1)}]</span>' if len(sejours) > 1 else ''}
                {f'<div style="font-size:11px;color:#475569;margin-top:3px;font-style:italic;line-height:1.3;">📝 <b>Observation :</b> ' + str(ln.get('observation') or ln.get('obs') or ln.get('remarque') or '').replace('\n', '<br>') + '</div>' if (ln.get('observation') or ln.get('obs') or ln.get('remarque')) else ''}
              </td>
              <td style="padding:8px;border-bottom:1px solid #e2e8f0;text-align:right;">{pu:,.2f}</td>
              <td style="padding:8px;border-bottom:1px solid #e2e8f0;text-align:center;">{int(qty) if qty.is_integer() else qty}</td>
              <td style="padding:8px;border-bottom:1px solid #e2e8f0;text-align:center;">{int(nuits) if nuits.is_integer() else nuits}</td>
              <td style="padding:8px;border-bottom:1px solid #e2e8f0;text-align:right;">{float(ln.get('montant_ht') or 0):,.2f}</td>
              <td style="padding:8px;border-bottom:1px solid #e2e8f0;text-align:center;">{ln.get('taux_tva', 9)}%</td>
              <td style="padding:8px;border-bottom:1px solid #e2e8f0;text-align:right;">{float(ln.get('montant_tva') or 0):,.2f}</td>
              <td style="padding:8px;border-bottom:1px solid #e2e8f0;text-align:right;font-weight:bold;">{tot_ttc:,.2f}</td>
            </tr>"""

        return f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
        <title>{'FACTURE PRO FORMA' if is_pro else 'FACTURE CLIENT'} {doc['name']}</title>
        <style>
          body {{ font-family:'Segoe UI',Arial,sans-serif; color:#0f172a; max-width:880px; margin:20px auto; padding:24px; border:1px solid #cbd5e1; background:#fff; }}
          .hdr {{ display:flex; justify-content:space-between; border-bottom:3px solid #b45309; padding-bottom:14px; margin-bottom:18px; }}
          .grid {{ display:flex; gap:16px; margin-bottom:16px; }}
          .box {{ flex:1; border:1px solid #cbd5e1; border-radius:6px; padding:12px; background:#f8fafc; font-size:12px; }}
          table {{ width:100%; border-collapse:collapse; margin-bottom:14px; font-size:12px; }}
          th {{ background:#0f172a; color:#fff; padding:8px; text-align:left; }}
          .words {{ background:#fffbeb; border-left:4px solid #d97706; padding:12px; font-size:12.5px; margin:16px 0; }}
          @media print {{ .no-print {{ display:none; }} body {{ border:none; margin:0; padding:10px; }} }}
        </style></head><body>
        <div class="no-print" style="margin-bottom:14px;text-align:right;">
          <button onclick="window.print()" style="padding:8px 18px;background:#0f172a;color:#fff;border:none;border-radius:6px;cursor:pointer;font-weight:bold;">🖨️ Imprimer / Enregistrer en PDF</button>
        </div>
        <div class="hdr">
          <div style="display:flex;align-items:center;gap:18px;">
            <img src="{LOGO_BASE64_URI}" alt="Logo Hôtel Saint Eugène" style="max-height:72px;width:auto;object-fit:contain;">
            <div>
              <h1 style="margin:0;font-size:20px;color:#0f172a;letter-spacing:0.5px;">{cfg['raison_sociale']} <span style="font-size:13px;color:#64748b;font-weight:normal;">({cfg.get('forme_juridique', 'SARL')})</span> <span style="color:#d97706;">★★★★</span></h1>
              <div style="font-size:11.5px;color:#475569;margin-top:4px;line-height:1.4;">
                {cfg['adresse']}<br>
                Tél : {cfg['telephone']} | Réservations : {cfg.get('email_reservation') or cfg['email']}<br>
                <b>RC :</b> {cfg['rc']} | <b>NIF :</b> {cfg['nif']} | <b>NIS :</b> {cfg.get('nis', '001416170291741')} | <b>AI :</b> {cfg['article_imposition']}
              </div>
            </div>
          </div>
          <div style="text-align:right;">
            <h2 style="margin:0;color:#b45309;font-size:18px;">{'FACTURE PRO FORMA' if is_pro else 'FACTURE CLIENT OFFICIELLE'}</h2>
            <div style="font-size:12px;margin-top:4px;"><b>N° :</b> {doc['name']}</div>
            <div style="font-size:12px;"><b>Date :</b> {doc['date_facture']}</div>
            <div style="font-size:12px;"><b>{'Validité' if is_pro else 'Échéance'} :</b> {doc.get('date_validite' if is_pro else 'date_echeance', '—')}</div>
            <div style="font-size:12px;"><b>Statut :</b> {doc.get('statut', 'Validée')}</div>
          </div>
        </div>
        <div class="grid">
          <div class="box">
            <b style="color:#b45309;">FACTURÉ À (CLIENT) :</b><br>
            <b style="font-size:14px;color:#0f172a;">{nom_client}</b><br>
            <span style="font-size:12px;color:#475569;"><b>Référence Société :</b> {ref_societe} • <b>Type :</b> {doc.get('type_client', cli.get('type_client', 'Corporate'))}</span><br>
            {cli.get('adresse','')}<br>
            <b>RC :</b> {cli.get('rc','—')} | <b>NIF :</b> {cli.get('nif','—')}<br>
            <b>NIS :</b> {cli.get('nis','—')} | <b>AI :</b> {cli.get('article_imposition','—')}
          </div>
          <div class="box">
            <b style="color:#b45309;">MODALITÉS DU RÈGLEMENT :</b><br>
            <b>Mode prévu :</b> {doc.get('mode_paiement_prevu','Virement')}<br>
            <b>Réf. Dossier :</b> {doc.get('ref_devis' if is_pro else 'ref_reservation','—')}<br>
            <b>Taxe de séjour :</b> 500 DZD / nuitée / pers. (Hébergement 4★)<br>
            <b>Ventilation TVA :</b> {doc.get('detail_tva','Conforme SCF')}
          </div>
        </div>

        {f"""<div style="margin-bottom:12px;"><b style="font-size:12px;color:#0f172a;">Détail des Périodes & Séjours :</b>
        <table style="margin-top:4px;">
          <tr style="background:#f1f5f9;color:#334155;"><th>Désignation Séjour</th><th style="text-align:center;">Date Arrivée</th><th style="text-align:center;">Date Départ</th><th style="text-align:center;">Nuitées</th><th style="text-align:center;">Personnes</th><th style="text-align:right;">Taxe Séjour (500 DZD)</th><th style="text-align:right;">Total Séjour TTC</th></tr>
          {stays_rows}
        </table></div>""" if len(sejours) > 0 else ""}

        <b style="font-size:12px;color:#0f172a;">Détail des Prestations Hôtelières & Services :</b>
        <table style="margin-top:4px;">
          <thead>
            <tr><th>Prestation / Type de Chambre</th><th style="text-align:right;">Prix unitaire TTC</th><th style="text-align:center;">Qté (Ch.)</th><th style="text-align:center;">Nuitées</th><th style="text-align:right;">Base HT</th><th style="text-align:center;">TVA</th><th style="text-align:right;">Montant TVA</th><th style="text-align:right;">Total TTC</th></tr>
          </thead>
          <tbody>{lines_rows}</tbody>
        </table>

        <table style="width:55%;margin-left:auto;font-size:12.5px;">
          <tr><td>Total HT</td><td style="text-align:right;font-weight:bold;">{float(doc.get('montant_ht') or 0):,.2f} DZD</td></tr>
          <tr><td>TVA Collectée (9% / 19%)</td><td style="text-align:right;">{float(doc.get('montant_tva') or 0):,.2f} DZD</td></tr>
          <tr><td>Taxe de Séjour 4★ (500 DZD × pers. × nuits)</td><td style="text-align:right;color:#0369a1;">{float(doc.get('taxe_sejour') or 0):,.2f} DZD</td></tr>
          <tr style="border-top:1px solid #cbd5e1;"><td>Total TTC Saisi</td><td style="text-align:right;font-weight:bold;">{float(doc.get('total_ttc_saisi') or doc.get('montant_ttc') or 0):,.2f} DZD</td></tr>
          <tr><td>Droit de Timbre Fiscal (Espèces)</td><td style="text-align:right;">{float(doc.get('droit_timbre') or 0):,.2f} DZD</td></tr>
          <tr style="background:#0f172a;color:#fff;font-weight:bold;font-size:13px;"><td>NET À PAYER TTC (DZD)</td><td style="text-align:right;color:#fbbf24;">{float(doc.get('montant_ttc') or 0):,.2f} DZD</td></tr>
          {f"""<tr><td>Montant Encaissé</td><td style="text-align:right;color:#16a34a;font-weight:bold;">{float(doc.get('montant_encaisse') or 0):,.2f} DZD</td></tr>
          <tr><td><b>Reste à Encaisser</b></td><td style="text-align:right;color:#dc2626;font-weight:bold;">{float(doc.get('reste_a_encaisser') or 0):,.2f} DZD</td></tr>""" if not is_pro else ""}
        </table>

        <div class="words">Arrêtée la présente {'Facture Pro Forma' if is_pro else 'Facture'} à la somme de :<br><b>« {doc.get('montant_en_lettres','')} »</b></div>
        <div style="display:flex;justify-content:space-between;margin-top:20px;padding-top:10px;border-top:1px solid #cbd5e1;font-size:11px;color:#475569;">
          <div>
            <b>Banque :</b> {cfg.get('banque', "Crédit Populaire d'Algérie (CPA)")} — {cfg.get('agence_bancaire', 'CPA Bab El Oued')}<br>
            <b>Code Agence :</b> {cfg.get('code_agence', '175')} | <b>Compte Bancaire :</b> {cfg.get('compte_bancaire', '004 00175 4000261090 62')}<br>
            <b>Capital Social :</b> {cfg['capital_social']} | <b>Forme Juridique :</b> {cfg.get('forme_juridique', 'SARL')}
          </div>
          <div style="text-align:right;min-width:200px;">
            <b>Cachet & Signature Direction</b><br><br><br>
            <i>HOTEL SAINT EUGENE 4★ Alger</i>
          </div>
        </div>
        </body></html>"""

    return f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><title>{doc['name']}</title>
    <style>body{{font-family:'Segoe UI',sans-serif;max-width:780px;margin:24px auto;padding:24px;border:1px solid #cbd5e1;}}table{{width:100%;border-collapse:collapse;margin-top:16px;}}th,td{{border:1px solid #cbd5e1;padding:9px;text-align:left;}}th{{background:#f1f5f9;width:45%;}}</style></head>
    <body><button onclick="window.print()" style="float:right;padding:7px 14px;background:#0f172a;color:#fff;border:none;border-radius:6px;cursor:pointer;">🖨️ Imprimer PDF</button>
    <h2>{doctype} — {doc['name']}</h2><p>{cfg['raison_sociale']} ({cfg['adresse']})</p>
    <table>{''.join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in doc.items())}</table></body></html>"""


class SaintEugeneHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path.endswith(".js"):
            js_file = APP_ROOT / parsed.path.lstrip("/")
            if js_file.exists():
                self.send_response(200)
                self.send_header("Content-Type", "application/javascript; charset=utf-8")
                self.end_headers()
                self.wfile.write(js_file.read_bytes())
                return
        if parsed.path == "/api/state":
            db = get_db()
            payload = {"schemas": SCHEMAS, "db": db, "dashboard": compute_dashboard_payload(db)}
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
            return

        if parsed.path == "/print":
            qs = urllib.parse.parse_qs(parsed.query)
            dt = qs.get("doctype", [""])[0]
            nm = qs.get("name", [""])[0]
            html = render_print_html(get_db(), dt, nm).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html)
            return

        body = HTML_INDEX.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path == "/api/delete":
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            dt = data["doctype"]
            name = data["name"]
            db = get_db()
            rows = db.setdefault(dt, [])
            db[dt] = [r for r in rows if r.get("name") != name]
            save_db(db)
            payload = {"schemas": SCHEMAS, "db": db, "dashboard": compute_dashboard_payload(db)}
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path == "/api/save":
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            dt = data["doctype"]
            doc = data["doc"]
            db = get_db()
            rows = db.setdefault(dt, [])
            existing_idx = next((i for i, r in enumerate(rows) if r.get("name") == doc.get("name")), None)
            if existing_idx is not None:
                rows[existing_idx] = doc
            else:
                rows.insert(0, doc)
            save_db(db)
            payload = {"schemas": SCHEMAS, "db": db, "dashboard": compute_dashboard_payload(db)}
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(body)


def main():
    port = 8080
    import socket
    def _get_lan_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.254.254.254', 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    lan_ip = _get_lan_ip()
    server = HTTPServer(("0.0.0.0", port), SaintEugeneHandler)
    url_lan = f"http://{lan_ip}:{port}" 
    url = f"http://localhost:{port}"
    print(f"==================================================================")
    print(f" Saint Eugène ERP 2026 est actif sur PC  : {url}")
    print(f" Accès direct depuis votre Téléphone (Wi-Fi) : {url_lan}")
    print(f"==================================================================")
    if "--no-browser" not in sys.argv:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    server.serve_forever()


if __name__ == "__main__":
    main()
