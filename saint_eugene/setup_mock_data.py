# -*- coding: utf-8 -*-
"""
Script de Simulation & Données Réalistes — Hôtel Saint Eugène 4★ (Alger) — Exercice 2026
Exécution :
    bench --site sainteugene.localhost execute saint_eugene.setup_mock_data.run

Injecte de manière idempotente :
- Comptes de Trésorerie (Caisse Principale, Caisse Réception, BNA Bologhine, BEA Alger, CPA Bab El Oued)
- Clients Corporate Algériens (Sonatrach, Air Algérie, ATM Mobilis, Cosider, Touring Club d'Algérie, Passagers)
- Fournisseurs Hôteliers (Grossiste F&B, Sonelgaz, SEAAL, Algérie Télécom, Blanchisserie, Maintenance CVC)
- Effectif Hôtelier (8 collaborateurs clés) & Fiches de Paie 2026 (CNAS 9% + IRG Algérie)
- Budget Annuel 2026 (12 mois x 5 catégories = 60 lignes budgétaires)
- Factures Clients (Payées, Partielles -> Orange, Échues -> Rouge, Validées -> Vert) & Encaissements
- Factures Fournisseurs, Charges & Décaissements
- PV de Caisse Mensuelle, Rapprochement Bancaire BNA avec suspens, Déclarations TVA G50
- Performances Hôtelières (84 chambres : Occupation, ADR, RevPAR), Immobilisations SCF, Emprunt CPA, Contrats & Prévisions Trésorerie
"""
from __future__ import annotations

import frappe
from frappe.utils import flt

from saint_eugene.api.budget_engine import refresh_all_budgets_2026
from saint_eugene.api.dashboard import compute_caisse_totals
from saint_eugene.tasks.daily import (
    run_daily_financial_alerts,
    update_overdue_invoices_and_contracts,
)
from saint_eugene.utils.fiscal_dz import DEFAULT_SETTINGS


def setup_hotel_settings() -> None:
    if frappe.db.exists("DocType", "SE Parametres Hotel"):
        doc = frappe.get_single("SE Parametres Hotel")
        for k, v in DEFAULT_SETTINGS.items():
            if hasattr(doc, k) and not getattr(doc, k, None):
                setattr(doc, k, v)
        doc.save(ignore_permissions=True)


def _insert_if_missing(doctype: str, filters: dict, payload: dict, submit: bool = False):
    existing = frappe.db.exists(doctype, filters)
    if existing:
        return frappe.get_doc(doctype, existing)
    doc = frappe.get_doc({"doctype": doctype, **payload})
    doc.insert(ignore_permissions=True)
    if submit and doc.meta.is_submittable:
        doc.submit()
    return doc


def setup_treasury_accounts() -> None:
    comptes = [
        {
            "nom_compte": "Caisse Principale Hôtel",
            "type_compte": "Caisse",
            "compte_scf": "531000",
            "solde_initial": 850_000.0,
        },
        {
            "nom_compte": "Caisse Réception & Restaurant",
            "type_compte": "Caisse",
            "compte_scf": "532000",
            "solde_initial": 320_000.0,
        },
        {
            "nom_compte": "BNA Agence Bologhine - DZD",
            "type_compte": "Banque",
            "banque": "Banque Nationale d'Algérie (BNA)",
            "numero_compte_rib": "00100614030001458921",
            "compte_scf": "512100",
            "solde_initial": 14_500_000.0,
        },
        {
            "nom_compte": "BEA Alger Centre - DZD",
            "type_compte": "Banque",
            "banque": "Banque Extérieure d'Algérie (BEA)",
            "numero_compte_rib": "00200012020008874105",
            "compte_scf": "512200",
            "solde_initial": 8_200_000.0,
        },
        {
            "nom_compte": "CPA Bab El Oued - DZD",
            "type_compte": "Banque",
            "banque": "Crédit Populaire d'Algérie (CPA)",
            "numero_compte_rib": "00400108401005593214",
            "compte_scf": "512300",
            "solde_initial": 4_100_000.0,
        },
    ]
    for c in comptes:
        _insert_if_missing("SE Compte Tresorerie", {"nom_compte": c["nom_compte"]}, c)


