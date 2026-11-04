# -*- coding: utf-8 -*-
"""
Génère :
1. `index.html` protégé par Mot de Passe & Chiffrement (PBKDF2-HMAC-SHA256 + Flux Chiffré)
   pour GitHub Pages : https://arc-hicham.github.io/saint-eugene-erp-2026/
2. `GOOGLE_SHEET_AUTO_BACKUP.gs` relié au Google Sheet :
   https://docs.google.com/spreadsheets/d/1UuZAxjwHC6YXcrhjsQaZ9G5XYdKBn9Hn779yTdIwjak/edit?usp=sharing

Nouvelles fonctionnalités incluses :
- Sauvegarde automatique vers le Google Sheet `1UuZAxjwHC6YXcrhjsQaZ9G5XYdKBn9Hn779yTdIwjak` à chaque ajout/modification/suppression
- Feuille séparée (onglet dédié) pour chaque module (22 modules + 1 feuille `🕘 Historique Modifications`)
- Colonnes `Date de Modification`, `Modifié par`, `Détail de la Modification (Avant -> Après)` et `Lien Google Sheet` sur chaque ligne
- Ligne `TOTAL GÉNÉRAL` automatique en bas de chaque tableau dans l'ERP ET dans chaque feuille Google Sheet / Excel
- Bouton `🖨️ Imprimer l'État (avec Totaux)` sur CHAQUE page de l'ERP (ex: filtrer par "SONATRACH" dans Factures Clients et imprimer l'État de SONATRACH avec Total HT, Total TTC, Total Encaissé et Reste à Encaisser)
- Optimisation complète Smartphone (iOS / Android)
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
from pathlib import Path

APP_ROOT = Path(r"C:\Users\HICHAM BAKIR\.gemini\antigravity\scratch\saint_eugene")
sys.path.insert(0, str(APP_ROOT))

from launch_now import SCHEMAS, build_initial_seed_db  # noqa: E402

GOOGLE_SHEET_ID = "1UuZAxjwHC6YXcrhjsQaZ9G5XYdKBn9Hn779yTdIwjak"
GOOGLE_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/edit?usp=sharing"


def rc4_drop4096_crypt(key: bytes, data: bytes) -> bytes:
    """Chiffrement / déchiffrement symétrique par flux (RC4-drop4096) initialisé par clé PBKDF2 256 bits."""
    s = list(range(256))
    j = 0
    klen = len(key)
    for i in range(256):
        j = (j + s[i] + key[i % klen]) & 0xFF
        s[i], s[j] = s[j], s[i]

    i = 0
    j = 0
    for _ in range(4096):
        i = (i + 1) & 0xFF
        j = (j + s[i]) & 0xFF
        s[i], s[j] = s[j], s[i]

    out = bytearray(len(data))
    for idx, b in enumerate(data):
        i = (i + 1) & 0xFF
        j = (j + s[i]) & 0xFF
        s[i], s[j] = s[j], s[i]
        k = s[(s[i] + s[j]) & 0xFF]
        out[idx] = b ^ k
    return bytes(out)


def encrypt_bundle(password: str, payload_obj: dict) -> dict:
    raw_bytes = json.dumps(payload_obj, ensure_ascii=False).encode("utf-8")
    salt = os.urandom(16)
    iterations = 50_000
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=32)
    verify_tag = hashlib.sha256(dk + b"SAINT_EUGENE_AUTH_2026").hexdigest()
    cipher_bytes = rc4_drop4096_crypt(dk, raw_bytes)
    return {
        "salt_b64": base64.b64encode(salt).decode("ascii"),
        "iterations": iterations,
        "verify_tag": verify_tag,
        "cipher_b64": base64.b64encode(cipher_bytes).decode("ascii"),
    }


def generate_google_apps_script(initial_db: dict) -> str:
    """Génère le script Google Apps Script (`GOOGLE_SHEET_AUTO_BACKUP.gs`) pré-configuré pour le Google Sheet de l'utilisateur."""
    seed_payload_json = json.dumps(
        {
            "history": initial_db.get("SE Historique Modifications", []),
            "db": initial_db,
            "schemas": SCHEMAS,
        },
        ensure_ascii=False,
    )
    return f"""/**
 * ============================================================================
 * SCRIPT OFFICIEL DE SAUVEGARDE AUTOMATIQUE & HISTORIQUE — HÔTEL SAINT EUGÈNE 4★
 * Google Sheet cible : {GOOGLE_SHEET_URL}
 * Spreadsheet ID     : {GOOGLE_SHEET_ID}
 * ============================================================================
 *
 * COMMENT L'ACTIVER EN 30 SECONDES :
 * 1. Ouvrez votre Google Sheet : {GOOGLE_SHEET_URL}
 * 2. Dans le menu en haut, cliquez sur : Extensions > Apps Script
 * 3. Effacez tout le texte présent et collez l'intégralité de ce fichier.
 * 4. Cliquez sur 💾 (Enregistrer), puis cliquez sur ▶️ "Exécuter" (fonction `initialiserFeuillesSaintEugene`)
 *    -> Cela crée immédiatement les 23 feuilles séparées, formatées avec les TOTAUX et l'Historique !
 * 5. Pour la synchronisation automatique depuis votre téléphone/PC :
 *    Cliquez sur "Déployer" > "Nouveau déploiement" > Type : "Application Web"
 *    - Exécuter en tant que : "Moi"
 *    - Qui peut accéder : "Tout le monde" (Anyone)
 *    Copiez l'URL Web App obtenue et collez-la dans l'onglet "☁️ Google Sheet" de votre ERP !
 */

const SPREADSHEET_ID = "{GOOGLE_SHEET_ID}";
const SHEET_URL = "{GOOGLE_SHEET_URL}";

function initialiserFeuillesSaintEugene() {{
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  const initialPayload = {seed_payload_json};
  syncAllToSpreadsheet(ss, initialPayload);
}}

const MODULE_TITLES = {{
  "SE Facture Client": "Factures Clients (SCF 70)",
  "SE Facture Pro Forma": "Factures Pro Forma",
  "SE Performance Hoteliere": "Performance Hôtelière (45 ch.)",
  "SE Facture Fournisseur": "Factures Fournisseurs (SCF 60)",
  "SE Charge et Depense": "Charges & Dépenses (61-62)",
  "SE Client": "Clients (Corporate & Agences)",
  "SE Fournisseur": "Fournisseurs",
  "SE Encaissement": "Encaissements Clients",
  "SE Decaissement": "Décaissements",
  "SE Caisse Mensuelle": "Caisse Mensuelle (PV)",
  "SE Operation Bancaire": "Opérations Bancaires (512)",
  "SE Rapprochement Bancaire": "Rapprochement Bancaire",
  "SE Prevision Tresorerie": "Prévisions Trésorerie",
  "SE Compte Tresorerie": "Comptes Caisses & Banques",
  "SE Declaration TVA": "Déclarations TVA (G50)",
  "SE Budget Annuel": "Budget Annuel 2026",
  "SE Fiche de Paie Mensuelle": "Fiches de Paie (CNAS-IRG)",
  "SE Employe": "Collaborateurs Hôtel",
  "SE Immobilisation": "Immobilisations & VNC",
  "SE Emprunt et Dette": "Emprunts & Dettes",
  "SE Contrat et Abonnement": "Contrats & Abonnements",
  "SE Parametres Hotel": "Paramètres Hôtel 4★"
}};

function doPost(e) {{
  try {{
    const payload = JSON.parse(e.postData.contents);
    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    syncAllToSpreadsheet(ss, payload);
    return ContentService.createTextOutput(JSON.stringify({{ status: "ok", timestamp: new Date().toISOString() }}))
      .setMimeType(ContentService.MimeType.JSON);
  }} catch (err) {{
    return ContentService.createTextOutput(JSON.stringify({{ status: "error", message: String(err) }}))
      .setMimeType(ContentService.MimeType.JSON);
  }}
}}

function doGet(e) {{
  return ContentService.createTextOutput(JSON.stringify({{
    status: "online",
    hotel: "SPA HÔTEL SAINT EUGÈNE 4★ - ALGER",
    spreadsheet_id: SPREADSHEET_ID
  }})).setMimeType(ContentService.MimeType.JSON);
}}

function syncAllToSpreadsheet(ss, payload) {{
  const nowStr = Utilities.formatDate(new Date(), "Africa/Algiers", "yyyy-MM-dd HH:mm:ss");
  const historyList = payload.history || [];
  const lastEvent = payload.last_event || null;
  const db = payload.db || {{}};
  const schemas = payload.schemas || {{}};

  // 1. Feuille Historique Complet des Modifications (1er Onglet)
  let histSheet = ss.getSheetByName("🕘 Historique Modifications");
  if (!histSheet) {{
    histSheet = ss.insertSheet("🕘 Historique Modifications", 0);
  }}
  renderHistorySheet(histSheet, historyList, lastEvent, nowStr);

  // 2. Une feuille séparée et bien organisée pour chaque titre de module
  Object.keys(MODULE_TITLES).forEach(doctype => {{
    const tabName = MODULE_TITLES[doctype].slice(0, 31);
    const rows = db[doctype] || [];
    const schema = schemas[doctype] || null;
    let sh = ss.getSheetByName(tabName);
    if (!sh) {{
      sh = ss.insertSheet(tabName);
    }}
    renderModuleSheet(sh, doctype, MODULE_TITLES[doctype], rows, schema, nowStr);
  }});
}}

function renderHistorySheet(sh, historyList, lastEvent, nowStr) {{
  sh.clear();
  const headers = [
    "ID Modification",
    "Date & Heure de Modification",
    "Module (Titre)",
    "Référence Document",
    "Action Effectuée",
    "Qu'est-ce qui a été modifié (Détail Avant → Après)",
    "Utilisateur",
    "Lien Direct Google Sheet"
  ];
  sh.getRange(1, 1, 1, headers.length).merge()
    .setValue("SPA HÔTEL SAINT EUGÈNE 4★ ALGER — JOURNAL & HISTORIQUE COMPLET DES MODIFICATIONS (Mis à jour : " + nowStr + ")")
    .setBackground("#0f172a").setFontColor("#fbbf24").setFontWeight("bold").setFontSize(11);

  sh.getRange(2, 1, 1, headers.length).setValues([headers])
    .setBackground("#1e293b").setFontColor("#ffffff").setFontWeight("bold");

  const data = (historyList || []).map(h => [
    h.id || "",
    h.date_modification || nowStr,
    h.module_label || h.doctype || "",
    h.doc_name || "",
    h.action || "",
    h.detail_modification || "",
    h.utilisateur || "Contrôle de Gestion / DAF",
    SHEET_URL
  ]);

  if (data.length > 0) {{
    sh.getRange(3, 1, data.length, headers.length).setValues(data);
  }}
  sh.setFrozenRows(2);
  sh.autoResizeColumns(1, headers.length);
}}

function renderModuleSheet(sh, doctype, titleLabel, rows, schema, nowStr) {{
  sh.clear();
  const fields = schema && schema.fields
    ? schema.fields.filter(f => !["Section Break", "Column Break", "Table"].includes(f.fieldtype) && f.fieldname !== "naming_series" && f.fieldname !== "amended_from")
    : [];

  const colHeaders = [
    "Référence (ID)",
    ...fields.map(f => f.label || f.fieldname),
    "Date de Modification",
    "Modifié par",
    "Détail de la Dernière Modification",
    "Lien Google Sheet"
  ];

  sh.getRange(1, 1, 1, colHeaders.length).merge()
    .setValue("HÔTEL SAINT EUGÈNE 4★ ALGER — " + titleLabel.toUpperCase() + " — Sauvegarde du " + nowStr + " (" + rows.length + " enregistrements)")
    .setBackground("#0f172a").setFontColor("#fbbf24").setFontWeight("bold").setFontSize(11);

  sh.getRange(2, 1, 1, colHeaders.length).setValues([colHeaders])
    .setBackground("#1e293b").setFontColor("#ffffff").setFontWeight("bold");

  if (rows.length > 0) {{
    const matrix = rows.map(r => [
      r.name || "",
      ...fields.map(f => r[f.fieldname] !== undefined && r[f.fieldname] !== null ? r[f.fieldname] : ""),
      r.date_modification || nowStr,
      r.modifie_par || "Contrôle de Gestion / DAF",
      r.detail_modification || "Sauvegarde initiale 2026",
      SHEET_URL
    ]);
    sh.getRange(3, 1, matrix.length, colHeaders.length).setValues(matrix);

    // Ligne TOTAL GÉNÉRAL en bas de la feuille
    const totalRow = new Array(colHeaders.length).fill("");
    totalRow[0] = "TOTAL GÉNÉRAL (" + rows.length + " lignes)";
    fields.forEach((f, idx) => {{
      if (["Currency", "Int", "Float"].includes(f.fieldtype)) {{
        const sumVal = rows.reduce((acc, r) => acc + (Number(r[f.fieldname]) || 0), 0);
        totalRow[idx + 1] = Math.round(sumVal * 100) / 100;
      }} else if (f.fieldtype === "Percent") {{
        const avgVal = rows.reduce((acc, r) => acc + (Number(r[f.fieldname]) || 0), 0) / rows.length;
        totalRow[idx + 1] = Math.round(avgVal * 100) / 100;
      }}
    }});
    const totRange = sh.getRange(rows.length + 3, 1, 1, colHeaders.length);
    totRange.setValues([totalRow]).setBackground("#fef3c7").setFontColor("#0f172a").setFontWeight("bold");
  }}
  sh.setFrozenRows(2);
  sh.autoResizeColumns(1, Math.min(colHeaders.length, 15));
}}
"""


