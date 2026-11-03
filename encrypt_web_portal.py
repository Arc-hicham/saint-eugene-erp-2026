# -*- coding: utf-8 -*-
"""
Génère `index.html` protégé par Mot de Passe & Chiffrement (PBKDF2-HMAC-SHA256 + Flux Chiffré)
pour GitHub Pages : https://arc-hicham.github.io/saint-eugene-erp-2026/

Optimisé Mobile (Smartphone iOS / Android) & Desktop :
- Sauvegarde persistante automatique (Factures, Encaissements, Caisse, Performance, etc.)
- Auto-remplissage intelligent (sélectionner une Facture dans Encaissement remplit Client, Montant restant, Compte)
- Calcul en temps réel dans le formulaire (TVA 9%/19%, Taxe de séjour 500 DZD, Droit de timbre, TTC, Reste à payer)
- Navigation mobile fluide (Menu tiroir + Barre d'action rapide en bas de l'écran téléphone)
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


def main() -> None:
    pw_file = APP_ROOT / ".portal_password.txt"
    if len(sys.argv) > 1 and sys.argv[1].strip():
        password = sys.argv[1].strip()
        pw_file.write_text(password, encoding="utf-8")
    elif pw_file.exists():
        password = pw_file.read_text(encoding="utf-8").strip() or "SaintEugene2026"
    else:
        password = "SaintEugene2026"
    initial_db = build_initial_seed_db()
    encrypted = encrypt_bundle(password, {"schemas": SCHEMAS, "initial_db": initial_db})
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
    top: 16px;
    left: 50%;
    transform: translateX(-50%) translateY(-120%);
    background: #065f46;
    color: #ffffff;
    padding: 11px 20px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 700;
    box-shadow: 0 10px 25px rgba(0,0,0,0.25);
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
    width: 275px;
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
  .nav-btn {{ width: 100%; text-align: left; background: transparent; border: none; color: #cbd5e1; padding: 9px 11px; border-radius: 6px; font-size: 13px; cursor: pointer; display: flex; align-items: center; justify-content: space-between; transition: 0.15s; }}
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
    padding: 8px 20px;
    flex-shrink: 0;
    gap: 10px;
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
  .topbar-title span#viewTitle {{ white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 52vw; }}
  .badge-scf {{ background: #fef3c7; color: #92400e; border: 1px solid #fcd34d; font-size: 11px; padding: 2px 8px; border-radius: 999px; font-weight: 600; white-space: nowrap; }}
  .topbar-actions {{ display: flex; align-items: center; gap: 7px; flex-wrap: wrap; }}
  .btn {{ padding: 8px 13px; border-radius: 7px; font-size: 12.5px; font-weight: 600; cursor: pointer; border: 1px solid var(--border); background: #fff; color: var(--text); transition: 0.15s; white-space: nowrap; }}
  .btn:hover {{ background: #f8fafc; }}
  .btn-primary {{ background: var(--navy); color: #fff; border-color: var(--navy); }}
  .btn-primary:hover {{ background: #1e293b; }}
  .btn-gold {{ background: #b45309; color: #fff; border-color: #b45309; }}
  .btn-gold:hover {{ background: #92400e; }}
  .btn-danger {{ background: #fef2f2; color: #dc2626; border-color: #fecaca; }}
  .content {{ flex: 1; overflow-y: auto; padding: 20px 24px; -webkit-overflow-scrolling: touch; }}

  /* KPI Grid */
  .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 13px; margin-bottom: 20px; }}
  .kpi-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 13px 15px; cursor: pointer; transition: transform 0.12s, box-shadow 0.12s; border-top: 4px solid #2563eb; }}
  .kpi-card:hover {{ transform: translateY(-2px); box-shadow: 0 6px 16px rgba(15,23,42,0.07); }}
  .kpi-label {{ font-size: 11px; color: var(--muted); font-weight: 600; text-transform: uppercase; margin-bottom: 5px; }}
  .kpi-val {{ font-size: 16.5px; font-weight: 800; color: var(--navy); }}

  /* Alerts & Charts */
  .alerts-panel {{ background: #fff; border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; margin-bottom: 20px; }}
  .alerts-panel h3 {{ margin: 0 0 10px 0; font-size: 13.5px; color: var(--navy); display: flex; align-items: center; gap: 8px; }}
  .alert-item {{ display: flex; align-items: center; justify-content: space-between; padding: 9px 12px; border-radius: 6px; margin-bottom: 6px; font-size: 12.5px; cursor: pointer; gap: 8px; }}
  .alert-item.red {{ background: #fef2f2; border-left: 4px solid var(--red); color: #991b1b; }}
  .alert-item.orange {{ background: #fff7ed; border-left: 4px solid var(--orange); color: #9a3412; }}
  .chart-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 16px; margin-bottom: 24px; }}
  .chart-box {{ background: #fff; border: 1px solid var(--border); border-radius: 10px; padding: 15px; min-width: 0; }}
  .chart-box h4 {{ margin: 0 0 12px 0; font-size: 13px; color: var(--navy); }}

  /* Tables */
  .table-card {{ background: #fff; border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }}
  .table-scroll {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
  .table-toolbar {{ padding: 12px 16px; border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; }}
  .search-input {{ padding: 9px 12px; border: 1px solid var(--border); border-radius: 7px; font-size: 14px; width: 280px; max-width: 100%; }}
  table.frappe-list {{ width: 100%; border-collapse: collapse; font-size: 12.8px; min-width: 600px; }}
  table.frappe-list th {{ background: #f8fafc; color: #475569; text-align: left; padding: 10px 12px; font-size: 11px; text-transform: uppercase; border-bottom: 1px solid var(--border); white-space: nowrap; }}
  table.frappe-list td {{ padding: 10px 12px; border-bottom: 1px solid #f1f5f9; }}
  table.frappe-list tr:hover td {{ background: #f8fafc; cursor: pointer; }}
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
    .topbar {{ padding: 8px 12px; min-height: 52px; }}
    .topbar-title {{ font-size: 13.5px; }}
    .topbar-title span#viewTitle {{ max-width: 46vw; }}
    .topbar-actions .hide-mobile {{ display: none; }}
    .content {{ padding: 12px 12px 80px 12px; }}
    .kpi-grid {{ grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 16px; }}
    .kpi-card {{ padding: 11px 12px; }}
    .kpi-label {{ font-size: 10px; }}
    .kpi-val {{ font-size: 14px; }}
    .chart-grid {{ grid-template-columns: 1fr; gap: 12px; }}
    .alert-item {{ flex-direction: column; align-items: flex-start; }}
    .search-input {{ width: 100%; font-size: 16px; }}
    .table-toolbar .btn {{ width: 100%; text-align: center; padding: 10px; font-size: 13.5px; }}
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

<div class="toast-banner" id="toastBanner">✅ Opération enregistrée et sauvegardée</div>

<!-- Portail d'authentification privé (Chiffrement PBKDF2-SHA256) -->
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
        <option value="Contrôle de Gestion / DAF">Contrôle de Gestion / DAF (Hicham Bakir)</option>
        <option value="Direction Générale">Direction Générale — Hôtel Saint Eugène</option>
        <option value="Chef Comptable SCF">Chef Comptable SCF & Audit</option>
      </select>
    </div>
    <div class="login-field">
      <label>Code d'Accès Confidentiel</label>
      <input type="password" id="loginPassword" placeholder="Entrez le code d'accès privé..." required autofocus>
    </div>
    <button type="submit" class="login-btn" id="loginBtn">🔓 Déverrouiller l'Espace Financier</button>
    <div class="login-footer">
      🔒 Données chiffrées de bout en bout (PBKDF2-SHA256) • Normes SCF Algérie
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
      <button class="menu-toggle-btn" onclick="toggleMobileSidebar()" title="Menu des 22 Modules">☰</button>
      <div class="topbar-title">
        <span id="viewTitle">Direction Saint Eugène 2026</span>
        <span class="badge-scf">Normes SCF Algérie • DZD</span>
      </div>
    </div>
    <div class="topbar-actions">
      <button class="btn hide-mobile" onclick="showWorkspace()">📊 Tableau de Bord</button>
      <button class="btn btn-gold hide-mobile" onclick="openNewDoc('SE Facture Client')">+ Nouvelle Facture Client</button>
      <button class="btn btn-primary hide-mobile" onclick="openNewDoc('SE Encaissement')">+ Nouvel Encaissement</button>
      <button class="btn" title="Réinitialiser les données initiales 2026" onclick="confirmResetDemoData()">🔄 Réinitialiser</button>
      <button class="btn" style="border-color:#fca5a5;color:#dc2626;" onclick="lockSession()">🔒</button>
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
  <button class="mob-nav-item highlight" onclick="openNewDoc('SE Encaissement')">
    <span class="ico">💰</span>
    <span>+ Encaissement</span>
  </button>
  <button class="mob-nav-item" onclick="showList('SE Facture Client')">
    <span class="ico">📋</span>
    <span>Factures</span>
  </button>
  <button class="mob-nav-item" onclick="toggleMobileSidebar(true)">
    <span class="ico">☰</span>
    <span>Modules</span>
  </button>
</nav>

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
const ENCRYPTED_BUNDLE = {encrypted_json};
const STORAGE_KEY = "saint_eugene_erp_2026_db_v3";
const SESSION_KEY = "saint_eugene_erp_2026_unlocked";

let SCHEMAS = {{}};
let INITIAL_DB = {{}};
let DB = {{}};
let CURRENT_DOCTYPE = null;
let CURRENT_DOC = null;
let CURRENT_IS_NEW = false;

function showToast(msg) {{
  const el = document.getElementById("toastBanner");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(window.__toastTimer);
  window.__toastTimer = setTimeout(() => el.classList.remove("show"), 3200);
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

async function tryDecryptBundle(password) {{
  const enc = new TextEncoder();
  const salt = b64ToBytes(ENCRYPTED_BUNDLE.salt_b64);
  const baseKey = await crypto.subtle.importKey("raw", enc.encode(password), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits(
    {{ name: "PBKDF2", salt, iterations: ENCRYPTED_BUNDLE.iterations, hash: "SHA-256" }},
    baseKey,
    256
  );
  const dk = new Uint8Array(bits);
  const suffix = enc.encode("SAINT_EUGENE_AUTH_2026");
  const checkBuf = new Uint8Array(dk.length + suffix.length);
  checkBuf.set(dk, 0);
  checkBuf.set(suffix, dk.length);
  const hashBuf = await crypto.subtle.digest("SHA-256", checkBuf);
  const tagHex = bytesToHex(new Uint8Array(hashBuf));
  if (tagHex !== ENCRYPTED_BUNDLE.verify_tag) {{
    return null;
  }}
  const cipherBytes = b64ToBytes(ENCRYPTED_BUNDLE.cipher_b64);
  const plainBytes = rc4Drop4096Decrypt(dk, cipherBytes);
  const jsonStr = new TextDecoder("utf-8").decode(plainBytes);
  return JSON.parse(jsonStr);
}}

async function handleUnlock(e) {{
  if (e) e.preventDefault();
  const pwd = document.getElementById("loginPassword").value.trim();
  const role = document.getElementById("loginRole").value;
  const errEl = document.getElementById("loginError");
  const btnEl = document.getElementById("loginBtn");
  errEl.style.display = "none";
  btnEl.textContent = "Vérification cryptographique...";

  try {{
    const bundle = await tryDecryptBundle(pwd);
    if (!bundle) {{
      errEl.style.display = "block";
      btnEl.textContent = "🔓 Déverrouiller l'Espace Financier";
      return;
    }}
    SCHEMAS = bundle.schemas;
    INITIAL_DB = bundle.initial_db;
    sessionStorage.setItem(SESSION_KEY, JSON.stringify({{ pwd, role }}));
    document.getElementById("activeUserBadge").textContent = `Connecté : ${{role}}`;
    document.getElementById("loginScreen").classList.add("hidden");
    DB = loadDB();
    renderSidebar();
    showWorkspace();
  }} catch (err) {{
    errEl.style.display = "block";
    btnEl.textContent = "🔓 Déverrouiller l'Espace Financier";
  }}
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
    const raw = localStorage.getItem(STORAGE_KEY) || localStorage.getItem("saint_eugene_erp_2026_db_v2");
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
  recomputeAllLinks(base);
  try {{
    localStorage.setItem(STORAGE_KEY, JSON.stringify(base));
  }} catch (e) {{}}
  return base;
}}

function saveDB() {{
  recomputeAllLinks(DB);
  try {{
    localStorage.setItem(STORAGE_KEY, JSON.stringify(DB));
  }} catch (e) {{}}
}}

function confirmResetDemoData() {{
  if (!confirm("Voulez-vous réinitialiser la base avec les données de démonstration 2026 ? (Vos ajouts locaux seront effacés)")) return;
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

  // 1. Factures Clients
  (db["SE Facture Client"] || []).forEach(fac => recomputeSingleInvoice(fac, db));

  // 2. Factures Fournisseurs
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

  // 3. Performance Hôtelière (45 ch.)
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

  // 4. Fiches de Paie (CNAS / IRG)
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

  // 5. Comptes de Trésorerie (Caisses & Banques)
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

  // 6. Caisse Mensuelle
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

  // 7. Déclarations TVA (G50)
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

  // 8. Budget Annuel 2026
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
    title: "Pilotage Direction",
    items: [
      {{ label: "📊 Direction Saint Eugène 2026", action: "workspace" }},
      {{ label: "⚙️ Paramètres Hôtel & Fiscalité 4★", doctype: "SE Parametres Hotel" }}
    ]
  }},
  {{
    title: "Facturation & Exploitation",
    items: [
      {{ label: "🧾 Factures Clients (SCF 70)", doctype: "SE Facture Client" }},
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
      const key = item.doctype || "workspace";
      const count = item.doctype && DB[item.doctype] ? DB[item.doctype].length : "";
      const active = activeKey === key ? "active" : "";
      const fn = item.doctype ? `showList('${{item.doctype}}')` : `showWorkspace()`;
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

function showList(doctype, search = "") {{
  toggleMobileSidebar(false);
  if (doctype === "SE Parametres Hotel") {{
    openDoc("SE Parametres Hotel", "SE Parametres Hotel");
    return;
  }}
  CURRENT_DOCTYPE = doctype;
  renderSidebar(doctype);
  const schema = SCHEMAS[doctype];
  const rows = DB[doctype] || [];
  const labelTitle = getNavLabel(doctype);
  document.getElementById("viewTitle").textContent = `${{labelTitle}} (${{rows.length}})`;

  const listFields = schema.fields.filter(f => f.in_list_view && !["Section Break", "Column Break", "Table"].includes(f.fieldtype)).slice(0, 6);
  const filtered = rows.filter(r => !search || JSON.stringify(r).toLowerCase().includes(search.toLowerCase()));

  let thHtml = `<th>Référence (ID)</th>` + listFields.map(f => `<th>${{f.label}}</th>`).join("");
  let trHtml = filtered.map(r => {{
    let tds = `<td><b>${{r.name}}</b></td>`;
    listFields.forEach(f => {{
      let val = r[f.fieldname];
      if (f.fieldtype === "Currency") {{
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
    return `<tr onclick="openDoc('${{doctype}}', '${{r.name.replace(/'/g, "\\\\'")}}')">${{tds}}</tr>`;
  }}).join("");

  document.getElementById("mainContent").innerHTML = `
    <div class="table-card">
      <div class="table-toolbar">
        <input class="search-input" placeholder="🔍 Rechercher dans ${{labelTitle}}..." value="${{search}}" oninput="showList('${{doctype}}', this.value)">
        <button class="btn btn-primary" onclick="openNewDoc('${{doctype}}')">+ Nouveau (${{labelTitle}})</button>
      </div>
      <div class="table-scroll">
        <table class="frappe-list">
          <thead><tr>${{thHtml}}</tr></thead>
          <tbody>${{trHtml || `<tr><td colspan="8" style="text-align:center;padding:24px;color:#64748b;">Aucun enregistrement</td></tr>`}}</tbody>
        </table>
      </div>
    </div>
  `;
}}

function generateNextDocName(doctype) {{
  const rows = DB[doctype] || [];
  const prefixes = {{
    "SE Facture Client": "FAC-CLI-2026-",
    "SE Encaissement": "ENC-2026-",
    "SE Facture Fournisseur": "FAC-FRN-2026-",
    "SE Decaissement": "DEC-2026-",
    "SE Charge et Depense": "CHG-2026-",
    "SE Fiche de Paie Mensuelle": "PAIE-2026-",
    "SE Operation Bancaire": "OPB-2026-",
    "SE Immobilisation": "IMMO-2026-",
    "SE Contrat et Abonnement": "CTR-2026-",
    "SE Employe": "SE-EMP-"
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

  // Valeurs intelligentes par défaut pour Facture Client & Encaissement
  if (doctype === "SE Facture Client") {{
    const firstClient = (DB["SE Client"] || [])[0];
    if (firstClient) {{
      doc.client = firstClient.name;
      doc.type_client = firstClient.type_client || "Corporate";
    }}
    doc.date_facture = "2026-11-03";
    doc.date_debut_sejour = "2026-11-01";
    doc.date_fin_sejour = "2026-11-03";
    doc.nuitees = 2;
    doc.nb_adultes = 1;
    doc.nature_prestation = "Hébergement";
    doc.taux_tva = "9";
    doc.appliquer_taxe_sejour = 1;
    doc.mode_paiement_prevu = "Virement";
    doc.date_echeance = "2026-12-03";
    doc.statut = "Validée";
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

  renderDocModal(doctype, doc, true);
}}

function renderDocModal(doctype, doc, isNew) {{
  CURRENT_DOCTYPE = doctype;
  CURRENT_DOC = doc;
  CURRENT_IS_NEW = !!isNew;
  const schema = SCHEMAS[doctype];
  document.getElementById("modalTitle").textContent = `${{isNew ? "➕ Nouveau" : doc.name}} — ${{getNavLabel(doctype)}}`;

  let formHtml = `<div class="form-grid">`;
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

  const printable = ["SE Facture Client", "SE Caisse Mensuelle", "SE Fiche de Paie Mensuelle", "SE Declaration TVA"].includes(doctype);
  let ftrHtml = `<div style="display:flex;gap:6px;flex-wrap:wrap;">`;
  if (printable && !isNew) {{
    ftrHtml += `<button class="btn btn-gold" onclick="openPrintPreview()">🖨️ PDF SCF</button>`;
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

  // Auto-calcul en direct pour Facture Client
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

  // Auto-remplissage en direct pour Encaissement Client
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

  // Auto-calcul en direct pour Performance Hôtelière (45 ch.)
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
  const rows = DB[CURRENT_DOCTYPE] || (DB[CURRENT_DOCTYPE] = []);
  const idx = rows.findIndex(r => r.name === CURRENT_DOC.name);
  if (idx >= 0) rows[idx] = CURRENT_DOC;
  else rows.unshift(CURRENT_DOC);

  // Si c'est une Facture Client d'un nouveau mois, créer automatiquement la ligne G50 correspondante si absente
  if (CURRENT_DOCTYPE === "SE Facture Client" && CURRENT_DOC.date_facture) {{
    const mois = String(CURRENT_DOC.date_facture).slice(0, 7);
    const g50List = DB["SE Declaration TVA"] || (DB["SE Declaration TVA"] = []);
    if (mois && !g50List.some(g => g.mois === mois)) {{
      g50List.push({{
        name: `G50-${{mois}}`,
        mois: mois,
        precompte_anterieur: 0,
        statut: "Déclarée (G50)"
      }});
    }}
  }}

  saveDB();
  const savedName = CURRENT_DOC.name;
  const savedDoctype = CURRENT_DOCTYPE;
  closeModal();
  renderSidebar(savedDoctype);
  if (savedDoctype === "SE Parametres Hotel") showWorkspace();
  else showList(savedDoctype);
  showToast(`✅ ${{savedName}} enregistré et sauvegardé !`);
}}

function deleteCurrentDoc() {{
  if (!confirm(`Supprimer définitivement ${{CURRENT_DOC.name}} ?`)) return;
  const rows = DB[CURRENT_DOCTYPE] || [];
  DB[CURRENT_DOCTYPE] = rows.filter(r => r.name !== CURRENT_DOC.name);
  saveDB();
  const dt = CURRENT_DOCTYPE;
  closeModal();
  renderSidebar(dt);
  showList(dt);
  showToast(`🗑️ ${{CURRENT_DOC.name}} supprimé`);
}}

function openPrintPreview() {{
  syncModalInputsToDoc();
  const doc = CURRENT_DOC;
  const cfg = DB["SE Parametres Hotel"][0];
  const w = window.open("", "_blank");
  if (CURRENT_DOCTYPE === "SE Facture Client") {{
    const cli = (DB["SE Client"] || []).find(c => c.name === doc.client) || {{}};
    w.document.write(`<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Facture ${{doc.name}}</title>
    <style>
      body {{ font-family:'Segoe UI',Arial,sans-serif; color:#0f172a; max-width:820px; margin:24px auto; padding:24px; border:1px solid #cbd5e1; }}
      .hdr {{ display:flex; justify-content:space-between; border-bottom:3px solid #b45309; padding-bottom:14px; margin-bottom:18px; flex-wrap:wrap; gap:12px; }}
      .grid {{ display:flex; gap:18px; margin-bottom:18px; flex-wrap:wrap; }}
      .box {{ flex:1; min-width:240px; border:1px solid #cbd5e1; border-radius:6px; padding:12px; background:#f8fafc; font-size:12.5px; }}
      table {{ width:100%; border-collapse:collapse; margin-bottom:16px; font-size:13px; }}
      th {{ background:#0f172a; color:#fff; padding:9px; text-align:left; }}
      td {{ padding:9px; border-bottom:1px solid #e2e8f0; }}
      .words {{ background:#fffbeb; border-left:4px solid #d97706; padding:12px; font-size:13px; margin:18px 0; }}
      @media print {{ .no-print {{ display:none; }} body {{ border:none; margin:0; }} }}
    </style></head><body>
    <div class="no-print" style="margin-bottom:14px;text-align:right;"><button onclick="window.print()" style="padding:8px 16px;background:#0f172a;color:#fff;border:none;border-radius:6px;cursor:pointer;">🖨️ Imprimer / Enregistrer en PDF</button></div>
    <div class="hdr">
      <div>
        <h1 style="margin:0;font-size:21px;">${{cfg.raison_sociale}} <span style="color:#d97706;">★★★★</span></h1>
        <div style="font-size:11.5px;color:#475569;margin-top:4px;">
          ${{cfg.adresse}}<br>Tél : ${{cfg.telephone}} | Email : ${{cfg.email}}<br>
          <b>RC :</b> ${{cfg.rc}} | <b>NIF :</b> ${{cfg.nif}} | <b>NIS :</b> ${{cfg.nis}} | <b>AI :</b> ${{cfg.article_imposition}}
        </div>
      </div>
      <div style="text-align:right;">
        <h2 style="margin:0;color:#b45309;">FACTURE SCF</h2>
        <div><b>N° :</b> ${{doc.name}}</div>
        <div><b>Date :</b> ${{doc.date_facture}}</div>
        <div><b>Échéance :</b> ${{doc.date_echeance}}</div>
        <div><b>Statut :</b> ${{doc.statut}}</div>
      </div>
    </div>
    <div class="grid">
      <div class="box">
        <b>FACTURÉ À :</b><br><b>${{doc.client}}</b> (${{doc.type_client || ''}})<br>
        ${{cli.adresse || ''}}<br>
        <b>RC :</b> ${{cli.rc || '—'}} | <b>NIF :</b> ${{cli.nif || '—'}}
      </div>
      <div class="box">
        <b>DÉTAILS DU SÉJOUR :</b><br>
        <b>Prestation :</b> ${{doc.nature_prestation}}<br>
        <b>Réf. Réservation :</b> ${{doc.ref_reservation || '—'}}<br>
        <b>Nuitées / Occupants :</b> ${{doc.nuitees || 1}} nuit(s) / ${{doc.nb_adultes || 1}} adulte(s)<br>
        <b>Mode de règlement :</b> ${{doc.mode_paiement_prevu || 'Virement'}}
      </div>
    </div>
    <table style="width:100%;max-width:460px;margin-left:auto;">
      <tr><td>Total HT</td><td style="text-align:right;"><b>${{fmtDZD(doc.montant_ht)}}</b></td></tr>
      <tr><td>TVA (${{doc.taux_tva}} %)</td><td style="text-align:right;">${{fmtDZD(doc.montant_tva)}}</td></tr>
      <tr><td>Taxe de Séjour 4★</td><td style="text-align:right;">${{fmtDZD(doc.taxe_sejour)}}</td></tr>
      <tr><td>Droit de Timbre Fiscal (Espèces)</td><td style="text-align:right;">${{fmtDZD(doc.droit_timbre)}}</td></tr>
      <tr style="background:#0f172a;color:#fff;font-weight:bold;"><td>NET À PAYER TTC (DZD)</td><td style="text-align:right;">${{fmtDZD(doc.montant_ttc)}}</td></tr>
      <tr><td>Montant Encaissé</td><td style="text-align:right;">${{fmtDZD(doc.montant_encaisse)}}</td></tr>
      <tr><td><b>Reste à Encaisser</b></td><td style="text-align:right;"><b>${{fmtDZD(doc.reste_a_encaisser)}}</b></td></tr>
    </table>
    <div class="words">Arrêtée la présente facture à la somme de :<br><b>« ${{doc.montant_en_lettres}} »</b></div>
    <div style="font-size:11.5px;color:#475569;"><b>RIB :</b> ${{cfg.rib_principal}} | <b>Capital Social :</b> ${{cfg.capital_social}}</div>
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
    print(f"OK: index.html chiffré et optimisé Mobile généré avec le code d'accès '{password}'.")


if __name__ == "__main__":
    main()
