# -*- coding: utf-8 -*-
"""
Moteur de calcul unique des Factures Clients & Factures Pro Forma — Hôtel Saint Eugène 4★.

PRINCIPE : l'utilisateur saisit le MONTANT TTC de chaque ligne (chambre ou service).
Le système en déduit automatiquement, ligne par ligne :

    Taxe de séjour = Nb personnes × Nb nuitées × Tarif (Paramètres Hôtel)   [chambres uniquement]
    TTC hors taxe de séjour = TTC saisi − Taxe de séjour   (si "Taxe de séjour incluse dans le TTC saisi" = Oui)
                            = TTC saisi                    (sinon, la taxe de séjour est ajoutée en plus)
    Montant HT  = TTC hors taxe de séjour / (1 + Taux TVA)
    Montant TVA = TTC hors taxe de séjour − Montant HT

Puis au niveau de la facture :

    Total TTC          = Σ (HT + TVA + Taxe de séjour) des lignes
    Droit de timbre    = calculé APRÈS, sur le Total TTC (règlement en Espèces uniquement)
    Net à payer        = Total TTC + Droit de timbre      (champ `montant_ttc`)

Le droit de timbre ne fait donc JAMAIS partie du TTC saisi utilisé pour la ventilation fiscale.

Gère : plusieurs types de chambres et services dans une même facture, et plusieurs
séjours séparés (chacun avec ses propres dates, nuitées et personnes).

Ce module fonctionne aussi bien avec des dictionnaires Python (serveur local / données de démo)
qu'avec des Documents Frappe (lignes de tables enfants).
"""
from __future__ import annotations

import json
from datetime import date, datetime

from saint_eugene.utils.fiscal_dz import compute_droit_timbre_algerie, montant_dzd_en_lettres

ROOM_TYPES = ("Single", "Double", "Twin", "Triple", "Suite Deluxe", "Suite Saint Eugène")
SERVICES = ("Dîner", "Déjeuner", "Coffee Break", "Location de salle")

ARTICLE_CATEGORY = {
    **{r: "Hébergement" for r in ROOM_TYPES},
    "Dîner": "Restauration",
    "Déjeuner": "Restauration",
    "Coffee Break": "Restauration",
    "Location de salle": "Séminaires & Banquets",
}

TOTAL_FIELDS = (
    "montant_ht",
    "montant_tva",
    "taxe_sejour",
    "total_ttc_saisi",
    "droit_timbre",
    "montant_ttc",
    "ht_hebergement",
    "ht_services",
    "nb_personnes_total",
    "nuitees_personnes",
    "nuitees",
    "date_arrivee",
    "date_depart",
    "nature_prestation",
    "detail_tva",
    "montant_en_lettres",
)


# ------------------------------------------------------------------------------
# Accès génériques (dict ou Document Frappe)
# ------------------------------------------------------------------------------
def _g(obj, key, default=None):
    if isinstance(obj, dict):
        val = obj.get(key, default)
    else:
        val = getattr(obj, key, default)
    return default if val is None else val


def _s(obj, key, value) -> None:
    if isinstance(obj, dict):
        obj[key] = value
    else:
        setattr(obj, key, value)


def _num(val, default: float = 0.0) -> float:
    try:
        if val is None or val == "":
            return default
        return float(val)
    except (TypeError, ValueError):
        return default


def _int(val, default: int = 0) -> int:
    try:
        if val is None or val == "":
            return default
        return int(float(val))
    except (TypeError, ValueError):
        return default


def _r2(val: float) -> float:
    return round(float(val) + 0.0, 2)


def _to_date(val):
    if not val:
        return None
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    try:
        return date.fromisoformat(str(val)[:10])
    except ValueError:
        return None


def nights_between(date_arrivee, date_depart, fallback: int = 1) -> int:
    d1, d2 = _to_date(date_arrivee), _to_date(date_depart)
    if d1 and d2:
        return max(1, (d2 - d1).days)
    return max(1, _int(fallback, 1))


def article_category(article: str) -> str:
    return ARTICLE_CATEGORY.get(article or "", "Restauration")


def default_vat_rate(article: str, cfg: dict) -> float:
    if article_category(article) == "Hébergement":
        return _num(cfg.get("taux_tva_hebergement_defaut"), 9.0)
    return _num(cfg.get("taux_tva_standard_defaut"), 19.0)