def setup_clients_and_suppliers() -> None:
    clients = [
        {
            "nom_client": "SONATRACH - Direction Générale Hydra",
            "type_client": "Corporate",
            "delai_paiement_jours": 30,
            "nif": "000016001245871",
            "nis": "0998160100452",
            "rc": "16/00-0012458B00",
            "article_imposition": "16120145879",
            "telephone": "+213 23 48 30 00",
            "adresse": "Djenane El Malik, Hydra, Alger",
        },
        {
            "nom_client": "Air Algérie - Direction des Opérations",
            "type_client": "Corporate",
            "delai_paiement_jours": 45,
            "nif": "000016001874512",
            "rc": "16/00-0021547B00",
            "telephone": "+213 21 98 63 63",
            "adresse": "1 Place Maurice Audin, Alger Centre",
        },
        {
            "nom_client": "ATM Mobilis - Direction Régionale Alger",
            "type_client": "Corporate",
            "delai_paiement_jours": 30,
            "nif": "000316096514203",
            "rc": "16/00-0965142B03",
            "telephone": "+213 23 92 10 00",
            "adresse": "Quartier d'Affaires Bab Ezzouar, Alger",
        },
        {
            "nom_client": "COSIDER Groupe Spa",
            "type_client": "Corporate",
            "delai_paiement_jours": 30,
            "nif": "000016004512398",
            "rc": "16/00-0045123B00",
            "telephone": "+213 23 53 40 40",
            "adresse": "Route de Dar El Beïda, Alger",
        },
        {
            "nom_client": "Touring Club d'Algérie (Agence)",
            "type_client": "Agence",
            "delai_paiement_jours": 15,
            "nif": "000116007891204",
            "rc": "16/00-0078912B01",
            "telephone": "+213 21 73 42 15",
            "adresse": "Rue Hassiba Ben Bouali, Alger",
        },
        {
            "nom_client": "Client Passager Comptoir (Walk-in)",
            "type_client": "Passager",
            "delai_paiement_jours": 0,
            "adresse": "Réception Hôtel Saint Eugène, Alger",
        },
    ]
    for cl in clients:
        _insert_if_missing("SE Client", {"nom_client": cl["nom_client"]}, cl)

    fournisseurs = [
        {
            "nom_fournisseur": "Sarl El Djazaïr Food & Beverage Pro",
            "categorie": "Alimentation & Boissons (F&B)",
            "nif": "001216088451209",
            "rc": "16/00-0884512B12",
            "rib": "00100614030009988776",
            "telephone": "+213 23 81 12 45",
        },
        {
            "nom_fournisseur": "SONELGAZ - Direction Distribution Bologhine",
            "categorie": "Énergie & Eau (Sonelgaz/SEAAL)",
            "nif": "000016000112233",
        },
        {
            "nom_fournisseur": "SEAAL - Eau et Assainissement d'Alger",
            "categorie": "Énergie & Eau (Sonelgaz/SEAAL)",
            "nif": "000616000445566",
        },
        {
            "nom_fournisseur": "Algérie Télécom Entreprises (Fibre Pro)",
            "categorie": "Télécom & IT",
            "nif": "000216000778899",
        },
        {
            "nom_fournisseur": "Blanchisserie Hôtelière de la Baie Spa",
            "categorie": "Produits d'Accueil & Linge",
            "nif": "001516077412365",
            "rib": "00400108401007741236",
        },
        {
            "nom_fournisseur": "Eurl Maghreb Ascenseurs & Climatisation CVC",
            "categorie": "Maintenance & Technique",
            "nif": "001416055321478",
            "rib": "00200012020005532147",
        },
    ]
    for frn in fournisseurs:
        _insert_if_missing("SE Fournisseur", {"nom_fournisseur": frn["nom_fournisseur"]}, frn)


