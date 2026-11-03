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

    # Factures Clients & Encaissements
    factures_seed = [
        ("FAC-CLI-2026-00001", "2026-01-12", "2026-02-11", "SONATRACH - Direction Générale Hydra", "Corporate", "Hébergement", "SE-RES-2026-001", "2026-01-05", "2026-01-12", 7, 12, 1, "Virement", 4200000.0, 9.0, ("ENC-2026-00001", "2026-01-28", "FULL", "Virement", "BNA Agence Bologhine - DZD", "VIR-SNT-2601")),
        ("FAC-CLI-2026-00002", "2026-01-20", "2026-01-20", "Client Passager Comptoir (Walk-in)", "Passager", "Hébergement", "SE-RES-2026-002", "2026-01-18", "2026-01-20", 2, 4, 1, "Espèces", 285000.0, 9.0, ("ENC-2026-00002", "2026-01-20", "FULL", "Espèces", "Caisse Principale Hôtel", "CAISSE-JAN-01")),
        ("FAC-CLI-2026-00003", "2026-01-25", "2026-02-24", "ATM Mobilis - Direction Régionale Alger", "Corporate", "Restauration", "SE-RES-2026-003", "", "", 1, 1, 0, "Virement", 2450000.0, 9.0, ("ENC-2026-00003", "2026-02-10", "FULL", "Virement", "BEA Alger Centre - DZD", "VIR-MOB-2602")),
        ("FAC-CLI-2026-00004", "2026-02-14", "2026-12-15", "COSIDER Groupe Spa", "Corporate", "Hébergement", "SE-RES-2026-004", "2026-02-10", "2026-02-14", 4, 10, 1, "Chèque", 4900000.0, 9.0, ("ENC-2026-00004", "2026-02-22", 2500000.0, "Chèque", "BNA Agence Bologhine - DZD", "CHQ-COS-884120")),
        ("FAC-CLI-2026-00005", "2026-02-20", "2026-03-07", "Touring Club d'Algérie (Agence)", "Agence", "Restauration", "SE-RES-2026-005", "", "", 1, 1, 0, "TPE", 2750000.0, 9.0, ("ENC-2026-00005", "2026-02-26", "FULL", "TPE", "CPA Bab El Oued - DZD", "TPE-CIB-9921")),
        ("FAC-CLI-2026-00006", "2026-03-05", "2026-04-19", "Air Algérie - Direction des Opérations", "Corporate", "Hébergement", "SE-RES-2026-006", "2026-03-01", "2026-03-05", 4, 15, 1, "Virement", 3850000.0, 9.0, None),
        ("FAC-CLI-2026-00007", "2026-03-18", "2026-12-28", "SONATRACH - Direction Générale Hydra", "Corporate", "Séminaires & Banquets", "SE-RES-2026-007", "", "", 1, 1, 0, "Virement", 2900000.0, 19.0, None),
    ]

    for fname, dfac, dech, cli, tcli, nat, ref, darr, ddep, nuits, adultes, app_ts, mode, ht, tva_r, enc in factures_seed:
        tva = round(ht * tva_r / 100.0, 2)
        ts = compute_taxe_sejour_algerie(nat, app_ts, adultes, nuits, 400.0)
        timbre = compute_droit_timbre_algerie(ht + tva + ts, mode, 1, 0.0)
        ttc = round(ht + tva + ts + timbre, 2)
        db["SE Facture Client"].append(
            {
                "name": fname,
                "date_facture": dfac,
                "date_echeance": dech,
                "client": cli,
                "type_client": tcli,
                "nature_prestation": nat,
                "ref_reservation": ref,
                "date_arrivee": darr,
                "date_depart": ddep,
                "nuitees": nuits,
                "nb_adultes": adultes,
                "appliquer_taxe_sejour": app_ts,
                "mode_paiement_prevu": mode,
                "montant_ht": ht,
                "taux_tva": tva_r,
                "montant_tva": tva,
                "taxe_sejour": ts,
                "droit_timbre": timbre,
                "montant_ttc": ttc,
                "montant_en_lettres": montant_dzd_en_lettres(ttc),
                "montant_encaisse": 0.0,
                "reste_a_encaisser": ttc,
                "statut": "Validée",
                "jours_retard": 0,
                "docstatus": 1,
            }
        )
        if enc:
            ename, denc, mnt_raw, emode, ecpte, eref = enc
            emnt = ttc if mnt_raw == "FULL" else float(mnt_raw)
            db["SE Encaissement"].append(
                {
                    "name": ename,
                    "date_encaissement": denc,
                    "client": cli,
                    "facture_liee": fname,
                    "montant": emnt,
                    "mode_paiement": emode,
                    "compte_destination": ecpte,
                    "ref_paiement": eref,
                    "statut_cheque": "En portefeuille (Non encaissé)" if emode == "Chèque" else "N/A",
                    "statut": "Validé",
                    "docstatus": 1,
                }
            )

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
    return db


