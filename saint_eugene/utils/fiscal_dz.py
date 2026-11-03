# -*- coding: utf-8 -*-
"""
Utilitaires Fiscaux & Réglementaires Algériens (SCF / DGI / Hôtellerie 4★)
- Paramètres centralisés `SE Parametres Hotel`
- Calcul du Droit de Timbre algérien sur paiements en Espèces (Code du Timbre)
- Calcul de la Taxe de Séjour Hôtelière 4★ (400 DZD / adulte / nuitée, hors base TVA)
- Conversion intégrale des montants DZD en toutes lettres en français (mention obligatoire facture Algérie)
"""
from __future__ import annotations

import math

import frappe
from frappe.utils import cint, flt

DEFAULT_SETTINGS = {
    "nom_hotel": "Hôtel Saint Eugène 4★ - Alger",
    "raison_sociale": "SPA HÔTEL SAINT EUGÈNE",
    "classement_etoiles": "4 Étoiles",
    "capital_social": "120 000 000,00 DZD",
    "adresse": "Front de Mer, Bologhine - 16090 Alger, Algérie",
    "telephone": "+213 (0) 21 95 40 00",
    "email": "direction.financiere@hotel-sainteugene.dz",
    "nif": "002616099124587",
    "nis": "099916090145821",
    "rc": "16/00-0991245B26",
    "article_imposition": "16094512874",
    "numero_employeur_cnas": "16 4458 92 01",
    "rib_principal": "BNA Agence Bologhine : 00100614030001458921",
    "capacite_chambres": 84,
    "taux_tva_hebergement_defaut": 9.0,
    "taux_tva_standard_defaut": 19.0,
    "taxe_sejour_nuitee_adulte": 400.0,
    "activer_droit_timbre_especes": 1,
    "plafond_droit_timbre": 0.0,
    "seuil_tresorerie_critique": 2_500_000.0,
    "delai_alerte_cheque_jours": 7,
    "delai_alerte_contrat_jours": 30,
}


@frappe.whitelist()
def get_hotel_settings() -> dict:
    """Retourne les paramètres de l'Hôtel Saint Eugène (avec repli sur DEFAULT_SETTINGS)."""
    cfg = dict(DEFAULT_SETTINGS)
    try:
        if frappe.db.exists("DocType", "SE Parametres Hotel"):
            doc = frappe.get_cached_doc("SE Parametres Hotel")
            for k in DEFAULT_SETTINGS:
                val = getattr(doc, k, None)
                if val is not None and val != "":
                    cfg[k] = val
    except Exception:
        pass
    return cfg


def compute_droit_timbre_algerie(
    montant_base: float,
    mode_paiement: str,
    activer: int | bool = 1,
    plafond: float = 0.0,
) -> float:
    """
    Calcule le Droit de Timbre algérien applicable exclusivement aux règlements en Espèces :
    - Exonéré si mode != 'Espèces' ou si montant <= 300 DZD
    - Calcul par tranche ou fraction de 100 DZD :
      * <= 30 000 DZD           : 1,0 DZD par tranche de 100 DZD (1%), minimum 5 DZD
      * 30 001 à 100 000 DZD    : 1,5 DZD par tranche de 100 DZD (1,5%)
      * > 100 000 DZD           : 2,0 DZD par tranche de 100 DZD (2%)
    - Si `plafond > 0` est configuré dans `SE Parametres Hotel`, plafonne le timbre à cette valeur.
    """
    if not activer or (mode_paiement or "").strip() != "Espèces":
        return 0.0

    base = flt(montant_base, 2)
    if base <= 300.0:
        return 0.0

    tranches_100 = math.ceil(base / 100.0)
    if base <= 30_000.0:
        timbre = tranches_100 * 1.0
    elif base <= 100_000.0:
        timbre = tranches_100 * 1.5
    else:
        timbre = tranches_100 * 2.0

    timbre = max(5.0, flt(timbre, 2))
    if flt(plafond) > 0:
        timbre = min(timbre, flt(plafond, 2))
    return flt(timbre, 2)