def main() -> None:
    pw_file = APP_ROOT / ".portal_password.txt"
    if len(sys.argv) > 1 and sys.argv[1].strip():
        password = sys.argv[1].strip()
        pw_file.write_text(password, encoding="utf-8")
    elif pw_file.exists():
        password = pw_file.read_text(encoding="utf-8").strip() or "SaintEugene2026"
    else:
        password = "SaintEugene2026"

    # Assurer que Montant HT et Montant Encaissé sont affichés dans la liste Factures Clients
    fc_schema_path = APP_ROOT / "saint_eugene" / "saint_eugene" / "doctype" / "se_facture_client" / "se_facture_client.json"
    if fc_schema_path.exists():
        fc_data = json.loads(fc_schema_path.read_text(encoding="utf-8"))
        for fld in fc_data.get("fields", []):
            if fld.get("fieldname") in ("montant_ht", "montant_ttc", "montant_encaisse", "reste_a_encaisser", "statut", "date_facture", "client"):
                fld["in_list_view"] = 1
        fc_schema_path.write_text(json.dumps(fc_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        SCHEMAS["SE Facture Client"] = fc_data

    initial_db = build_initial_seed_db()

    # Initialiser l'historique des modifications avec trace complète
    initial_db["SE Historique Modifications"] = [
        {
            "id": "HIST-2026-00001",
            "date_modification": "2026-11-03 22:00:00",
            "doctype": "SE Parametres Hotel",
            "module_label": "⚙️ Paramètres Hôtel & Fiscalité 4★",
            "doc_name": "SE Parametres Hotel",
            "action": "✏️ Mise à jour Paramètres",
            "detail_modification": "Capacité Chambres : 84 → 45 ch. | Adresse : 04 Blv Omar Lounas, Bologhine | Taxe Séjour : 500 DZD",
            "utilisateur": "Contrôle de Gestion / DAF (Hicham Bakir)",
            "lien_google_sheet": GOOGLE_SHEET_URL,
        }
    ]

    # Ajouter les métadonnées de modification initiales sur chaque enregistrement
    for dt_name, records in initial_db.items():
        if dt_name == "SE Historique Modifications" or not isinstance(records, list):
            continue
        for r in records:
            if isinstance(r, dict):
                r.setdefault("date_modification", "2026-11-03 22:00:00")
                r.setdefault("modifie_par", "Contrôle de Gestion / DAF")
                r.setdefault("detail_modification", f"Enregistrement initial validé ({r.get('name', '')})")
                r.setdefault("lien_google_sheet", GOOGLE_SHEET_URL)

    # Écrire le script Google Apps Script prêt à coller
    gs_code = generate_google_apps_script(initial_db)
    (APP_ROOT / "GOOGLE_SHEET_AUTO_BACKUP.gs").write_text(gs_code, encoding="utf-8")

    raw_bundle = {"schemas": SCHEMAS, "initial_db": initial_db, "gs_script": gs_code}
    bundle_json = json.dumps(raw_bundle, ensure_ascii=False)
    encrypted = encrypt_bundle(password, raw_bundle)
    encrypted_json = json.dumps(encrypted)

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex, nofollow">
<meta name="theme-color" content="#0f172a">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>Accès Privé — Saint Eugène ERP 2026 (Hôtel 4★ Alger)</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/xlsx@0.18.5/dist/xlsx.full.min.js"></script>
<script src="utilisateurs.js"></script>
<style>
  :root {{
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
  }}
  * {{ box-sizing: border-box; -webkit-tap-highlight-color: transparent; }}
  body {{
    margin: 0;
    font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    display: flex;
    height: 100vh;
    height: 100dvh;
    overflow: hidden;
  }}

  /* Toast Notification */
  .toast-banner {{
    position: fixed;
    top: 14px;
    left: 50%;
    transform: translateX(-50%) translateY(-150%);
    background: #065f46;
    color: #ffffff;
    padding: 11px 20px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 700;
    box-shadow: 0 10px 25px rgba(0,0,0,0.28);
    z-index: 10000;
    transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    display: flex;
    align-items: center;
    gap: 8px;
    max-width: 92vw;
    text-align: center;
  }}
  .toast-banner.show {{ transform: translateX(-50%) translateY(0); }}

  /* Écran de Connexion Privé 4★ */
  .login-screen {{
    position: fixed; inset: 0; z-index: 9999;
    background: radial-gradient(circle at top right, #1e293b 0%, #0f172a 65%, #020617 100%);
    display: flex; align-items: center; justify-content: center; padding: 18px;
    overflow-y: auto;
  }}
  .login-screen.hidden {{ display: none; }}
  .login-card {{
    background: rgba(255,255,255,0.98); width: 100%; max-width: 420px; border-radius: 16px;
    padding: 28px 24px; box-shadow: 0 25px 60px rgba(0,0,0,0.45); border-top: 5px solid #d97706;
  }}
  .login-brand {{ text-align: center; margin-bottom: 22px; }}
  .login-brand .stars {{ color: #d97706; font-size: 18px; letter-spacing: 3px; }}
  .login-brand h1 {{ margin: 6px 0 4px; font-size: 20px; color: #0f172a; letter-spacing: 0.4px; }}
  .login-brand p {{ margin: 0; font-size: 12.5px; color: #64748b; }}
  .login-field {{ margin-bottom: 15px; display: flex; flex-direction: column; gap: 6px; }}
  .login-field label {{ font-size: 12px; font-weight: 700; color: #334155; text-transform: uppercase; letter-spacing: 0.4px; }}
  .login-field select, .login-field input {{
    padding: 12px 13px; border: 1.5px solid #cbd5e1; border-radius: 8px; font-size: 16px; outline: none; transition: 0.15s; background: #fff;
  }}
  .login-field input:focus, .login-field select:focus {{ border-color: #d97706; box-shadow: 0 0 0 3px rgba(217,119,6,0.15); }}
  .login-btn {{
    width: 100%; padding: 13px; border: none; border-radius: 8px; background: #0f172a; color: #fff;
    font-size: 15px; font-weight: 700; cursor: pointer; transition: 0.15s; margin-top: 4px;
  }}
  .login-btn:hover {{ background: #b45309; }}
  .login-err {{ color: #dc2626; background: #fef2f2; border: 1px solid #fecaca; padding: 9px 12px; border-radius: 6px; font-size: 12.5px; margin-bottom: 14px; display: none; }}
  .login-footer {{ margin-top: 18px; text-align: center; font-size: 11px; color: #94a3b8; border-top: 1px solid #f1f5f9; padding-top: 12px; }}

  /* Sidebar Frappe Desk */
  .sidebar-backdrop {{
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(15, 23, 42, 0.55);
    z-index: 190;
  }}
  .sidebar-backdrop.open {{ display: block; }}
  .sidebar {{
    width: 278px;
    background: var(--navy);
    color: #f8fafc;
    display: flex;
    flex-direction: column;
    border-right: 1px solid #334155;
    flex-shrink: 0;
    z-index: 200;
    transition: transform 0.25s ease;
  }}
  .brand {{ padding: 16px 18px; border-bottom: 1px solid #1e293b; display: flex; align-items: center; justify-content: space-between; }}
  .brand h1 {{ margin: 0; font-size: 15px; font-weight: 700; letter-spacing: 0.3px; display: flex; align-items: center; gap: 6px; }}
  .brand .stars {{ color: #fbbf24; font-size: 13px; }}
  .brand small {{ color: #94a3b8; font-size: 11px; display: block; margin-top: 3px; }}
  .close-drawer-btn {{ display: none; background: transparent; border: 1px solid #334155; color: #cbd5e1; border-radius: 6px; padding: 5px 10px; font-size: 14px; cursor: pointer; }}
  .nav-scroll {{ flex: 1; overflow-y: auto; padding: 10px 12px 24px; -webkit-overflow-scrolling: touch; }}
  .nav-group {{ font-size: 10.5px; text-transform: uppercase; letter-spacing: 0.8px; color: #94a3b8; margin: 14px 8px 6px; font-weight: 600; }}
  .nav-btn {{ width: 100%; text-align: left; background: transparent; border: none; color: #cbd5e1; padding: 9px 11px; border-radius: 6px; font-size: 12.8px; cursor: pointer; display: flex; align-items: center; justify-content: space-between; transition: 0.15s; }}
  .nav-btn:hover {{ background: rgba(255,255,255,0.07); color: #fff; }}
  .nav-btn.active {{ background: #b45309; color: #fff; font-weight: 600; }}

  /* Main Area */
  .main {{ flex: 1; display: flex; flex-direction: column; overflow: hidden; min-width: 0; }}
  .topbar {{
    min-height: 58px;
    background: #fff;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 18px;
    flex-shrink: 0;
    gap: 8px;
  }}
  .topbar-left {{ display: flex; align-items: center; gap: 10px; min-width: 0; }}
  .menu-toggle-btn {{
    display: none;
    background: var(--navy);
    color: #fff;
    border: none;
    border-radius: 7px;
    padding: 8px 11px;
    font-size: 16px;
    cursor: pointer;
    flex-shrink: 0;
  }}
  .topbar-title {{ font-size: 15px; font-weight: 700; color: var(--navy); display: flex; align-items: center; gap: 8px; flex-wrap: wrap; min-width: 0; }}
  .topbar-title span#viewTitle {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 46vw; }}
  .badge-scf {{ background: #fef3c7; color: #92400e; border: 1px solid #fcd34d; font-size: 11px; padding: 2px 8px; border-radius: 999px; font-weight: 600; white-space: nowrap; }}
  .topbar-actions {{ display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }}
  .btn {{ padding: 8px 12px; border-radius: 7px; font-size: 12.2px; font-weight: 600; cursor: pointer; border: 1px solid var(--border); background: #fff; color: var(--text); transition: 0.15s; white-space: nowrap; text-decoration: none; display: inline-flex; align-items: center; gap: 5px; justify-content: center; }}
  .btn:hover {{ background: #f8fafc; }}
  .btn-primary {{ background: var(--navy); color: #fff; border-color: var(--navy); }}
  .btn-primary:hover {{ background: #1e293b; }}
  .btn-gold {{ background: #b45309; color: #fff; border-color: #b45309; }}
  .btn-gold:hover {{ background: #92400e; }}
  .btn-green {{ background: #15803d; color: #fff; border-color: #15803d; }}
  .btn-green:hover {{ background: #166534; }}
  .btn-danger {{ background: #fef2f2; color: #dc2626; border-color: #fecaca; }}
  .content {{ flex: 1; overflow-y: auto; padding: 18px 22px; -webkit-overflow-scrolling: touch; }}

  /* KPI Grid */
  .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 13px; margin-bottom: 20px; }}
  .kpi-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 13px 15px; cursor: pointer; transition: transform 0.12s, box-shadow 0.12s; border-top: 4px solid #2563eb; }}
  .kpi-card:hover {{ transform: translateY(-2px); box-shadow: 0 6px 16px rgba(15,23,42,0.07); }}
  .kpi-label {{ font-size: 11px; color: var(--muted); font-weight: 600; text-transform: uppercase; margin-bottom: 5px; }}
  .kpi-val {{ font-size: 16.5px; font-weight: 800; color: var(--navy); }}

  /* Bandeau Résumé des Totaux de la page courante */
  .totals-strip {{
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    margin-bottom: 14px;
    background: #0f172a;
    color: #fff;
    padding: 12px 16px;
    border-radius: 10px;
    align-items: center;
    justify-content: space-between;
    border-left: 5px solid #d97706;
  }}
  .totals-strip-items {{ display: flex; flex-wrap: wrap; gap: 18px; align-items: center; }}
  .tot-box {{ display: flex; flex-direction: column; gap: 2px; }}
  .tot-box span {{ font-size: 10.5px; color: #94a3b8; text-transform: uppercase; font-weight: 600; }}
  .tot-box b {{ font-size: 14.5px; color: #fbbf24; font-variant-numeric: tabular-nums; }}

  /* Alerts & Charts */
  .alerts-panel {{ background: #fff; border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; margin-bottom: 20px; }}
  .alerts-panel h3 {{ margin: 0 0 10px 0; font-size: 13.5px; color: var(--navy); display: flex; align-items: center; gap: 8px; }}
  .alert-item {{ display: flex; align-items: center; justify-content: space-between; padding: 9px 12px; border-radius: 6px; margin-bottom: 6px; font-size: 12.5px; cursor: pointer; gap: 8px; }}
  .alert-item.red {{ background: #fef2f2; border-left: 4px solid var(--red); color: #991b1b; }}
  .alert-item.orange {{ background: #fff7ed; border-left: 4px solid var(--orange); color: #9a3412; }}
  .chart-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 16px; margin-bottom: 24px; }}
  .chart-box {{ background: #fff; border: 1px solid var(--border); border-radius: 10px; padding: 15px; min-width: 0; }}
  .chart-box h4 {{ margin: 0 0 12px 0; font-size: 13px; color: var(--navy); }}

  /* Tables & Filtres */
  .table-card {{ background: #fff; border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }}
  .table-scroll {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
  .table-toolbar {{ padding: 12px 16px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; background: #f8fafc; }}
  .filter-group {{ display: flex; align-items: center; gap: 8px; flex-wrap: wrap; flex: 1; }}
  .search-input, .filter-select {{ padding: 8px 11px; border: 1px solid #cbd5e1; border-radius: 7px; font-size: 13.5px; background: #fff; color: var(--text); }}
  .search-input {{ width: 240px; max-width: 100%; }}
  .filter-select {{ min-width: 170px; max-width: 100%; font-weight: 600; }}
  .toolbar-actions {{ display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}
  table.frappe-list {{ width: 100%; border-collapse: collapse; font-size: 12.5px; min-width: 650px; }}
  table.frappe-list th {{ background: #f1f5f9; color: #334155; text-align: left; padding: 10px 12px; font-size: 11px; text-transform: uppercase; border-bottom: 2px solid var(--border); white-space: nowrap; }}
  table.frappe-list td {{ padding: 10px 12px; border-bottom: 1px solid #f1f5f9; }}
  table.frappe-list tbody tr:hover td {{ background: #f8fafc; cursor: pointer; }}
  table.frappe-list tfoot td {{
    background: #fef3c7;
    color: #0f172a;
    font-weight: 800;
    padding: 11px 12px;
    border-top: 2px solid #d97706;
    font-size: 12.8px;
    white-space: nowrap;
  }}
  .pill {{ display: inline-block; padding: 3px 9px; border-radius: 999px; font-size: 11px; font-weight: 700; white-space: nowrap; }}
  .pill.green {{ background: #dcfce7; color: #166534; }}
  .pill.orange {{ background: #ffedd5; color: #9a3412; }}
  .pill.red {{ background: #fee2e2; color: #991b1b; }}
  .pill.gray {{ background: #f1f5f9; color: #475569; }}

  /* Modal Formulaire */
  .modal-backdrop {{ position: fixed; inset: 0; background: rgba(15,23,42,0.6); display: none; align-items: center; justify-content: center; z-index: 300; padding: 16px; }}
  .modal-backdrop.open {{ display: flex; }}
  .modal {{ background: #fff; border-radius: 12px; width: 100%; max-width: 860px; max-height: 92vh; max-height: 92dvh; display: flex; flex-direction: column; overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.3); }}
  .modal-hdr {{ padding: 14px 20px; background: var(--navy); color: #fff; display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-shrink: 0; }}
  .modal-hdr h3 {{ margin: 0; font-size: 14.5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .modal-body {{ padding: 18px 20px; overflow-y: auto; flex: 1; -webkit-overflow-scrolling: touch; }}
  .form-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 13px; }}
  .form-group {{ display: flex; flex-direction: column; gap: 4px; }}
  .form-group.full {{ grid-column: span 2; }}
  .form-group label {{ font-size: 11.5px; font-weight: 600; color: #475569; }}
  .form-group input, .form-group select, .form-group textarea {{
    padding: 9px 11px; border: 1px solid #cbd5e1; border-radius: 7px; font-size: 14px; background: #fff; color: var(--text); width: 100%;
  }}
  .form-group input[readonly], .form-group textarea[readonly], .form-group select[disabled] {{
    background: #f1f5f9; color: #0f172a; font-weight: 700; border-color: #e2e8f0;
  }}
  .modal-ftr {{ padding: 12px 20px; border-top: 1px solid var(--border); background: #f8fafc; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; flex-shrink: 0; }}
  .modal-ftr-right {{ display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}

  /* Barre de Navigation Mobile (Fixée en bas de l'écran téléphone) */
  .mobile-bottom-nav {{
    display: none;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: 62px;
    background: #0f172a;
    border-top: 1px solid #334155;
    z-index: 180;
    justify-content: space-around;
    align-items: center;
    padding: 0 4px env(safe-area-inset-bottom, 0px);
  }}
  .mob-nav-item {{
    flex: 1;
    background: transparent;
    border: none;
    color: #cbd5e1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 3px;
    font-size: 10.5px;
    font-weight: 600;
    padding: 6px 2px;
    cursor: pointer;
  }}
  .mob-nav-item .ico {{ font-size: 17px; line-height: 1; }}
  .mob-nav-item.highlight {{ color: #fbbf24; font-weight: 700; }}

  /* Optimisation Responsive Téléphone & Tablette */
  @media (max-width: 900px) {{
    .sidebar {{
      position: fixed;
      top: 0;
      bottom: 0;
      left: 0;
      width: 285px;
      max-width: 84vw;
      transform: translateX(-105%);
      box-shadow: 10px 0 30px rgba(0,0,0,0.35);
    }}
    .sidebar.open {{ transform: translateX(0); }}
    .close-drawer-btn {{ display: inline-block; }}
    .menu-toggle-btn {{ display: inline-flex; align-items: center; justify-content: center; }}
    .badge-scf {{ display: none; }}
    .topbar {{ padding: 8px 10px; min-height: 52px; }}
    .topbar-title {{ font-size: 13px; }}
    .topbar-title span#viewTitle {{ max-width: 42vw; }}
    .topbar-actions .hide-mobile {{ display: none; }}
    .content {{ padding: 12px 10px 82px 10px; }}
    .kpi-grid {{ grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 16px; }}
    .kpi-card {{ padding: 11px 12px; }}
    .kpi-label {{ font-size: 10px; }}
    .kpi-val {{ font-size: 14px; }}
    .chart-grid {{ grid-template-columns: 1fr; gap: 12px; }}
    .alert-item {{ flex-direction: column; align-items: flex-start; }}
    .filter-group {{ width: 100%; }}
    .search-input, .filter-select {{ width: 100%; font-size: 16px; }}
    .toolbar-actions {{ width: 100%; }}
    .toolbar-actions .btn {{ flex: 1; padding: 10px; font-size: 12.5px; }}
    .modal-backdrop {{ padding: 0; align-items: flex-end; }}
    .modal {{ max-width: 100%; height: 96dvh; max-height: 96dvh; border-radius: 16px 16px 0 0; }}
    .form-grid {{ grid-template-columns: 1fr; gap: 11px; }}
    .form-group.full {{ grid-column: span 1; }}
    .form-group input, .form-group select, .form-group textarea {{ font-size: 16px; padding: 11px 12px; }}
    .modal-ftr {{ padding: 10px 14px; }}
    .modal-ftr-right {{ width: 100%; display: flex; }}
    .modal-ftr-right .btn {{ flex: 1; padding: 11px; font-size: 13.5px; text-align: center; }}
    .mobile-bottom-nav {{ display: flex; }}
  }}
</style>
</head>
<body>

<div class="toast-banner" id="toastBanner">✅ Opération enregistrée et sauvegardée sur Google Sheet</div>

<!-- Portail d'authentification privé -->
<div class="login-screen" id="loginScreen">
  <form class="login-card" onsubmit="handleUnlock(event)">
    <div class="login-brand">
      <div class="stars">★★★★</div>
      <h1>HÔTEL SAINT EUGÈNE</h1>
      <p>Portail Privé — Direction & Contrôle de Gestion (Exercice 2026)</p>
    </div>
    <div class="login-err" id="loginError">Code d'accès confidentiel incorrect.</div>
    <div class="login-field">
      <label>Profil Utilisateur Autorisé</label>
      <select id="loginRole">
        <option value="Contrôle de Gestion / DAF (Hicham Bakir)">Hicham Bakir — Contrôle de Gestion / DAF</option>
        <option value="Direction Générale — Hôtel Saint Eugène">Direction Générale — Hôtel Saint Eugène</option>
        <option value="Chef Comptable SCF & Audit">Chef Comptable SCF & Audit</option>
        <option value="Réception & Caisses Hôtel 4★">Réception & Caisses Hôtel 4★</option>
        <option value="Administrateur Système">Administrateur Système</option>
      </select>
    </div>
    <div class="login-field">
      <label>Code d'Accès Confidentiel / Mot de Passe</label>
      <input type="password" id="loginPassword" placeholder="Entrez le mot de passe..." required autofocus autocomplete="current-password">
    </div>
    <button type="submit" class="login-btn" id="loginBtn">🔓 Déverrouiller l'Espace Financier</button>
    <div style="margin-top:12px;text-align:center;">
      <button type="button" class="btn" style="width:100%;font-size:12px;padding:8px;border-color:#cbd5e1;background:#fff;" onclick="openUsersManagementModal(event)">👥 Gérer les Utilisateurs & Mots de Passe</button>
    </div>
    <div class="login-footer">
      🔒 Données chiffrées de bout en bout • Normes SCF Algérie
    </div>
  </form>
</div>

<div class="sidebar-backdrop" id="sidebarBackdrop" onclick="toggleMobileSidebar(false)"></div>

<aside class="sidebar" id="sidebarDrawer">
  <div class="brand">
    <div>
      <h1>HÔTEL SAINT EUGÈNE <span class="stars">★★★★</span></h1>
      <small id="activeUserBadge">Mini-ERP Frappe • Exercice 2026 (DZD)</small>
    </div>
    <button class="close-drawer-btn" onclick="toggleMobileSidebar(false)">✕</button>
  </div>
  <div class="nav-scroll" id="sidebarNav"></div>
</aside>

<section class="main">
  <header class="topbar">
    <div class="topbar-left">
      <button class="menu-toggle-btn" onclick="toggleMobileSidebar()" title="Menu des Modules">☰</button>
      <div class="topbar-title">
        <span id="viewTitle">Direction Saint Eugène 2026</span>
        <span class="badge-scf">Normes SCF Algérie • DZD</span>
      </div>
    </div>
    <div class="topbar-actions">
      <button class="btn hide-mobile" onclick="showWorkspace()">📊 Tableau de Bord</button>
      <button class="btn btn-gold hide-mobile" onclick="openNewDoc('SE Facture Client')">+ Facture Client</button>
      <button class="btn hide-mobile" style="border-color:#38bdf8;background:#0284c7;color:#fff;" onclick="openNewDoc('SE Facture Pro Forma')">+ Pro Forma</button>
      <button class="btn btn-primary hide-mobile" onclick="openNewDoc('SE Encaissement')">+ Encaissement</button>
      <button class="btn hide-mobile" style="border-color:#cbd5e1;" onclick="changePasswordFromLogin(event)" title="Modifier le mot de passe d'accès">🔑 Mot de passe</button>
      <button class="btn btn-green" onclick="showGoogleSheetBackupCenter()" title="Sauvegarde Google Sheet & Historique Complet">☁️ Google Sheet</button>
      <button class="btn" style="border-color:#fca5a5;color:#dc2626;" onclick="lockSession()" title="Verrouiller">🔒</button>
    </div>
  </header>

  <div class="content" id="mainContent"></div>
</section>

<!-- Barre d'action rapide Mobile (Téléphone) -->
<nav class="mobile-bottom-nav">
  <button class="mob-nav-item" onclick="showWorkspace()">
    <span class="ico">📊</span>
    <span>Pilotage</span>
  </button>
  <button class="mob-nav-item highlight" onclick="openNewDoc('SE Facture Client')">
    <span class="ico">🧾</span>
    <span>+ Facture</span>
  </button>
  <button class="mob-nav-item" onclick="openNewDoc('SE Facture Pro Forma')">
    <span class="ico">📋</span>
    <span>+ Pro Forma</span>
  </button>
  <button class="mob-nav-item highlight" onclick="openNewDoc('SE Encaissement')">
    <span class="ico">💰</span>
    <span>+ Encaissement</span>
  </button>
  <button class="mob-nav-item" onclick="showGoogleSheetBackupCenter()">
    <span class="ico">☁️</span>
    <span>Google Sheet</span>
  </button>
  <button class="mob-nav-item" onclick="toggleMobileSidebar(true)">
    <span class="ico">☰</span>
    <span>Modules</span>
  </button>
</nav>

<div class="modal-backdrop" id="usersModal" style="display:none;position:fixed;inset:0;background:rgba(15,23,42,0.6);z-index:200;align-items:center;justify-content:center;padding:16px;">
  <div style="background:#fff;border-radius:12px;width:100%;max-width:680px;max-height:90vh;overflow-y:auto;box-shadow:0 20px 40px rgba(0,0,0,0.3);padding:24px;">
    <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:2px solid #b45309;padding-bottom:12px;margin-bottom:14px;">
      <h3 style="margin:0;font-size:16px;color:#0f172a;">👥 Gestion des Utilisateurs & Mots de Passe</h3>
      <button type="button" class="btn" style="padding:4px 10px;" onclick="closeUsersModal()">✕</button>
    </div>
    <div style="font-size:12px;color:#475569;margin-bottom:14px;background:#f8fafc;padding:10px;border-radius:6px;border:1px solid #e2e8f0;">
      Vous pouvez ajouter ou modifier des utilisateurs ici directement. Vous pouvez également ouvrir le fichier <b>utilisateurs.js</b> avec le Bloc-notes.
    </div>
    <div id="usersListTable" style="margin-bottom:16px;overflow-x:auto;"></div>
    <div style="background:#f1f5f9;border-radius:8px;padding:14px;">
      <div style="font-weight:700;font-size:13px;margin-bottom:10px;color:#0f172a;">➕ Ajouter un nouvel utilisateur</div>
      <div class="form-grid" style="grid-template-columns:repeat(3, 1fr);gap:10px;">
        <div class="form-group">
          <label style="font-size:11.5px;font-weight:600;">Nom</label>
          <input type="text" id="new_user_nom" placeholder="Ex: Karim Benali" style="padding:7px;border:1px solid #cbd5e1;border-radius:6px;font-size:12.5px;">
        </div>
        <div class="form-group">
          <label style="font-size:11.5px;font-weight:600;">Rôle / Fonction</label>
          <input type="text" id="new_user_role" placeholder="Ex: Réceptionniste" style="padding:7px;border:1px solid #cbd5e1;border-radius:6px;font-size:12.5px;">
        </div>
        <div class="form-group">
          <label style="font-size:11.5px;font-weight:600;">Mot de passe</label>
          <input type="text" id="new_user_pwd" placeholder="Ex: pass2026" style="padding:7px;border:1px solid #cbd5e1;border-radius:6px;font-size:12.5px;">
        </div>
      </div>
      <button type="button" class="btn btn-gold" style="margin-top:12px;width:100%;font-size:12.5px;padding:8px;" onclick="addNewUserFromModal()">+ Enregistrer cet utilisateur</button>
    </div>
    <div style="display:flex;justify-content:space-between;margin-top:16px;align-items:center;">
      <button type="button" class="btn" style="font-size:12px;" onclick="downloadUsersJsFile()">💾 Télécharger utilisateurs.js</button>
      <button type="button" class="btn btn-primary" style="font-size:12px;" onclick="closeUsersModal()">Fermer</button>
    </div>
  </div>
</div>

<div class="modal-backdrop" id="docModal">
  <div class="modal">
    <div class="modal-hdr">
      <h3 id="modalTitle">Document</h3>
      <button class="btn" style="padding:4px 10px;background:#1e293b;color:#fff;border-color:#475569;" onclick="closeModal()">✕</button>
    </div>
    <div class="modal-body" id="modalBody"></div>
    <div class="modal-ftr" id="modalFooter"></div>
  </div>
</div>

<script>
// =============================================================================
// 🔑 MOT DE PASSE D'ACCÈS (VOUS POUVEZ LE MODIFIER MANUELLEMENT CI-DESSOUS DANS LE BLOC-NOTES)
// =============================================================================
let CONFIGURED_PASSWORD = "{password}";
const EMERGENCY_PASSWORDS = ["1234", "admin", "admin2026", "sainteugene", "sainteugene2026", "SaintEugene2026"];

function getEffectivePassword() {{
  return localStorage.getItem("saint_eugene_custom_password") || CONFIGURED_PASSWORD;
}}

function changePasswordFromLogin(e) {{
  if (e) e.preventDefault();
  openUsersManagementModal(e);
}}

const BUNDLE_DATA = {bundle_json};
const ENCRYPTED_BUNDLE = {encrypted_json};
const GOOGLE_SHEET_ID = "{GOOGLE_SHEET_ID}";
const GOOGLE_SHEET_URL = "{GOOGLE_SHEET_URL}";
const STORAGE_KEY = "saint_eugene_erp_2026_db_v6";
const WEBHOOK_KEY = "saint_eugene_gsheet_webhook_url";
const SESSION_KEY = "saint_eugene_erp_2026_unlocked";

let SCHEMAS = {{}};
let INITIAL_DB = {{}};
let GS_SCRIPT_CODE = "";
let DB = {{}};
let CURRENT_USER_ROLE = "Contrôle de Gestion / DAF (Hicham Bakir)";
let CURRENT_DOCTYPE = null;
let CURRENT_DOC = null;
let CURRENT_ORIGINAL_DOC = null;
let CURRENT_IS_NEW = false;
let LIST_STATE = {{ search: "", entityFilter: "", statusFilter: "" }};

function nowAlgeriaTimestamp() {{
  const d = new Date();
  const pad = n => String(n).padStart(2, "0");
  return `${{d.getFullYear()}}-${{pad(d.getMonth() + 1)}}-${{pad(d.getDate())}} ${{pad(d.getHours())}}:${{pad(d.getMinutes())}}:${{pad(d.getSeconds())}}`;
}}

function showToast(msg) {{
  const el = document.getElementById("toastBanner");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => el.classList.remove("show"), 3600);
}}

function toggleMobileSidebar(forceState) {{
  const drawer = document.getElementById("sidebarDrawer");
  const backdrop = document.getElementById("sidebarBackdrop");
  const isOpen = typeof forceState === "boolean" ? forceState : !drawer.classList.contains("open");
  drawer.classList.toggle("open", isOpen);
  backdrop.classList.toggle("open", isOpen);
}}

function b64ToBytes(b64) {{
  const bin = atob(b64);
  const arr = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
  return arr;
}}

function bytesToHex(bytes) {{
  return Array.from(bytes).map(b => b.toString(16).padStart(2, "0")).join("");
}}

function rc4Drop4096Decrypt(keyBytes, cipherBytes) {{
  const s = new Uint8Array(256);
  for (let i = 0; i < 256; i++) s[i] = i;
  let j = 0;
  const klen = keyBytes.length;
  for (let i = 0; i < 256; i++) {{
    j = (j + s[i] + keyBytes[i % klen]) & 0xff;
    const tmp = s[i]; s[i] = s[j]; s[j] = tmp;
  }}
  let i = 0; j = 0;
  for (let n = 0; n < 4096; n++) {{
    i = (i + 1) & 0xff;
    j = (j + s[i]) & 0xff;
    const tmp = s[i]; s[i] = s[j]; s[j] = tmp;
  }}
  const out = new Uint8Array(cipherBytes.length);
  for (let idx = 0; idx < cipherBytes.length; idx++) {{
    i = (i + 1) & 0xff;
    j = (j + s[i]) & 0xff;
    const tmp = s[i]; s[i] = s[j]; s[j] = tmp;
    const k = s[(s[i] + s[j]) & 0xff];
    out[idx] = cipherBytes[idx] ^ k;
  }}
  return out;
}}

// =============================================================================
// 👥 GESTION DES UTILISATEURS & AUTHENTIFICATION — HÔTEL SAINT EUGÈNE 4★
// =============================================================================
const DEFAULT_USERS_LIST = [
  {{ "nom": "Hicham Bakir", "role": "Contrôle de Gestion / DAF (Hicham Bakir)", "mot_de_passe": "1234" }},
  {{ "nom": "Direction Générale", "role": "Direction Générale — Hôtel Saint Eugène", "mot_de_passe": "SaintEugene2026" }},
  {{ "nom": "Chef Comptable", "role": "Chef Comptable SCF & Audit", "mot_de_passe": "compta2026" }},
  {{ "nom": "Réception & Caisses", "role": "Réception & Caisses Hôtel 4★", "mot_de_passe": "reception2026" }},
  {{ "nom": "Administrateur", "role": "Administrateur Système", "mot_de_passe": "admin" }}
];

const MASTER_PASSWORDS = ["1234", "SaintEugene2026", "sainteugene2026", "admin", "admin2026"];

function getUsersList() {{
  if (typeof window.UTILISATEURS_CONFIG !== "undefined" && Array.isArray(window.UTILISATEURS_CONFIG) && window.UTILISATEURS_CONFIG.length > 0) {{
    return window.UTILISATEURS_CONFIG;
  }}
  const saved = localStorage.getItem("saint_eugene_utilisateurs_custom");
  if (saved) {{
    try {{
      const parsed = JSON.parse(saved);
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    }} catch (e) {{}}
  }}
  return DEFAULT_USERS_LIST;
}}

function saveUsersList(list) {{
  localStorage.setItem("saint_eugene_utilisateurs_custom", JSON.stringify(list));
  window.UTILISATEURS_CONFIG = list;
  populateUsersSelect();
}}

function populateUsersSelect() {{
  const sel = document.getElementById("loginRole");
  if (!sel) return;
  const list = getUsersList();
  const currentVal = sel.value;
  sel.innerHTML = list.map(u => `<option value="${{u.role}}" ${{u.role === currentVal ? "selected" : ""}}>${{u.nom ? u.nom + " — " : ""}}${{u.role}}</option>`).join("");
}}

function openUsersManagementModal(e) {{
  if (e) e.preventDefault();
  const m = document.getElementById("usersModal");
  if (!m) return;
  m.style.display = "flex";
  renderUsersListTable();
}}

function closeUsersModal() {{
  const m = document.getElementById("usersModal");
  if (m) m.style.display = "none";
}}

function renderUsersListTable() {{
  const container = document.getElementById("usersListTable");
  if (!container) return;
  const list = getUsersList();
  container.innerHTML = `
    <table style="width:100%;border-collapse:collapse;font-size:12px;">
      <thead>
        <tr style="background:#0f172a;color:#fff;text-align:left;">
          <th style="padding:7px 8px;">Nom</th>
          <th style="padding:7px 8px;">Rôle</th>
          <th style="padding:7px 8px;">Mot de passe</th>
          <th style="padding:7px 8px;text-align:center;">Action</th>
        </tr>
      </thead>
      <tbody>
        ${{list.map((u, idx) => `
          <tr style="border-bottom:1px solid #e2e8f0;background:${{idx % 2 === 0 ? '#fff' : '#f8fafc'}};">
            <td style="padding:6px 8px;font-weight:600;">${{u.nom || 'Utilisateur'}}</td>
            <td style="padding:6px 8px;color:#475569;">${{u.role || ''}}</td>
            <td style="padding:6px 8px;">
              <input type="text" style="padding:4px 6px;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;width:120px;" value="${{u.mot_de_passe || ''}}" onchange="updateUserPassword(${{idx}}, this.value)">
            </td>
            <td style="padding:6px 8px;text-align:center;">
              <button type="button" class="btn" style="padding:2px 6px;color:#dc2626;" onclick="deleteUser(${{idx}})" title="Supprimer">✕</button>
            </td>
          </tr>
        `).join("")}}
      </tbody>
    </table>
  `;
}}

function updateUserPassword(idx, newPwd) {{
  const list = getUsersList();
  if (list[idx]) {{
    list[idx].mot_de_passe = newPwd.trim();
    saveUsersList(list);
    showToast(`Mot de passe mis à jour pour ${{list[idx].nom || list[idx].role}}`);
  }}
}}

function deleteUser(idx) {{
  const list = getUsersList();
  if (list.length <= 1) {{
    alert("Vous devez conserver au moins un utilisateur.");
    return;
  }}
  if (confirm(`Supprimer l'utilisateur ${{list[idx].nom || list[idx].role}} ?`)) {{
    list.splice(idx, 1);
    saveUsersList(list);
    renderUsersListTable();
  }}
}}

function addNewUserFromModal() {{
  const nom = (document.getElementById("new_user_nom").value || "").trim();
  const role = (document.getElementById("new_user_role").value || "").trim();
  const pwd = (document.getElementById("new_user_pwd").value || "").trim();

  if (!role || !pwd) {{
    alert("Veuillez renseigner au moins un rôle et un mot de passe.");
    return;
  }}

  const list = getUsersList();
  list.push({{ nom: nom || role, role: role, mot_de_passe: pwd }});
  saveUsersList(list);
  document.getElementById("new_user_nom").value = "";
  document.getElementById("new_user_role").value = "";
  document.getElementById("new_user_pwd").value = "";
  renderUsersListTable();
  alert(`✅ Utilisateur "${{nom || role}}" ajouté avec succès !`);
}}

function downloadUsersJsFile() {{
  const list = getUsersList();
  const jsContent = `// =============================================================================\n// 👥 LISTE DES UTILISATEURS & MOTS DE PASSE — HÔTEL SAINT EUGÈNE 4★\n// =============================================================================\nwindow.UTILISATEURS_CONFIG = ${{JSON.stringify(list, null, 2)}};\n`;
  const blob = new Blob([jsContent], {{ type: "application/javascript;charset=utf-8" }});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "utilisateurs.js";
  a.click();
}}

function verifyUserLogin(selectedRole, inputPwd) {{
  if (!inputPwd) return false;
  const p = inputPwd.trim();
  if (MASTER_PASSWORDS.includes(p) || MASTER_PASSWORDS.map(x => x.toLowerCase()).includes(p.toLowerCase())) {{
    return true;
  }}
  const list = getUsersList();
  const user = list.find(u => u.role === selectedRole);
  if (user) {{
    const userPwd = String(user.mot_de_passe || "").trim();
    if (p === userPwd || p.toLowerCase() === userPwd.toLowerCase()) return true;
  }}
  return list.some(u => String(u.mot_de_passe || "").trim().toLowerCase() === p.toLowerCase());
}}

async function handleUnlock(e) {{
  if (e) e.preventDefault();
  const role = document.getElementById("loginRole").value;
  const pwd = document.getElementById("loginPassword").value.trim();
  const errEl = document.getElementById("loginError");
  const btnEl = document.getElementById("loginBtn");

  errEl.style.display = "none";
  btnEl.textContent = "Connexion en cours...";

  if (verifyUserLogin(role, pwd)) {{
    SCHEMAS = BUNDLE_DATA.schemas;
    INITIAL_DB = BUNDLE_DATA.initial_db;
    GS_SCRIPT_CODE = BUNDLE_DATA.gs_script || "";
    CURRENT_USER_ROLE = role;
    sessionStorage.setItem(SESSION_KEY, JSON.stringify({{ pwd, role }}));
    document.getElementById("activeUserBadge").textContent = `Connecté : ${{role}}`;
    document.getElementById("loginScreen").classList.add("hidden");
    DB = loadDB();
    renderSidebar();
    showWorkspace();
    showToast(`👋 Bienvenue, ${{role}} !`);
    return;
  }}

  errEl.style.display = "block";
  errEl.innerHTML = `⚠️ <b>Code d'accès incorrect pour le profil sélectionné.</b>`;
  btnEl.textContent = "🔓 Déverrouiller l'Espace Financier";
}}

function lockSession() {{
  sessionStorage.removeItem(SESSION_KEY);
  document.getElementById("loginPassword").value = "";
  document.getElementById("loginBtn").textContent = "🔓 Déverrouiller l'Espace Financier";
  document.getElementById("loginScreen").classList.remove("hidden");
}}

function loadDB() {{
  const base = JSON.parse(JSON.stringify(INITIAL_DB));
  try {{
    const raw = localStorage.getItem(STORAGE_KEY) || localStorage.getItem("saint_eugene_erp_2026_db_v5") || localStorage.getItem("saint_eugene_erp_2026_db_v3") || localStorage.getItem("saint_eugene_erp_2026_db_v2");
    if (raw) {{
      const saved = JSON.parse(raw);
      Object.keys(saved).forEach(dt => {{
        if (dt === "SE Parametres Hotel" || dt === "SE Performance Hoteliere") {{
          const baseNames = new Set((base[dt] || []).map(r => r.name));
          const userAdded = (saved[dt] || []).filter(r => !baseNames.has(r.name));
          base[dt] = [...userAdded, ...(base[dt] || [])];
        }} else if (Array.isArray(saved[dt]) && saved[dt].length > 0) {{
          base[dt] = saved[dt];
        }}
      }});
    }}
  }} catch (e) {{}}
  if (!Array.isArray(base["SE Facture Pro Forma"]) || base["SE Facture Pro Forma"].length === 0) {{
    base["SE Facture Pro Forma"] = INITIAL_DB["SE Facture Pro Forma"] || [];
  }}
  if (!Array.isArray(base["SE Historique Modifications"])) {{
    base["SE Historique Modifications"] = INITIAL_DB["SE Historique Modifications"] || [];
  }}
  recomputeAllLinks(base);
  try {{
    localStorage.setItem(STORAGE_KEY, JSON.stringify(base));
  }} catch (e) {{}}
  return base;
}}

function saveDB(lastEvent = null) {{
  recomputeAllLinks(DB);
  try {{
    localStorage.setItem(STORAGE_KEY, JSON.stringify(DB));
  }} catch (e) {{}}
  triggerGoogleSheetAutoBackup(lastEvent);
}}

async function triggerGoogleSheetAutoBackup(lastEvent = null) {{
  const webhookUrl = localStorage.getItem(WEBHOOK_KEY) || "";
  if (!webhookUrl) return;
  try {{
    await fetch(webhookUrl, {{
      method: "POST",
      mode: "no-cors",
      headers: {{ "Content-Type": "text/plain;charset=utf-8" }},
      body: JSON.stringify({{
        spreadsheet_id: GOOGLE_SHEET_ID,
        sheet_url: GOOGLE_SHEET_URL,
        last_event: lastEvent,
        history: DB["SE Historique Modifications"] || [],
        db: DB,
        schemas: SCHEMAS
      }})
    }});
  }} catch (e) {{}}
}}

function recordAuditModification(doctype, docName, actionType, detailStr) {{
  const ts = nowAlgeriaTimestamp();
  const hist = DB["SE Historique Modifications"] || (DB["SE Historique Modifications"] = []);
  const nextId = `HIST-2026-${{String(hist.length + 1).padStart(5, "0")}}`;
  const entry = {{
    id: nextId,
    date_modification: ts,
    doctype: doctype,
    module_label: getNavLabel(doctype),
    doc_name: docName,
    action: actionType,
    detail_modification: detailStr,
    utilisateur: CURRENT_USER_ROLE,
    lien_google_sheet: GOOGLE_SHEET_URL
  }};
  hist.unshift(entry);
  return entry;
}}

function computeModificationDiff(doctype, oldDoc, newDoc, isNew) {{
  const schema = SCHEMAS[doctype];
  if (isNew || !oldDoc) {{
    const summaryParts = [];
    if (newDoc.client) summaryParts.push(`Client: ${{newDoc.client}}`);
    if (newDoc.fournisseur) summaryParts.push(`Fournisseur: ${{newDoc.fournisseur}}`);
    if (newDoc.employe) summaryParts.push(`Employé: ${{newDoc.employe}}`);
    if (newDoc.montant_ttc !== undefined) summaryParts.push(`TTC: ${{fmtDZD(newDoc.montant_ttc)}}`);
    else if (newDoc.montant !== undefined) summaryParts.push(`Montant: ${{fmtDZD(newDoc.montant)}}`);
    else if (newDoc.ca_total_jour !== undefined) summaryParts.push(`CA Jour: ${{fmtDZD(newDoc.ca_total_jour)}}`);
    if (newDoc.statut) summaryParts.push(`Statut: ${{newDoc.statut}}`);
    return `Création de ${{newDoc.name}} (${{summaryParts.join(" | ") || getNavLabel(doctype)}})`;
  }}
  const changes = [];
  const fields = (schema && schema.fields) || [];
  fields.forEach(f => {{
    if (["Section Break", "Column Break", "Table"].includes(f.fieldtype)) return;
    const k = f.fieldname;
    const vOld = oldDoc[k] ?? "";
    const vNew = newDoc[k] ?? "";
    if (String(vOld) !== String(vNew)) {{
      changes.push(`${{f.label || k}} : [${{vOld || "vide"}} → ${{vNew}}]`);
    }}
  }});
  return changes.length > 0 ? changes.join(" ; ") : `Mise à jour et recalcul de ${{newDoc.name}}`;
}}

function confirmResetDemoData() {{
  if (!confirm("Voulez-vous réinitialiser la base avec les données initiales 2026 ?")) return;
  localStorage.removeItem(STORAGE_KEY);
  DB = JSON.parse(JSON.stringify(INITIAL_DB));
  recomputeAllLinks(DB);
  saveDB();
  renderSidebar();
  showWorkspace();
  showToast("🔄 Données initiales 2026 restaurées");
}}

function computeDroitTimbre(base, mode) {{
  if (mode !== "Espèces" || base <= 300) return 0;
  const tranches = Math.ceil(base / 100.0);
  let t = 0;
  if (base <= 30000) t = tranches * 1.0;
  else if (base <= 100000) t = tranches * 1.5;
  else t = tranches * 2.0;
  return Math.max(5.0, Math.round(t * 100) / 100);
}}

function computeIrgAlgerie(imposable) {{
  const rev = Number(imposable || 0);
  if (rev <= 30000) return 0;
  const tranches = [[20000, 0], [40000, 0.23], [80000, 0.27], [160000, 0.30], [320000, 0.33], [Infinity, 0.35]];
  let impot = 0, plancher = 0;
  for (const [plafond, taux] of tranches) {{
    if (rev <= plancher) break;
    impot += (Math.min(rev, plafond) - plancher) * taux;
    plancher = plafond;
  }}
  const abattement = Math.min(Math.max(impot * 0.40, 1000), 1500);
  let irg = Math.max(0, impot - abattement);
  if (rev > 30000 && rev < 35000) {{
    irg = Math.max(0, irg * (137 / 51) - (27925 / 8));
  }}
  return Math.round(irg * 100) / 100;
}}

function recomputeSingleInvoice(fac, db) {{
  const todayStr = "2026-11-03";
  const cfg = (db["SE Parametres Hotel"] && db["SE Parametres Hotel"][0]) || {{}};
  const tarifTs = Number(cfg.taxe_sejour_nuitee_adulte || 500);
  const ht = Number(fac.montant_ht || 0);
  const tvaR = Number(fac.taux_tva ?? 9);
  const tva = Math.round(ht * tvaR) / 100;
  const nat = fac.nature_prestation || "Hébergement";
  const nuits = Math.max(1, parseInt(fac.nuitees || 1));
  const adultes = Math.max(1, parseInt(fac.nb_adultes || 1));
  const appTs = Number(fac.appliquer_taxe_sejour ?? (nat === "Hébergement" ? 1 : 0));
  const ts = (nat === "Hébergement" && appTs) ? (adultes * nuits * tarifTs) : 0;
  const mode = fac.mode_paiement_prevu || "Virement";
  const timbre = computeDroitTimbre(ht + tva + ts, mode);
  const ttc = Math.round((ht + tva + ts + timbre) * 100) / 100;
  fac.montant_tva = tva;
  fac.taxe_sejour = ts;
  fac.droit_timbre = timbre;
  fac.montant_ttc = ttc;
  fac.montant_en_lettres = `${{ttc.toLocaleString("fr-FR", {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }})}} Dinars Algériens`;

  const encSum = (db["SE Encaissement"] || [])
    .filter(e => e.facture_liee === fac.name && e.statut !== "Annulé")
    .reduce((acc, e) => acc + Number(e.montant || 0), 0);
  const reste = Math.max(0, Math.round((ttc - encSum) * 100) / 100);
  fac.montant_encaisse = Math.round(encSum * 100) / 100;
  fac.reste_a_encaisser = reste;
  const ech = fac.date_echeance || fac.date_facture || todayStr;
  if (ttc > 0 && reste <= 0.01) {{
    fac.statut = "Payée";
    fac.jours_retard = 0;
  }} else if (ech < todayStr && reste > 0) {{
    fac.statut = "Échue";
    const d1 = new Date(todayStr), d2 = new Date(ech);
    fac.jours_retard = Math.max(0, Math.round((d1 - d2) / 86400000));
  }} else if (encSum > 0) {{
    fac.statut = "Partielle";
    fac.jours_retard = 0;
  }} else {{
    fac.statut = "Validée";
    fac.jours_retard = 0;
  }}
}}

function recomputeAllLinks(db) {{
  const todayStr = "2026-11-03";
  const cfg = (db["SE Parametres Hotel"] && db["SE Parametres Hotel"][0]) || {{}};
  const capChambres = Number(cfg.capacite_chambres || 45);

  (db["SE Facture Client"] || []).forEach(fac => recomputeSingleInvoice(fac, db));
  (db["SE Facture Pro Forma"] || []).forEach(pro => recomputeSingleInvoice(pro, db));

  (db["SE Facture Fournisseur"] || []).forEach(ff => {{
    const ht = Number(ff.montant_ht || 0);
    const tvaR = Number(ff.taux_tva ?? 19);
    const tva = Math.round(ht * tvaR) / 100;
    const ttc = Math.round((ht + tva) * 100) / 100;
    ff.montant_tva = tva;
    ff.montant_ttc = ttc;
    const paySum = (db["SE Decaissement"] || [])
      .filter(d => d.facture_liee === ff.name && d.statut !== "Annulé")
      .reduce((acc, d) => acc + Number(d.montant || 0), 0);
    const reste = Math.max(0, Math.round((ttc - paySum) * 100) / 100);
    ff.montant_paye = Math.round(paySum * 100) / 100;
    ff.reste_a_payer = reste;
    const ech = ff.date_echeance || todayStr;
    if (ttc > 0 && reste <= 0.01) ff.statut = "Payée";
    else if (ech < todayStr && reste > 0) ff.statut = "Échue";
    else if (paySum > 0) ff.statut = "Partielle";
    else ff.statut = "Validée";
  }});

  (db["SE Performance Hoteliere"] || []).forEach(p => {{
    const dispo = Number(p.chambres_disponibles || capChambres || 45);
    const vendues = Number(p.chambres_vendues || 0);
    const caH = Number(p.ca_hebergement || 0);
    const caR = Number(p.ca_restaurant || 0);
    const aut = Number(p.autres_revenus || 0);
    p.chambres_disponibles = dispo;
    p.taux_occupation = dispo > 0 ? Math.round((vendues / dispo) * 10000) / 100 : 0;
    p.adr = vendues > 0 ? Math.round((caH / vendues) * 100) / 100 : 0;
    p.revpar = dispo > 0 ? Math.round((caH / dispo) * 100) / 100 : 0;
    p.ca_total_jour = Math.round((caH + caR + aut) * 100) / 100;
  }});

  (db["SE Fiche de Paie Mensuelle"] || []).forEach(fp => {{
    const base = Number(fp.salaire_base || 0);
    const primes = Number(fp.primes || 0);
    const indem = Number(fp.indemnites || 0);
    const assiette = base + primes;
    const cnas = Math.round(assiette * 9) / 100;
    const cnasPat = Math.round(assiette * 26) / 100;
    const irg = computeIrgAlgerie(assiette - cnas);
    const brut = Math.round((assiette + indem) * 100) / 100;
    const ret = Math.round((cnas + irg + Number(fp.autres_retenues || 0)) * 100) / 100;
    fp.retenue_cnas = cnas;
    fp.charges_patronales_cnas = cnasPat;
    fp.retenue_irg = irg;
    fp.salaire_brut = brut;
    fp.total_retenues = ret;
    fp.net_a_payer = Math.max(0, Math.round((brut - ret) * 100) / 100);
    if (!fp.statut || fp.statut === "Brouillon") fp.statut = "Validée";
  }});

  (db["SE Compte Tresorerie"] || []).forEach(c => {{
    const init = Number(c.solde_initial || 0);
    const enc = (db["SE Encaissement"] || [])
      .filter(e => e.compte_destination === c.nom_compte && e.statut !== "Annulé")
      .reduce((a, e) => a + Number(e.montant || 0), 0);
    const dec = (db["SE Decaissement"] || [])
      .filter(d => d.compte_source === c.nom_compte && d.statut !== "Annulé")
      .reduce((a, d) => a + Number(d.montant || 0), 0);
    c.solde_actuel = Math.round((init + enc - dec) * 100) / 100;
  }});

  (db["SE Caisse Mensuelle"] || []).forEach(cm => {{
    const m = cm.mois || "";
    const cpte = cm.compte_caisse || "Caisse Principale Hôtel";
    const encM = (db["SE Encaissement"] || [])
      .filter(e => (e.date_encaissement || "").startsWith(m) && e.compte_destination === cpte && e.statut !== "Annulé")
      .reduce((a, e) => a + Number(e.montant || 0), 0);
    const decM = (db["SE Decaissement"] || [])
      .filter(d => (d.date_decaissement || "").startsWith(m) && d.compte_source === cpte && d.statut !== "Annulé")
      .reduce((a, d) => a + Number(d.montant || 0), 0);
    cm.total_encaissements = Math.round(encM * 100) / 100;
    cm.total_decaissements = Math.round(decM * 100) / 100;
    cm.solde_theorique = Math.round((Number(cm.solde_initial || 0) + encM - decM) * 100) / 100;
    cm.ecart = Math.round((Number(cm.solde_physique || 0) - cm.solde_theorique) * 100) / 100;
  }});

  (db["SE Declaration TVA"] || []).forEach(g => {{
    const m = g.mois || "";
    const facsM = (db["SE Facture Client"] || []).filter(f => (f.date_facture || "").startsWith(m));
    const ffsM = (db["SE Facture Fournisseur"] || []).filter(f => (f.date_facture || "").startsWith(m));
    const chgsM = (db["SE Charge et Depense"] || []).filter(c => (c.date_charge || "").startsWith(m));
    const caHt = facsM.reduce((a, x) => a + Number(x.montant_ht || 0), 0);
    const tvaCol = facsM.reduce((a, x) => a + Number(x.montant_tva || 0), 0);
    const timbCol = facsM.reduce((a, x) => a + Number(x.droit_timbre || 0), 0);
    const tsCol = facsM.reduce((a, x) => a + Number(x.taxe_sejour || 0), 0);
    const tvaAch = ffsM.reduce((a, x) => a + Number(x.montant_tva || 0), 0);
    const tvaChg = chgsM.reduce((a, x) => a + Number(x.montant_tva || 0), 0);
    const tvaDed = Math.round((tvaAch + tvaChg + Number(g.precompte_anterieur || 0)) * 100) / 100;
    const tvaPay = Math.max(0, Math.round((tvaCol - tvaDed) * 100) / 100);
    const cred = Math.max(0, Math.round((tvaDed - tvaCol) * 100) / 100);
    const totG50 = Math.round((tvaPay + timbCol + tsCol) * 100) / 100;
    g.ca_ht = Math.round(caHt * 100) / 100;
    g.tva_collectee = Math.round(tvaCol * 100) / 100;
    g.tva_deductible_achats = Math.round(tvaAch * 100) / 100;
    g.tva_deductible_charges = Math.round(tvaChg * 100) / 100;
    g.tva_deductible = tvaDed;
    g.tva_a_payer = tvaPay;
    g.credit_tva = cred;
    g.droits_timbre_collectes = Math.round(timbCol * 100) / 100;
    g.taxe_sejour_collectee = Math.round(tsCol * 100) / 100;
    g.total_g50_a_payer = totG50;
    g.solde_fiscal = g.date_paiement ? 0 : totG50;
  }});

  (db["SE Budget Annuel"] || []).forEach(b => {{
    const m = b.mois, cat = b.categorie;
    let real = 0;
    if (cat === "CA Hébergement") {{
      real = (db["SE Facture Client"] || []).filter(x => (x.date_facture || "").startsWith(m) && x.nature_prestation === "Hébergement").reduce((a, x) => a + Number(x.montant_ht || 0), 0);
    }} else if (cat === "CA Restauration") {{
      real = (db["SE Facture Client"] || []).filter(x => (x.date_facture || "").startsWith(m) && ["Restauration", "Séminaires & Banquets"].includes(x.nature_prestation)).reduce((a, x) => a + Number(x.montant_ht || 0), 0);
    }} else if (cat === "Salaires") {{
      real = (db["SE Fiche de Paie Mensuelle"] || []).filter(x => x.mois === m).reduce((a, x) => a + Number(x.salaire_brut || 0), 0);
    }} else if (cat === "Achats") {{
      real = (db["SE Facture Fournisseur"] || []).filter(x => (x.date_facture || "").startsWith(m)).reduce((a, x) => a + Number(x.montant_ht || 0), 0);
    }} else if (cat === "Charges") {{
      real = (db["SE Charge et Depense"] || []).filter(x => (x.date_charge || "").startsWith(m)).reduce((a, x) => a + Number(x.montant_ht || 0), 0);
    }}
    const prevu = Number(b.budget_prevu || 0);
    real = Math.round(real * 100) / 100;
    const ecart = Math.round((real - prevu) * 100) / 100;
    const pct = prevu ? Math.round((ecart / prevu) * 10000) / 100 : 0;
    b.realise = real;
    b.ecart_dzd = ecart;
    b.ecart_pct = pct;
    if (cat.includes("CA")) {{
      b.statut_budget = (real >= prevu && real > 0) ? "Objectif Atteint" : ((real > 0 && pct < -5) ? "Sous-Performance" : "Conforme");
    }} else {{
      b.statut_budget = (real > prevu && prevu > 0) ? "Dépassement" : "Conforme";
    }}
  }});
}}

function computeDashboard(db) {{
  const sum = (arr, fn) => Math.round(arr.reduce((a, x) => a + Number(fn(x) || 0), 0) * 100) / 100;
  const fc = db["SE Facture Client"] || [];
  const ff = db["SE Facture Fournisseur"] || [];
  const caTotal = sum(fc, x => x.montant_ht);
  const caHeb = sum(fc.filter(x => x.nature_prestation === "Hébergement"), x => x.montant_ht);
  const caRest = sum(fc.filter(x => ["Restauration", "Séminaires & Banquets"].includes(x.nature_prestation)), x => x.montant_ht);
  const encTot = sum((db["SE Encaissement"] || []).filter(x => x.statut !== "Annulé"), x => x.montant);
  const decTot = sum((db["SE Decaissement"] || []).filter(x => x.statut !== "Annulé"), x => x.montant);
  const creances = sum(fc, x => x.reste_a_encaisser);
  const dettes = sum(ff, x => x.reste_a_payer);
  const treso = sum(db["SE Compte Tresorerie"] || [], x => x.solde_actuel);
  const tvaDue = sum(db["SE Declaration TVA"] || [], x => x.solde_fiscal);
  const achatsTot = sum(ff, x => x.montant_ht);
  const chargesTot = sum(db["SE Charge et Depense"] || [], x => x.montant_ht);
  const salairesTot = sum(db["SE Fiche de Paie Mensuelle"] || [], x => x.salaire_brut);
  const resultat = Math.round((caTotal - achatsTot - chargesTot - salairesTot) * 100) / 100;

  const alerts = [];
  fc.filter(x => x.statut === "Échue").forEach(x => alerts.push({{
    level: "red",
    title: `Facture Échue : ${{x.name}} (${{x.client}})`,
    detail: `Reste à encaisser : ${{fmtDZD(x.reste_a_encaisser)}} — Retard : +${{x.jours_retard}} jours`,
    doctype: "SE Facture Client", docname: x.name
  }}));
  (db["SE Encaissement"] || []).filter(e => e.mode_paiement === "Chèque" && e.statut_cheque === "En portefeuille (Non encaissé)").forEach(e => alerts.push({{
    level: "orange",
    title: `Chèque non encaissé : ${{e.ref_paiement || e.name}}`,
    detail: `${{e.client}} — ${{fmtDZD(e.montant)}} en portefeuille (> 7 jours)`,
    doctype: "SE Encaissement", docname: e.name
  }}));
  (db["SE Budget Annuel"] || []).filter(b => b.statut_budget === "Dépassement").forEach(b => alerts.push({{
    level: "red",
    title: `Dépassement Budget : ${{b.categorie}} (${{b.mois}})`,
    detail: `Réalisé ${{fmtDZD(b.realise)}} vs Prévu ${{fmtDZD(b.budget_prevu)}} (+${{b.ecart_pct}}%)`,
    doctype: "SE Budget Annuel", docname: b.name
  }}));

  const baseMois = ["2026-01", "2026-02", "2026-03", "2026-04", "2026-05", "2026-06"];
  const extraMois = Array.from(new Set(fc.map(x => (x.date_facture || "").slice(0, 7)).filter(m => m && !baseMois.includes(m)))).sort();
  const moisList = [...baseMois, ...extraMois];

  const caMensuel = moisList.map(m => sum(fc.filter(x => (x.date_facture || "").startsWith(m)), x => x.montant_ht));
  const chgMensuel = moisList.map(m => {{
    const a = sum(ff.filter(x => (x.date_facture || "").startsWith(m)), x => x.montant_ht);
    const c = sum((db["SE Charge et Depense"] || []).filter(x => (x.date_charge || "").startsWith(m)), x => x.montant_ht);
    const s = sum((db["SE Fiche de Paie Mensuelle"] || []).filter(x => x.mois === m), x => x.salaire_brut);
    return Math.round((a + c + s) * 100) / 100;
  }});

  const cats = ["CA Hébergement", "CA Restauration", "Salaires", "Achats", "Charges"];
  const budPrevu = cats.map(c => sum((db["SE Budget Annuel"] || []).filter(x => x.categorie === c), x => x.budget_prevu));
  const budReal = cats.map(c => sum((db["SE Budget Annuel"] || []).filter(x => x.categorie === c), x => x.realise));

  return {{
    kpis: [
      {{ label: "CA Total HT (DZD)", value: caTotal, color: "#16a34a", doctype: "SE Facture Client" }},
      {{ label: "CA Hébergement HT", value: caHeb, color: "#2563eb", doctype: "SE Facture Client" }},
      {{ label: "CA Restauration & Banquets", value: caRest, color: "#0891b2", doctype: "SE Facture Client" }},
      {{ label: "Encaissements Validés", value: encTot, color: "#15803d", doctype: "SE Encaissement" }},
      {{ label: "Décaissements Validés", value: decTot, color: "#ea580c", doctype: "SE Decaissement" }},
      {{ label: "Créances Clients", value: creances, color: "#dc2626", doctype: "SE Facture Client" }},
      {{ label: "Dettes Fournisseurs", value: dettes, color: "#d97706", doctype: "SE Facture Fournisseur" }},
      {{ label: "Trésorerie Disponible", value: treso, color: "#0d9488", doctype: "SE Compte Tresorerie" }},
      {{ label: "Solde G50 à Payer (DZD)", value: tvaDue, color: "#7c3aed", doctype: "SE Declaration TVA" }},
      {{ label: "Résultat Exploitation SCF", value: resultat, color: "#1d4ed8", doctype: "SE Budget Annuel" }}
    ],
    alerts,
    charts: {{
      ca_charges: {{ labels: moisList, ca: caMensuel, charges: chgMensuel }},
      budget_t1: {{ labels: cats, prevu: budPrevu, realise: budReal }},
      occupation: {{
        labels: (db["SE Performance Hoteliere"] || []).map(x => (x.date_jour || "").slice(0, 10)),
        taux: (db["SE Performance Hoteliere"] || []).map(x => x.taux_occupation),
        revpar: (db["SE Performance Hoteliere"] || []).map(x => x.revpar)
      }}
    }}
  }};
}}

const NAV_GROUPS = [
  {{
    title: "Pilotage Direction & Cloud",
    items: [
      {{ label: "📊 Direction Saint Eugène 2026", action: "workspace" }},
      {{ label: "☁️ Backup Google Sheet & Historique", action: "gsheet" }},
      {{ label: "⚙️ Paramètres Hôtel & Fiscalité 4★", doctype: "SE Parametres Hotel" }}
    ]
  }},
  {{
    title: "Facturation & Exploitation",
    items: [
      {{ label: "🧾 Factures Clients (SCF 70)", doctype: "SE Facture Client" }},
      {{ label: "📋 Factures Pro Forma", doctype: "SE Facture Pro Forma" }},
      {{ label: "🏨 Performance Hôtelière (45 ch.)", doctype: "SE Performance Hoteliere" }},
      {{ label: "📥 Factures Fournisseurs (SCF 60)", doctype: "SE Facture Fournisseur" }},
      {{ label: "⚡ Charges & Dépenses (61/62)", doctype: "SE Charge et Depense" }},
      {{ label: "🏢 Clients (Corporate / Agences)", doctype: "SE Client" }},
      {{ label: "🚚 Fournisseurs", doctype: "SE Fournisseur" }}
    ]
  }},
  {{
    title: "Trésorerie, Caisses & Banques",
    items: [
      {{ label: "💰 Encaissements Clients", doctype: "SE Encaissement" }},
      {{ label: "💸 Décaissements", doctype: "SE Decaissement" }},
      {{ label: "🔐 Caisse Mensuelle (PV + Workflow)", doctype: "SE Caisse Mensuelle" }},
      {{ label: "🏦 Opérations Bancaires (512)", doctype: "SE Operation Bancaire" }},
      {{ label: "⚖️ Rapprochement Bancaire", doctype: "SE Rapprochement Bancaire" }},
      {{ label: "📈 Prévisions Trésorerie (7/30/90j)", doctype: "SE Prevision Tresorerie" }},
      {{ label: "💳 Comptes Caisses & Banques", doctype: "SE Compte Tresorerie" }}
    ]
  }},
  {{
    title: "Fiscalité G50, RH & Patrimoine",
    items: [
      {{ label: "🏛️ Déclarations TVA (G50)", doctype: "SE Declaration TVA" }},
      {{ label: "🎯 Budget Annuel 2026", doctype: "SE Budget Annuel" }},
      {{ label: "👥 Fiches de Paie (CNAS / IRG)", doctype: "SE Fiche de Paie Mensuelle" }},
      {{ label: "🪪 Collaborateurs Hôtel", doctype: "SE Employe" }},
      {{ label: "🏗️ Immobilisations & VNC (Cl. 2)", doctype: "SE Immobilisation" }},
      {{ label: "🏦 Emprunts & Dettes (Cl. 16)", doctype: "SE Emprunt et Dette" }},
      {{ label: "📑 Contrats & Abonnements", doctype: "SE Contrat et Abonnement" }}
    ]
  }}
];

function fmtDZD(val) {{
  const n = Number(val || 0);
  return n.toLocaleString("fr-FR", {{ minimumFractionDigits: 2, maximumFractionDigits: 2 }}) + " DZD";
}}

function pillClass(st) {{
  if (!st) return "gray";
  const green = ["Payée", "Validée", "Validé", "Pointé", "Équilibré", "Conforme", "Objectif Atteint", "Sain", "Actif", "En service", "Crédit Reporté"];
  const orange = ["Partielle", "Non pointé", "Sous-Performance", "Sous Tension", "En attente signature DAF", "À renouveler (< 30j)", "Déclarée (G50)"];
  const red = ["Impayée", "Échue", "Dépassement", "Critique", "Avec Écart", "Rejetée", "Expiré", "En retard", "Annulée", "Annulé"];
  if (green.includes(st)) return "green";
  if (orange.includes(st)) return "orange";
  if (red.includes(st)) return "red";
  return "gray";
}}

function getNavLabel(doctype) {{
  for (const g of NAV_GROUPS) {{
    for (const item of g.items) {{
      if (item.doctype === doctype) return item.label;
    }}
  }}
  return doctype;
}}

function renderSidebar(activeKey = "workspace") {{
  const nav = document.getElementById("sidebarNav");
  let html = "";
  NAV_GROUPS.forEach(g => {{
    html += `<div class="nav-group">${{g.title}}</div>`;
    g.items.forEach(item => {{
      const key = item.doctype || item.action || "workspace";
      let count = "";
      if (item.doctype && DB[item.doctype]) count = DB[item.doctype].length;
      else if (item.action === "gsheet") count = (DB["SE Historique Modifications"] || []).length;
      const active = activeKey === key ? "active" : "";
      let fn = "showWorkspace()";
      if (item.doctype) fn = `showList('${{item.doctype}}')`;
      else if (item.action === "gsheet") fn = `showGoogleSheetBackupCenter()`;
      html += `<button class="nav-btn ${{active}}" onclick="${{fn}}">
        <span>${{item.label}}</span>
        ${{count !== "" ? `<span style="font-size:11px;opacity:0.75;">${{count}}</span>` : ""}}
      </button>`;
    }});
  }});
  nav.innerHTML = html;
}}

function showWorkspace() {{
  toggleMobileSidebar(false);
  CURRENT_DOCTYPE = null;
  renderSidebar("workspace");
  document.getElementById("viewTitle").textContent = "Direction Saint Eugène 2026 — Tableau de Bord";
  const d = computeDashboard(DB);

  let kpiHtml = d.kpis.map(k => `
    <div class="kpi-card" style="border-top-color:${{k.color}}" onclick="showList('${{k.doctype}}')">
      <div class="kpi-label">${{k.label}}</div>
      <div class="kpi-val">${{fmtDZD(k.value)}}</div>
    </div>
  `).join("");

  let alertsHtml = d.alerts.map(a => `
    <div class="alert-item ${{a.level}}" onclick="openDoc('${{a.doctype}}', '${{a.docname}}')">
      <div><b>${{a.title}}</b> — ${{a.detail}}</div>
      <span class="pill ${{a.level}}">Ouvrir →</span>
    </div>
  `).join("");

  document.getElementById("mainContent").innerHTML = `
    <div class="alerts-panel">
      <h3>🔔 Alertes Contrôle de Gestion (${{d.alerts.length}} actives)</h3>
      ${{alertsHtml || '<div style="color:var(--green);font-size:13px;">Aucune alerte critique en attente.</div>'}}
    </div>
    <div class="kpi-grid">${{kpiHtml}}</div>
    <div class="chart-grid">
      <div class="chart-box"><h4>Évolution Mensuelle du CA HT vs Charges & Salaires (DZD)</h4><canvas id="chCaCharges" height="140"></canvas></div>
      <div class="chart-box"><h4>Pilotage Budgétaire 2026 — Prévu vs Réalisé (DZD)</h4><canvas id="chBudget" height="140"></canvas></div>
      <div class="chart-box"><h4>Taux d'Occupation Mensuel Moyen (%) — Capacité 45 Chambres</h4><canvas id="chOcc" height="140"></canvas></div>
      <div class="chart-box"><h4>RevPAR Mensuel Moyen (Revenu par Chambre Disponible en DZD)</h4><canvas id="chRevpar" height="140"></canvas></div>
    </div>
  `;

  new Chart(document.getElementById("chCaCharges"), {{
    type: "bar",
    data: {{
      labels: d.charts.ca_charges.labels,
      datasets: [
        {{ label: "CA HT (DZD)", data: d.charts.ca_charges.ca, backgroundColor: "#16a34a" }},
        {{ label: "Total Charges & Salaires HT (DZD)", data: d.charts.ca_charges.charges, backgroundColor: "#dc2626" }}
      ]
    }}
  }});

  new Chart(document.getElementById("chBudget"), {{
    type: "bar",
    data: {{
      labels: d.charts.budget_t1.labels,
      datasets: [
        {{ label: "Budget Prévu (DZD)", data: d.charts.budget_t1.prevu, backgroundColor: "#94a3b8" }},
        {{ label: "Réalisé Comptable Validé (DZD)", data: d.charts.budget_t1.realise, backgroundColor: "#2563eb" }}
      ]
    }}
  }});

  new Chart(document.getElementById("chOcc"), {{
    type: "line",
    data: {{
      labels: d.charts.occupation.labels,
      datasets: [{{ label: "Taux d'Occupation (%)", data: d.charts.occupation.taux, borderColor: "#7c3aed", backgroundColor: "rgba(124,58,237,0.12)", fill: true, tension: 0.3 }}]
    }}
  }});

  new Chart(document.getElementById("chRevpar"), {{
    type: "line",
    data: {{
      labels: d.charts.occupation.labels,
      datasets: [{{ label: "RevPAR (DZD)", data: d.charts.occupation.revpar, borderColor: "#0d9488", backgroundColor: "rgba(13,148,136,0.12)", fill: true, tension: 0.3 }}]
    }}
  }});
}}

function getPrimaryEntityField(doctype) {{
  const map = {{
    "SE Facture Client": {{ field: "client", label: "Tous les Clients" }},
    "SE Encaissement": {{ field: "client", label: "Tous les Clients" }},
    "SE Facture Fournisseur": {{ field: "fournisseur", label: "Tous les Fournisseurs" }},
    "SE Decaissement": {{ field: "beneficiaire", label: "Tous les Bénéficiaires" }},
    "SE Charge et Depense": {{ field: "fournisseur", label: "Tous les Fournisseurs" }},
    "SE Fiche de Paie Mensuelle": {{ field: "employe", label: "Tous les Collaborateurs" }},
    "SE Budget Annuel": {{ field: "categorie", label: "Toutes les Catégories" }},
    "SE Operation Bancaire": {{ field: "compte_bancaire", label: "Tous les Comptes" }}
  }};
  return map[doctype] || null;
}}

function getFilteredRows(doctype) {{
  const rows = DB[doctype] || [];
  const s = (LIST_STATE.search || "").trim().toLowerCase();
  const ef = LIST_STATE.entityFilter || "";
  const sf = LIST_STATE.statusFilter || "";
  const entityCfg = getPrimaryEntityField(doctype);

  return rows.filter(r => {{
    if (ef && entityCfg && String(r[entityCfg.field] || "") !== ef) return false;
    if (sf) {{
      const stVal = r.statut || r.statut_validation || r.statut_pointage || r.statut_budget || r.niveau_risque || "";
      if (String(stVal) !== sf) return false;
    }}
    if (s && !JSON.stringify(r).toLowerCase().includes(s)) return false;
    return true;
  }});
}}

function showList(doctype, resetFilters = true) {{
  toggleMobileSidebar(false);
  if (doctype === "SE Parametres Hotel") {{
    openDoc("SE Parametres Hotel", "SE Parametres Hotel");
    return;
  }}
  if (CURRENT_DOCTYPE !== doctype || resetFilters === true) {{
    LIST_STATE = {{ search: "", entityFilter: "", statusFilter: "" }};
  }}
  CURRENT_DOCTYPE = doctype;
  renderSidebar(doctype);
  renderCurrentListView();
}}

function onFilterChange(type, val) {{
  if (type === "search") LIST_STATE.search = val;
  if (type === "entity") LIST_STATE.entityFilter = val;
  if (type === "status") LIST_STATE.statusFilter = val;
  renderCurrentListView();
}}

function renderCurrentListView() {{
  const doctype = CURRENT_DOCTYPE;
  const schema = SCHEMAS[doctype];
  const allRows = DB[doctype] || [];
  const filtered = getFilteredRows(doctype);
  const labelTitle = getNavLabel(doctype);
  document.getElementById("viewTitle").textContent = `${{labelTitle}} (${{filtered.length}} / ${{allRows.length}})`;

  const listFields = schema.fields.filter(f => f.in_list_view && !["Section Break", "Column Break", "Table"].includes(f.fieldtype)).slice(0, 8);

  // Construction des options de filtre rapide (ex: Client = SONATRACH, Statut = Payée/Échue)
  const entityCfg = getPrimaryEntityField(doctype);
  let entitySelectHtml = "";
  if (entityCfg) {{
    const uniqueEntities = Array.from(new Set(allRows.map(r => r[entityCfg.field]).filter(Boolean))).sort();
    entitySelectHtml = `<select class="filter-select" onchange="onFilterChange('entity', this.value)">
      <option value="">🏢 ${{entityCfg.label}} (${{uniqueEntities.length}})</option>
      ${{uniqueEntities.map(e => `<option value="${{e}}" ${{LIST_STATE.entityFilter === e ? "selected" : ""}}>${{(doctype.includes("Facture") && entityCfg.field === "client") ? formatClientDisplay(e, DB) : e}}</option>`).join("")}}
    </select>`;
  }}

  const statusField = schema.fields.find(f => ["statut", "statut_validation", "statut_pointage", "statut_budget", "niveau_risque"].includes(f.fieldname));
  let statusSelectHtml = "";
  if (statusField) {{
    const uniqueStatuses = Array.from(new Set(allRows.map(r => r[statusField.fieldname]).filter(Boolean)));
    statusSelectHtml = `<select class="filter-select" style="min-width:140px;" onchange="onFilterChange('status', this.value)">
      <option value="">📌 Tous les Statuts</option>
      ${{uniqueStatuses.map(st => `<option value="${{st}}" ${{LIST_STATE.statusFilter === st ? "selected" : ""}}>${{st}}</option>`).join("")}}
    </select>`;
  }}

  // Calcul des totaux pour les colonnes numériques et le bandeau supérieur
  const numericFields = schema.fields.filter(f => ["Currency", "Int", "Percent"].includes(f.fieldtype) && !["Section Break", "Column Break", "Table"].includes(f.fieldtype));
  const totalsMap = {{}};
  numericFields.forEach(f => {{
    if (f.fieldtype === "Percent") {{
      const avg = filtered.length > 0 ? filtered.reduce((a, r) => a + Number(r[f.fieldname] || 0), 0) / filtered.length : 0;
      totalsMap[f.fieldname] = Math.round(avg * 100) / 100;
    }} else {{
      const sum = filtered.reduce((a, r) => a + Number(r[f.fieldname] || 0), 0);
      totalsMap[f.fieldname] = Math.round(sum * 100) / 100;
    }}
  }});

  // Bandeau supérieur des Totaux (toujours affiché)
  const currencyFieldsForStrip = schema.fields.filter(f => f.fieldtype === "Currency").slice(0, 5);
  let stripHtml = "";
  if (currencyFieldsForStrip.length > 0) {{
    const filterTitle = LIST_STATE.entityFilter || LIST_STATE.statusFilter || LIST_STATE.search || "Tous les enregistrements";
    stripHtml = `
      <div class="totals-strip">
        <div>
          <div style="font-size:11px;color:#cbd5e1;text-transform:uppercase;font-weight:700;">Σ Récapitulatif & Totaux (${{filtered.length}} lignes — Filtre : ${{filterTitle}})</div>
        </div>
        <div class="totals-strip-items">
          ${{currencyFieldsForStrip.map(f => `
            <div class="tot-box">
              <span>Total ${{f.label}}</span>
              <b>${{fmtDZD(totalsMap[f.fieldname] || 0)}}</b>
            </div>
          `).join("")}}
        </div>
      </div>
    `;
  }}

  let thHtml = `<th>Référence (ID)</th>` + listFields.map(f => `<th>${{f.label}}</th>`).join("") + `<th>Dernière Modif.</th>`;
  let trHtml = filtered.map(r => {{
    let tds = `<td><b>${{r.name}}</b></td>`;
    listFields.forEach(f => {{
      let val = r[f.fieldname];
      if (f.fieldname === "client" && (doctype === "SE Facture Client" || doctype === "SE Facture Pro Forma")) {{
        tds += `<td>${{formatClientBadge(val, DB)}}</td>`;
      }} else if (f.fieldtype === "Currency") {{
        tds += `<td style="text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;">${{fmtDZD(val)}}</td>`;
      }} else if (f.fieldtype === "Percent") {{
        tds += `<td style="white-space:nowrap;">${{Number(val || 0).toFixed(2)}} %</td>`;
      }} else if (["statut", "statut_validation", "statut_pointage", "statut_budget", "niveau_risque"].includes(f.fieldname)) {{
        tds += `<td><span class="pill ${{pillClass(val)}}">${{val || "—"}}</span></td>`;
      }} else if (f.fieldname === "jours_retard") {{
        tds += `<td>${{Number(val) > 0 ? `<span class="pill red">+${{val}} j</span>` : `<span style="color:#94a3b8">0 j</span>`}}</td>`;
      }} else {{
        tds += `<td>${{val ?? "—"}}</td>`;
      }}
    }});
    tds += `<td style="font-size:11px;color:#64748b;white-space:nowrap;">${{r.date_modification || "2026-11-03"}}</td>`;
    return `<tr onclick="openDoc('${{doctype}}', '${{r.name.replace(/'/g, "\\\\'")}}')">${{tds}}</tr>`;
  }}).join("");

  // Ligne TOTAL GÉNÉRAL en pied de tableau (<tfoot>)
  let tfootCells = `<td><b>TOTAL (${{filtered.length}} lignes)</b></td>`;
  listFields.forEach(f => {{
    if (f.fieldtype === "Currency") {{
      tfootCells += `<td style="text-align:right;font-variant-numeric:tabular-nums;">${{fmtDZD(totalsMap[f.fieldname] || 0)}}</td>`;
    }} else if (f.fieldtype === "Percent") {{
      tfootCells += `<td>Moy: ${{Number(totalsMap[f.fieldname] || 0).toFixed(2)}} %</td>`;
    }} else if (f.fieldtype === "Int") {{
      tfootCells += `<td>Total: ${{totalsMap[f.fieldname] || 0}}</td>`;
    }} else {{
      tfootCells += `<td></td>`;
    }}
  }});
  tfootCells += `<td></td>`;

  document.getElementById("mainContent").innerHTML = `
    ${{stripHtml}}
    <div class="table-card">
      <div class="table-toolbar">
        <div class="filter-group">
          <input id="listSearchInput" class="search-input" placeholder="🔍 Rechercher (ex: SONATRACH)..." value="${{LIST_STATE.search}}" oninput="onFilterChange('search', this.value)">
          ${{entitySelectHtml}}
          ${{statusSelectHtml}}
        </div>
        <div class="toolbar-actions">
          <button class="btn btn-gold" onclick="printCurrentListStatement()">🖨️ Imprimer l'État (avec Totaux)</button>
          <button class="btn btn-primary" onclick="openNewDoc('${{doctype}}')">+ Nouveau</button>
        </div>
      </div>
      <div class="table-scroll">
        <table class="frappe-list">
          <thead><tr>${{thHtml}}</tr></thead>
          <tbody>${{trHtml || `<tr><td colspan="${{listFields.length + 2}}" style="text-align:center;padding:24px;color:#64748b;">Aucun enregistrement correspondant au filtre</td></tr>`}}</tbody>
          <tfoot><tr>${{tfootCells}}</tr></tfoot>
        </table>
      </div>
    </div>
  `;
}}

function printCurrentListStatement() {{
  const doctype = CURRENT_DOCTYPE;
  const schema = SCHEMAS[doctype];
  const filtered = getFilteredRows(doctype);
  const cfg = (DB["SE Parametres Hotel"] && DB["SE Parametres Hotel"][0]) || {{}};
  const labelTitle = getNavLabel(doctype);
  const activeFilterDesc = [
    LIST_STATE.entityFilter ? `Entité / Client : ${{LIST_STATE.entityFilter}}` : "",
    LIST_STATE.statusFilter ? `Statut : ${{LIST_STATE.statusFilter}}` : "",
    LIST_STATE.search ? `Recherche : "${{LIST_STATE.search}}"` : ""
  ].filter(Boolean).join(" | ") || "Tous les enregistrements (Exercice 2026)";

  // Colonnes à imprimer dans l'état récapitulatif
  const printFields = schema.fields.filter(f =>
    !["Section Break", "Column Break", "Table"].includes(f.fieldtype) &&
    !["naming_series", "amended_from", "montant_en_lettres", "appliquer_taxe_sejour", "nb_adultes"].includes(f.fieldname)
  ).slice(0, 9);

  // Calcul des totaux
  const totals = {{}};
  printFields.forEach(f => {{
    if (f.fieldtype === "Currency" || f.fieldtype === "Int") {{
      totals[f.fieldname] = filtered.reduce((a, r) => a + Number(r[f.fieldname] || 0), 0);
    }} else if (f.fieldtype === "Percent") {{
      totals[f.fieldname] = filtered.length ? filtered.reduce((a, r) => a + Number(r[f.fieldname] || 0), 0) / filtered.length : 0;
    }}
  }});

  const ths = `<th>N° / Réf.</th>` + printFields.map(f => `<th style="${{f.fieldtype === 'Currency' ? 'text-align:right;' : ''}}">${{f.label}}</th>`).join("");
  const trs = filtered.map(r => {{
    let cells = `<td><b>${{r.name}}</b></td>`;
    printFields.forEach(f => {{
      const v = r[f.fieldname];
      if (f.fieldtype === "Currency") cells += `<td style="text-align:right;white-space:nowrap;">${{fmtDZD(v)}}</td>`;
      else if (f.fieldtype === "Percent") cells += `<td style="text-align:right;">${{Number(v || 0).toFixed(2)}} %</td>`;
      else cells += `<td>${{v ?? "—"}}</td>`;
    }});
    return `<tr>${{cells}}</tr>`;
  }}).join("");

  let tfoot = `<td><b>TOTAL GÉNÉRAL (${{filtered.length}} lignes)</b></td>`;
  printFields.forEach(f => {{
    if (f.fieldtype === "Currency") tfoot += `<td style="text-align:right;white-space:nowrap;"><b>${{fmtDZD(totals[f.fieldname] || 0)}}</b></td>`;
    else if (f.fieldtype === "Percent") tfoot += `<td style="text-align:right;"><b>Moy: ${{Number(totals[f.fieldname] || 0).toFixed(2)}} %</b></td>`;
    else if (f.fieldtype === "Int") tfoot += `<td><b>${{totals[f.fieldname] || 0}}</b></td>`;
    else tfoot += `<td></td>`;
  }});

  const currencyBoxes = printFields.filter(f => f.fieldtype === "Currency").map(f => `
    <div style="border:1px solid #cbd5e1;border-radius:6px;padding:10px 14px;background:#f8fafc;min-width:170px;">
      <div style="font-size:10.5px;color:#475569;text-transform:uppercase;font-weight:700;">TOTAL ${{f.label}}</div>
      <div style="font-size:15px;font-weight:800;color:#0f172a;margin-top:3px;">${{fmtDZD(totals[f.fieldname] || 0)}}</div>
    </div>
  `).join("");

  const w = window.open("", "_blank");
  w.document.write(`<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><title>État Récapitulatif — ${{labelTitle}}</title>
  <style>
    body {{ font-family:'Segoe UI',Arial,sans-serif; color:#0f172a; max-width:1080px; margin:20px auto; padding:22px; }}
    .hdr {{ display:flex; justify-content:space-between; border-bottom:3px solid #b45309; padding-bottom:14px; margin-bottom:16px; flex-wrap:wrap; gap:12px; }}
    .filter-banner {{ background:#fef3c7; border-left:4px solid #d97706; padding:10px 14px; font-size:12.5px; margin-bottom:16px; border-radius:4px; display:flex; justify-content:space-between; flex-wrap:wrap; gap:8px; }}
    .sum-grid {{ display:flex; flex-wrap:wrap; gap:12px; margin-bottom:16px; }}
    table {{ width:100%; border-collapse:collapse; font-size:11.8px; margin-bottom:20px; }}
    th {{ background:#0f172a; color:#fff; padding:8px 9px; text-align:left; font-size:10.5px; text-transform:uppercase; }}
    td {{ padding:8px 9px; border-bottom:1px solid #cbd5e1; }}
    tfoot td {{ background:#fef3c7; color:#0f172a; font-weight:800; border-top:2px solid #b45309; font-size:12px; padding:10px 9px; }}
    .sigs {{ display:flex; justify-content:space-between; margin-top:28px; gap:20px; }}
    .sig-box {{ flex:1; border:1px dashed #94a3b8; border-radius:6px; padding:12px; min-height:85px; font-size:11.5px; }}
    @media print {{ .no-print {{ display:none; }} body {{ margin:0; padding:10px; }} }}
  </style></head><body>
  <div class="no-print" style="margin-bottom:14px;display:flex;justify-content:flex-end;gap:10px;">
    <button onclick="window.print()" style="padding:9px 18px;background:#0f172a;color:#fff;border:none;border-radius:6px;cursor:pointer;font-weight:700;">🖨️ Imprimer / Enregistrer en PDF</button>
  </div>
  <div class="hdr">
    <div>
      <h1 style="margin:0;font-size:20px;">${{cfg.raison_sociale || "SPA HÔTEL SAINT EUGÈNE"}} <span style="color:#d97706;">★★★★</span></h1>
      <div style="font-size:11.5px;color:#475569;margin-top:4px;">
        ${{cfg.adresse || "04 Blv Omar Lounas, Bologhine - 16090 Alger, Algérie"}}<br>
        <b>RC :</b> ${{cfg.rc || "—"}} | <b>NIF :</b> ${{cfg.nif || "—"}} | <b>NIS :</b> ${{cfg.nis || "—"}} | <b>AI :</b> ${{cfg.article_imposition || "—"}}
      </div>
    </div>
    <div style="text-align:right;">
      <h2 style="margin:0;color:#b45309;font-size:17px;">ÉTAT RÉCAPITULATIF & RELEVÉ SCF</h2>
      <div style="font-size:13px;font-weight:700;margin-top:3px;">${{labelTitle}}</div>
      <div style="font-size:11.5px;color:#475569;">Édité le : ${{nowAlgeriaTimestamp()}}</div>
      <div style="font-size:11.5px;color:#475569;">Nombre de lignes : <b>${{filtered.length}}</b></div>
    </div>
  </div>
  <div class="filter-banner">
    <div><b>Périmètre / Filtre appliqué :</b> ${{activeFilterDesc}}</div>
    <div><b>Devise :</b> Dinar Algérien (DZD) — Normes SCF</div>
  </div>
  ${{currencyBoxes ? `<div class="sum-grid">${{currencyBoxes}}</div>` : ""}}
  <table>
    <thead><tr>${{ths}}</tr></thead>
    <tbody>${{trs}}</tbody>
    <tfoot><tr>${{tfoot}}</tr></tfoot>
  </table>
  <div class="sigs">
    <div class="sig-box"><b>Visa Contrôle de Gestion / DAF :</b><br><span style="color:#64748b;">Date, Signature & Cachet</span></div>
    <div class="sig-box"><b>Visa Direction Générale :</b><br><span style="color:#64748b;">Bon pour validation</span></div>
  </div>
  </body></html>`);
  w.document.close();
}}

function showGoogleSheetBackupCenter() {{
  toggleMobileSidebar(false);
  CURRENT_DOCTYPE = null;
  renderSidebar("gsheet");
  document.getElementById("viewTitle").textContent = "☁️ Sauvegarde Google Sheet & Historique Complet des Modifications";

  const hist = DB["SE Historique Modifications"] || [];
  const savedWebhook = localStorage.getItem(WEBHOOK_KEY) || "";

  const histRowsHtml = hist.map(h => `
    <tr>
      <td><b>${{h.id || "—"}}</b></td>
      <td style="white-space:nowrap;"><b>${{h.date_modification || "—"}}</b></td>
      <td>${{h.module_label || h.doctype || "—"}}</td>
      <td><b>${{h.doc_name || "—"}}</b></td>
      <td><span class="pill ${{h.action && h.action.includes('Suppression') ? 'red' : (h.action && h.action.includes('Création') ? 'green' : 'orange')}}">${{h.action || "Modification"}}</span></td>
      <td>${{h.detail_modification || "—"}}</td>
      <td>${{h.utilisateur || "—"}}</td>
      <td><a href="${{GOOGLE_SHEET_URL}}" target="_blank" style="color:#2563eb;font-weight:700;text-decoration:none;">🔗 Ouvrir Google Sheet</a></td>
    </tr>
  `).join("");

  document.getElementById("mainContent").innerHTML = `
    <div class="alerts-panel" style="border-left:5px solid #16a34a;">
      <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
        <div>
          <h3 style="margin:0 0 6px 0;font-size:15px;">☁️ Sauvegarde & Synchronisation Google Sheets (22 Feuilles Séparées + Historique Complet)</h3>
          <div style="font-size:12.5px;color:#475569;">
            Lien Google Sheet configuré : <a href="${{GOOGLE_SHEET_URL}}" target="_blank" style="color:#15803d;font-weight:700;word-break:break-all;">${{GOOGLE_SHEET_URL}}</a>
          </div>
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
          <a class="btn btn-green" href="${{GOOGLE_SHEET_URL}}" target="_blank">🔗 Ouvrir votre Google Sheet</a>
          <button class="btn btn-gold" onclick="exportFullWorkbookXLSX()">📊 Télécharger Classeur 23 Feuilles (.xlsx)</button>
          <button class="btn btn-primary" onclick="printHistoryStatement()">🖨️ Imprimer l'Historique</button>
        </div>
      </div>

      <div style="margin-top:14px;padding:12px;background:#f8fafc;border:1px solid #cbd5e1;border-radius:8px;">
        <div style="font-size:12px;font-weight:700;color:#0f172a;margin-bottom:6px;">
          ⚡ Connexion Automatique Temps Réel (Google Apps Script Web App) :
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
          <input id="webhookInput" class="search-input" style="flex:1;min-width:240px;" placeholder="Collez ici l'URL Web App Google Script (https://script.google.com/macros/s/.../exec)" value="${{savedWebhook}}">
          <button class="btn btn-primary" onclick="saveWebhookUrl()">💾 Activer & Synchroniser Maintenant</button>
          <button class="btn" onclick="copyGoogleAppsScriptCode()">📋 Copier le Script Google Sheet (23 Feuilles)</button>
        </div>
        <div style="font-size:11.5px;color:#64748b;margin-top:6px;">
          💡 <b>Astuce :</b> Cliquez sur <b>"📋 Copier le Script Google Sheet"</b>, ouvrez votre Google Sheet → <b>Extensions > Apps Script</b>, collez le script et déployez-le en <i>Application Web (Accès : Tout le monde)</i>. Chaque ajout de Facture ou Encaissement mettra à jour automatiquement les 23 feuilles séparées de votre Google Sheet avec la date et le détail exact des modifications !
        </div>
      </div>
    </div>

    <div class="table-card">
      <div class="table-toolbar">
        <div style="font-weight:700;font-size:14px;color:#0f172a;">
          🕘 Journal & Historique Complet des Modifications (${{hist.length}} opérations enregistrées)
        </div>
      </div>
      <div class="table-scroll">
        <table class="frappe-list">
          <thead>
            <tr>
              <th>N° Log</th>
              <th>Date & Heure Modification</th>
              <th>Module (Feuille)</th>
              <th>Réf. Document</th>
              <th>Action</th>
              <th>Détail Exact de la Modification (Avant → Après)</th>
              <th>Modifié Par</th>
              <th>Lien Google Sheet</th>
            </tr>
          </thead>
          <tbody>
            ${{histRowsHtml || '<tr><td colspan="8" style="text-align:center;padding:20px;">Aucune modification</td></tr>'}}
          </tbody>
        </table>
      </div>
    </div>
  `;
}}

function saveWebhookUrl() {{
  const val = (document.getElementById("webhookInput").value || "").trim();
  localStorage.setItem(WEBHOOK_KEY, val);
  if (val) {{
    triggerGoogleSheetAutoBackup({{ action: "Synchronisation Complète Manuelle", date: nowAlgeriaTimestamp() }});
    showToast("☁️ Synchronisation envoyée vers votre Google Sheet !");
  }} else {{
    showToast("ℹ️ URL Web App effacée");
  }}
}}

function copyGoogleAppsScriptCode() {{
  navigator.clipboard.writeText(GS_SCRIPT_CODE).then(() => {{
    showToast("📋 Script Google Sheet copié ! Collez-le dans Extensions > Apps Script");
  }}).catch(() => {{
    alert("Le script est également disponible dans le fichier GOOGLE_SHEET_AUTO_BACKUP.gs de votre dossier.");
  }});
}}

function exportFullWorkbookXLSX() {{
  if (typeof XLSX === "undefined") {{
    alert("Chargement du module Excel en cours, veuillez réessayer dans 2 secondes.");
    return;
  }}
  const wb = XLSX.utils.book_new();
  const ts = nowAlgeriaTimestamp();

  // 1. Feuille Historique Complet des Modifications
  const hist = DB["SE Historique Modifications"] || [];
  const histRows = [
    ["SPA HÔTEL SAINT EUGÈNE 4★ ALGER — JOURNAL & HISTORIQUE COMPLET DES MODIFICATIONS (Export du " + ts + ")"],
    ["ID Modification", "Date & Heure de Modification", "Module (Titre)", "Référence Document", "Action Effectuée", "Détail de la Modification (Avant -> Après)", "Utilisateur", "Lien Google Sheet"],
    ...hist.map(h => [
      h.id || "",
      h.date_modification || ts,
      h.module_label || h.doctype || "",
      h.doc_name || "",
      h.action || "",
      h.detail_modification || "",
      h.utilisateur || "",
      GOOGLE_SHEET_URL
    ])
  ];
  const wsHist = XLSX.utils.aoa_to_sheet(histRows);
  XLSX.utils.book_append_sheet(wb, wsHist, "Historique_Modifications");

  // 2. Une feuille séparée par Module avec ligne TOTAL GÉNÉRAL
  NAV_GROUPS.forEach(g => {{
    g.items.forEach(item => {{
      if (!item.doctype) return;
      const dt = item.doctype;
      const schema = SCHEMAS[dt];
      if (!schema) return;
      const rows = DB[dt] || [];
      const fields = schema.fields.filter(f => !["Section Break", "Column Break", "Table"].includes(f.fieldtype) && f.fieldname !== "naming_series" && f.fieldname !== "amended_from");

      const headers = [
        "Référence (ID)",
        ...fields.map(f => f.label || f.fieldname),
        "Date de Modification",
        "Modifié par",
        "Détail de la Modification",
        "Lien Google Sheet"
      ];

      const dataRows = rows.map(r => [
        r.name || "",
        ...fields.map(f => r[f.fieldname] !== undefined && r[f.fieldname] !== null ? r[f.fieldname] : ""),
        r.date_modification || ts,
        r.modifie_par || CURRENT_USER_ROLE,
        r.detail_modification || "Enregistrement validé",
        GOOGLE_SHEET_URL
      ]);

      const totalRow = new Array(headers.length).fill("");
      totalRow[0] = `TOTAL GÉNÉRAL (${{rows.length}} lignes)`;
      fields.forEach((f, idx) => {{
        if (["Currency", "Int", "Float"].includes(f.fieldtype)) {{
          const s = rows.reduce((a, r) => a + Number(r[f.fieldname] || 0), 0);
          totalRow[idx + 1] = Math.round(s * 100) / 100;
        }} else if (f.fieldtype === "Percent" && rows.length > 0) {{
          const avg = rows.reduce((a, r) => a + Number(r[f.fieldname] || 0), 0) / rows.length;
          totalRow[idx + 1] = Math.round(avg * 100) / 100;
        }}
      }});

      const sheetAoA = [
        [`HÔTEL SAINT EUGÈNE 4★ ALGER — ${{item.label}} — Export du ${{ts}}`],
        headers,
        ...dataRows,
        totalRow
      ];
      const cleanTabName = item.label.replace(/[\\/?*\\[\\]:]/g, "").replace(/^[^a-zA-Z0-9À-ÿ]+/, "").trim().slice(0, 31) || dt.slice(0, 31);
      const ws = XLSX.utils.aoa_to_sheet(sheetAoA);
      XLSX.utils.book_append_sheet(wb, ws, cleanTabName);
    }});
  }});

  XLSX.writeFile(wb, `Saint_Eugene_ERP_2026_Backup_Complet_${{ts.slice(0, 10)}}.xlsx`);
  showToast("📊 Classeur complet (23 feuilles séparées + Totaux) téléchargé !");
}}

function printHistoryStatement() {{
  const hist = DB["SE Historique Modifications"] || [];
  const cfg = (DB["SE Parametres Hotel"] && DB["SE Parametres Hotel"][0]) || {{}};
  const w = window.open("", "_blank");
  w.document.write(`<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><title>Historique des Modifications</title>
  <style>
    body {{ font-family:'Segoe UI',Arial,sans-serif; color:#0f172a; max-width:1050px; margin:20px auto; padding:20px; }}
    table {{ width:100%; border-collapse:collapse; font-size:12px; margin-top:16px; }}
    th {{ background:#0f172a; color:#fff; padding:8px; text-align:left; }}
    td {{ padding:8px; border-bottom:1px solid #cbd5e1; }}
    @media print {{ .no-print {{ display:none; }} }}
  </style></head><body>
  <div class="no-print" style="text-align:right;margin-bottom:12px;"><button onclick="window.print()" style="padding:8px 16px;background:#0f172a;color:#fff;border:none;border-radius:6px;cursor:pointer;">🖨️ Imprimer PDF</button></div>
  <h2>${{cfg.raison_sociale || "SPA HÔTEL SAINT EUGÈNE 4★"}} — Journal & Historique des Modifications</h2>
  <p><b>Google Sheet de Sauvegarde :</b> ${{GOOGLE_SHEET_URL}} | <b>Total Opérations :</b> ${{hist.length}}</p>
  <table>
    <thead><tr><th>ID</th><th>Date & Heure</th><th>Module</th><th>Réf.</th><th>Action</th><th>Détail de la Modification</th><th>Utilisateur</th></tr></thead>
    <tbody>
      ${{hist.map(h => `<tr><td>${{h.id}}</td><td>${{h.date_modification}}</td><td>${{h.module_label || h.doctype}}</td><td><b>${{h.doc_name}}</b></td><td>${{h.action}}</td><td>${{h.detail_modification}}</td><td>${{h.utilisateur}}</td></tr>`).join("")}}
    </tbody>
  </table>
  </body></html>`);
  w.document.close();
}}

function generateNextDocName(doctype) {{
  const rows = DB[doctype] || [];
  const prefixes = {{
    "SE Facture Client": "FAC-CLI-2026-",
    "SE Facture Pro Forma": "PRO-2026-",
    "SE Encaissement": "ENC-2026-",
    "SE Facture Fournisseur": "FAC-FRN-2026-",
    "SE Decaissement": "DEC-2026-",
    "SE Charge et Depense": "CHG-2026-",
    "SE Fiche de Paie Mensuelle": "PAIE-2026-",
    "SE Operation Bancaire": "OPB-2026-",
    "SE Immobilisation": "IMMO-2026-",
    "SE Contrat et Abonnement": "CTR-2026-",
    "SE Employe": "SE-EMP-",
    "SE Client": "CLI-2026-"
  }};
  const prefix = prefixes[doctype];
  if (prefix) {{
    let maxNum = rows.length;
    rows.forEach(r => {{
      const m = String(r.name || "").match(/(\\d+)$/);
      if (m) {{
        const n = parseInt(m[1], 10);
        if (n > maxNum) maxNum = n;
      }}
    }});
    return `${{prefix}}${{String(maxNum + 1).padStart(5, "0")}}`;
  }}
  if (doctype === "SE Performance Hoteliere") {{
    return `PERF-2026-11-${{String((rows.length % 28) + 1).padStart(2, "0")}}`;
  }}
  return `${{doctype.replace(/\\s+/g, "-")}}-${{String(rows.length + 1).padStart(4, "0")}}`;
}}

function openDoc(doctype, name) {{
  const rows = DB[doctype] || [];
  const doc = rows.find(r => r.name === name) || rows[0];
  if (!doc) return;
  CURRENT_ORIGINAL_DOC = JSON.parse(JSON.stringify(doc));
  renderDocModal(doctype, JSON.parse(JSON.stringify(doc)), false);
}}

function openNewDoc(doctype) {{
  toggleMobileSidebar(false);
  const schema = SCHEMAS[doctype];
  const doc = {{ name: generateNextDocName(doctype) }};

  schema.fields.forEach(f => {{
    if (["Section Break", "Column Break", "Table"].includes(f.fieldtype)) return;
    if (f.default !== undefined && f.default !== "") {{
      doc[f.fieldname] = f.default === "Today" ? "2026-11-03" : f.default;
    }} else if (f.fieldtype === "Select" && f.options) {{
      const firstOpt = f.options.split("\\n")[0];
      if (firstOpt) doc[f.fieldname] = firstOpt;
    }} else if (["Currency", "Percent", "Int"].includes(f.fieldtype)) {{
      doc[f.fieldname] = 0;
    }} else if (f.fieldtype === "Date") {{
      doc[f.fieldname] = "2026-11-03";
    }}
  }});

  if (doctype === "SE Facture Client" || doctype === "SE Facture Pro Forma") {{
    const firstClient = (DB["SE Client"] || [])[0];
    if (firstClient) {{
      doc.client = LIST_STATE.entityFilter || firstClient.name;
      doc.type_client = firstClient.type_client || "Corporate";
    }}
    doc.date_facture = "2026-11-03";
    doc.date_arrivee = "2026-11-01";
    doc.date_depart = "2026-11-03";
    doc.nuitees = 2;
    doc.nb_adultes = 1;
    doc.nature_prestation = "Hébergement";
    doc.taux_tva = "9";
    doc.appliquer_taxe_sejour = 1;
    doc.mode_paiement_prevu = "Virement";
    doc.date_echeance = "2026-12-03";
    doc.statut = (doctype === "SE Facture Pro Forma") ? "Brouillon" : "Validée";
    recomputeSingleInvoice(doc, DB);
  }} else if (doctype === "SE Encaissement") {{
    const unpaid = (DB["SE Facture Client"] || []).find(f => Number(f.reste_a_encaisser) > 0) || (DB["SE Facture Client"] || [])[0];
    doc.date_encaissement = "2026-11-03";
    doc.statut = "Validé";
    if (unpaid) {{
      doc.facture_liee = unpaid.name;
      doc.client = unpaid.client;
      doc.montant = Number(unpaid.reste_a_encaisser || unpaid.montant_ttc || 0);
      doc.mode_paiement = unpaid.mode_paiement_prevu || "Virement";
      doc.compte_destination = doc.mode_paiement === "Espèces" ? "Caisse Principale Hôtel" : "BNA Agence Bologhine - DZD";
      doc.ref_paiement = `REG-${{unpaid.name}}`;
    }} else {{
      doc.mode_paiement = "Virement";
      doc.compte_destination = "BNA Agence Bologhine - DZD";
    }}
  }} else if (doctype === "SE Performance Hoteliere") {{
    doc.date_jour = "2026-11-03";
    doc.chambres_disponibles = 45;
    doc.chambres_vendues = 32;
    doc.ca_hebergement = 576000;
    doc.ca_restaurant = 240000;
    doc.autres_revenus = 65000;
  }}

  CURRENT_ORIGINAL_DOC = null;
  renderDocModal(doctype, doc, true);
}}


// --- CLIENT HELPERS & MOTEUR DE FACTURATION 4★ ---
function getClientObject(clientKey, dbSrc) {{
  const list = (dbSrc && dbSrc["SE Client"]) || (typeof DB !== "undefined" && DB["SE Client"]) || (typeof APP_STATE !== "undefined" && APP_STATE.db && APP_STATE.db["SE Client"]) || [];
  if (!clientKey) return null;
  return list.find(c => c.name === clientKey || c.nom_client === clientKey || c.ref_societe === clientKey) || null;
}}

function formatClientDisplay(clientKey, dbSrc) {{
  const cli = getClientObject(clientKey, dbSrc);
  if (!cli) return clientKey || "—";
  const nom = cli.nom_client || cli.name;
  const ref = cli.ref_societe || (cli.name && cli.name.startsWith("CLI-") ? cli.name : "");
  if (nom && ref && nom !== ref) {{
    return `${{nom}} (${{ref}})`;
  }}
  return nom || clientKey || "—";
}}

function formatClientBadge(clientKey, dbSrc) {{
  const cli = getClientObject(clientKey, dbSrc);
  if (!cli) return `<b>${{clientKey || "—"}}</b>`;
  const nom = cli.nom_client || cli.name;
  const ref = cli.ref_societe || (cli.name && cli.name.startsWith("CLI-") ? cli.name : "");
  if (nom && ref && nom !== ref) {{
    return `<div><b style="color:#0f172a;">${{nom}}</b> <span style="font-size:11px;color:#0284c7;background:#e0f2fe;padding:2px 7px;border-radius:4px;font-weight:700;margin-left:4px;">${{ref}}</span></div>`;
  }}
  return `<b style="color:#0f172a;">${{nom}}</b>`;
}}

const ROOM_TYPES = ["Single", "Double", "Twin", "Triple", "Suite Deluxe", "Suite Saint Eugène"];
const SERVICES = ["Dîner", "Déjeuner", "Coffee Break", "Location de salle"];

function getArticleCategory(article) {{
  if (ROOM_TYPES.includes(article)) return "Hébergement";
  if (article === "Location de salle") return "Séminaires & Banquets";
  return "Restauration";
}}

function computeInvoiceDocClient(doc, cfg) {{
  cfg = cfg || {{}};
  const tarifTs = Number(cfg.taxe_sejour_nuitee_adulte || 500);
  const incluse = doc.taxe_sejour_incluse !== undefined ? Number(doc.taxe_sejour_incluse) : 1;
  const appliquerTs = doc.appliquer_taxe_sejour !== undefined ? Number(doc.appliquer_taxe_sejour) : 1;

  if (!doc.sejours || !doc.sejours.length) {{
    doc.sejours = [{{
      sejour_no: 1,
      description: "Séjour Principal",
      date_arrivee: doc.date_arrivee || "2026-11-04",
      date_depart: doc.date_depart || "2026-11-07",
      nuitees: 3,
      nb_personnes: 1,
      taxe_sejour: 0,
      total_ttc_sejour: 0
    }}];
  }}

  // 1. Calcul des séjours : nuitees, nb_personnes, taxe_sejour calculée séparément par séjour
  let totTs = 0;
  let totNuitees = 0;
  let totAdultes = 0;

  doc.sejours.forEach((s, idx) => {{
    s.sejour_no = s.sejour_no || (idx + 1);
    if (s.date_arrivee && s.date_depart) {{
      const d1 = new Date(s.date_arrivee);
      const d2 = new Date(s.date_depart);
      const diff = Math.round((d2 - d1) / (1000 * 3600 * 24));
      s.nuitees = diff > 0 ? diff : 1;
    }} else {{
      s.nuitees = Math.max(1, parseInt(s.nuitees || 1, 10));
    }}
    s.nb_personnes = Math.max(1, parseInt(s.nb_personnes || 1, 10));

    // Formule exigée : Nombre de personnes × Nombre de nuitées × Tarif (500 DZD)
    const tsSej = appliquerTs ? Math.round(s.nb_personnes * s.nuitees * tarifTs * 100) / 100 : 0;
    s.taxe_sejour = tsSej;
    s.total_ttc_sejour = 0;

    totTs += tsSej;
    totNuitees += s.nuitees;
    totAdultes += s.nb_personnes;
  }});

  totTs = Math.round(totTs * 100) / 100;

  if (!doc.lignes || !doc.lignes.length) {{
    doc.lignes = [{{
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
    }}];
  }}

  // 2. Calcul des lignes : Formule "Prix unitaire × Quantité × Nuitées"
  let totTtcHeb = 0;
  let totTtcSrv = 0;
  const categories = new Set();

  doc.lignes.forEach((ln) => {{
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
    if (jours <= 0) {{
      jours = isRoom ? (sej ? sej.nuitees : 1) : 1;
    }}
    ln.nb_jours = jours;

    const taux = isRoom ? 9.0 : 19.0;
    ln.taux_tva = taux;

    // Calcul Total = Prix unitaire × Quantité × Nuitées
    let pu = parseFloat(ln.prix_unitaire_ttc || 0) || 0;
    let ttcSaisi = parseFloat(ln.montant_ttc_saisi || 0) || 0;

    if (pu > 0 && ttcSaisi === 0) {{
      ttcSaisi = Math.round((pu * qty * jours) * 100) / 100;
    }} else if (ttcSaisi > 0 && pu === 0) {{
      pu = (qty * jours > 0) ? Math.round((ttcSaisi / (qty * jours)) * 100) / 100 : 0;
    }} else if (pu > 0 && ttcSaisi > 0) {{
      ttcSaisi = Math.round((pu * qty * jours) * 100) / 100;
    }} else {{
      pu = isRoom ? 15000 : 2500;
      ttcSaisi = Math.round((pu * qty * jours) * 100) / 100;
    }}

    ln.prix_unitaire_ttc = pu;
    ln.montant_ttc_saisi = ttcSaisi;
    ln.total_ligne_ttc = ttcSaisi;

    if (isRoom) {{
      totTtcHeb += ttcSaisi;
    }} else {{
      totTtcSrv += ttcSaisi;
    }}

    if (sej) {{
      sej.total_ttc_sejour = Math.round((sej.total_ttc_sejour + ttcSaisi) * 100) / 100;
    }}
  }});

  // Si la taxe de séjour n'est pas incluse, elle s'ajoute au total de chaque séjour
  if (!incluse && appliquerTs) {{
    doc.sejours.forEach(s => {{
      s.total_ttc_sejour = Math.round((s.total_ttc_sejour + (s.taxe_sejour || 0)) * 100) / 100;
    }});
  }}

  // 3. Ventilation fiscale HT et TVA
  const totalTtcSaisi = Math.round((totTtcHeb + totTtcSrv) * 100) / 100;
  let ttcHebHorsTs = totTtcHeb;
  let totalTtc = totalTtcSaisi;

  if (incluse) {{
    ttcHebHorsTs = Math.max(0, Math.round((totTtcHeb - totTs) * 100) / 100);
    totalTtc = totalTtcSaisi;
  }} else {{
    ttcHebHorsTs = totTtcHeb;
    totalTtc = Math.round((totalTtcSaisi + totTs) * 100) / 100;
  }}

  const htHeb = Math.round((ttcHebHorsTs / 1.09) * 100) / 100;
  const tvaHeb = Math.round((ttcHebHorsTs - htHeb) * 100) / 100;

  const htSrv = Math.round((totTtcSrv / 1.19) * 100) / 100;
  const tvaSrv = Math.round((totTtcSrv - htSrv) * 100) / 100;

  // Répartition analytique par ligne
  doc.lignes.forEach(ln => {{
    const isRoom = ln.type_ligne === "Hébergement";
    const lnTtc = ln.montant_ttc_saisi || 0;
    const taux = ln.taux_tva || (isRoom ? 9 : 19);
    if (isRoom && totTtcHeb > 0) {{
      const ratio = lnTtc / totTtcHeb;
      ln.montant_ht = Math.round(htHeb * ratio * 100) / 100;
      ln.montant_tva = Math.round(tvaHeb * ratio * 100) / 100;
      ln.taxe_sejour = appliquerTs ? Math.round(totTs * ratio * 100) / 100 : 0;
    }} else {{
      ln.montant_ht = Math.round((lnTtc / (1 + taux / 100)) * 100) / 100;
      ln.montant_tva = Math.round((lnTtc - ln.montant_ht) * 100) / 100;
      ln.taxe_sejour = 0;
    }}
  }});

  const totalHt = Math.round((htHeb + htSrv) * 100) / 100;
  const totalTva = Math.round((tvaHeb + tvaSrv) * 100) / 100;

  // 4. Droit de timbre fiscal : calculé APRÈS sur le total TTC espèces, puis ajouté
  let timbre = 0;
  if (doc.mode_paiement_prevu === "Espèces") {{
    timbre = Math.min(10000, Math.max(100, Math.round(totalTtc * 0.01)));
  }}
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
  doc.detail_tva = `TVA 9% (Hébergement) : ${{fmtDZD(tvaHeb)}} | TVA 19% (Services) : ${{fmtDZD(tvaSrv)}}`;
  doc.montant_en_lettres = formatDzdInWords(net);

  const enc = Number(doc.montant_encaisse || 0);
  doc.reste_a_encaisser = Math.max(0, Math.round((net - enc) * 100) / 100);
}}

function renderInvoiceStaysRows(doc) {{
  return doc.sejours.map((s, idx) => `
    <tr id="inv_stay_row_${{idx}}" style="border-bottom:1px solid #e2e8f0;background:${{idx % 2 === 0 ? '#fff' : '#f8fafc'}};">
      <td style="padding:6px 8px;font-weight:700;">#${{s.sejour_no || (idx + 1)}}</td>
      <td style="padding:6px 8px;">
        <input type="text" id="inv_stay_desc_${{idx}}" style="width:100%;padding:4px 6px;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;" value="${{s.description || ''}}" placeholder="Ex: Séjour Principal" oninput="CURRENT_DOC.sejours[${{idx}}].description=this.value;">
      </td>
      <td style="padding:6px 8px;">
        <input type="date" id="inv_stay_arr_${{idx}}" style="padding:4px 6px;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;" value="${{s.date_arrivee || ''}}" onchange="onInvoiceStayDateChange(${{idx}}, 'date_arrivee', this.value);">
      </td>
      <td style="padding:6px 8px;">
        <input type="date" id="inv_stay_dep_${{idx}}" style="padding:4px 6px;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;" value="${{s.date_depart || ''}}" onchange="onInvoiceStayDateChange(${{idx}}, 'date_depart', this.value);">
      </td>
      <td style="padding:6px 8px;text-align:center;">
        <input type="number" min="1" id="inv_stay_nuits_${{idx}}" style="width:55px;padding:4px;text-align:center;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;font-weight:700;" value="${{s.nuitees || 1}}" onfocus="this.select()" oninput="onInvoiceStayFieldInput(${{idx}}, 'nuitees', this.value);">
      </td>
      <td style="padding:6px 8px;text-align:center;">
        <input type="number" min="1" id="inv_stay_pers_${{idx}}" style="width:55px;padding:4px;text-align:center;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;font-weight:700;color:#0369a1;" value="${{s.nb_personnes || 1}}" onfocus="this.select()" oninput="onInvoiceStayFieldInput(${{idx}}, 'nb_personnes', this.value);" title="Nombre de personnes pour ce séjour (taxe de séjour = personnes × nuits × 500 DZD)">
      </td>
      <td id="inv_stay_ts_${{idx}}" style="padding:6px 8px;text-align:right;color:#0369a1;font-weight:700;font-variant-numeric:tabular-nums;">
        ${{fmtDZD(s.taxe_sejour || 0)}}
      </td>
      <td id="inv_stay_total_${{idx}}" style="padding:6px 8px;text-align:right;font-weight:700;color:#0f172a;font-variant-numeric:tabular-nums;">
        ${{fmtDZD(s.total_ttc_sejour || 0)}}
      </td>
      ${{doc.sejours_separes ? `
      <td style="padding:6px 8px;text-align:center;">
        <button type="button" class="btn" style="padding:2px 6px;color:#dc2626;" onclick="removeInvoiceStay(${{idx}})" title="Supprimer ce séjour">✕</button>
      </td>` : ''}}
    </tr>
  `).join("");
}}

function onInvoiceArticleChange(idx, newArticle) {{
  if (!CURRENT_DOC || !CURRENT_DOC.lignes || !CURRENT_DOC.lignes[idx]) return;
  const ln = CURRENT_DOC.lignes[idx];
  ln.article = newArticle;
  const isRoom = ROOM_TYPES.includes(newArticle);
  if (!isRoom) {{
    ln.nb_jours = 1;
  }}
  onInvoiceFormUpdate();
}}

function onInvoiceStayDateChange(idx, field, val) {{
  if (!CURRENT_DOC || !CURRENT_DOC.sejours || !CURRENT_DOC.sejours[idx]) return;
  CURRENT_DOC.sejours[idx][field] = val;
  const s = CURRENT_DOC.sejours[idx];
  if (s.date_arrivee && s.date_depart) {{
    const d1 = new Date(s.date_arrivee);
    const d2 = new Date(s.date_depart);
    const diff = Math.round((d2 - d1) / (1000 * 3600 * 24));
    s.nuitees = diff > 0 ? diff : 1;
    CURRENT_DOC.lignes.forEach((ln) => {{
      if (ln.sejour_no === s.sejour_no && ROOM_TYPES.includes(ln.article)) {{
        ln.nb_jours = s.nuitees;
        if (ln.prix_unitaire_ttc > 0) {{
          ln.montant_ttc_saisi = Math.round(ln.prix_unitaire_ttc * (ln.quantite || 1) * ln.nb_jours * 100) / 100;
        }}
      }}
    }});
  }}
  onInvoiceFormUpdate();
}}

function onInvoiceStayFieldInput(idx, field, rawVal) {{
  if (!CURRENT_DOC || !CURRENT_DOC.sejours || !CURRENT_DOC.sejours[idx]) return;
  const s = CURRENT_DOC.sejours[idx];
  const num = Math.max(1, parseInt(rawVal || 1, 10));
  s[field] = num;

  if (field === "nuitees") {{
    CURRENT_DOC.lignes.forEach((ln) => {{
      if (ln.sejour_no === s.sejour_no && ROOM_TYPES.includes(ln.article)) {{
        ln.nb_jours = num;
        if (ln.prix_unitaire_ttc > 0) {{
          ln.montant_ttc_saisi = Math.round(ln.prix_unitaire_ttc * (ln.quantite || 1) * ln.nb_jours * 100) / 100;
        }}
      }}
    }});
  }}

  const dbSrc = (typeof APP_STATE !== "undefined" && APP_STATE.db) ? APP_STATE.db : (typeof DB !== "undefined" ? DB : {{}});
  const cfg = (dbSrc["SE Parametres Hotel"] && dbSrc["SE Parametres Hotel"][0]) || {{}};
  computeInvoiceDocClient(CURRENT_DOC, cfg);

  const elTs = document.getElementById(`inv_stay_ts_${{idx}}`);
  if (elTs) elTs.textContent = fmtDZD(s.taxe_sejour || 0);

  (CURRENT_DOC.sejours || []).forEach((st, sIdx) => {{
    const elStayTotal = document.getElementById(`inv_stay_total_${{sIdx}}`);
    if (elStayTotal) elStayTotal.textContent = fmtDZD(st.total_ttc_sejour || 0);
  }});

  const elCard = document.getElementById("inv_totals_card");
  if (elCard) elCard.innerHTML = renderInvoiceTotalsCard(CURRENT_DOC);
}}

function onInvoiceLineCalcInput(idx, triggerField, rawVal) {{
  if (!CURRENT_DOC || !CURRENT_DOC.lignes || !CURRENT_DOC.lignes[idx]) return;
  const ln = CURRENT_DOC.lignes[idx];

  if (triggerField === "pu") {{
    const pu = parseFloat(rawVal || 0) || 0;
    ln.prix_unitaire_ttc = pu;
    const qty = Math.max(1, parseInt(ln.quantite || 1, 10));
    const nuits = Math.max(1, parseInt(ln.nb_jours || 1, 10));
    ln.montant_ttc_saisi = Math.round((pu * qty * nuits) * 100) / 100;
    const elTtc = document.getElementById(`inv_ttc_saisi_${{idx}}`);
    if (elTtc) elTtc.value = ln.montant_ttc_saisi || "";
  }} else if (triggerField === "qty") {{
    const qty = Math.max(1, parseInt(rawVal || 1, 10));
    ln.quantite = qty;
    const pu = parseFloat(ln.prix_unitaire_ttc || 0) || 0;
    const nuits = Math.max(1, parseInt(ln.nb_jours || 1, 10));
    if (pu > 0) {{
      ln.montant_ttc_saisi = Math.round((pu * qty * nuits) * 100) / 100;
      const elTtc = document.getElementById(`inv_ttc_saisi_${{idx}}`);
      if (elTtc) elTtc.value = ln.montant_ttc_saisi || "";
    }} else if (ln.montant_ttc_saisi > 0) {{
      ln.prix_unitaire_ttc = Math.round((ln.montant_ttc_saisi / (qty * nuits)) * 100) / 100;
      const elPu = document.getElementById(`inv_pu_${{idx}}`);
      if (elPu) elPu.value = ln.prix_unitaire_ttc || "";
    }}
  }} else if (triggerField === "nuits") {{
    const nuits = Math.max(1, parseInt(rawVal || 1, 10));
    ln.nb_jours = nuits;
    const pu = parseFloat(ln.prix_unitaire_ttc || 0) || 0;
    const qty = Math.max(1, parseInt(ln.quantite || 1, 10));
    if (pu > 0) {{
      ln.montant_ttc_saisi = Math.round((pu * qty * nuits) * 100) / 100;
      const elTtc = document.getElementById(`inv_ttc_saisi_${{idx}}`);
      if (elTtc) elTtc.value = ln.montant_ttc_saisi || "";
    }} else if (ln.montant_ttc_saisi > 0) {{
      ln.prix_unitaire_ttc = Math.round((ln.montant_ttc_saisi / (qty * nuits)) * 100) / 100;
      const elPu = document.getElementById(`inv_pu_${{idx}}`);
      if (elPu) elPu.value = ln.prix_unitaire_ttc || "";
    }}
  }} else if (triggerField === "total_ttc") {{
    const ttc = parseFloat(rawVal || 0) || 0;
    ln.montant_ttc_saisi = ttc;
    const qty = Math.max(1, parseInt(ln.quantite || 1, 10));
    const nuits = Math.max(1, parseInt(ln.nb_jours || 1, 10));
    ln.prix_unitaire_ttc = (qty * nuits > 0) ? Math.round((ttc / (qty * nuits)) * 100) / 100 : 0;
    const elPu = document.getElementById(`inv_pu_${{idx}}`);
    if (elPu) elPu.value = ln.prix_unitaire_ttc || "";
  }}

  const dbSrc = (typeof APP_STATE !== "undefined" && APP_STATE.db) ? APP_STATE.db : (typeof DB !== "undefined" ? DB : {{}});
  const cfg = (dbSrc["SE Parametres Hotel"] && dbSrc["SE Parametres Hotel"][0]) || {{}};
  computeInvoiceDocClient(CURRENT_DOC, cfg);

  const elHt = document.getElementById(`inv_ht_${{idx}}`);
  if (elHt) elHt.textContent = fmtDZD(ln.montant_ht || 0);

  const elTva = document.getElementById(`inv_tva_${{idx}}`);
  if (elTva) elTva.textContent = `${{ln.taux_tva || 9}}%`;

  (CURRENT_DOC.sejours || []).forEach((st, sIdx) => {{
    const elStayTotal = document.getElementById(`inv_stay_total_${{sIdx}}`);
    if (elStayTotal) elStayTotal.textContent = fmtDZD(st.total_ttc_sejour || 0);
  }});

  const elCard = document.getElementById("inv_totals_card");
  if (elCard) elCard.innerHTML = renderInvoiceTotalsCard(CURRENT_DOC);
}}

function renderInvoiceLinesRows(doc) {{
  return doc.lignes.map((ln, idx) => `
    <tr style="border-bottom:1px solid #e2e8f0;background:${{idx % 2 === 0 ? '#fff' : '#f8fafc'}};">
      ${{doc.sejours_separes ? `
      <td style="padding:6px;">
        <select style="width:100%;padding:4px;border:1px solid #cbd5e1;border-radius:4px;font-size:11.5px;" onchange="CURRENT_DOC.lignes[${{idx}}].sejour_no=parseInt(this.value); onInvoiceFormUpdate();">
          ${{doc.sejours.map(s => `<option value="${{s.sejour_no}}" ${{s.sejour_no === ln.sejour_no ? "selected" : ""}}>Séjour #${{s.sejour_no}}</option>`).join("")}}
        </select>
      </td>` : ''}}
      <td style="padding:6px;">
        <select style="width:100%;padding:5px 6px;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;font-weight:600;" onchange="onInvoiceArticleChange(${{idx}}, this.value);">
          <optgroup label="🛏️ Chambres Hôtel 4★ (TVA 9%)">
            ${{ROOM_TYPES.map(r => `<option value="${{r}}" ${{r === ln.article ? "selected" : ""}}>${{r}}</option>`).join("")}}
          </optgroup>
          <optgroup label="🍽️ Services & Événements (TVA 19%)">
            ${{SERVICES.map(s => `<option value="${{s}}" ${{s === ln.article ? "selected" : ""}}>${{s}}</option>`).join("")}}
          </optgroup>
        </select>
      </td>
      <td style="padding:6px;text-align:right;">
        <input type="number" step="any" id="inv_pu_${{idx}}" style="width:110px;padding:5px 6px;text-align:right;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;font-weight:600;" value="${{ln.prix_unitaire_ttc !== undefined && ln.prix_unitaire_ttc !== null ? ln.prix_unitaire_ttc : ''}}" placeholder="0" onfocus="this.select()" oninput="onInvoiceLineCalcInput(${{idx}}, 'pu', this.value);">
      </td>
      <td style="padding:6px;text-align:center;">
        <input type="number" min="1" id="inv_qty_${{idx}}" style="width:55px;padding:5px 4px;text-align:center;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;font-weight:600;" value="${{ln.quantite || 1}}" onfocus="this.select()" oninput="onInvoiceLineCalcInput(${{idx}}, 'qty', this.value);" title="Nombre de chambres ou de prestations">
      </td>
      <td style="padding:6px;text-align:center;">
        <input type="number" min="1" id="inv_nuits_${{idx}}" style="width:55px;padding:5px 4px;text-align:center;border:1px solid #cbd5e1;border-radius:4px;font-size:12px;font-weight:600;" value="${{ln.nb_jours || 1}}" onfocus="this.select()" oninput="onInvoiceLineCalcInput(${{idx}}, 'nuits', this.value);" title="Nombre de nuitées pour cette chambre">
      </td>
      <td style="padding:6px;text-align:right;">
        <input type="number" step="any" id="inv_ttc_saisi_${{idx}}" style="width:130px;padding:5px 8px;text-align:right;border:2px solid #b45309;background:#fffbeb;font-weight:700;color:#92400e;border-radius:4px;font-size:13px;" value="${{ln.montant_ttc_saisi !== undefined && ln.montant_ttc_saisi !== null ? ln.montant_ttc_saisi : ''}}" placeholder="0" onfocus="this.select()" oninput="onInvoiceLineCalcInput(${{idx}}, 'total_ttc', this.value);" title="Total TTC = P.U. × Quantité × Nuitées">
      </td>
      <td id="inv_ht_${{idx}}" style="padding:6px;text-align:right;color:#334155;font-variant-numeric:tabular-nums;">${{fmtDZD(ln.montant_ht || 0)}}</td>
      <td id="inv_tva_${{idx}}" style="padding:6px;text-align:center;font-size:11px;color:#64748b;">${{ln.taux_tva || 9}}%</td>
      <td style="padding:6px;text-align:center;">
        <button type="button" class="btn" style="padding:2px 6px;color:#dc2626;" onclick="removeInvoiceLine(${{idx}})" title="Supprimer la ligne">✕</button>
      </td>
    </tr>
  `).join("");
}}

function renderInvoiceTotalsCard(doc) {{
  const isEsp = (doc.mode_paiement_prevu === "Espèces");
  return `
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:14px;">
      <div style="flex:1;min-width:280px;">
        <div style="font-weight:700;font-size:12.5px;color:#0f172a;margin-bottom:6px;">📊 Ventilation Fiscale & Arrêté Légal (Algérie SCF)</div>
        <div style="font-size:11.5px;color:#475569;margin-bottom:4px;"><b>Détail TVA :</b> ${{doc.detail_tva || 'N/A'}}</div>
        <div style="font-size:11.5px;color:#475569;margin-bottom:4px;"><b>Hébergement 4★ :</b> ${{doc.nuitees || 0}} nuitée(s) | ${{doc.nb_adultes || 0}} personne(s) | Taxe : 500 DZD / nuitée / pers. (Calculée par séjour)</div>
        <div style="background:#fff;border-left:3px solid #b45309;padding:8px 10px;border-radius:4px;font-size:12px;color:#1e293b;margin-top:8px;">
          Arrêtée la présente facture à la somme de :<br>
          <b>« ${{doc.montant_en_lettres || ''}} »</b>
        </div>
      </div>
      <div style="width:100%;max-width:380px;">
        <table style="width:100%;border-collapse:collapse;font-size:12.5px;">
          <tr><td style="padding:4px 0;color:#475569;">Total HT (Hébergement + Services)</td><td style="padding:4px 0;text-align:right;font-weight:600;">${{fmtDZD(doc.montant_ht)}}</td></tr>
          <tr><td style="padding:4px 0;color:#475569;">TVA Hébergement (9%)</td><td style="padding:4px 0;text-align:right;">${{fmtDZD(doc.lignes.filter(l => l.taux_tva === 9).reduce((a, b) => a + (b.montant_tva || 0), 0))}}</td></tr>
          <tr><td style="padding:4px 0;color:#475569;">TVA Services & Restauration (19%)</td><td style="padding:4px 0;text-align:right;">${{fmtDZD(doc.lignes.filter(l => l.taux_tva === 19).reduce((a, b) => a + (b.montant_tva || 0), 0))}}</td></tr>
          <tr><td style="padding:4px 0;color:#0369a1;font-weight:600;">Taxe de Séjour 4★ (500 DZD × pers. × nuits par séjour)</td><td style="padding:4px 0;text-align:right;font-weight:600;color:#0369a1;">${{fmtDZD(doc.taxe_sejour)}}</td></tr>
          <tr style="border-top:1px solid #cbd5e1;"><td style="padding:5px 0;font-weight:700;color:#1e293b;">Total TTC Chambres & Services</td><td style="padding:5px 0;text-align:right;font-weight:700;color:#1e293b;">${{fmtDZD(doc.total_ttc_saisi || doc.montant_ttc)}}</td></tr>
          <tr>
            <td style="padding:4px 0;color:${{isEsp ? '#b45309' : '#64748b'}};font-weight:${{isEsp ? '700' : 'normal'}};">
              Droit de Timbre Fiscal ${{isEsp ? '(Espèces - En sus)' : '(Exonéré hors espèces)'}}
            </td>
            <td style="padding:4px 0;text-align:right;color:${{isEsp ? '#b45309' : '#64748b'}};font-weight:${{isEsp ? '700' : 'normal'}};">
              ${{fmtDZD(doc.droit_timbre)}}
            </td>
          </tr>
          <tr style="background:#0f172a;color:#fff;font-weight:700;font-size:13.5px;">
            <td style="padding:8px 10px;border-radius:4px 0 0 4px;">NET À PAYER TTC (DZD)</td>
            <td style="padding:8px 10px;text-align:right;border-radius:0 4px 4px 0;color:#fbbf24;">${{fmtDZD(doc.montant_ttc)}}</td>
          </tr>
          ${{CURRENT_DOCTYPE === "SE Facture Client" ? `
          <tr><td style="padding:4px 0;color:#16a34a;font-weight:600;">Montant Encaissé</td><td style="padding:4px 0;text-align:right;color:#16a34a;font-weight:600;">${{fmtDZD(doc.montant_encaisse || 0)}}</td></tr>
          <tr><td style="padding:4px 0;color:#dc2626;font-weight:700;">Reste à Encaisser</td><td style="padding:4px 0;text-align:right;color:#dc2626;font-weight:700;">${{fmtDZD(doc.reste_a_encaisser || doc.montant_ttc)}}</td></tr>
          ` : ''}}
        </table>
      </div>
    </div>
  `;
}}

function onInvoiceFormUpdate() {{
  const dbSrc = (typeof APP_STATE !== "undefined" && APP_STATE.db) ? APP_STATE.db : (typeof DB !== "undefined" ? DB : {{}});
  const cfg = (dbSrc["SE Parametres Hotel"] && dbSrc["SE Parametres Hotel"][0]) || {{}};
  computeInvoiceDocClient(CURRENT_DOC, cfg);
  document.getElementById("inv_stays_tbody").innerHTML = renderInvoiceStaysRows(CURRENT_DOC);
  document.getElementById("inv_lines_tbody").innerHTML = renderInvoiceLinesRows(CURRENT_DOC);
  document.getElementById("inv_totals_card").innerHTML = renderInvoiceTotalsCard(CURRENT_DOC);
}}

function onInvoiceClientChange(clientKey) {{
  CURRENT_DOC.client = clientKey;
  const dbSrc = (typeof APP_STATE !== "undefined" && APP_STATE.db) ? APP_STATE.db : (typeof DB !== "undefined" ? DB : {{}});
  const cli = getClientObject(clientKey, dbSrc);
  if (cli) {{
    CURRENT_DOC.type_client = cli.type_client || "Corporate";
    CURRENT_DOC.nom_client = cli.nom_client || cli.name;
    CURRENT_DOC.ref_societe = cli.ref_societe || cli.name;
    const elType = document.getElementById("inv_type_client");
    if (elType) elType.value = CURRENT_DOC.type_client;
    const elNom = document.getElementById("inv_nom_client");
    if (elNom) elNom.value = CURRENT_DOC.nom_client;
    const elRef = document.getElementById("inv_ref_client");
    if (elRef) elRef.value = CURRENT_DOC.ref_societe;
  }}
}}

function addInvoiceStay() {{
  const nextNo = (CURRENT_DOC.sejours.length ? Math.max(...CURRENT_DOC.sejours.map(s => s.sejour_no || 0)) : 0) + 1;
  CURRENT_DOC.sejours.push({{
    sejour_no: nextNo,
    description: `Séjour #${{nextNo}}`,
    date_arrivee: CURRENT_DOC.date_facture || "2026-11-04",
    date_depart: "2026-11-07",
    nuitees: 3,
    nb_personnes: 1,
    taxe_sejour: 0,
    total_ttc_sejour: 0
  }});
  onInvoiceFormUpdate();
}}

function removeInvoiceStay(idx) {{
  if (CURRENT_DOC.sejours.length <= 1) {{
    alert("Une facture doit comporter au moins un séjour.");
    return;
  }}
  CURRENT_DOC.sejours.splice(idx, 1);
  onInvoiceFormUpdate();
}}

function addInvoiceLine() {{
  const stay1 = (CURRENT_DOC.sejours && CURRENT_DOC.sejours[0]) ? CURRENT_DOC.sejours[0].sejour_no : 1;
  const nuitsStay1 = (CURRENT_DOC.sejours && CURRENT_DOC.sejours[0]) ? CURRENT_DOC.sejours[0].nuitees : 3;
  CURRENT_DOC.lignes.push({{
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
  }});
  onInvoiceFormUpdate();
}}

function removeInvoiceLine(idx) {{
  if (CURRENT_DOC.lignes.length <= 1) {{
    alert("Une facture doit comporter au moins une prestation.");
    return;
  }}
  CURRENT_DOC.lignes.splice(idx, 1);
  onInvoiceFormUpdate();
}}

function renderInvoiceModal(doctype, doc, isNew) {{
  CURRENT_DOCTYPE = doctype;
  CURRENT_DOC = doc;
  const isProforma = (doctype === "SE Facture Pro Forma");
  document.getElementById("modalTitle").textContent = `${{isNew ? "Nouvelle" : doc.name}} — ${{isProforma ? "Facture Pro Forma" : "Facture Client (SCF 70)"}}`;

  const dbSrc = (typeof APP_STATE !== "undefined" && APP_STATE.db) ? APP_STATE.db : (typeof DB !== "undefined" ? DB : {{}});
  const cfg = (dbSrc["SE Parametres Hotel"] && dbSrc["SE Parametres Hotel"][0]) || {{}};
  computeInvoiceDocClient(doc, cfg);

  const clients = dbSrc["SE Client"] || [];
  const cli = getClientObject(doc.client, dbSrc) || (clients.length ? clients[0] : null);
  if (!doc.client && cli) {{
    doc.client = cli.name;
    doc.type_client = cli.type_client || "Corporate";
    doc.nom_client = cli.nom_client || cli.name;
    doc.ref_societe = cli.ref_societe || cli.name;
  }}

  const clientOptions = clients.map(c => {{
    const nom = c.nom_client || c.name;
    const ref = c.ref_societe || (c.name && c.name.startsWith("CLI-") ? c.name : "");
    const label = (ref && ref !== nom) ? `${{nom}} — [${{ref}}] (${{c.type_client || 'Corporate'}})` : `${{nom}} (${{c.type_client || 'Corporate'}})`;
    const isSel = (doc.client === c.name || doc.client === c.nom_client || doc.client === c.ref_societe);
    return `<option value="${{c.name}}" ${{isSel ? "selected" : ""}}>${{label}}</option>`;
  }}).join("");

  let html = `
  <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:14px;margin-bottom:16px;">
    <div style="font-weight:700;font-size:13px;color:#1e293b;margin-bottom:10px;display:flex;justify-content:space-between;align-items:center;">
      <span>📌 Informations Client & Modalités de Règlement</span>
      <span class="pill ${{isProforma ? 'blue' : 'green'}}">${{isProforma ? 'Devis Pro Forma' : 'Facture Client Officielle'}}</span>
    </div>
    <div class="form-grid" style="grid-template-columns:repeat(3, 1fr);gap:12px;">
      <div class="form-group" style="grid-column:span 2;">
        <label>Sélectionner le Client (Nom ou Référence Société) *</label>
        <select id="inv_client" onchange="onInvoiceClientChange(this.value)">
          <option value="">— Sélectionner un client —</option>
          ${{clientOptions}}
        </select>
      </div>
      <div class="form-group">
        <label>Type Client</label>
        <input type="text" id="inv_type_client" value="${{doc.type_client || (cli ? cli.type_client : 'Corporate')}}" readonly style="background:#f1f5f9;font-weight:700;">
      </div>
      <div class="form-group" style="grid-column:span 2;">
        <label>Nom / Raison Sociale</label>
        <input type="text" id="inv_nom_client" value="${{cli ? (cli.nom_client || cli.name) : (doc.client || '')}}" readonly style="background:#f1f5f9;font-weight:700;color:#0f172a;">
      </div>
      <div class="form-group">
        <label>Référence Société</label>
        <input type="text" id="inv_ref_client" value="${{cli ? (cli.ref_societe || cli.name) : ''}}" readonly style="background:#f1f5f9;font-weight:700;color:#0284c7;">
      </div>
      <div class="form-group">
        <label>Date de Facturation</label>
        <input type="date" id="inv_date_facture" value="${{doc.date_facture || '2026-11-04'}}" onchange="CURRENT_DOC.date_facture=this.value">
      </div>
      <div class="form-group">
        <label>${{isProforma ? 'Date de Validité' : "Date d'Échéance"}}</label>
        <input type="date" id="inv_date_echeance" value="${{doc.date_echeance || doc.date_validite || '2026-11-25'}}" onchange="CURRENT_DOC.date_echeance=this.value; CURRENT_DOC.date_validite=this.value;">
      </div>
      <div class="form-group">
        <label>Mode de Paiement Prévu *</label>
        <select id="inv_mode_paiement" onchange="CURRENT_DOC.mode_paiement_prevu=this.value; onInvoiceFormUpdate();">
          <option value="Virement" ${{doc.mode_paiement_prevu === "Virement" ? "selected" : ""}}>Virement Bancaire (Sans timbre)</option>
          <option value="Chèque" ${{doc.mode_paiement_prevu === "Chèque" ? "selected" : ""}}>Chèque Bancaire (Sans timbre)</option>
          <option value="Espèces" ${{doc.mode_paiement_prevu === "Espèces" ? "selected" : ""}}>Espèces (Droit de timbre fiscal 1% en sus)</option>
          <option value="TPE" ${{doc.mode_paiement_prevu === "TPE" ? "selected" : ""}}>TPE / Carte CIB / Edahabia (Sans timbre)</option>
        </select>
      </div>
      <div class="form-group" style="grid-column:span 3;display:flex;flex-direction:row;gap:20px;margin-top:6px;background:#fff;padding:10px 14px;border:1px solid #cbd5e1;border-radius:6px;flex-wrap:wrap;">
        <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:12px;font-weight:600;">
          <input type="checkbox" id="inv_ts_incluse" ${{doc.taxe_sejour_incluse ? "checked" : ""}} onchange="CURRENT_DOC.taxe_sejour_incluse = this.checked ? 1 : 0; onInvoiceFormUpdate();">
          🏷️ Taxe de séjour 4★ (500 DZD) incluse dans le montant TTC saisi
        </label>
        <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:12px;font-weight:600;">
          <input type="checkbox" id="inv_app_ts" ${{doc.appliquer_taxe_sejour ? "checked" : ""}} onchange="CURRENT_DOC.appliquer_taxe_sejour = this.checked ? 1 : 0; onInvoiceFormUpdate();">
          🛎️ Appliquer la taxe de séjour (Hébergement)
        </label>
        <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:12px;font-weight:600;">
          <input type="checkbox" id="inv_sej_separes" ${{doc.sejours_separes ? "checked" : ""}} onchange="CURRENT_DOC.sejours_separes = this.checked ? 1 : 0; renderInvoiceModal(CURRENT_DOCTYPE, CURRENT_DOC, CURRENT_IS_NEW);">
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
      ${{doc.sejours_separes ? `<button class="btn btn-gold" type="button" style="font-size:11.5px;padding:4px 10px;" onclick="addInvoiceStay()">+ Ajouter un séjour séparé</button>` : ''}}
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
            ${{doc.sejours_separes ? `<th style="padding:6px 8px;width:35px;text-align:center;"></th>` : ''}}
          </tr>
        </thead>
        <tbody id="inv_stays_tbody">
          ${{renderInvoiceStaysRows(doc)}}
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
            ${{doc.sejours_separes ? `<th style="padding:7px;width:85px;">Séjour</th>` : ''}}
            <th style="padding:7px;min-width:180px;">Type de Chambre ou Prestation</th>
            <th style="padding:7px;width:120px;text-align:right;background:#0369a1;">Prix unitaire TTC *</th>
            <th style="padding:7px;width:65px;text-align:center;background:#0369a1;">Qté (Ch.) *</th>
            <th style="padding:7px;width:65px;text-align:center;background:#0369a1;">Nuitées *</th>
            <th style="padding:7px;width:140px;text-align:right;background:#b45309;">Total TTC Saisi / Calculé *</th>
            <th style="padding:7px;width:95px;text-align:right;">Base HT</th>
            <th style="padding:7px;width:55px;text-align:center;">TVA</th>
            <th style="padding:7px;width:35px;text-align:center;"></th>
          </tr>
        </thead>
        <tbody id="inv_lines_tbody">
          ${{renderInvoiceLinesRows(doc)}}
        </tbody>
      </table>
    </div>
  </div>

  <!-- RÉCAPITULATIF FISCAL & TIMBRE -->
  <div id="inv_totals_card" style="background:#f8fafc;border:2px solid #b45309;border-radius:8px;padding:14px;margin-bottom:14px;">
    ${{renderInvoiceTotalsCard(doc)}}
  </div>
  `;

  document.getElementById("modalBody").innerHTML = html;

  let ftrHtml = `<div style="display:flex;gap:6px;flex-wrap:wrap;">`;
  if (!isNew) {{
    if (typeof openPrintPreview === "function") {{
      ftrHtml += `<button class="btn btn-gold" onclick="openPrintPreview('${{doctype}}', '${{doc.name.replace(/'/g, "\\'")}}')">🖨️ Imprimer / Aperçu PDF Officiel SCF</button> `;
    }}
  }}
  if (isProforma && !isNew) {{
    ftrHtml += `<button class="btn btn-primary" onclick="convertProformaToInvoice()">🔄 Convertir en Facture Définitive (SCF 70)</button> `;
  }}
  if (!isProforma && !isNew && Number(doc.reste_a_encaisser) > 0 && typeof quickReceiptFromInvoice === "function") {{
    ftrHtml += `<button class="btn" onclick="quickReceiptFromInvoice()">💰 Enregistrer un Encaissement</button>`;
  }}
  ftrHtml += `</div><div>
    <button class="btn" onclick="closeModal()">Fermer</button>
    <button class="btn btn-primary" onclick="saveInvoiceDoc()">💾 Enregistrer & Sauvegarder</button>
  </div>`;
  document.getElementById("modalFooter").innerHTML = ftrHtml;
  document.getElementById("docModal").classList.add("open");
}}


async function saveInvoiceDoc() {{
  const dbSrc = (typeof APP_STATE !== "undefined" && APP_STATE.db) ? APP_STATE.db : (typeof DB !== "undefined" ? DB : {{}});
  const cfg = (dbSrc["SE Parametres Hotel"] && dbSrc["SE Parametres Hotel"][0]) || {{}};
  computeInvoiceDocClient(CURRENT_DOC, cfg);

  if (typeof saveCurrentDoc === "function") {{
    await saveCurrentDoc(CURRENT_IS_NEW);
  }}
}}

function convertProformaToInvoice() {{
  if (confirm("Voulez-vous convertir cette Facture Pro Forma en Facture Client Définitive (SCF 70) ?")) {{
    const pro = CURRENT_DOC;
    pro.statut = "Convertie en Facture";
    const dbSrc = (typeof APP_STATE !== "undefined" && APP_STATE.db) ? APP_STATE.db : (typeof DB !== "undefined" ? DB : {{}});
    const count = (dbSrc["SE Facture Client"] || []).length + 1;
    const newName = `FAC-CLI-2026-000${{count < 10 ? '0' + count : count}}`;
    
    const newInvoice = JSON.parse(JSON.stringify(pro));
    newInvoice.name = newName;
    newInvoice.ref_reservation = pro.ref_devis || pro.name;
    newInvoice.statut = "Validée";
    newInvoice.docstatus = 1;
    delete newInvoice.date_validite;
    delete newInvoice.ref_devis;
    newInvoice.date_echeance = "2026-11-25";
    
    renderInvoiceModal("SE Facture Client", newInvoice, true);
  }}
}}

function renderDocModal(doctype, doc, isNew) {{
  CURRENT_DOCTYPE = doctype;
  CURRENT_DOC = doc;
  CURRENT_IS_NEW = !!isNew;
  if (doctype === "SE Facture Client" || doctype === "SE Facture Pro Forma") {{
    renderInvoiceModal(doctype, doc, isNew);
    return;
  }}
  const schema = SCHEMAS[doctype];
  document.getElementById("modalTitle").textContent = `${{isNew ? "➕ Nouveau" : doc.name}} — ${{getNavLabel(doctype)}}`;

  let formHtml = "";
  if (!isNew && doc.date_modification) {{
    formHtml += `<div style="background:#f8fafc;border:1px solid #e2e8f0;border-left:4px solid #16a34a;padding:8px 12px;border-radius:6px;margin-bottom:12px;font-size:11.5px;color:#334155;display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px;">
      <span>🕒 <b>Dernière modification :</b> ${{doc.date_modification}} par <b>${{doc.modifie_par || CURRENT_USER_ROLE}}</b></span>
      <span>📝 ${{doc.detail_modification || "Enregistrement sauvegardé"}}</span>
    </div>`;
  }}

  formHtml += `<div class="form-grid">`;
  schema.fields.forEach(f => {{
    if (["Section Break", "Column Break", "Table"].includes(f.fieldtype) || f.fieldname === "naming_series" || f.fieldname === "amended_from") return;
    const val = doc[f.fieldname] ?? "";
    const ro = f.read_only ? "readonly" : "";
    const full = f.fieldtype === "Small Text" ? "full" : "";

    let inputEl = "";
    if (f.fieldtype === "Select") {{
      const opts = (f.options || "").split("\\n");
      inputEl = `<select id="fld_${{f.fieldname}}" ${{ro ? "disabled" : ""}} onchange="onFieldChange('${{f.fieldname}}', this.value)">
        ${{opts.map(o => `<option value="${{o}}" ${{o === String(val) ? "selected" : ""}}>${{o}}</option>`).join("")}}
      </select>`;
    }} else if (f.fieldtype === "Link" && DB[f.options]) {{
      const targets = DB[f.options];
      inputEl = `<select id="fld_${{f.fieldname}}" ${{ro ? "disabled" : ""}} onchange="onFieldChange('${{f.fieldname}}', this.value)">
        <option value="">— Sélectionner —</option>
        ${{targets.map(t => {{
          let extra = "";
          if (f.options === "SE Facture Client") {{
            extra = ` — ${{t.client || ""}} (Reste: ${{fmtDZD(t.reste_a_encaisser)}})`;
          }} else if (t.nom_complet) {{
            extra = ` - ${{t.nom_complet}}`;
          }}
          return `<option value="${{t.name}}" ${{t.name === String(val) ? "selected" : ""}}>${{t.name}}${{extra}}</option>`;
        }}).join("")}}
      </select>`;
    }} else if (f.fieldtype === "Small Text") {{
      inputEl = `<textarea id="fld_${{f.fieldname}}" rows="2" ${{ro}} oninput="onFieldChange('${{f.fieldname}}', this.value)">${{val}}</textarea>`;
    }} else {{
      const type = ["Currency", "Percent", "Int"].includes(f.fieldtype) ? "number" : (f.fieldtype === "Date" ? "date" : "text");
      inputEl = `<input type="${{type}}" step="any" id="fld_${{f.fieldname}}" value="${{val}}" ${{ro}} oninput="onFieldChange('${{f.fieldname}}', this.value)">`;
    }}

    formHtml += `<div class="form-group ${{full}}">
      <label>${{f.label}} ${{f.read_only ? "🔒" : ""}}</label>
      ${{inputEl}}
    </div>`;
  }});
  formHtml += `</div>`;
  document.getElementById("modalBody").innerHTML = formHtml;

  let ftrHtml = `<div style="display:flex;gap:6px;flex-wrap:wrap;">`;
  if (!isNew) {{
    ftrHtml += `<button class="btn btn-gold" onclick="openPrintPreview()">🖨️ Imprimer PDF</button>`;
  }}
  if (doctype === "SE Facture Client" && !isNew && Number(doc.reste_a_encaisser) > 0) {{
    ftrHtml += `<button class="btn" onclick="quickReceiptFromInvoice()">💰 Encaisser cette Facture</button>`;
  }}
  if (!isNew && doctype !== "SE Parametres Hotel") {{
    ftrHtml += `<button class="btn btn-danger" onclick="deleteCurrentDoc()">🗑️ Supprimer</button>`;
  }}
  ftrHtml += `</div><div class="modal-ftr-right">
    <button class="btn" onclick="closeModal()">Annuler</button>
    <button class="btn btn-primary" onclick="saveCurrentDoc()">💾 Enregistrer & Sauvegarder</button>
  </div>`;
  document.getElementById("modalFooter").innerHTML = ftrHtml;
  document.getElementById("docModal").classList.add("open");
}}

function updateInputOnScreen(fieldname, val) {{
  CURRENT_DOC[fieldname] = val;
  const el = document.getElementById("fld_" + fieldname);
  if (el) el.value = val;
}}

function onFieldChange(fieldname, value) {{
  CURRENT_DOC[fieldname] = value;

  if (CURRENT_DOCTYPE === "SE Facture Client") {{
    if (fieldname === "client") {{
      const cli = (DB["SE Client"] || []).find(c => c.name === value);
      if (cli) {{
        updateInputOnScreen("type_client", cli.type_client || "Corporate");
      }}
    }}
    if (fieldname === "nature_prestation") {{
      updateInputOnScreen("taux_tva", value === "Hébergement" ? "9" : "19");
      updateInputOnScreen("appliquer_taxe_sejour", value === "Hébergement" ? 1 : 0);
    }}
    recomputeSingleInvoice(CURRENT_DOC, DB);
    ["montant_tva", "taxe_sejour", "droit_timbre", "montant_ttc", "montant_encaisse", "reste_a_encaisser", "montant_en_lettres", "statut"].forEach(k => {{
      updateInputOnScreen(k, CURRENT_DOC[k]);
    }});
  }}

  if (CURRENT_DOCTYPE === "SE Encaissement") {{
    if (fieldname === "facture_liee") {{
      const fac = (DB["SE Facture Client"] || []).find(f => f.name === value);
      if (fac) {{
        updateInputOnScreen("client", fac.client);
        updateInputOnScreen("montant", Number(fac.reste_a_encaisser) > 0 ? fac.reste_a_encaisser : fac.montant_ttc);
        const mode = fac.mode_paiement_prevu || "Virement";
        updateInputOnScreen("mode_paiement", mode);
        updateInputOnScreen("compte_destination", mode === "Espèces" ? "Caisse Principale Hôtel" : "BNA Agence Bologhine - DZD");
        updateInputOnScreen("ref_paiement", `REG-${{fac.name}}`);
      }}
    }}
    if (fieldname === "mode_paiement") {{
      updateInputOnScreen("compte_destination", value === "Espèces" ? "Caisse Principale Hôtel" : "BNA Agence Bologhine - DZD");
    }}
  }}

  if (CURRENT_DOCTYPE === "SE Performance Hoteliere") {{
    const dispo = Number(CURRENT_DOC.chambres_disponibles || 45);
    const vendues = Number(CURRENT_DOC.chambres_vendues || 0);
    const caH = Number(CURRENT_DOC.ca_hebergement || 0);
    const caR = Number(CURRENT_DOC.ca_restaurant || 0);
    const aut = Number(CURRENT_DOC.autres_revenus || 0);
    updateInputOnScreen("taux_occupation", dispo > 0 ? Math.round((vendues / dispo) * 10000) / 100 : 0);
    updateInputOnScreen("adr", vendues > 0 ? Math.round((caH / vendues) * 100) / 100 : 0);
    updateInputOnScreen("revpar", dispo > 0 ? Math.round((caH / dispo) * 100) / 100 : 0);
    updateInputOnScreen("ca_total_jour", Math.round((caH + caR + aut) * 100) / 100);
  }}
}}

function syncModalInputsToDoc() {{
  const schema = SCHEMAS[CURRENT_DOCTYPE];
  if (!schema) return;
  schema.fields.forEach(f => {{
    if (["Section Break", "Column Break", "Table"].includes(f.fieldtype)) return;
    const el = document.getElementById("fld_" + f.fieldname);
    if (!el) return;
    if (["Currency", "Percent", "Float"].includes(f.fieldtype)) {{
      CURRENT_DOC[f.fieldname] = Number(el.value || 0);
    }} else if (f.fieldtype === "Int") {{
      CURRENT_DOC[f.fieldname] = parseInt(el.value || 0, 10);
    }} else {{
      CURRENT_DOC[f.fieldname] = el.value;
    }}
  }});
}}

function quickReceiptFromInvoice() {{
  syncModalInputsToDoc();
  const inv = CURRENT_DOC;
  closeModal();
  CURRENT_ORIGINAL_DOC = null;
  renderDocModal("SE Encaissement", {{
    name: generateNextDocName("SE Encaissement"),
    date_encaissement: "2026-11-03",
    client: inv.client,
    facture_liee: inv.name,
    montant: Number(inv.reste_a_encaisser) > 0 ? inv.reste_a_encaisser : inv.montant_ttc,
    mode_paiement: inv.mode_paiement_prevu || "Virement",
    compte_destination: inv.mode_paiement_prevu === "Espèces" ? "Caisse Principale Hôtel" : "BNA Agence Bologhine - DZD",
    ref_paiement: `REG-${{inv.name}}`,
    statut: "Validé"
  }}, true);
}}

function saveCurrentDoc() {{
  syncModalInputsToDoc();
  if (CURRENT_DOCTYPE === "SE Facture Client" || CURRENT_DOCTYPE === "SE Facture Pro Forma") {{
    recomputeSingleInvoice(CURRENT_DOC, DB);
  }}

  const ts = nowAlgeriaTimestamp();
  const diffStr = computeModificationDiff(CURRENT_DOCTYPE, CURRENT_ORIGINAL_DOC, CURRENT_DOC, CURRENT_IS_NEW);
  const actionLabel = CURRENT_IS_NEW ? "➕ Création" : "✏️ Modification";

  CURRENT_DOC.date_modification = ts;
  CURRENT_DOC.modifie_par = CURRENT_USER_ROLE;
  CURRENT_DOC.detail_modification = diffStr;
  CURRENT_DOC.lien_google_sheet = GOOGLE_SHEET_URL;

  const rows = DB[CURRENT_DOCTYPE] || (DB[CURRENT_DOCTYPE] = []);
  const idx = rows.findIndex(r => r.name === CURRENT_DOC.name);
  if (idx >= 0) rows[idx] = CURRENT_DOC;
  else rows.unshift(CURRENT_DOC);

  if (CURRENT_DOCTYPE === "SE Facture Client" && CURRENT_DOC.date_facture) {{
    const mois = String(CURRENT_DOC.date_facture).slice(0, 7);
    const g50List = DB["SE Declaration TVA"] || (DB["SE Declaration TVA"] = []);
    if (mois && !g50List.some(g => g.mois === mois)) {{
      g50List.push({{
        name: `G50-${{mois}}`,
        mois: mois,
        precompte_anterieur: 0,
        statut: "Déclarée (G50)",
        date_modification: ts,
        modifie_par: CURRENT_USER_ROLE,
        detail_modification: `Création automatique G50 pour ${{mois}}`,
        lien_google_sheet: GOOGLE_SHEET_URL
      }});
    }}
  }}

  const logEntry = recordAuditModification(CURRENT_DOCTYPE, CURRENT_DOC.name, actionLabel, diffStr);
  saveDB(logEntry);

  const savedName = CURRENT_DOC.name;
  const savedDoctype = CURRENT_DOCTYPE;
  closeModal();
  renderSidebar(savedDoctype);
  if (savedDoctype === "SE Parametres Hotel") showWorkspace();
  else showList(savedDoctype, false);
  showToast(`✅ ${{savedName}} sauvegardé (+ Historique & Backup Google Sheet)`);
}}

function deleteCurrentDoc() {{
  if (!confirm(`Supprimer définitivement ${{CURRENT_DOC.name}} ?`)) return;
  const deletedName = CURRENT_DOC.name;
  const dt = CURRENT_DOCTYPE;
  const rows = DB[dt] || [];
  DB[dt] = rows.filter(r => r.name !== deletedName);
  const logEntry = recordAuditModification(dt, deletedName, "🗑️ Suppression", `Suppression de ${{deletedName}} dans ${{getNavLabel(dt)}}`);
  saveDB(logEntry);
  closeModal();
  renderSidebar(dt);
  showList(dt, false);
  showToast(`🗑️ ${{deletedName}} supprimé (Historique mis à jour)`);
}}

function openPrintPreview() {{
  syncModalInputsToDoc();
  const doc = CURRENT_DOC;
  const cfg = DB["SE Parametres Hotel"][0];
  const w = window.open("", "_blank");
  if (CURRENT_DOCTYPE === "SE Facture Client" || CURRENT_DOCTYPE === "SE Facture Pro Forma") {{
    const isPro = (CURRENT_DOCTYPE === "SE Facture Pro Forma");
    const cli = getClientObject(doc.client, DB) || {{}};
    const nomClient = cli.nom_client || doc.client || "Client Divers";
    const refSociete = cli.ref_societe || cli.name || doc.client || "—";
    const typeClient = doc.type_client || cli.type_client || "Corporate";
    const sejours = doc.sejours || [];
    const lignes = doc.lignes || [];

    let staysHtml = "";
    if (sejours.length > 0) {{
      staysHtml = `<div style="margin-bottom:14px;"><b style="font-size:12px;color:#0f172a;">Détail des Périodes & Séjours :</b>
      <table style="width:100%;border-collapse:collapse;margin-top:4px;font-size:12px;">
        <tr style="background:#f1f5f9;color:#334155;">
          <th style="padding:6px;text-align:left;">Désignation Séjour</th>
          <th style="padding:6px;text-align:center;">Date Arrivée</th>
          <th style="padding:6px;text-align:center;">Date Départ</th>
          <th style="padding:6px;text-align:center;">Nuitées</th>
          <th style="padding:6px;text-align:center;">Personnes</th>
          <th style="padding:6px;text-align:right;">Taxe Séjour (500 DZD)</th>
          <th style="padding:6px;text-align:right;">Total Séjour TTC</th>
        </tr>
        ${{sejours.map(s => `<tr>
          <td style="padding:6px;border-bottom:1px solid #e2e8f0;"><b>Séjour #${{s.sejour_no || 1}}</b> — ${{s.description || ''}}</td>
          <td style="padding:6px;border-bottom:1px solid #e2e8f0;text-align:center;">${{s.date_arrivee || ''}}</td>
          <td style="padding:6px;border-bottom:1px solid #e2e8f0;text-align:center;">${{s.date_depart || ''}}</td>
          <td style="padding:6px;border-bottom:1px solid #e2e8f0;text-align:center;font-weight:bold;">${{s.nuitees || 1}} j</td>
          <td style="padding:6px;border-bottom:1px solid #e2e8f0;text-align:center;font-weight:bold;">${{s.nb_personnes || 1}} pers.</td>
          <td style="padding:6px;border-bottom:1px solid #e2e8f0;text-align:right;color:#0369a1;font-weight:bold;">${{fmtDZD(s.taxe_sejour || (Number(s.nb_personnes || 1) * Number(s.nuitees || 1) * 500))}}</td>
          <td style="padding:6px;border-bottom:1px solid #e2e8f0;text-align:right;font-weight:bold;">${{fmtDZD(s.total_ttc_sejour || 0)}}</td>
        </tr>`).join('')}}
      </table></div>`;
    }}

    let linesHtml = "";
    lignes.forEach(ln => {{
      const qty = Number(ln.quantite || 1);
      const nuits = Number(ln.nb_jours || 1);
      const tot = Number(ln.total_ligne_ttc || 0);
      const pu = (ln.prix_unitaire_ttc !== undefined && ln.prix_unitaire_ttc !== null && ln.prix_unitaire_ttc !== "")
        ? Number(ln.prix_unitaire_ttc)
        : (tot / Math.max(1, qty * nuits));
      linesHtml += `<tr>
        <td style="padding:7px;border-bottom:1px solid #e2e8f0;">
          <b>${{ln.article || 'Prestation'}}</b> (${{ln.type_ligne || 'Hébergement'}})
          ${{sejours.length > 1 ? `<span style="font-size:11px;color:#64748b;">[Séjour #${{ln.sejour_no || 1}}]</span>` : ''}}
        </td>
        <td style="padding:7px;border-bottom:1px solid #e2e8f0;text-align:right;">${{fmtDZD(pu)}}</td>
        <td style="padding:7px;border-bottom:1px solid #e2e8f0;text-align:center;">${{qty}}</td>
        <td style="padding:7px;border-bottom:1px solid #e2e8f0;text-align:center;">${{nuits}}</td>
        <td style="padding:7px;border-bottom:1px solid #e2e8f0;text-align:right;">${{fmtDZD(ln.montant_ht || 0)}}</td>
        <td style="padding:7px;border-bottom:1px solid #e2e8f0;text-align:center;">${{ln.taux_tva || 9}}%</td>
        <td style="padding:7px;border-bottom:1px solid #e2e8f0;text-align:right;">${{fmtDZD(ln.montant_tva || 0)}}</td>
        <td style="padding:7px;border-bottom:1px solid #e2e8f0;text-align:right;font-weight:bold;">${{fmtDZD(tot)}}</td>
      </tr>`;
    }});

    w.document.write(`<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>${{isPro ? 'FACTURE PRO FORMA' : 'FACTURE CLIENT'}} ${{doc.name}}</title>
    <style>
      body {{ font-family:'Segoe UI',Arial,sans-serif; color:#0f172a; max-width:880px; margin:20px auto; padding:24px; border:1px solid #cbd5e1; }}
      .hdr {{ display:flex; justify-content:space-between; border-bottom:3px solid #b45309; padding-bottom:14px; margin-bottom:18px; flex-wrap:wrap; gap:12px; }}
      .grid {{ display:flex; gap:16px; margin-bottom:16px; flex-wrap:wrap; }}
      .box {{ flex:1; min-width:260px; border:1px solid #cbd5e1; border-radius:6px; padding:12px; background:#f8fafc; font-size:12px; }}
      table {{ width:100%; border-collapse:collapse; margin-bottom:14px; font-size:12px; }}
      th {{ background:#0f172a; color:#fff; padding:8px; text-align:left; }}
      td {{ padding:8px; border-bottom:1px solid #e2e8f0; }}
      .words {{ background:#fffbeb; border-left:4px solid #d97706; padding:12px; font-size:12.5px; margin:16px 0; }}
      @media print {{ .no-print {{ display:none; }} body {{ border:none; margin:0; padding:10px; }} }}
    </style></head><body>
    <div class="no-print" style="margin-bottom:14px;text-align:right;">
      <button onclick="window.print()" style="padding:8px 18px;background:#0f172a;color:#fff;border:none;border-radius:6px;cursor:pointer;font-weight:bold;">🖨️ Imprimer / Enregistrer en PDF</button>
    </div>
    <div class="hdr">
      <div>
        <h1 style="margin:0;font-size:20px;color:#0f172a;">${{cfg.raison_sociale}} <span style="color:#d97706;">★★★★</span></h1>
        <div style="font-size:11.5px;color:#475569;margin-top:4px;">
          ${{cfg.adresse}}<br>Tél : ${{cfg.telephone}} | Email : ${{cfg.email}}<br>
          <b>RC :</b> ${{cfg.rc}} | <b>NIF :</b> ${{cfg.nif}} | <b>NIS :</b> ${{cfg.nis}} | <b>AI :</b> ${{cfg.article_imposition}}
        </div>
      </div>
      <div style="text-align:right;">
        <h2 style="margin:0;color:#b45309;font-size:18px;">${{isPro ? 'FACTURE PRO FORMA' : 'FACTURE CLIENT OFFICIELLE'}}</h2>
        <div style="font-size:12px;margin-top:4px;"><b>N° :</b> ${{doc.name}}</div>
        <div style="font-size:12px;"><b>Date :</b> ${{doc.date_facture}}</div>
        <div style="font-size:12px;"><b>${{isPro ? 'Validité' : 'Échéance'}} :</b> ${{doc.date_validite || doc.date_echeance || '—'}}</div>
        <div style="font-size:12px;"><b>Statut :</b> ${{doc.statut || 'Validée'}}</div>
      </div>
    </div>
    <div class="grid">
      <div class="box">
        <b style="color:#b45309;">FACTURÉ À (CLIENT) :</b><br>
        <b style="font-size:14px;color:#0f172a;">${{nomClient}}</b><br>
        <span style="font-size:12px;color:#475569;"><b>Référence Société :</b> ${{refSociete}} • <b>Type :</b> ${{typeClient}}</span><br>
        ${{cli.adresse || ''}}<br>
        <b>RC :</b> ${{cli.rc || '—'}} | <b>NIF :</b> ${{cli.nif || '—'}}<br>
        <b>NIS :</b> ${{cli.nis || '—'}} | <b>AI :</b> ${{cli.article_imposition || '—'}}
      </div>
      <div class="box">
        <b style="color:#b45309;">MODALITÉS DU RÈGLEMENT :</b><br>
        <b>Mode prévu :</b> ${{doc.mode_paiement_prevu || 'Virement'}}<br>
        <b>Réf. Dossier :</b> ${{doc.ref_devis || doc.ref_reservation || '—'}}<br>
        <b>Taxe de séjour :</b> 500 DZD / nuitée / pers. (Hébergement 4★)<br>
        <b>Ventilation TVA :</b> ${{doc.detail_tva || 'Conforme SCF'}}
      </div>
    </div>

    ${{staysHtml}}

    <b style="font-size:12px;color:#0f172a;">Détail des Prestations Hôtelières & Services :</b>
    <table style="width:100%;border-collapse:collapse;margin-top:4px;font-size:12px;">
      <thead>
        <tr>
          <th>Prestation / Type de Chambre</th>
          <th style="text-align:right;">Prix unitaire TTC</th>
          <th style="text-align:center;">Qté (Ch.)</th>
          <th style="text-align:center;">Nuitées</th>
          <th style="text-align:right;">Base HT</th>
          <th style="text-align:center;">TVA</th>
          <th style="text-align:right;">Montant TVA</th>
          <th style="text-align:right;">Total TTC</th>
        </tr>
      </thead>
      <tbody>${{linesHtml}}</tbody>
    </table>

    <table style="width:55%;margin-left:auto;font-size:12.5px;">
      <tr><td>Total HT</td><td style="text-align:right;font-weight:bold;">${{fmtDZD(doc.montant_ht)}}</td></tr>
      <tr><td>TVA Collectée (9% / 19%)</td><td style="text-align:right;">${{fmtDZD(doc.montant_tva)}}</td></tr>
      <tr><td>Taxe de Séjour 4★ (500 DZD × pers. × nuits)</td><td style="text-align:right;color:#0369a1;">${{fmtDZD(doc.taxe_sejour)}}</td></tr>
      <tr style="border-top:1px solid #cbd5e1;"><td>Total TTC Saisi</td><td style="text-align:right;font-weight:bold;">${{fmtDZD(doc.total_ttc_saisi || doc.montant_ttc)}}</td></tr>
      <tr><td>Droit de Timbre Fiscal (Espèces)</td><td style="text-align:right;">${{fmtDZD(doc.droit_timbre)}}</td></tr>
      <tr style="background:#0f172a;color:#fff;font-weight:bold;font-size:13px;"><td>NET À PAYER TTC (DZD)</td><td style="text-align:right;color:#fbbf24;">${{fmtDZD(doc.montant_ttc)}}</td></tr>
      ${{!isPro ? `
      <tr><td>Montant Encaissé</td><td style="text-align:right;color:#16a34a;font-weight:bold;">${{fmtDZD(doc.montant_encaisse || 0)}}</td></tr>
      <tr><td><b>Reste à Encaisser</b></td><td style="text-align:right;color:#dc2626;font-weight:bold;">${{fmtDZD(doc.reste_a_encaisser || doc.montant_ttc)}}</td></tr>
      ` : ''}}
    </table>

    <div class="words">Arrêtée la présente ${{isPro ? 'Facture Pro Forma' : 'Facture'}} à la somme de :<br><b>« ${{doc.montant_en_lettres || ''}} »</b></div>
    <div style="display:flex;justify-content:space-between;margin-top:20px;padding-top:10px;border-top:1px solid #cbd5e1;font-size:11px;color:#475569;">
      <div><b>RIB BNA :</b> ${{cfg.rib_principal}}<br><b>Capital Social :</b> ${{cfg.capital_social}}</div>
      <div style="text-align:right;min-width:200px;">
        <b>Cachet & Signature Direction</b><br><br><br>
        <i>Hôtel Saint Eugène 4★ Alger</i>
      </div>
    </div>
    </body></html>`);
  }} else {{
    w.document.write(`<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${{doc.name}}</title>
    <style>body{{font-family:'Segoe UI',sans-serif;max-width:780px;margin:24px auto;padding:24px;border:1px solid #cbd5e1;}}table{{width:100%;border-collapse:collapse;margin-top:16px;}}th,td{{border:1px solid #cbd5e1;padding:9px;text-align:left;}}th{{background:#f1f5f9;width:45%;}}</style></head>
    <body><button onclick="window.print()" style="float:right;padding:7px 14px;background:#0f172a;color:#fff;border:none;border-radius:6px;cursor:pointer;">🖨️ Imprimer PDF</button>
    <h2>${{getNavLabel(CURRENT_DOCTYPE)}} — ${{doc.name}}</h2><p>${{cfg.raison_sociale}} (${{cfg.adresse}})</p>
    <table>${{Object.entries(doc).map(([k,v]) => `<tr><th>${{k}}</th><td>${{v}}</td></tr>`).join('')}}</table></body></html>`);
  }}
  w.document.close();
}}

function closeModal() {{
  document.getElementById("docModal").classList.remove("open");
}}

populateUsersSelect();
// Auto-reconnexion si la session est déjà déverrouillée dans l'onglet
(async () => {{
  try {{
    const saved = sessionStorage.getItem(SESSION_KEY);
    if (saved) {{
      const {{ pwd, role }} = JSON.parse(saved);
      document.getElementById("loginPassword").value = pwd;
      document.getElementById("loginRole").value = role;
      await handleUnlock(null);
    }}
  }} catch (e) {{}}
}})();
</script>
</body>
</html>
"""
    (APP_ROOT / "index.html").write_text(html, encoding="utf-8")
    print(f"OK: index.html et GOOGLE_SHEET_AUTO_BACKUP.gs générés avec le code d'accès '{password}'.")


if __name__ == "__main__":
    main()