def recompute_all_links(db: dict) -> None:
    """Exécute tous les recalculs automatiques (Factures, Comptes Trésorerie, Opérations Bancaires, Budget 2026, Prévisions)."""
    today_str = "2026-11-03"

    # 1. Factures Clients
    for fac in db["SE Facture Client"]:
        ht = float(fac.get("montant_ht") or 0)
        tva_r = float(fac.get("taux_tva") or 9)
        tva = round(ht * tva_r / 100.0, 2)
        nat = fac.get("nature_prestation") or "Hébergement"
        app_ts = int(fac.get("appliquer_taxe_sejour", 1 if nat == "Hébergement" else 0))
        nuits = max(1, int(fac.get("nuitees") or 1))
        adultes = max(1, int(fac.get("nb_adultes") or 1))
        mode = fac.get("mode_paiement_prevu") or "Virement"
        ts = compute_taxe_sejour_algerie(nat, app_ts, adultes, nuits, 400.0)
        timbre = compute_droit_timbre_algerie(ht + tva + ts, mode, 1, 0.0)
        ttc = round(ht + tva + ts + timbre, 2)
        fac["montant_tva"] = tva
        fac["taxe_sejour"] = ts
        fac["droit_timbre"] = timbre
        fac["montant_ttc"] = ttc
        fac["montant_en_lettres"] = montant_dzd_en_lettres(ttc)

        enc_sum = round(
            sum(
                float(e.get("montant") or 0)
                for e in db["SE Encaissement"]
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
            return json.loads(DB_FILE.read_text(encoding="utf-8"))
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
  .modal { background: #fff; border-radius: 12px; width: 100%; max-width: 860px; max-height: 90vh; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.25); }
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
      <button class="btn btn-primary" onclick="openNewDoc('SE Encaissement')">+ Nouvel Encaissement</button>
    </div>
  </header>

  <div class="content" id="mainContent"></div>
</section>

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
let APP_STATE = { schemas: {}, db: {}, dashboard: {} };
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
    title: "Fiscalité G50, RH & Patrimoine",
    items: [
      { label: "🏛️ Déclarations TVA (G50)", doctype: "SE Declaration TVA" },
      { label: "🎯 Budget Annuel 2026", doctype: "SE Budget Annuel" },
      { label: "👥 Fiches de Paie (CNAS / IRG)", doctype: "SE Fiche de Paie Mensuelle" },
      { label: "🪪 Collaborateurs Hôtel", doctype: "SE Employe" },
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
  const orange = ["Partielle", "Non pointé", "Sous-Performance", "Sous Tension", "En attente signature DAF", "À renouveler (< 30j)", "Déclarée (G50)"];
  const red = ["Impayée", "Échue", "Dépassement", "Critique", "Avec Écart", "Rejetée", "Expiré", "En retard", "Annulée", "Annulé"];
  if (green.includes(st)) return "green";
  if (orange.includes(st)) return "orange";
  if (red.includes(st)) return "red";
  return "gray";
}

async function loadState() {
  const res = await fetch("/api/state");
  APP_STATE = await res.json();
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
      const count = item.doctype && APP_STATE.db[item.doctype] ? APP_STATE.db[item.doctype].length : "";
      const active = activeKey === key ? "active" : "";
      const fn = item.doctype ? `showList('${item.doctype}')` : `showWorkspace()`;
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

  let thHtml = `<th>Référence (ID)</th>` + listFields.map(f => `<th>${f.label}</th>`).join("");
  let trHtml = filtered.map(r => {
    let tds = `<td><b>${r.name}</b></td>`;
    listFields.forEach(f => {
      let val = r[f.fieldname];
      if (f.fieldtype === "Currency") {
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

function renderDocModal(doctype, doc, isNew) {
  CURRENT_DOCTYPE = doctype;
  CURRENT_DOC = doc;
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
  let ftrHtml = `<div>`;
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
  closeModal();
  if (CURRENT_DOCTYPE === "SE Parametres Hotel") showWorkspace();
  else showList(CURRENT_DOCTYPE);
}

function openPrintPreview(doctype, name) {
  window.open(`/print?doctype=${encodeURIComponent(doctype)}&name=${encodeURIComponent(name)}`, "_blank");
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

    if doctype == "SE Facture Client":
        cli = next((c for c in db["SE Client"] if c["name"] == doc.get("client")), {})
        return f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><title>Facture {doc['name']}</title>
        <style>
          body {{ font-family:'Segoe UI',Arial,sans-serif; color:#0f172a; max-width:820px; margin:24px auto; padding:24px; border:1px solid #cbd5e1; }}
          .hdr {{ display:flex; justify-content:space-between; border-bottom:3px solid #b45309; padding-bottom:14px; margin-bottom:18px; }}
          .grid {{ display:flex; gap:18px; margin-bottom:18px; }}
          .box {{ flex:1; border:1px solid #cbd5e1; border-radius:6px; padding:12px; background:#f8fafc; font-size:12.5px; }}
          table {{ width:100%; border-collapse:collapse; margin-bottom:16px; font-size:13px; }}
          th {{ background:#0f172a; color:#fff; padding:9px; text-align:left; }}
          td {{ padding:9px; border-bottom:1px solid #e2e8f0; }}
          .words {{ background:#fffbeb; border-left:4px solid #d97706; padding:12px; font-size:13px; margin:18px 0; }}
          @media print {{ .no-print {{ display:none; }} body {{ border:none; margin:0; }} }}
        </style></head><body>
        <div class="no-print" style="margin-bottom:14px;text-align:right;"><button onclick="window.print()" style="padding:8px 16px;background:#0f172a;color:#fff;border:none;border-radius:6px;cursor:pointer;">🖨️ Imprimer / Enregistrer en PDF</button></div>
        <div class="hdr">
          <div>
            <h1 style="margin:0;font-size:21px;">{cfg['raison_sociale']} <span style="color:#d97706;">★★★★</span></h1>
            <div style="font-size:11.5px;color:#475569;margin-top:4px;">
              {cfg['adresse']}<br>Tél : {cfg['telephone']} | Email : {cfg['email']}<br>
              <b>RC :</b> {cfg['rc']} | <b>NIF :</b> {cfg['nif']} | <b>NIS :</b> {cfg['nis']} | <b>AI :</b> {cfg['article_imposition']}
            </div>
          </div>
          <div style="text-align:right;">
            <h2 style="margin:0;color:#b45309;">FACTURE SCF</h2>
            <div><b>N° :</b> {doc['name']}</div>
            <div><b>Date :</b> {doc['date_facture']}</div>
            <div><b>Échéance :</b> {doc['date_echeance']}</div>
            <div><b>Statut :</b> {doc['statut']}</div>
          </div>
        </div>
        <div class="grid">
          <div class="box">
            <b>FACTURÉ À :</b><br><b>{doc['client']}</b> ({doc.get('type_client','')})<br>
            {cli.get('adresse','')}<br>
            <b>RC :</b> {cli.get('rc','—')} | <b>NIF :</b> {cli.get('nif','—')}<br>
            <b>NIS :</b> {cli.get('nis','—')} | <b>AI :</b> {cli.get('article_imposition','—')}
          </div>
          <div class="box">
            <b>DÉTAILS DU SÉJOUR :</b><br>
            <b>Prestation :</b> {doc['nature_prestation']}<br>
            <b>Réf. Réservation :</b> {doc.get('ref_reservation','—')}<br>
            <b>Nuitées / Occupants :</b> {doc.get('nuitees',1)} nuit(s) / {doc.get('nb_adultes',1)} adulte(s)<br>
            <b>Mode de règlement :</b> {doc.get('mode_paiement_prevu','Virement')}
          </div>
        </div>
        <table>
          <thead><tr><th>Désignation</th><th style="text-align:center;">Nuitées</th><th style="text-align:right;">TVA</th><th style="text-align:right;">Montant HT (DZD)</th></tr></thead>
          <tbody><tr><td><b>{doc['nature_prestation']}</b> — Hôtel Saint Eugène 4★ Alger</td><td style="text-align:center;">{doc.get('nuitees',1)}</td><td style="text-align:right;">{doc['taux_tva']} %</td><td style="text-align:right;">{doc['montant_ht']:,.2f} DZD</td></tr></tbody>
        </table>
        <table style="width:55%;margin-left:auto;">
          <tr><td>Total HT</td><td style="text-align:right;"><b>{doc['montant_ht']:,.2f} DZD</b></td></tr>
          <tr><td>TVA ({doc['taux_tva']} %)</td><td style="text-align:right;">{doc['montant_tva']:,.2f} DZD</td></tr>
          <tr><td>Taxe de Séjour 4★ (400 DZD × pers. × nuits)</td><td style="text-align:right;">{doc.get('taxe_sejour',0):,.2f} DZD</td></tr>
          <tr><td>Droit de Timbre Fiscal (Espèces)</td><td style="text-align:right;">{doc.get('droit_timbre',0):,.2f} DZD</td></tr>
          <tr style="background:#0f172a;color:#fff;font-weight:bold;"><td>NET À PAYER TTC (DZD)</td><td style="text-align:right;">{doc['montant_ttc']:,.2f} DZD</td></tr>
          <tr><td>Montant Encaissé</td><td style="text-align:right;">{doc['montant_encaisse']:,.2f} DZD</td></tr>
          <tr><td><b>Reste à Encaisser</b></td><td style="text-align:right;"><b>{doc['reste_a_encaisser']:,.2f} DZD</b></td></tr>
        </table>
        <div class="words">Arrêtée la présente facture à la somme de :<br><b>« {doc.get('montant_en_lettres','')} »</b></div>
        <div style="font-size:11.5px;color:#475569;"><b>RIB :</b> {cfg['rib_principal']} | <b>Capital Social :</b> {cfg['capital_social']}</div>
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
    server = HTTPServer(("127.0.0.1", port), SaintEugeneHandler)
    url = f"http://localhost:{port}"
    print(f"==================================================================")
    print(f" Saint Eugène ERP 2026 est actif sur : {url}")
    print(f"==================================================================")
    if "--no-browser" not in sys.argv:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    server.serve_forever()


if __name__ == "__main__":
    main()