# ------------------------------------------------------------------------------
# Calcul principal
# ------------------------------------------------------------------------------
def compute_invoice(header, sejours: list, lignes: list, cfg: dict) -> dict:
    """
    Calcule tous les montants. Modifie `sejours` et `lignes` sur place et retourne
    un dictionnaire des totaux d'en-tête (voir TOTAL_FIELDS) + la liste `errors`.
    """
    tarif_ts = _num(cfg.get("taxe_sejour_nuitee_adulte"), 500.0)
    incluse = _int(_g(header, "taxe_sejour_incluse", 1), 1) == 1
    appliquer_ts = _int(_g(header, "appliquer_taxe_sejour", 1), 1) == 1
    errors: list[str] = []

    # 1. Séjours : nuitées propres à chaque séjour
    sej_by_no = {}
    for idx, sej in enumerate(sejours, start=1):
        no = _int(_g(sej, "sejour_no"), idx) or idx
        _s(sej, "sejour_no", no)
        nuits = nights_between(_g(sej, "date_arrivee"), _g(sej, "date_depart"), _g(sej, "nuitees", 1))
        _s(sej, "nuitees", nuits)
        _s(sej, "nb_personnes", 0)
        _s(sej, "total_ttc_sejour", 0.0)
        sej_by_no[no] = sej
    first_sej = sejours[0] if sejours else None

    # 2. Lignes
    tot = {"ht": 0.0, "tva": 0.0, "ts": 0.0, "ttc": 0.0, "ht_heb": 0.0, "ht_srv": 0.0, "pers": 0, "pn": 0}
    vat_buckets: dict[float, list[float]] = {}
    categories: set[str] = set()

    for idx, ln in enumerate(lignes, start=1):
        article = _g(ln, "article", "") or "Double"
        cat = article_category(article)
        is_room = cat == "Hébergement"
        categories.add(cat)
        _s(ln, "type_ligne", cat)

        no = _int(_g(ln, "sejour_no"), 1) or 1
        sej = sej_by_no.get(no, first_sej)
        if sej is not None:
            no = _int(_g(sej, "sejour_no"), 1)
        _s(ln, "sejour_no", no)

        qty = max(1, _int(_g(ln, "quantite"), 1))
        _s(ln, "quantite", qty)

        if is_room:
            jours = _int(_g(sej, "nuitees"), 1) if sej is not None else max(1, _int(_g(ln, "nb_jours"), 1))
            personnes = max(1, _int(_g(ln, "nb_personnes"), qty))
        else:
            jours = max(1, _int(_g(ln, "nb_jours"), 1))
            personnes = _int(_g(ln, "nb_personnes"), 0)
        _s(ln, "nb_jours", jours)
        _s(ln, "nb_personnes", personnes)

        raw_rate = _g(ln, "taux_tva", None)
        taux = default_vat_rate(article, cfg) if raw_rate in (None, "") else _num(raw_rate)
        _s(ln, "taux_tva", taux)

        ttc_saisi = _r2(_num(_g(ln, "montant_ttc_saisi")))
        _s(ln, "montant_ttc_saisi", ttc_saisi)

        ts = _r2(personnes * jours * tarif_ts) if (is_room and appliquer_ts) else 0.0
        if incluse:
            ttc_hors_ts = _r2(ttc_saisi - ts)
            total_ligne = ttc_saisi
        else:
            ttc_hors_ts = ttc_saisi
            total_ligne = _r2(ttc_saisi + ts)

        if ttc_hors_ts < 0:
            errors.append(
                f"Ligne {idx} ({article}) : le TTC saisi ({ttc_saisi:,.2f} DZD) est inférieur "
                f"à la taxe de séjour ({ts:,.2f} DZD)."
            )
            ttc_hors_ts = 0.0
            total_ligne = ts

        ht = _r2(ttc_hors_ts / (1.0 + taux / 100.0)) if taux > -100 else ttc_hors_ts
        tva = _r2(ttc_hors_ts - ht)
        pu = _r2(ttc_hors_ts / (qty * jours)) if qty * jours else 0.0

        _s(ln, "taxe_sejour", ts)
        _s(ln, "montant_ht", ht)
        _s(ln, "montant_tva", tva)
        _s(ln, "total_ligne_ttc", _r2(total_ligne))
        _s(ln, "prix_unitaire_ttc", pu)

        tot["ht"] += ht
        tot["tva"] += tva
        tot["ts"] += ts
        tot["ttc"] += total_ligne
        if is_room:
            tot["ht_heb"] += ht
            tot["pers"] += personnes
            tot["pn"] += personnes * jours
            if sej is not None:
                _s(sej, "nb_personnes", _int(_g(sej, "nb_personnes"), 0) + personnes)
        else:
            tot["ht_srv"] += ht
        if sej is not None:
            _s(sej, "total_ttc_sejour", _r2(_num(_g(sej, "total_ttc_sejour")) + total_ligne))

        bucket = vat_buckets.setdefault(taux, [0.0, 0.0])
        bucket[0] += ht
        bucket[1] += tva

    total_ttc = _r2(tot["ttc"])

    # 3. Droit de timbre : calculé APRÈS, sur le total TTC, puis ajouté
    timbre = compute_droit_timbre_algerie(
        montant_base=total_ttc,
        mode_paiement=_g(header, "mode_paiement_prevu", "Virement"),
        activer=_int(cfg.get("activer_droit_timbre_especes"), 1),
        plafond=_num(cfg.get("plafond_droit_timbre"), 0.0),
    )
    net = _r2(total_ttc + timbre)

    # 4. Synthèse
    if categories == {"Hébergement"}:
        nature = "Hébergement"
    elif categories == {"Restauration"}:
        nature = "Restauration"
    elif categories == {"Séminaires & Banquets"}:
        nature = "Séminaires & Banquets"
    elif categories:
        nature = "Mixte"
    else:
        nature = "Hébergement"

    detail_tva = " | ".join(
        f"TVA {rate:g}% : base HT {vals[0]:,.2f} — TVA {vals[1]:,.2f}".replace(",", " ")
        for rate, vals in sorted(vat_buckets.items())
    )

    arrivals = [d for d in (_to_date(_g(s, "date_arrivee")) for s in sejours) if d]
    departures = [d for d in (_to_date(_g(s, "date_depart")) for s in sejours) if d]

    return {
        "montant_ht": _r2(tot["ht"]),
        "montant_tva": _r2(tot["tva"]),
        "taxe_sejour": _r2(tot["ts"]),
        "total_ttc_saisi": total_ttc,
        "droit_timbre": timbre,
        "montant_ttc": net,
        "ht_hebergement": _r2(tot["ht_heb"]),
        "ht_services": _r2(tot["ht_srv"]),
        "nb_personnes_total": int(tot["pers"]),
        "nuitees_personnes": int(tot["pn"]),
        "nuitees": sum(_int(_g(s, "nuitees"), 0) for s in sejours) if sejours else 0,
        "date_arrivee": min(arrivals).isoformat() if arrivals else _g(header, "date_arrivee", ""),
        "date_depart": max(departures).isoformat() if departures else _g(header, "date_depart", ""),
        "nature_prestation": nature,
        "detail_tva": detail_tva,
        "montant_en_lettres": montant_dzd_en_lettres(net),
        "errors": errors,
    }


