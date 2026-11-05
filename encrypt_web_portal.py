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

from launch_now import SCHEMAS, build_initial_seed_db
import rh_module  # noqa: E402

GOOGLE_SHEET_ID = "1UuZAxjwHC6YXcrhjsQaZ9G5XYdKBn9Hn779yTdIwjak"
GOOGLE_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/edit?usp=sharing"
LOGO_BASE64_URI = "data:image/png;base64,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"


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

    // Sauvegarde miroir pour synchronisation multi-appareils (Téléphone <-> PC)
    let syncSheet = ss.getSheetByName("_SYNC_DB_");
    if (!syncSheet) {{
      syncSheet = ss.insertSheet("_SYNC_DB_");
      try {{ syncSheet.hideSheet(); }} catch(err) {{}}
    }}
    const syncData = JSON.stringify({{
      db: payload.db || {{}},
      history: payload.history || [],
      last_event: payload.last_event || null,
      timestamp: new Date().toISOString()
    }});
    syncSheet.getRange(1, 1).setValue(syncData);

    return ContentService.createTextOutput(JSON.stringify({{ status: "ok", timestamp: new Date().toISOString() }}))
      .setMimeType(ContentService.MimeType.JSON);
  }} catch (err) {{
    return ContentService.createTextOutput(JSON.stringify({{ status: "error", message: String(err) }}))
      .setMimeType(ContentService.MimeType.JSON);
  }}
}}