def setup_employees_and_payroll() -> None:
    employes_data = [
        ("Karim Benali", "Directeur d'Exploitation", "Direction & Administration", 185_000.0),
        ("Amel Mansouri", "Chef Comptable SCF", "Direction & Administration", 125_000.0),
        ("Yacine Khelifi", "Chef de Réception", "Réception & Hébergement", 92_000.0),
        ("Nadia Boudiaf", "Gouvernante Générale", "Étages & Housekeeping", 85_000.0),
        ("Mourad Zerrouki", "Chef Exécutif Cuisine", "Restauration & Cuisine", 135_000.0),
        ("Sofiane Meziane", "Maître d'Hôtel", "Restauration & Cuisine", 78_000.0),
        ("Rachid Hamidi", "Responsable Technique & CVC", "Maintenance & Sécurité", 88_000.0),
        ("Meriem Saïdi", "Réceptionniste Bilingue", "Réception & Hébergement", 58_000.0),
    ]
    emp_ids = []
    for nom, fct, dept, base in employes_data:
        existing_name = frappe.db.get_value("SE Employe", {"nom_complet": nom}, "name")
        if existing_name:
            emp_ids.append((existing_name, base))
        else:
            doc = frappe.get_doc(
                {
                    "doctype": "SE Employe",
                    "nom_complet": nom,
                    "fonction": fct,
                    "departement": dept,
                    "salaire_base": base,
                    "date_embauche": "2023-03-01",
                    "statut": "Actif",
                }
            ).insert(ignore_permissions=True)
            emp_ids.append((doc.name, base))

    # Génération des fiches de paie validées sur T1 2026 (2026-01 à 2026-03)
    for mois in ("2026-01", "2026-02", "2026-03"):
        for emp_id, base in emp_ids:
            _insert_if_missing(
                "SE Fiche de Paie Mensuelle",
                {"mois": mois, "employe": emp_id},
                {
                    "mois": mois,
                    "employe": emp_id,
                    "salaire_base": base,
                    "primes": round(base * 0.10, 2),
                    "indemnites": 6_500.0,
                    "auto_calcul_irg": 1,
                    "mode_paiement": "Virement",
                    "ref_paiement": f"VIR-PAIE-{mois}-{emp_id}",
                },
                submit=True,
            )


def setup_annual_budget_2026() -> None:
    """Crée les 60 lignes budgétaires (12 mois x 5 postes) avec saisonnalité hôtelière Alger."""
    saison_coef = {
        1: 0.90, 2: 0.95, 3: 0.85, 4: 1.00, 5: 1.10, 6: 1.20,
        7: 1.25, 8: 1.20, 9: 1.15, 10: 1.10, 11: 1.00, 12: 1.05,
    }
    bases = {
        "CA Hébergement": 6_800_000.0,
        "CA Restauration": 2_600_000.0,
        "Salaires": 1_050_000.0,
        "Achats": 1_450_000.0,
        "Charges": 750_000.0,
    }
    for m in range(1, 13):
        mois = f"2026-{m:02d}"
        coef = saison_coef[m]
        for cat, base_val in bases.items():
            prevu = round(base_val * (coef if "CA" in cat or cat == "Achats" else 1.0), -3)
            _insert_if_missing(
                "SE Budget Annuel",
                {"mois": mois, "categorie": cat},
                {"mois": mois, "categorie": cat, "budget_prevu": prevu},
            )


