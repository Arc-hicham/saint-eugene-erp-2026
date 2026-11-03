# Saint Eugène ERP 2026 (`saint_eugene`)

**Mini-ERP Frappe v15 100% sur mesure — Hôtel Saint Eugène 4★ (Alger)**  
*Administration • Comptabilité SCF • Trésorerie DZD • Facturation • Paie CNAS/IRG • Pilotage Budgétaire 2026*

## Fonctionnalités Clés
- **16 DocTypes Métiers + 4 Référentiels Tiers/Trésorerie/RH + 1 Table Enfant** avec `Track Changes` activé et verrouillage `Read Only` des champs calculés.
- **Liaisons Automatiques & Contrôle Interne** :
  - Recalcul SQL idempotent (`SUM`) des soldes factures clients/fournisseurs et des comptes de trésorerie (Caisses 53 & Banques 512) à chaque validation/annulation d'encaissement ou décaissement.
  - Calcul automatique du barème **CNAS (9% salarié / 26% employeur)** et **IRG Algérie** sur les fiches de paie.
  - Liquidation automatique de la **TVA G50** (taux réduit touristique 9% et taux normal 19%, échéance le 20 M+1).
  - Alimentation temps réel du **Budget Annuel 2026** (`Réalisé`, `Écart DZD`, `Écart %`) via `doc_events` Frappe Hooks.
  - Tâches planifiées quotidiennes (`scheduler_events`) : calcul des jours de retard et alertes Frappe Desk (factures échues, chèques non encaissés, dépassements budget, trésorerie critique).
- **Workspace "Direction Saint Eugène 2026"** : 10 Number Cards KPI, 4 Dashboard Charts et indicateurs visuels Rouge / Orange / Vert sur toutes les vues listes.

## Installation rapide (WSL2 / Ubuntu)
```bash
chmod +x install_docker_wsl2.sh
./install_docker_wsl2.sh
```