def compute_invoice_dict(doc: dict, cfg: dict) -> dict:
    """Variante pour dictionnaires purs (serveur local, données de démonstration)."""
    if not _int(doc.get("sejours_separes"), 0) or not doc.get("sejours"):
        existing = (doc.get("sejours") or [{}])[0]
        doc["sejours"] = [
            {
                "sejour_no": 1,
                "date_arrivee": doc.get("date_arrivee") or existing.get("date_arrivee", ""),
                "date_depart": doc.get("date_depart") or existing.get("date_depart", ""),
            }
        ]
        for ln in doc.get("lignes") or []:
            ln["sejour_no"] = 1
    res = compute_invoice(doc, doc["sejours"], doc.get("lignes") or [], cfg)
    for k in TOTAL_FIELDS:
        doc[k] = res[k]
    return res


# ------------------------------------------------------------------------------
# Adaptateur Frappe (Factures Clients & Pro Forma)
# ------------------------------------------------------------------------------
def apply_to_frappe_doc(doc) -> None:
    """Appelé dans `validate()` de SE Facture Client et SE Facture Pro Forma."""
    import frappe
    from frappe import _

    from saint_eugene.utils.fiscal_dz import get_hotel_settings

    cfg = get_hotel_settings()

    if not doc.get("lignes"):
        frappe.throw(_("Ajoutez au moins une ligne (type de chambre ou service) avec son montant TTC."))

    if not int(doc.get("sejours_separes") or 0):
        doc.set("sejours", [])
        doc.append(
            "sejours",
            {"sejour_no": 1, "date_arrivee": doc.get("date_arrivee"), "date_depart": doc.get("date_depart")},
        )
        for ln in doc.get("lignes"):
            ln.sejour_no = 1
    elif not doc.get("sejours"):
        frappe.throw(_("Mode « séjours séparés » : ajoutez au moins un séjour avec ses dates."))

    for sej in doc.get("sejours"):
        if sej.date_arrivee and sej.date_depart and _to_date(sej.date_depart) < _to_date(sej.date_arrivee):
            frappe.throw(_("Séjour {0} : la date de départ précède la date d'arrivée.").format(sej.sejour_no))

    res = compute_invoice(doc, doc.get("sejours"), doc.get("lignes"), cfg)
    if res["errors"]:
        frappe.throw("<br>".join(res["errors"]))
    for k in TOTAL_FIELDS:
        doc.set(k, res[k])


def _register_whitelist():
    try:
        import frappe
    except ImportError:  # pragma: no cover - serveur local sans Frappe
        return None
    if not hasattr(frappe, "whitelist"):
        return None
    return frappe.whitelist()


_wl = _register_whitelist()


def preview_invoice(doc) -> dict:
    """Calcul temps réel appelé par le formulaire Frappe (aucune écriture en base)."""
    from saint_eugene.utils.fiscal_dz import get_hotel_settings

    data = json.loads(doc) if isinstance(doc, str) else dict(doc)
    data["sejours"] = [dict(s) for s in (data.get("sejours") or [])]
    data["lignes"] = [dict(ln) for ln in (data.get("lignes") or [])]
    res = compute_invoice_dict(data, get_hotel_settings())
    return {
        "totals": {k: data.get(k) for k in TOTAL_FIELDS},
        "sejours": data["sejours"],
        "lignes": data["lignes"],
        "errors": res["errors"],
    }


if _wl is not None:
    preview_invoice = _wl(preview_invoice)