def setup_invoices_payments_and_expenses() -> None:
    # Factures Clients T1 2026 (avec cas Payée, Partielle [Orange], Échue [Rouge], Validée [Vert])
    factures_spec = [
        # Janvier 2026 - Payées (Virement Corporate + Espèces Comptoir avec Droit de Timbre & Taxe Séjour 4★)
        {
            "ref_reservation": "SE-RES-2026-001",
            "date_facture": "2026-01-12",
            "date_echeance": "2026-02-11",
            "client": "SONATRACH - Direction Générale Hydra",
            "nature_prestation": "Hébergement",
            "date_arrivee": "2026-01-05",
            "date_depart": "2026-01-12",
            "nb_adultes": 12,
            "appliquer_taxe_sejour": 1,
            "mode_paiement_prevu": "Virement",
            "montant_ht": 4_200_000.0,
            "taux_tva": 9.0,
            "encaissement": ("2026-01-28", "FULL", "Virement", "BNA Agence Bologhine - DZD", "VIR-SNT-2601"),
        },
        {
            "ref_reservation": "SE-RES-2026-002",
            "date_facture": "2026-01-20",
            "date_echeance": "2026-01-20",
            "client": "Client Passager Comptoir (Walk-in)",
            "nature_prestation": "Hébergement",
            "date_arrivee": "2026-01-18",
            "date_depart": "2026-01-20",
            "nb_adultes": 4,
            "appliquer_taxe_sejour": 1,
            "mode_paiement_prevu": "Espèces",
            "montant_ht": 285_000.0,
            "taux_tva": 9.0,
            "encaissement": ("2026-01-20", "FULL", "Espèces", "Caisse Principale Hôtel", "CAISSE-JAN-01"),
        },
        {
            "ref_reservation": "SE-RES-2026-003",
            "date_facture": "2026-01-25",
            "date_echeance": "2026-02-24",
            "client": "ATM Mobilis - Direction Régionale Alger",
            "nature_prestation": "Restauration",
            "mode_paiement_prevu": "Virement",
            "montant_ht": 2_450_000.0,
            "taux_tva": 9.0,
            "encaissement": ("2026-02-10", "FULL", "Virement", "BEA Alger Centre - DZD", "VIR-MOB-2602"),
        },
        # Février 2026 - Dont 1 Partielle et 1 Chèque en portefeuille non encaissé (> 7j)
        {
            "ref_reservation": "SE-RES-2026-004",
            "date_facture": "2026-02-14",
            "date_echeance": "2026-12-15",
            "client": "COSIDER Groupe Spa",
            "nature_prestation": "Hébergement",
            "date_arrivee": "2026-02-10",
            "date_depart": "2026-02-14",
            "nb_adultes": 10,
            "appliquer_taxe_sejour": 1,
            "mode_paiement_prevu": "Chèque",
            "montant_ht": 4_900_000.0,
            "taux_tva": 9.0,
            "encaissement": ("2026-02-22", 2_500_000.0, "Chèque", "BNA Agence Bologhine - DZD", "CHQ-COS-884120"),
        },
        {
            "ref_reservation": "SE-RES-2026-005",
            "date_facture": "2026-02-20",
            "date_echeance": "2026-03-07",
            "client": "Touring Club d'Algérie (Agence)",
            "nature_prestation": "Restauration",
            "mode_paiement_prevu": "TPE",
            "montant_ht": 2_750_000.0,
            "taux_tva": 9.0,
            "encaissement": ("2026-02-26", "FULL", "TPE", "CPA Bab El Oued - DZD", "TPE-CIB-9921"),
        },
        # Mars 2026 - Dont 1 Facture ÉCHUE (Impayée > échéance -> Badge Rouge + Alerte !)
        {
            "ref_reservation": "SE-RES-2026-006",
            "date_facture": "2026-03-05",
            "date_echeance": "2026-04-19",
            "client": "Air Algérie - Direction des Opérations",
            "nature_prestation": "Hébergement",
            "montant_ht": 3_850_000.0,
            "taux_tva": 9.0,
            "encaissement": None,  # Impayée échue !
        },
        {
            "ref_reservation": "SE-RES-2026-007",
            "date_facture": "2026-03-18",
            "date_echeance": "2026-12-28",
            "client": "SONATRACH - Direction Générale Hydra",
            "nature_prestation": "Séminaires & Banquets",
            "montant_ht": 2_900_000.0,
            "taux_tva": 19.0,
            "encaissement": None,  # Validée non échue -> Vert !
        },
    ]

    for spec in factures_spec:
        enc_info = spec.pop("encaissement")
        fac = _insert_if_missing(
            "SE Facture Client",
            {"ref_reservation": spec["ref_reservation"]},
            spec,
            submit=True,
        )
        if enc_info:
            dt_enc, mnt, mode, cpte, ref_p = enc_info
            montant_enc = flt(fac.montant_ttc) if mnt == "FULL" else flt(mnt)
            _insert_if_missing(
                "SE Encaissement",
                {"ref_paiement": ref_p},
                {
                    "date_encaissement": dt_enc,
                    "client": fac.client,
                    "facture_liee": fac.name,
                    "montant": montant_enc,
                    "mode_paiement": mode,
                    "compte_destination": cpte,
                    "ref_paiement": ref_p,
                    "statut_cheque": "En portefeuille (Non encaissé)" if mode == "Chèque" else "N/A",
                },
                submit=True,
            )

    # Factures Fournisseurs & Décaissements
    frn_specs = [
        (
            "FF-2026-0101",
            "Sarl El Djazaïr Food & Beverage Pro",
            "2026-01-10",
            "2026-02-10",
            "Approvisionnement viandes, poissons frais & épicerie fine Restaurant",
            1_320_000.0,
            ("2026-01-29", 1_570_800.0, "Virement", "BNA Agence Bologhine - DZD", "VIR-FRN-0101"),
        ),
        (
            "FF-2026-0204",
            "Blanchisserie Hôtelière de la Baie Spa",
            "2026-02-12",
            "2026-03-12",
            "Traitement & repassage linge chambres 4★ - Février 2026",
            640_000.0,
            ("2026-02-25", 400_000.0, "Chèque", "BNA Agence Bologhine - DZD", "CHQ-BNA-45012"),
        ),
        (
            "FF-2026-0309",
            "Sarl El Djazaïr Food & Beverage Pro",
            "2026-03-08",
            "2026-04-08",
            "Denrées alimentaires & boissons - Banquets Mars 2026",
            1_280_000.0,
            None,
        ),
    ]
    for num_ff, frn, d_fac, d_ech, obj, ht, dec_info in frn_specs:
        ff = _insert_if_missing(
            "SE Facture Fournisseur",
            {"numero_facture_fournisseur": num_ff},
            {
                "numero_facture_fournisseur": num_ff,
                "fournisseur": frn,
                "date_facture": d_fac,
                "date_echeance": d_ech,
                "objet": obj,
                "montant_ht": ht,
                "taux_tva": 19.0,
            },
            submit=True,
        )
        if dec_info:
            dt_dec, mnt, mode, cpte, ref_d = dec_info
            _insert_if_missing(
                "SE Decaissement",
                {"ref_paiement": ref_d},
                {
                    "date_decaissement": dt_dec,
                    "type_beneficiaire": "Fournisseur",
                    "fournisseur": frn,
                    "beneficiaire": frn,
                    "facture_liee": ff.name,
                    "motif": obj,
                    "montant": mnt,
                    "mode_paiement": mode,
                    "compte_source": cpte,
                    "ref_paiement": ref_d,
                    "validation_daf": 1,
                },
                submit=True,
            )

    # Décaissement espèces sur Caisse Principale pour tester SE Caisse Mensuelle Janvier 2026
    _insert_if_missing(
        "SE Decaissement",
        {"ref_paiement": "BON-CAISSE-2601-01"},
        {
            "date_decaissement": "2026-01-22",
            "type_beneficiaire": "Autre Bénéficiaire",
            "beneficiaire": "Régie Achats Urgents Cuisine & Réception",
            "motif": "Fleurs hall, courses fraîches marché & fournitures accueil",
            "montant": 145_000.0,
            "mode_paiement": "Espèces",
            "compte_source": "Caisse Principale Hôtel",
            "ref_paiement": "BON-CAISSE-2601-01",
            "validation_daf": 1,
        },
        submit=True,
    )

    # Charges & Dépenses (dont dépassement volontaire en Mars 2026 > 750 000 DZD pour déclencher l'alerte Budget !)
    charges_specs = [
        ("2026-01-27", "Électricité & Gaz (Sonelgaz)", "Technique & Maintenance", "SONELGAZ - Direction Distribution Bologhine", 420_000.0),
        ("2026-01-28", "Eau (SEAAL)", "Hébergement", "SEAAL - Eau et Assainissement d'Alger", 165_000.0),
        ("2026-02-26", "Internet & Télécom", "Administration Générale", "Algérie Télécom Entreprises (Fibre Pro)", 95_000.0),
        ("2026-02-27", "Électricité & Gaz (Sonelgaz)", "Technique & Maintenance", "SONELGAZ - Direction Distribution Bologhine", 440_000.0),
        ("2026-03-19", "Maintenance & Réparations", "Technique & Maintenance", "Eurl Maghreb Ascenseurs & Climatisation CVC", 520_000.0),
        ("2026-03-26", "Électricité & Gaz (Sonelgaz)", "Technique & Maintenance", "SONELGAZ - Direction Distribution Bologhine", 390_000.0),
    ]
    for d_chg, nat, dept, frn, ht in charges_specs:
        _insert_if_missing(
            "SE Charge et Depense",
            {"date_charge": d_chg, "nature": nat, "montant_ht": ht},
            {
                "date_charge": d_chg,
                "nature": nat,
                "departement": dept,
                "fournisseur": frn,
                "montant_ht": ht,
                "taux_tva": 19.0,
                "description": f"Charge d'exploitation {nat} - {d_chg[:7]}",
            },
            submit=True,
        )