def compute_taxe_sejour_algerie(
    nature_prestation: str,
    appliquer: int | bool,
    nb_adultes: int,
    nuitees: int,
    tarif_unitaire: float = 400.0,
) -> float:
    """
    Calcule la Taxe de Séjour hôtelière algérienne (400 DZD / adulte / nuitée en hôtel 4★).
    Applicable uniquement sur les prestations d'hébergement, hors assiette de TVA.
    """
    if not appliquer or nature_prestation != "Hébergement":
        return 0.0
    adultes = max(1, cint(nb_adultes or 1))
    nb_nuits = max(1, cint(nuitees or 1))
    return flt(adultes * nb_nuits * flt(tarif_unitaire), 2)


# ==============================================================================
# CONVERTISSEUR MONTANT DZD EN TOUTES LETTRES (FRANÇAIS - ZÉRO DÉPENDANCE)
# ==============================================================================

_UNITES = [
    "", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf",
    "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize",
    "dix-sept", "dix-huit", "dix-neuf",
]

_DIZAINES = [
    "", "dix", "vingt", "trente", "quarante", "cinquante", "soixante",
    "soixante", "quatre-vingt", "quatre-vingt",
]


def _under_100(n: int) -> str:
    if n < 20:
        return _UNITES[n]
    d, u = divmod(n, 10)
    if d in (7, 9):
        sub = 10 + u
        if d == 7 and sub == 11:
            return "soixante et onze"
        return f"{_DIZAINES[d]}-{_UNITES[sub]}"
    if u == 0:
        return "quatre-vingts" if d == 8 else _DIZAINES[d]
    if u == 1 and d != 8:
        return f"{_DIZAINES[d]} et un"
    return f"{_DIZAINES[d]}-{_UNITES[u]}"


def _under_1000(n: int) -> str:
    if n < 100:
        return _under_100(n)
    c, r = divmod(n, 100)
    if c == 1:
        prefix = "cent"
    else:
        prefix = f"{_UNITES[c]} cents" if r == 0 else f"{_UNITES[c]} cent"
    return prefix if r == 0 else f"{prefix} {_under_100(r)}"


def _int_to_french(n: int) -> str:
    if n == 0:
        return "zéro"
    parts: list[str] = []

    milliards, n = divmod(n, 1_000_000_000)
    if milliards:
        lbl = "milliard" if milliards == 1 else "milliards"
        parts.append(f"{_under_1000(milliards)} {lbl}")

    millions, n = divmod(n, 1_000_000)
    if millions:
        lbl = "million" if millions == 1 else "millions"
        parts.append(f"{_under_1000(millions)} {lbl}")

    milliers, reste = divmod(n, 1_000)
    if milliers:
        if milliers == 1:
            parts.append("mille")
        else:
            # 'quatre-vingts' perd son 's' devant 'mille'
            m_txt = _under_1000(milliers).removesuffix("quatre-vingts")
            if _under_1000(milliers).endswith("quatre-vingts"):
                m_txt = m_txt + "quatre-vingt"
            else:
                m_txt = _under_1000(milliers)
            if m_txt.endswith(" cents"):
                m_txt = m_txt[:-1]
            parts.append(f"{m_txt} mille")

    if reste:
        parts.append(_under_1000(reste))

    return " ".join(parts).strip()


@frappe.whitelist()
def montant_dzd_en_lettres(montant: float) -> str:
    """
    Convertit un montant numérique DZD en mention légale algérienne :
    Exemple : 4578000.50 -> 'Quatre millions cinq cent soixante-dix-huit mille Dinars Algériens et cinquante Centimes'
    """
    val = abs(flt(montant, 2))
    dinars = int(val)
    centimes = int(round((val - dinars) * 100))
    if centimes == 100:
        dinars += 1
        centimes = 0

    dinars_txt = _int_to_french(dinars)
    devise_lbl = "Dinar Algérien" if dinars <= 1 else "Dinars Algériens"
    phrase = f"{dinars_txt.capitalize()} {devise_lbl}"

    if centimes > 0:
        cent_lbl = "Centime" if centimes == 1 else "Centimes"
        phrase += f" et {_int_to_french(centimes)} {cent_lbl}"

    return phrase