function doGet(e) {{
  try {{
    const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
    let syncSheet = ss.getSheetByName("_SYNC_DB_");
    let syncData = null;
    if (syncSheet) {{
      const val = syncSheet.getRange(1, 1).getValue();
      if (val) {{
        try {{ syncData = JSON.parse(val); }} catch(err) {{}}
      }}
    }}
    return ContentService.createTextOutput(JSON.stringify({{
      status: "online",
      hotel: "SPA HÔTEL SAINT EUGÈNE 4★ - ALGER",
      spreadsheet_id: SPREADSHEET_ID,
      data: syncData
    }})).setMimeType(ContentService.MimeType.JSON);
  }} catch (err) {{
    return ContentService.createTextOutput(JSON.stringify({{
      status: "error",
      message: String(err)
    }})).setMimeType(ContentService.MimeType.JSON);
  }}
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
    sanitized_db = rh_module.sanitize_db_for_backup(initial_db)
    gs_code = generate_google_apps_script(sanitized_db)
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
<script src="rh_module.js"></script>
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

const LOGO_BASE64_URI = "{LOGO_BASE64_URI}";
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
var DB = {{}};
window.DB = DB;
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
    window.DB = DB;
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


async function pullFromGoogleSheet(silent = false) {{
  const webhookUrl = (localStorage.getItem(WEBHOOK_KEY) || "").trim();
  if (!webhookUrl) {{
    if (!silent) showToast("⚠️ Veuillez d'abord renseigner l'URL Web App dans le centre Google Sheet !");
    return false;
  }}
  try {{
    if (!silent) showToast("⏳ Récupération des données depuis Google Sheet...");
    const url = webhookUrl + (webhookUrl.includes("?") ? "&" : "?") + "action=pull&_t=" + Date.now();
    const resp = await fetch(url, {{ method: "GET" }});
    if (!resp.ok) throw new Error("HTTP " + resp.status);
    const json = await resp.json();
    if (json && json.data && json.data.db) {{
      const remoteDb = json.data.db;
      Object.keys(remoteDb).forEach(dt => {{
        if (!DB[dt]) DB[dt] = [];
        const localMap = new Map((DB[dt] || []).map(r => [r.name, r]));
        (remoteDb[dt] || []).forEach(remDoc => {{
          const locDoc = localMap.get(remDoc.name);
          if (!locDoc) {{
            DB[dt].unshift(remDoc);
          }} else {{
            const dRem = remDoc.date_modification || "";
            const dLoc = locDoc.date_modification || "";
            if (dRem >= dLoc) {{
              Object.assign(locDoc, remDoc);
            }}
          }}
        }});
      }});
      if (json.data.history && Array.isArray(json.data.history)) {{
        const histMap = new Map((DB["SE Historique Modifications"] || []).map(h => [h.id, h]));
        json.data.history.forEach(h => {{
          if (!histMap.has(h.id)) {{
            DB["SE Historique Modifications"].unshift(h);
          }}
        }});
      }}
      recomputeAllLinks(DB);
      try {{ localStorage.setItem(STORAGE_KEY, JSON.stringify(DB)); }} catch(e) {{}}
      renderSidebar(CURRENT_DOCTYPE);
      if (CURRENT_DOCTYPE) showList(CURRENT_DOCTYPE, false);
      else showWorkspace();
      if (!silent) showToast("✅ Synchronisation réussie ! Vos données sont à jour avec le Téléphone et le PC.");
      return true;
    }} else {{
      if (!silent) showToast("ℹ️ Google Sheet connecté mais aucune sauvegarde _SYNC_DB_ trouvée pour l'instant.");
      return false;
    }}
  }} catch (e) {{
    console.warn("Pull Google Sheet error:", e);
    if (!silent) showToast("⚠️ Impossible de joindre Google Sheet (Vérifiez le déploiement Web App 'Tout le monde').");
    return false;
  }}
}}

async function syncBothWaysGoogleSheet() {{
  const webhookUrl = (localStorage.getItem(WEBHOOK_KEY) || "").trim();
  if (!webhookUrl) {{
    showGoogleSheetBackupCenter();
    showToast("⚠️ Configurez l'URL Web App Google Sheet pour synchroniser automatiquement.");
    return;
  }}
  showToast("⏳ Synchronisation Téléphone ↔ PC ↔ Google Sheet en cours...");
  triggerGoogleSheetAutoBackup({{ action: "Synchronisation Bidirectionnelle", date: nowAlgeriaTimestamp() }});
  setTimeout(async () => {{
    await pullFromGoogleSheet(false);
  }}, 1500);
}}

function exportSyncJson() {{
  const payload = {{
    db: DB,
    history: DB["SE Historique Modifications"] || [],
    export_date: nowAlgeriaTimestamp(),
    user: CURRENT_USER_ROLE
  }};
  const str = JSON.stringify(payload, null, 2);
  const blob = new Blob([str], {{ type: "application/json" }});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `saint_eugene_sync_${{Date.now()}}.json`;
  a.click();
  showToast("📥 Fichier de synchronisation téléchargé ! Transférez-le sur votre autre appareil.");
}}

function importSyncJsonFile(inputEl) {{
  const file = inputEl.files && inputEl.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = (e) => {{
    try {{
      const parsed = JSON.parse(e.target.result);
      if (parsed.db) {{
        DB = parsed.db;
        if (parsed.history) DB["SE Historique Modifications"] = parsed.history;
        recomputeAllLinks(DB);
        try {{ localStorage.setItem(STORAGE_KEY, JSON.stringify(DB)); }} catch(err) {{}}
        renderSidebar(CURRENT_DOCTYPE);
        if (CURRENT_DOCTYPE) showList(CURRENT_DOCTYPE, false);
        else showWorkspace();
        showToast("✅ Synchronisation importée avec succès ! La base est à jour.");
      }} else {{
        alert("Fichier JSON invalide (clé 'db' manquante).");
      }}
    }} catch(err) {{
      alert("Erreur de lecture du fichier JSON : " + err.message);
    }}
  }};
  reader.readAsText(file);
}}

function saveDB(lastEvent = null) {{
  window.DB = DB;
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
    title: "👥 Ressources Humaines & Paie",
    items: [
      {{ label: "📊 Tableau de Bord RH", action: "rh_dashboard" }},
      {{ label: "🪪 Collaborateurs Hôtel", action: "rh_employees" }},
      {{ label: "⚡ Centre de Paie & Bulletins", action: "rh_payroll" }},
      {{ label: "🏛️ Déclarations CNAS & Congés", action: "rh_cnas" }}
    ]
  }},
  {{
    title: "Fiscalité G50 & Patrimoine",
    items: [
      {{ label: "🏛️ Déclarations TVA (G50)", doctype: "SE Declaration TVA" }},
      {{ label: "🎯 Budget Annuel 2026", doctype: "SE Budget Annuel" }},
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
  const orange = ["Partielle", "Non pointé", "Sous-Performance", "Sous Tension", "En attente signature DAF", "À renouveler (< 30j)", "Déclarée (G50)", "Non validée"];
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
      if (item.action === "rh_employees" && DB["SE Employe"]) count = DB["SE Employe"].length;
      else if (item.action === "rh_payroll" && DB["SE Fiche de Paie Mensuelle"]) count = DB["SE Fiche de Paie Mensuelle"].length;
      else if (item.doctype && DB[item.doctype]) count = DB[item.doctype].length;
      else if (item.action === "gsheet") count = (DB["SE Historique Modifications"] || []).length;
      const active = activeKey === key ? "active" : "";
      let fn = "showWorkspace()";
      if (item.action && item.action.startsWith("rh_")) {{
        const sub = item.action.replace("rh_", "");
        fn = `window.showRhModule('${{sub}}')`;
      }} else if (item.doctype) {{
        fn = `showList('${{item.doctype}}')`;
      }} else if (item.action === "gsheet") {{
        fn = `showGoogleSheetBackupCenter()`;
      }}
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

  let thHtml = `<th>Référence (ID)</th>` + listFields.map(f => `<th>${{f.label}}</th>`).join("") + `<th>Dernière Modif.</th><th style="text-align:center;width:48px;">Action</th>`;
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
  tfootCells += `<td></td><td></td>`;

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

      <div style="margin-top:14px;padding:12px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;margin-bottom:12px;">
        <div style="font-size:12.5px;font-weight:700;color:#1e3a8a;margin-bottom:6px;">
          📱 Synchronisation Multi-Appareils (Téléphone ↔ Ordinateur) :
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
          <button class="btn btn-primary" onclick="syncBothWaysGoogleSheet()">🔄 Synchroniser Téléphone ↔ PC (via Google Sheet)</button>
          <button class="btn btn-gold" onclick="exportSyncJson()">📤 Exporter Données (Fichier JSON)</button>
          <label class="btn" style="cursor:pointer;background:#fff;border-color:#cbd5e1;display:inline-flex;align-items:center;">
            📥 Importer Données (JSON)
            <input type="file" accept=".json" style="display:none;" onchange="importSyncJsonFile(this)">
          </label>
        </div>
        <div style="font-size:11.5px;color:#1e40af;margin-top:8px;line-height:1.5;">
          🌐 <b>Accès Direct Réseau Wi-Fi :</b> Si votre téléphone et ce PC sont connectés au même réseau Wi-Fi, ouvrez directement l'adresse <b><a href="http://192.168.1.28:8080" target="_blank" style="color:#1d4ed8;font-weight:700;">http://192.168.1.28:8080</a></b> sur le navigateur de votre téléphone ! Toutes vos actions seront directement et instantanément synchronisées sur votre PC.
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

function getArticleCategory(article) {{
  if (ROOM_TYPES.includes(article)) return "Hébergement";
  if (article === "Location de salle") return "Séminaires & Banquets";
  return "Restauration";
}}


function formatDzdInWords(montant) {{
  const val = Math.abs(Number(montant) || 0);
  const dinars = Math.floor(val);
  const centimes = Math.round((val - dinars) * 100);
  const units = ["zéro", "un", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf",
    "dix", "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf"];
  const tens = ["", "", "vingt", "trente", "quarante", "cinquante", "soixante", "soixante-dix", "quatre-vingts", "quatre-vingt-dix"];
  function convertUnder100(n) {{
    if (n < 20) return units[n];
    const t = Math.floor(n / 10);
    const u = n % 10;
    if (t === 7) return u === 1 ? "soixante et onze" : ("soixante-" + units[10 + u]);
    if (t === 8) return u === 0 ? "quatre-vingts" : ("quatre-vingt-" + units[u]);
    if (t === 9) return "quatre-vingt-" + units[10 + u];
    if (u === 1) return tens[t] + " et un";
    return u === 0 ? tens[t] : (tens[t] + "-" + units[u]);
  }}
  function convertUnder1000(n) {{
    if (n === 0) return "";
    const h = Math.floor(n / 100);
    const r = n % 100;
    let res = "";
    if (h === 1) res = "cent";
    else if (h > 1) res = units[h] + " cent" + (r === 0 ? "s" : "");
    if (r > 0) res = res ? (res + " " + convertUnder100(r)) : convertUnder100(r);
    return res;
  }}
  function intToFrench(n) {{
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
  }}
  const dinarsTxt = intToFrench(dinars);
  const capDinars = dinarsTxt.charAt(0).toUpperCase() + dinarsTxt.slice(1);
  const dev = dinars <= 1 ? "Dinar Algérien" : "Dinars Algériens";
  let phrase = capDinars + " " + dev;
  if (centimes > 0) phrase += " et " + intToFrench(centimes) + " " + (centimes === 1 ? "Centime" : "Centimes");
  return phrase;
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
                    <optgroup label="🛏️ Catégories Officielles Chambres 4★ (TVA 9%)">
            ${{[
              "Single Standard [SGL-STD]",
              "Single Vue Mer [SGL-MER]",
              "Double Standard [DBL-STD]",
              "Double Vue Mer [DBL-MER]",
              "Chambre Twin [TWIN]",
              "Chambre Triple [TRP]",
              "Suite Deluxe [SDL]",
              "Suite Saint Eugène [SSE]"
            ].map(r => `<option value="${{r}}" ${{r === ln.article ? "selected" : ""}}>${{r}}</option>`).join("")}}
          </optgroup>
          <optgroup label="🛏️ Catégories Standards & Historiques (TVA 9%)">
            ${{["Single", "Double", "Twin", "Triple"].map(r => `<option value="${{r}}" ${{r === ln.article ? "selected" : ""}}>${{r}}</option>`).join("")}}
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
      <td style="padding:6px;">
        <textarea rows="1" placeholder="Observations chambre (ex: VIP, lit sup, vue mer...)" oninput="CURRENT_DOC.lignes[${{idx}}].observation=this.value; CURRENT_DOC.lignes[${{idx}}].obs=this.value; CURRENT_DOC.lignes[${{idx}}].remarque=this.value;" style="width:100%;box-sizing:border-box;padding:4px 6px;border:1px solid #cbd5e1;border-radius:4px;font-size:11.5px;resize:vertical;min-height:30px;line-height:1.3;font-family:inherit;">${{ln.observation || ln.obs || ln.remarque || ''}}</textarea>
      </td>
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
      ${{isProforma ? `
      <div class="form-group">
        <label>Statut Pro Forma *</label>
        <select id="inv_statut" onchange="CURRENT_DOC.statut=this.value;">
          <option value="Non validée" ${{doc.statut === "Non validée" || !doc.statut ? "selected" : ""}}>Non validée</option>
          <option value="Validée" ${{doc.statut === "Validée" ? "selected" : ""}}>Validée</option>
        </select>
      </div>` : ''}}
      <div class="form-group">
        <label>N° Bon de Commande (BC) / Réf. Commande</label>
        <input type="text" id="inv_bon_commande" placeholder="Ex: BC-2026/045 ou Réf Client..." value="${{doc.bon_commande || doc.num_bon_commande || ''}}" onchange="CURRENT_DOC.bon_commande=this.value; CURRENT_DOC.num_bon_commande=this.value;">
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
            <th style="padding:7px;min-width:140px;">Observations (Chambre)</th>
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

  let ftrHtml = `<div style="display:flex;gap:6px;flex-wrap:wrap;align-items:center;">`;
  if (!isNew) {{
    ftrHtml += `<button type="button" class="btn" style="background:#fee2e2;color:#991b1b;border:1px solid #fecaca;font-weight:600;padding:6px 12px;margin-right:6px;" onclick="triggerDeleteDoc('${{doctype}}', '${{doc.name.replace(/'/g, "\\'")}}')">🗑️ Supprimer</button>`;
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
  const bcInput = document.getElementById("inv_bon_commande");
  if (bcInput) {{
    CURRENT_DOC.bon_commande = bcInput.value.trim();
    CURRENT_DOC.num_bon_commande = bcInput.value.trim();
  }}
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
    ftrHtml += `<button type="button" class="btn" style="background:#fee2e2;color:#991b1b;border:1px solid #fecaca;font-weight:600;padding:6px 12px;margin-right:6px;" onclick="triggerDeleteDoc('${{doctype}}', '${{doc.name.replace(/'/g, "\\'")}}')">🗑️ Supprimer</button>`;
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


let PENDING_DELETE_DOCTYPE = null;
let PENDING_DELETE_NAME = null;

function checkDeleteIntegrity(doctype, docName) {{
  const db = (typeof DB !== "undefined" ? DB : ((typeof APP_STATE !== "undefined" && APP_STATE.db) ? APP_STATE.db : {{}}));
  if (doctype === "SE Client") {{
    const facs = (db["SE Facture Client"] || []).filter(f => f.client === docName || f.nom_client === docName || f.ref_societe === docName);
    if (facs.length > 0) {{
      return {{
        blocked: true,
        message: `⚠️ <b>Suppression bloquée pour conformité comptable SCF :</b> Ce client est lié à <b>${{facs.length}} facture(s) enregistrée(s)</b> (ex: ${{facs[0].name}}). La suppression directe briserait le lettrage des comptes tiers (SCF 411). Veuillez plutôt archiver ou désactiver ce client.`
      }};
    }}
  }} else if (doctype === "SE Facture Client") {{
    const encs = (db["SE Encaissement"] || []).filter(e => e.facture_liee === docName && e.statut !== "Annulé");
    if (encs.length > 0) {{
      return {{
        blocked: true,
        message: `⚠️ <b>Suppression bloquée :</b> Cette facture est rattachée à <b>${{encs.length}} encaissement(s) comptabilisé(s)</b> (ex: ${{encs[0].name}}). Supprimez ou annulez d'abord les encaissements pour préserver les écritures de trésorerie (SCF 512/530).`
      }};
    }}
  }} else if (doctype === "SE Fournisseur") {{
    const facs = (db["SE Facture Fournisseur"] || []).filter(f => f.fournisseur === docName);
    if (facs.length > 0) {{
      return {{
        blocked: true,
        message: `⚠️ <b>Suppression bloquée :</b> Ce fournisseur possède <b>${{facs.length}} facture(s) d'achat</b> (ex: ${{facs[0].name}}). La suppression directe compromettrait la déclaration de TVA déductible (G50).`
      }};
    }}
  }} else if (doctype === "SE Facture Fournisseur") {{
    const decs = (db["SE Decaissement"] || []).filter(d => d.facture_liee === docName && d.statut !== "Annulé");
    if (decs.length > 0) {{
      return {{
        blocked: true,
        message: `⚠️ <b>Suppression bloquée :</b> Cette facture fournisseur est associée à <b>${{decs.length}} décaissement(s)</b>. Supprimez d'abord les règlements correspondants.`
      }};
    }}
  }} else if (doctype === "SE Employe") {{
    const paies = (db["SE Fiche de Paie Mensuelle"] || []).filter(p => p.employe === docName);
    if (paies.length > 0) {{
      return {{
        blocked: true,
        message: `⚠️ <b>Suppression déconseillée pour conformité CNAS :</b> Cet employé possède <b>${{paies.length}} bulletin(s) de paie</b>. Pour préserver l'historique social et les déclarations DAS/CNAS, il est recommandé de renseigner sa <b>Date de sortie</b> et la situation <b>'Sorti'</b>.`
      }};
    }}
  }} else if (doctype === "SE Compte Tresorerie") {{
    return {{
      blocked: true,
      message: `⚠️ <b>Compte réservé :</b> Les comptes de trésorerie officiels (CPA, BNA, Caisses) sont indispensables à la comptabilité générale.`
    }};
  }}
  return {{ blocked: false, message: "" }};
}}

function triggerDeleteDoc(doctype, docName) {{
  PENDING_DELETE_DOCTYPE = doctype;
  PENDING_DELETE_NAME = docName;
  const detailsEl = document.getElementById("deleteDocDetails");
  const warnEl = document.getElementById("deleteWarningBlock");
  const btnEl = document.getElementById("btnConfirmDelete");
  if (detailsEl) {{
    detailsEl.innerHTML = `<b>Élément sélectionné :</b> ${{docName}} <span style="color:#64748b;">(${{getNavLabel(doctype)}})</span>`;
  }}
  const check = checkDeleteIntegrity(doctype, docName);
  if (check.blocked) {{
    warnEl.style.display = "block";
    warnEl.innerHTML = check.message;
    btnEl.disabled = true;
    btnEl.style.opacity = "0.45";
    btnEl.style.cursor = "not-allowed";
    btnEl.title = "Action bloquée pour protéger l'intégrité comptable";
  }} else {{
    warnEl.style.display = "none";
    warnEl.innerHTML = "";
    btnEl.disabled = false;
    btnEl.style.opacity = "1";
    btnEl.style.cursor = "pointer";
    btnEl.title = "";
  }}
  document.getElementById("deleteConfirmModal").classList.add("open");
}}

function closeDeleteConfirmModal() {{
  document.getElementById("deleteConfirmModal").classList.remove("open");
  PENDING_DELETE_DOCTYPE = null;
  PENDING_DELETE_NAME = null;
}}

async function executeDeleteDoc() {{
  if (!PENDING_DELETE_DOCTYPE || !PENDING_DELETE_NAME) return;
  const dt = PENDING_DELETE_DOCTYPE;
  const name = PENDING_DELETE_NAME;
  closeDeleteConfirmModal();
  closeModal();

  const rows = DB[dt] || [];
  DB[dt] = rows.filter(r => r.name !== name);
  if (typeof APP_STATE !== "undefined" && APP_STATE.db && APP_STATE.db[dt]) {{
    APP_STATE.db[dt] = APP_STATE.db[dt].filter(r => r.name !== name);
  }}

  const logEntry = recordAuditModification(dt, name, "🗑️ Suppression", `Suppression de ${{name}} dans ${{getNavLabel(dt)}}`);
  saveDB(logEntry);
  renderSidebar(dt);
  if (typeof rhRenderActiveView === "function" && typeof RH_STATE !== "undefined" && dt === "SE Employe") {{
    rhRenderActiveView();
  }}
  showList(dt, false);
  showToast(`🗑️ ${{name}} supprimé avec succès.`);
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
          ${{(ln.observation || ln.obs || ln.remarque) ? `<div style="font-size:11px;color:#475569;margin-top:3px;font-style:italic;line-height:1.3;">📝 <b>Observation :</b> ${{String(ln.observation || ln.obs || ln.remarque).split(String.fromCharCode(10)).join('<br>')}}</div>` : ''}}
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
      <div style="display:flex;align-items:center;gap:18px;">
        <img src="${{LOGO_BASE64_URI}}" alt="Logo Hôtel Saint Eugène" style="max-height:72px;width:auto;object-fit:contain;">
        <div>
          <h1 style="margin:0;font-size:20px;color:#0f172a;letter-spacing:0.5px;">${{cfg.raison_sociale}} <span style="font-size:13px;color:#64748b;font-weight:normal;">(${{cfg.forme_juridique || 'SARL'}})</span> <span style="color:#d97706;">★★★★</span></h1>
          <div style="font-size:11.5px;color:#475569;margin-top:4px;line-height:1.4;">
            ${{cfg.adresse}}<br>
            Tél : ${{cfg.telephone}} | Réservations : ${{cfg.email_reservation || cfg.email}}<br>
            <b>RC :</b> ${{cfg.rc}} | <b>NIF :</b> ${{cfg.nif}} | <b>NIS :</b> ${{cfg.nis || '001416170291741'}} | <b>AI :</b> ${{cfg.article_imposition}}
          </div>
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
      <div>
        <b>Banque :</b> ${{cfg.banque || "Crédit Populaire d'Algérie (CPA)"}} — ${{cfg.agence_bancaire || "CPA Bab El Oued"}}<br>
        <b>Code Agence :</b> ${{cfg.code_agence || "175"}} | <b>Compte Bancaire :</b> ${{cfg.compte_bancaire || "004 00175 4000261090 62"}}<br>
        <b>Capital Social :</b> ${{cfg.capital_social}} | <b>Forme Juridique :</b> ${{cfg.forme_juridique || "SARL"}}
      </div>
      <div style="text-align:right;min-width:200px;">
        <b>Cachet & Signature Direction</b><br><br><br>
        <i>HOTEL SAINT EUGENE 4★ Alger</i>
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