def setup_controls_assets_and_kpis() -> None:
    # 1. Clôture Caisse Mensuelle Janvier 2026 (calculée dynamiquement selon les mouvements réels)
    caisse_jan = compute_caisse_totals("2026-01", "Caisse Principale Hôtel")
    solde_phys_jan = flt(850_000.0 + caisse_jan["total_encaissements"] - caisse_jan["total_decaissements"], 2)
    _insert_if_missing(
        "SE Caisse Mensuelle",
        {"mois": "2026-01", "compte_caisse": "Caisse Principale Hôtel"},
        {
            "mois": "2026-01",
            "compte_caisse": "Caisse Principale Hôtel",
            "solde_initial": 850_000.0,
            "solde_physique": solde_phys_jan,
            "justification": "Inventaire physique contradictoire conforme au centime près.",
        },
        submit=True,
    )

    # 2. Rapprochement Bancaire Janvier 2026 sur BNA Bologhine
    from saint_eugene.saint_eugene.doctype.se_rapprochement_bancaire.se_rapprochement_bancaire import (
        get_book_balance_at_month_end,
    )

    solde_512_jan = get_book_balance_at_month_end("2026-01", "BNA Agence Bologhine - DZD")
    # Supposons un chèque fournisseur de 120 000 DZD non encore présenté sur le relevé -> relevé = solde_512 + 120 000
    _insert_if_missing(
        "SE Rapprochement Bancaire",
        {"mois": "2026-01", "compte_bancaire": "BNA Agence Bologhine - DZD"},
        {
            "mois": "2026-01",
            "compte_bancaire": "BNA Agence Bologhine - DZD",
            "solde_comptable": flt(solde_512_jan),
            "solde_releve_bancaire": flt(solde_512_jan + 120_000.0),
            "lignes_suspens": [
                {
                    "date_operation": "2026-01-30",
                    "type_ecart": "Chèque émis non débité",
                    "reference": "CHQ-BNA-45009",
                    "libelle": "Chèque émis en circulation (non débité au 31/01)",
                    "sens": "À déduire du relevé (-)",
                    "montant": 120_000.0,
                }
            ],
        },
        submit=True,
    )

    # 3. Déclarations TVA G50 Janvier & Février 2026
    _insert_if_missing(
        "SE Declaration TVA",
        {"mois": "2026-01"},
        {"mois": "2026-01", "precompte_anterieur": 0.0, "date_paiement": "2026-02-18"},
        submit=True,
    )
    _insert_if_missing(
        "SE Declaration TVA",
        {"mois": "2026-02"},
        {"mois": "2026-02", "precompte_anterieur": 0.0},
        submit=True,
    )

    # 4. Performance Hôtelière (échantillon mensuel représentatif pour les graphiques 2026 - 84 chambres)
    perf_samples = [
        ("2026-01-15", 56, 1_008_000.0, 385_000.0, 65_000.0),
        ("2026-02-15", 61, 1_128_500.0, 420_000.0, 80_000.0),
        ("2026-03-15", 53, 954_000.0, 360_000.0, 95_000.0),
        ("2026-04-15", 65, 1_235_000.0, 460_000.0, 110_000.0),
        ("2026-05-15", 70, 1_365_000.0, 510_000.0, 140_000.0),
        ("2026-06-15", 74, 1_480_000.0, 560_000.0, 150_000.0),
    ]
    for d_jour, vendues, ca_h, ca_r, autres in perf_samples:
        _insert_if_missing(
            "SE Performance Hoteliere",
            {"date_jour": d_jour},
            {
                "date_jour": d_jour,
                "chambres_disponibles": 84,
                "chambres_vendues": vendues,
                "ca_hebergement": ca_h,
                "ca_restaurant": ca_r,
                "autres_revenus": autres,
            },
        )

    # 5. Immobilisations SCF
    immos = [
        ("Groupe Électrogène Insonorisé 400 kVA", "Bâtiment & Agencements (213)", "2024-06-01", 9_800_000.0, 10),
        ("Équipements Cuisine Inox & Chambres Froides", "Équipements Cuisine & Froid (215)", "2025-01-15", 6_500_000.0, 8),
        ("Rénovation Literie King Size (42 Chambres Vue Mer)", "Mobilier & Literie Chambres (2184)", "2025-11-01", 5_400_000.0, 5),
        ("Serveurs Locaux & Terminaux TPE/PMS", "Matériel Informatique & PMS (2183)", "2026-01-05", 1_450_000.0, 3),
    ]
    for nom_im, cat, d_acq, val, dur in immos:
        _insert_if_missing(
            "SE Immobilisation",
            {"nom_immobilisation": nom_im},
            {
                "nom_immobilisation": nom_im,
                "categorie": cat,
                "date_acquisition": d_acq,
                "valeur_acquisition": val,
                "duree_amortissement": dur,
            },
        )

    # 6. Emprunt Bancaire Bonifié Tourisme CPA
    _insert_if_missing(
        "SE Emprunt et Dette",
        {"organisme": "CPA Direction Grandes Entreprises Alger"},
        {
            "organisme": "CPA Direction Grandes Entreprises Alger",
            "type_emprunt": "Crédit d'Investissement Hôtelier Bonifié",
            "taux_interet_annuel": 3.5,
            "capital_initial": 45_000_000.0,
            "mensualite": 825_000.0,
            "capital_rembourse": 11_250_000.0,
            "interets_payes": 1_840_000.0,
            "prochaine_echeance": "2026-11-30",
        },
    )

    # 7. Contrats & Abonnements
    _insert_if_missing(
        "SE Contrat et Abonnement",
        {"fournisseur": "Eurl Maghreb Ascenseurs & Climatisation CVC", "type_contrat": "Maintenance Ascenseurs"},
        {
            "fournisseur": "Eurl Maghreb Ascenseurs & Climatisation CVC",
            "type_contrat": "Maintenance Ascenseurs",
            "date_debut": "2026-01-01",
            "date_fin": "2026-12-31",
            "montant_echeance": 95_000.0,
            "frequence": "Mensuelle",
            "prochaine_echeance": "2026-11-15",
        },
    )

    # 8. Prévision de Trésorerie Glissante
    _insert_if_missing(
        "SE Prevision Tresorerie",
        {"date_prevision": "2026-03-31"},
        {"date_prevision": "2026-03-31", "seuil_alerte_minimum": 2_500_000.0},
    )


def run() -> dict:
    """Point d'entrée principal pour injecter toutes les données de démonstration 2026."""
    setup_hotel_settings()
    setup_treasury_accounts()
    setup_clients_and_suppliers()
    setup_employees_and_payroll()
    setup_annual_budget_2026()
    setup_invoices_payments_and_expenses()
    setup_controls_assets_and_kpis()

    # Synchronisation complète des retards, du Budget 2026 et des notifications Desk
    overdue_res = update_overdue_invoices_and_contracts()
    budget_res = refresh_all_budgets_2026()
    alerts_res = run_daily_financial_alerts()
    frappe.db.commit()

    summary = {
        "status": "success",
        "hotel": "Hôtel Saint Eugène 4★ - Alger",
        "exercice": 2026,
        "devise": "DZD",
        "overdue_check": overdue_res,
        "budget_sync": budget_res,
        "alerts": alerts_res,
    }
    print(summary)
    return summary
