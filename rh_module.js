/* ==============================================================================
   MODULE RH & PAIE — HÔTEL SAINT EUGÈNE 4★ ALGER
   Architecture épurée, ultra-rapide, intuitive et optimisée mobile & desktop
   Gestion Date d'Entrée / Date de Sortie avec exclusion automatique de la masse salariale
   Conformité Code du Travail Algérien (Loi 90-11) & Normes SCF Algérie
   ============================================================================== */

(function(){
  "use strict";

  function rhTodayDate(){
    if (typeof window.todayAlgeriaDate === "function") return window.todayAlgeriaDate();
    const d = new Date();
    const pad = n => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
  }

  function rhCurrentMonth(){
    if (typeof window.currentAlgeriaMonth === "function") return window.currentAlgeriaMonth();
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  }

  // État local du module RH (période détectée automatiquement sur le mois en cours)
  window.RH_STATE = {
    activeTab: "dashboard", // "dashboard", "employees", "payroll", "cnas"
    currentEmpId: null,
    payrollPeriod: rhCurrentMonth(),
    filterSearch: "",
    filterSituation: "TOUS" // "TOUS", "Actif", "Sorti", "Non déclaré"
  };

  // Utilitaires de formatage
  function rhFmtMoney(v){
    const n = Number(v) || 0;
    return n.toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " DZD";
  }

  function rhFmtDate(d){
    if(!d) return "—";
    try {
      const parts = String(d).split("T")[0].split("-");
      if(parts.length === 3) return parts[2] + "/" + parts[1] + "/" + parts[0];
      return d;
    } catch(e){ return d; }
  }

  function rhDaysDiff(targetDate){
    if(!targetDate) return 9999;
    const now = new Date();
    const t = new Date(targetDate);
    return Math.ceil((t - now) / (1000 * 60 * 60 * 24));
  }

  // RÈGLE MÉTIER FONDAMENTALE : Détecter si le salarié est encore dans l'hôtel
  // Si Date de Sortie renseignée OU Statut === 'Sorti' => L'employé a quitté l'hôtel
  function rhIsEmployeEnPoste(e){
    if(!e) return false;
    if(e.date_sortie && String(e.date_sortie).trim() !== "") return false;
    const sit = String(e.statut_professionnel || e.situation || "").trim();
    if(sit === "Sorti") return false;
    return true;
  }

  // Barème IRG Algérien officiel
  function rhCalcIrg(salaireImposable){
    const s = Math.max(0, Number(salaireImposable) || 0);
    if(s <= 30000) return 0;
    let brutIrg = 0, base = s;
    if(base > 320000){ brutIrg += (base - 320000) * 0.35; base = 320000; }
    if(base > 160000){ brutIrg += (base - 160000) * 0.33; base = 160000; }
    if(base > 80000){ brutIrg += (base - 80000) * 0.30; base = 80000; }
    if(base > 40000){ brutIrg += (base - 40000) * 0.27; base = 40000; }
    if(base > 20000){ brutIrg += (base - 20000) * 0.23; base = 20000; }

    let abat = Math.min(Math.max(brutIrg * 0.40, 1000), 1500);
    let netIrg = Math.max(0, brutIrg - abat);
    if(s > 30000 && s < 35000){
      netIrg = Math.max(0, netIrg * (137/51) - (27925/8));
    }
    return Math.round(netIrg * 100) / 100;
  }

  // Accès aux données universel (supporte window.APP_STATE, window.DB et variables globales)
  function rhGetDb(){
    if(window.APP_STATE && window.APP_STATE.db) return window.APP_STATE.db;
    if(window.DB) return window.DB;
    if(typeof APP_STATE !== "undefined" && APP_STATE && APP_STATE.db) return APP_STATE.db;
    if(typeof DB !== "undefined" && DB) return DB;
    for(const k of ["APP_STATE", "DB", "STATE", "erpDb"]){
      if(window[k] && window[k].db) return window[k].db;
      if(window[k] && Array.isArray(window[k]["SE Employe"])) return window[k];
    }
    return {};
  }

  function rhGetRows(dt){
    const db = rhGetDb();
    return Array.isArray(db[dt]) ? db[dt] : [];
  }

  // Sauvegarde universelle asynchrone garantie
  async function rhSaveDoc(doctype, doc, isNew=false){
    // 1. Mise à jour immédiate en mémoire
    const targetDb = rhGetDb();
    if(targetDb){
      if(!targetDb[doctype]) targetDb[doctype] = [];
      const idx = targetDb[doctype].findIndex(x => x.name === doc.name);
      if(idx >= 0){
        targetDb[doctype][idx] = Object.assign({}, targetDb[doctype][idx], doc);
      } else {
        targetDb[doctype].unshift(doc);
      }
    }

    if(window.APP_STATE && window.APP_STATE.db && window.APP_STATE.db !== targetDb){
      const list = window.APP_STATE.db[doctype] || (window.APP_STATE.db[doctype] = []);
      const idx = list.findIndex(x => x.name === doc.name);
      if(idx >= 0) list[idx] = Object.assign({}, list[idx], doc);
      else list.unshift(doc);
    }

    if(window.DB && window.DB !== targetDb){
      const list = window.DB[doctype] || (window.DB[doctype] = []);
      const idx = list.findIndex(x => x.name === doc.name);
      if(idx >= 0) list[idx] = Object.assign({}, list[idx], doc);
      else list.unshift(doc);
    }

    // 2. Sauvegarde vers le serveur local launch_now.py uniquement si exécuté en local
    const isLocalHost = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1");
    if(isLocalHost && typeof fetch === "function"){
      try {
        const res = await fetch("/api/save", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ doctype: doctype, doc: doc, is_new: isNew })
        });
        if(res.ok){
          const payload = await res.json();
          if(payload && payload.db){
            if(window.APP_STATE) window.APP_STATE = payload;
            if(typeof APP_STATE !== "undefined") APP_STATE = payload;
            window.DB = payload.db;
            if(typeof DB !== "undefined") DB = payload.db;
          }
        }
      } catch(e){
        console.warn("Mode autonome (fetch local ignoré):", e);
      }
    }

    // 3. Sauvegarde portail web chiffré index.html + Traçabilité Audit
    let logEntry = null;
    if(typeof window.recordAuditModification === "function"){
      try {
        const act = isNew ? "➕ Création RH" : "✏️ Mise à jour RH";
        logEntry = window.recordAuditModification(doctype, doc.name, act, `${act} : ${doc.nom_complet || doc.employe_nom || doc.name}`);
      } catch(e){}
    }
    if(typeof window.saveDB === "function"){
      try { window.saveDB(logEntry); } catch(e){}
    } else if(typeof saveDB === "function"){
      try { saveDB(logEntry); } catch(e){}
    }

    // 4. Rafraîchissement des compteurs de la barre latérale
    if(typeof renderSidebar === "function"){
      try { renderSidebar(RH_STATE.activeTab ? "rh_" + RH_STATE.activeTab : "workspace"); } catch(e){}
    }

    rhNotify("✅ " + (doc.nom_complet || doc.name) + " enregistré avec succès !", "success");
    rhRenderActiveView();
  }

  // Notification Toast intégrée
  function rhNotify(msg, type="info"){
    let el = document.getElementById("rh-toast");
    if(!el){
      el = document.createElement("div");
      el.id = "rh-toast";
      el.style.cssText = "position:fixed;bottom:24px;right:24px;z-index:999999;padding:12px 20px;border-radius:8px;font-weight:700;font-size:13px;box-shadow:0 8px 24px rgba(0,0,0,0.25);transition:all 0.3s ease;display:none;";
      document.body.appendChild(el);
    }
    el.style.display = "block";
    el.style.opacity = "1";
    if(type === "success"){
      el.style.background = "#059669"; el.style.color = "#ffffff";
    } else if(type === "error"){
      el.style.background = "#dc2626"; el.style.color = "#ffffff";
    } else {
      el.style.background = "#0f172a"; el.style.color = "#38bdf8";
    }
    el.innerHTML = msg;
    setTimeout(() => {
      el.style.opacity = "0";
      setTimeout(() => el.style.display = "none", 300);
    }, 3500);
  }

  // En-tête principal épuré avec bouton RETOUR AU TABLEAU DE BORD ERP
  function rhRenderHeader(){
    const emps = rhGetRows("SE Employe");
    const enPosteCount = emps.filter(rhIsEmployeEnPoste).length;
    const activeTab = RH_STATE.activeTab;

    return `
      <div style="background:#0f172a;color:#ffffff;border-radius:12px;padding:16px 20px;margin-bottom:16px;box-shadow:0 4px 16px rgba(15,23,42,0.15);">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
          <div style="display:flex;align-items:center;gap:12px;">
            <button onclick="window.rhRetourErp()" style="background:#334155;color:#ffffff;border:1px solid #475569;border-radius:8px;padding:8px 16px;font-size:13px;font-weight:700;cursor:pointer;display:flex;align-items:center;gap:8px;transition:background 0.2s;">
              ⬅️ Retour au Tableau de Bord Principal
            </button>
            <div>
              <div style="font-size:11px;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;font-weight:700;">Hôtel Saint Eugène 4★ Alger</div>
              <div style="font-size:18px;font-weight:800;color:#f8fafc;">Espace RH & Paie Simplifié</div>
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:8px;">
            <button onclick="window.rhModalNouveauSalarie()" style="background:#059669;color:#fff;border:none;border-radius:8px;padding:9px 16px;font-size:13px;font-weight:700;cursor:pointer;display:flex;align-items:center;gap:6px;box-shadow:0 4px 12px rgba(5,150,105,0.3);">
              ➕ Ajouter un Salarié
            </button>
          </div>
        </div>

        <!-- 4 Onglets Clairs et Directs -->
        <div style="display:flex;gap:8px;margin-top:16px;border-top:1px solid #334155;padding-top:12px;overflow-x:auto;">
          <button onclick="window.rhGoTab('dashboard')" style="background:${activeTab === 'dashboard' ? '#d97706' : '#1e293b'};color:#fff;border:none;padding:8px 16px;border-radius:6px;font-size:13px;font-weight:700;cursor:pointer;display:flex;align-items:center;gap:6px;">
            📊 1. Tableau de Bord RH
          </button>
          <button onclick="window.rhGoTab('employees')" style="background:${activeTab === 'employees' ? '#d97706' : '#1e293b'};color:#fff;border:none;padding:8px 16px;border-radius:6px;font-size:13px;font-weight:700;cursor:pointer;display:flex;align-items:center;gap:6px;">
            👥 2. Salariés (${enPosteCount} en poste / ${emps.length} total)
          </button>
          <button onclick="window.rhGoTab('payroll')" style="background:${activeTab === 'payroll' ? '#d97706' : '#1e293b'};color:#fff;border:none;padding:8px 16px;border-radius:6px;font-size:13px;font-weight:700;cursor:pointer;display:flex;align-items:center;gap:6px;">
            ⚡ 3. Centre de Paie & Bulletins
          </button>
          <button onclick="window.rhGoTab('cnas')" style="background:${activeTab === 'cnas' ? '#d97706' : '#1e293b'};color:#fff;border:none;padding:8px 16px;border-radius:6px;font-size:13px;font-weight:700;cursor:pointer;display:flex;align-items:center;gap:6px;">
            🏛️ 4. CNAS & Congés
          </button>
        </div>
      </div>
    `;
  }

  // Action RETOUR ERP
  window.rhRetourErp = function(){
    if(typeof showWorkspace === "function"){
      showWorkspace();
    } else if(typeof window.showWorkspace === "function"){
      window.showWorkspace();
    } else {
      window.location.reload();
    }
  };

  window.rhGoTab = function(t){
    RH_STATE.activeTab = t;
    rhRenderActiveView();
  };

  /* ==============================================================================
     1. VUE TABLEAU DE BORD SIMPLIFIÉ
     Calcul de Masse Salariale STRICTEMENT sur les salariés EN POSTE (Hors sortis)
     ============================================================================== */
  function rhRenderDashboardView(){
    const emps = rhGetRows("SE Employe");
    const contrats = rhGetRows("SE Contrat RH");

    const totalStaff = emps.length;
    const enPosteEmps = emps.filter(rhIsEmployeEnPoste);
    const sortisEmps = emps.filter(e => !rhIsEmployeEnPoste(e));

    const actifs = enPosteEmps.filter(e => (e.statut_professionnel || e.situation) === "Actif" || (!e.statut_professionnel && !e.situation)).length;
    const nonDeclares = enPosteEmps.filter(e => (e.statut_professionnel || e.situation) === "Non déclaré").length;
    const sortis = sortisEmps.length;

    // LOGIQUE IMPORTANTE : La masse salariale contractuelle additionne UNIQUEMENT les salariés en poste !
    // Si un employé a une Date de Sortie (ou est Sorti), son salaire est EXCLU de la masse salariale active !
    const masseContractuelleActive = enPosteEmps.reduce((acc, e) => acc + (Number(e.salaire_base_contractuel) || 0), 0);
    const cnasPatronaleActive = Math.round(masseContractuelleActive * 0.26);

    // Contrats CDD à expiration < 30j (uniquement pour les salariés toujours en poste)
    const contratsExp = contrats.filter(c => {
      const emp = emps.find(x => x.name === c.employe);
      if(emp && !rhIsEmployeEnPoste(emp)) return false;
      return c.statut === "Actif" && c.type_contrat === "CDD" && rhDaysDiff(c.date_fin) <= 30 && rhDaysDiff(c.date_fin) >= 0;
    });

    return `
      <!-- Cartes KPI Essentielles -->
      <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:14px;margin-bottom:20px;">
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:16px;box-shadow:0 2px 4px rgba(0,0,0,0.02);">
          <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">Effectif Actif en Poste</div>
          <div style="font-size:28px;font-weight:800;color:#0f172a;margin:4px 0;">${enPosteEmps.length} <span style="font-size:14px;color:#64748b;font-weight:500;">/ ${totalStaff} total</span></div>
          <div style="font-size:12px;color:#059669;font-weight:600;">🟢 ${actifs} Actifs • 🔴 ${sortis} Sortis de l'hôtel • 🟠 ${nonDeclares} Non déclarés</div>
        </div>

        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:16px;box-shadow:0 2px 4px rgba(0,0,0,0.02);">
          <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">Masse Salariale Active (Salariés en Poste)</div>
          <div style="font-size:20px;font-weight:800;color:#0284c7;margin:4px 0;">${rhFmtMoney(masseContractuelleActive)}</div>
          <div style="font-size:11px;color:#059669;font-weight:600;">✅ Exclut automatiquement les ${sortis} salariés sortis</div>
        </div>

        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:16px;box-shadow:0 2px 4px rgba(0,0,0,0.02);">
          <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">Cotisations CNAS (26% Patronale Active)</div>
          <div style="font-size:20px;font-weight:800;color:#d97706;margin:4px 0;">${rhFmtMoney(cnasPatronaleActive)}</div>
          <div style="font-size:11px;color:#64748b;">Charges sociales du personnel en poste</div>
        </div>

        <div style="background:#fff;border:1px solid ${contratsExp.length > 0 ? '#fecaca' : '#e2e8f0'};border-radius:10px;padding:16px;">
          <div style="font-size:11px;color:${contratsExp.length > 0 ? '#dc2626' : '#64748b'};font-weight:700;text-transform:uppercase;">Contrats à Échéance (< 30j)</div>
          <div style="font-size:28px;font-weight:800;color:${contratsExp.length > 0 ? '#dc2626' : '#059669'};margin:4px 0;">${contratsExp.length}</div>
          <div style="font-size:11px;color:#64748b;">Salariés actifs à renouveler</div>
        </div>
      </div>

      <!-- Alertes & Actions Rapides -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;">
        <!-- Alertes RH -->
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:16px;">
          <div style="font-size:13px;font-weight:800;color:#0f172a;margin-bottom:12px;display:flex;align-items:center;gap:8px;">
            <span>🔔</span> <span>État du Personnel & Mouvements</span>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px;">
            ${sortis > 0 ? `
              <div style="background:#f1f5f9;border:1px solid #cbd5e1;padding:10px;border-radius:6px;font-size:12px;color:#334155;">
                <strong>ℹ️ Salariés Sortis :</strong> ${sortis} collaborateur(s) ont quitté l'établissement et sont retirés du calcul de paie.
              </div>
            ` : ''}

            ${contratsExp.length > 0 ? `
              <div style="background:#fee2e2;border:1px solid #fecaca;padding:10px;border-radius:6px;font-size:12px;color:#991b1b;">
                <strong>⚠️ Échéance Contrat CDD :</strong> ${contratsExp[0].nom_complet || contratsExp[0].employe} expire le ${rhFmtDate(contratsExp[0].date_fin)}.
              </div>
            ` : `<div style="font-size:12px;color:#059669;padding:6px;">✅ Tous les contrats actifs sont à jour.</div>`}

            ${nonDeclares > 0 ? `
              <div style="background:#fffbeb;border:1px solid #fde68a;padding:10px;border-radius:6px;font-size:12px;color:#92400e;">
                <strong>⚠️ Salariés Non Déclarés :</strong> ${nonDeclares} collaborateur(s) en attente d'immatriculation CNAS.
              </div>
            ` : `<div style="font-size:12px;color:#059669;padding:6px;">✅ Tous les salariés en poste sont déclarés CNAS.</div>`}
          </div>
        </div>

        <!-- Raccourcis Directs -->
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:16px;">
          <div style="font-size:13px;font-weight:800;color:#0f172a;margin-bottom:12px;display:flex;align-items:center;gap:8px;">
            <span>⚡</span> <span>Actions Rapides</span>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
            <button onclick="window.rhModalNouveauSalarie()" style="background:#f8fafc;border:1px solid #cbd5e1;border-radius:8px;padding:12px;font-size:12px;font-weight:700;color:#0f172a;cursor:pointer;text-align:left;">
              ➕ Nouveau Salarié
            </button>
            <button onclick="window.rhGoTab('payroll')" style="background:#f8fafc;border:1px solid #cbd5e1;border-radius:8px;padding:12px;font-size:12px;font-weight:700;color:#0f172a;cursor:pointer;text-align:left;">
              ⚡ Calculer la Paie (En poste)
            </button>
            <button onclick="window.rhGoTab('employees')" style="background:#f8fafc;border:1px solid #cbd5e1;border-radius:8px;padding:12px;font-size:12px;font-weight:700;color:#0f172a;cursor:pointer;text-align:left;">
              🪪 Liste des Salariés
            </button>
            <button onclick="window.rhGoTab('cnas')" style="background:#f8fafc;border:1px solid #cbd5e1;border-radius:8px;padding:12px;font-size:12px;font-weight:700;color:#0f172a;cursor:pointer;text-align:left;">
              🏛️ Déclarations CNAS
            </button>
          </div>
        </div>
      </div>
    `;
  }

  // Rendu du badge de situation
  function rhRenderSituationBadge(sit, dateSortie){
    if(dateSortie && String(dateSortie).trim() !== "" || sit === "Sorti"){
      return `<span style="background:#fee2e2;color:#991b1b;padding:3px 8px;border-radius:6px;font-weight:700;font-size:11px;display:inline-flex;align-items:center;gap:4px;">🔴 Sorti</span>`;
    }
    const s = String(sit || "Actif").trim();
    if(s === "Actif"){
      return `<span style="background:#dcfce7;color:#166534;padding:3px 8px;border-radius:6px;font-weight:700;font-size:11px;display:inline-flex;align-items:center;gap:4px;">🟢 Actif</span>`;
    } else if(s === "Non déclaré"){
      return `<span style="background:#fef3c7;color:#92400e;padding:3px 8px;border-radius:6px;font-weight:700;font-size:11px;display:inline-flex;align-items:center;gap:4px;">🟠 Non déclaré</span>`;
    }
    return `<span style="background:#f1f5f9;color:#475569;padding:3px 8px;border-radius:6px;font-weight:600;font-size:11px;">${s}</span>`;
  }

  /* ==============================================================================
     2. VUE SALARIÉS & DOSSIERS RH (Avec Date d'Entrée & Date de Sortie)
     ============================================================================== */
  function rhRenderEmployeesView(){
    const emps = rhGetRows("SE Employe");
    const search = (RH_STATE.filterSearch || "").toLowerCase();
    const filterSit = RH_STATE.filterSituation || "TOUS";

    const filtered = emps.filter(e => {
      const isEnPoste = rhIsEmployeEnPoste(e);
      const sit = !isEnPoste ? "Sorti" : (e.statut_professionnel || e.situation || "Actif");
      if(filterSit === "Actif" && !isEnPoste) return false;
      if(filterSit === "Sorti" && isEnPoste) return false;
      if(filterSit === "Non déclaré" && sit !== "Non déclaré") return false;

      const q = (e.name + " " + (e.nom_complet||"") + " " + (e.departement||"") + " " + (e.fonction||"") + " " + sit).toLowerCase();
      return q.includes(search);
    });

    let html = `
      <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:18px;">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:16px;">
          <div>
            <h3 style="margin:0;font-size:16px;color:#0f172a;">Effectif du Personnel (${emps.length} Collaborateurs)</h3>
            <div style="font-size:12px;color:#64748b;">Suivi des dates d'entrée et de sortie. Les salariés ayant une date de sortie sont exclus de la masse salariale.</div>
          </div>
          <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <!-- Filtre par Situation -->
            <select onchange="window.rhFilterSituation(this.value)" style="padding:8px 12px;border:1px solid #cbd5e1;border-radius:6px;font-size:12px;font-weight:600;background:#fff;cursor:pointer;">
              <option value="TOUS" ${filterSit === 'TOUS' ? 'selected' : ''}>Toutes situations (${emps.length})</option>
              <option value="Actif" ${filterSit === 'Actif' ? 'selected' : ''}>🟢 En poste uniquement (${emps.filter(rhIsEmployeEnPoste).length})</option>
              <option value="Sorti" ${filterSit === 'Sorti' ? 'selected' : ''}>🔴 Sortis de l'hôtel (${emps.filter(e => !rhIsEmployeEnPoste(e)).length})</option>
              <option value="Non déclaré" ${filterSit === 'Non déclaré' ? 'selected' : ''}>🟠 Non déclarés</option>
            </select>
            <input type="text" placeholder="🔍 Rechercher salarié, poste..." value="${RH_STATE.filterSearch}" oninput="window.rhSearchEmp(this.value)" style="padding:8px 12px;border:1px solid #cbd5e1;border-radius:6px;font-size:12px;width:200px;">
            ${(window.CURRENT_USER && window.CURRENT_USER.role === "Consultant") ? '' : `<button onclick="window.rhModalNouveauSalarie()" style="background:#059669;color:#fff;border:none;border-radius:6px;padding:8px 14px;font-size:12px;font-weight:700;cursor:pointer;display:flex;align-items:center;gap:4px;">
              ➕ Ajouter un Salarié
            </button>`}
          </div>
        </div>

        <div style="overflow-x:auto;">
          <table style="width:100%;font-size:12px;border-collapse:collapse;border:1px solid #e2e8f0;">
            <thead>
              <tr style="background:#f1f5f9;color:#475569;text-align:left;">
                <th style="padding:10px;">Matricule</th>
                <th style="padding:10px;">Nom & Prénom</th>
                <th style="padding:10px;">Département</th>
                <th style="padding:10px;">Fonction</th>
                <th style="padding:10px;">Contrat</th>
                <th style="padding:10px;">Date d'Entrée</th>
                <th style="padding:10px;">Date de Sortie</th>
                <th style="padding:10px;">Salaire Base</th>
                <th style="padding:10px;">Situation</th>
                <th style="padding:10px;">N° CNAS</th>
                <th style="padding:10px;text-align:right;">Actions</th>
              </tr>
            </thead>
            <tbody>
    `;

    if(filtered.length === 0){
      html += `<tr><td colspan="11" style="padding:30px;text-align:center;color:#64748b;">Aucun salarié trouvé dans cette sélection.</td></tr>`;
    } else {
      filtered.forEach(e => {
        const isEnPoste = rhIsEmployeEnPoste(e);
        const dateEntree = e.date_embauche || e.date_entree || e.date_recrutement;
        const dateSortie = e.date_sortie;
        const situation = !isEnPoste ? "Sorti" : (e.statut_professionnel || e.situation || "Actif");

        html += `
          <tr style="border-bottom:1px solid #f1f5f9;background:${!isEnPoste ? '#fff5f5' : '#ffffff'};">
            <td style="padding:10px;font-weight:700;color:${isEnPoste ? '#0284c7' : '#94a3b8'};">${e.name}</td>
            <td style="padding:10px;font-weight:700;color:#0f172a;">
              ${e.nom_complet || (e.prenom + ' ' + e.nom)}
              ${!isEnPoste ? `<span style="font-size:10px;color:#dc2626;font-weight:600;margin-left:4px;">(A quitté l'hôtel)</span>` : ''}
            </td>
            <td style="padding:10px;">${e.departement || '—'}</td>
            <td style="padding:10px;">${e.fonction || '—'}</td>
            <td style="padding:10px;"><span style="background:#e0f2fe;color:#0369a1;padding:2px 8px;border-radius:4px;font-weight:700;">${e.type_contrat || 'CDI'}</span></td>
            <td style="padding:10px;font-weight:600;color:#1e293b;">${rhFmtDate(dateEntree)}</td>
            <td style="padding:10px;font-weight:700;color:${dateSortie ? '#dc2626' : '#059669'};">
              ${dateSortie ? `🚪 ${rhFmtDate(dateSortie)}` : '<span style="color:#059669;font-weight:600;">— En poste</span>'}
            </td>
            <td style="padding:10px;font-weight:600;${!isEnPoste ? 'text-decoration:line-through;color:#94a3b8;' : ''}">
              ${rhFmtMoney(e.salaire_base_contractuel)}
            </td>
            <td style="padding:10px;">${rhRenderSituationBadge(situation, dateSortie)}</td>
            <td style="padding:10px;color:${e.n_assurance ? '#475569' : '#dc2626'};font-weight:${e.n_assurance ? '400' : '600'};">
              ${e.n_assurance || (situation === 'Non déclaré' ? 'Non déclaré' : '—')}
            </td>
            <td style="padding:10px;text-align:right;white-space:nowrap;">
              ${(window.CURRENT_USER && window.CURRENT_USER.role === "Consultant") ? '<span style="color:#94a3b8;font-size:11px;">Lecture Seule</span>' : `
              <button onclick="window.rhModalModifierEmploye('${e.name}')" style="background:#f1f5f9;border:1px solid #cbd5e1;padding:4px 8px;border-radius:4px;font-size:11px;cursor:pointer;font-weight:600;margin-right:4px;">✏️ Modifier</button>
              ${(!window.CURRENT_USER || window.CURRENT_USER.role === "Administrateur") ? `<button onclick="window.rhSupprimerEmploye('${e.name}')" style="background:#fee2e2;color:#991b1b;border:1px solid #fecaca;padding:4px 8px;border-radius:4px;font-size:11px;cursor:pointer;font-weight:600;">🗑️</button>` : ''}
              `}
            </td>
          </tr>
        `;
      });
    }

    html += `</tbody></table></div></div>`;
    return html;
  }

  window.rhSearchEmp = function(v){
    RH_STATE.filterSearch = v;
    rhRenderActiveView();
  };

  window.rhFilterSituation = function(s){
    RH_STATE.filterSituation = s;
    rhRenderActiveView();
  };

  // Suppression d'un salarié avec confirmation unifiée et contrôle d'intégrité
  window.rhSupprimerEmploye = function(empId){
    const curRole = (window.CURRENT_USER ? window.CURRENT_USER.role : "Administrateur");
    if (curRole !== "Administrateur") {
      alert("Action non autorisée : Seul un Administrateur a le droit de supprimer un collaborateur.");
      return;
    }
    if(typeof window.triggerDeleteDoc === "function"){
      window.triggerDeleteDoc("SE Employe", empId);
      return;
    }
    if(!confirm(`Êtes-vous sûr de vouloir supprimer cet élément ? Cette action peut être irréversible.\n\nSalarié : ${empId}`)){
      return;
    }
    const db = rhGetDb();
    if(db["SE Employe"]){
      db["SE Employe"] = db["SE Employe"].filter(x => x.name !== empId);
    }
    if(window.APP_STATE && window.APP_STATE.db && window.APP_STATE.db["SE Employe"]){
      window.APP_STATE.db["SE Employe"] = window.APP_STATE.db["SE Employe"].filter(x => x.name !== empId);
    }
    if(window.DB && window.DB["SE Employe"]){
      window.DB["SE Employe"] = window.DB["SE Employe"].filter(x => x.name !== empId);
    }

    if(typeof window.saveDB === "function"){
      try { window.saveDB(); } catch(e){}
    }

    if(typeof renderSidebar === "function"){
      try { renderSidebar(RH_STATE.activeTab ? "rh_" + RH_STATE.activeTab : "workspace"); } catch(e){}
    }

    rhNotify(`Salarié ${empId} supprimé.`, "info");
    rhRenderActiveView();
  };

  /* ==============================================================================
     3. VUE CENTRE DE PAIE & BULLETINS (Calcul UNIQUEMENT pour les salariés en poste)
     ============================================================================== */
  function rhRenderPayrollView(){
    const emps = rhGetRows("SE Employe");
    const enPosteEmps = emps.filter(rhIsEmployeEnPoste);
    const paies = rhGetRows("SE Fiche de Paie Mensuelle").filter(p => p.periode === RH_STATE.payrollPeriod);

    const masseBrute = paies.reduce((a, b) => a + (Number(b.salaire_brut) || 0), 0);
    const net = paies.reduce((a, b) => a + (Number(b.net_a_payer) || 0), 0);
    const cnas9 = paies.reduce((a, b) => a + (Number(b.retenue_cnas_salariale) || 0), 0);
    const cnas26 = paies.reduce((a, b) => a + (Number(b.cotisation_cnas_patronale) || (Number(b.salaire_brut)*0.26) || 0), 0);

    return `
      <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:18px;">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:16px;">
          <div>
            <h3 style="margin:0;font-size:16px;color:#0f172a;">Gestion de la Paie (${RH_STATE.payrollPeriod})</h3>
            <div style="font-size:12px;color:#64748b;">Calcul automatique sur les <strong>${enPosteEmps.length} salariés en poste</strong>. Les salariés ayant quitté l'hôtel sont exclus.</div>
          </div>
          <div style="display:flex;gap:10px;align-items:center;">
            <select onchange="window.rhChangePeriod(this.value)" style="padding:8px 12px;border:1px solid #cbd5e1;border-radius:6px;font-size:13px;font-weight:700;">
              ${(() => {
                const yr = new Date().getFullYear();
                const mNames = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"];
                return mNames.map((mn, i) => {
                  const val = `${yr}-${String(i + 1).padStart(2, "0")}`;
                  return `<option value="${val}" ${RH_STATE.payrollPeriod === val ? "selected" : ""}>${mn} ${yr}</option>`;
                }).reverse().join("");
              })()}
            </select>
            <button onclick="window.rhCalculerPaieMasse()" style="background:#059669;color:#fff;border:none;border-radius:6px;padding:8px 16px;font-size:12px;font-weight:700;cursor:pointer;">
              ⚡ Calculer la Paie (${enPosteEmps.length} Salariés en poste)
            </button>
          </div>
        </div>

        <!-- Synthèse -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(180px, 1fr));gap:12px;margin-bottom:18px;">
          <div style="background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">
            <div style="font-size:11px;color:#64748b;font-weight:700;">MASSE BRUTE DU MOIS</div>
            <div style="font-size:18px;font-weight:800;color:#0f172a;">${rhFmtMoney(masseBrute)}</div>
          </div>
          <div style="background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">
            <div style="font-size:11px;color:#64748b;font-weight:700;">NET TOTAL À PAYER</div>
            <div style="font-size:18px;font-weight:800;color:#059669;">${rhFmtMoney(net)}</div>
          </div>
          <div style="background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">
            <div style="font-size:11px;color:#64748b;font-weight:700;">CNAS SALARIALE (9%)</div>
            <div style="font-size:18px;font-weight:800;color:#dc2626;">${rhFmtMoney(cnas9)}</div>
          </div>
          <div style="background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">
            <div style="font-size:11px;color:#64748b;font-weight:700;">CNAS PATRONALE (26%)</div>
            <div style="font-size:18px;font-weight:800;color:#475569;">${rhFmtMoney(cnas26)}</div>
          </div>
        </div>

        <table style="width:100%;font-size:12px;border-collapse:collapse;border:1px solid #e2e8f0;">
          <thead>
            <tr style="background:#f1f5f9;color:#475569;text-align:left;">
              <th style="padding:10px;">Matricule</th>
              <th style="padding:10px;">Salarié</th>
              <th style="padding:10px;">Département</th>
              <th style="padding:10px;">Salaire Brut</th>
              <th style="padding:10px;">CNAS (9%)</th>
              <th style="padding:10px;">IRG</th>
              <th style="padding:10px;font-weight:800;color:#059669;">Net à Payer</th>
              <th style="padding:10px;">Bulletin</th>
            </tr>
          </thead>
          <tbody>
    `;

    if(paies.length === 0){
      html += `<tr><td colspan="8" style="padding:30px;text-align:center;color:#64748b;">Aucun bulletin calculé pour ce mois. Cliquez sur "Calculer la Paie".</td></tr>`;
    } else {
      paies.forEach(p => {
        html += `
          <tr style="border-bottom:1px solid #f1f5f9;">
            <td style="padding:10px;font-weight:700;">${p.employe}</td>
            <td style="padding:10px;font-weight:700;">${p.employe_nom}</td>
            <td style="padding:10px;">${p.departement || '—'}</td>
            <td style="padding:10px;font-weight:700;">${rhFmtMoney(p.salaire_brut)}</td>
            <td style="padding:10px;color:#dc2626;">-${rhFmtMoney(p.retenue_cnas_salariale)}</td>
            <td style="padding:10px;color:#d97706;">-${rhFmtMoney(p.retenue_irg)}</td>
            <td style="padding:10px;font-weight:800;color:#059669;">${rhFmtMoney(p.net_a_payer)}</td>
            <td style="padding:10px;">
              <button onclick="window.rhImprimerBulletin('${p.name}')" style="background:#0f172a;color:#fff;border:none;padding:5px 10px;border-radius:4px;font-size:11px;cursor:pointer;font-weight:700;">🖨️ Imprimer</button>
            </td>
          </tr>
        `;
      });
    }

    html += `</tbody></table></div>`;
    return html;
  }

  window.rhChangePeriod = function(p){
    RH_STATE.payrollPeriod = p;
    rhRenderActiveView();
  };

  window.rhCalculerPaieMasse = function(){
    const db = rhGetDb();
    if(!db["SE Fiche de Paie Mensuelle"]) db["SE Fiche de Paie Mensuelle"] = [];
    // UNIQUEMENT LES SALARIÉS EN POSTE (Ceux avec Date de Sortie sont EXCLUS)
    const emps = (db["SE Employe"] || []).filter(rhIsEmployeEnPoste);
    const per = RH_STATE.payrollPeriod;

    emps.forEach(e => {
      const base = Number(e.salaire_base_contractuel) || Number(e.salaire_base_declare) || 45000;
      const primes = 11000; // Panier 6000 + Transport 5000
      const brut = base + primes;
      const cnas9 = Math.round(brut * 0.09 * 100) / 100;
      const imposable = brut - cnas9;
      const irg = rhCalcIrg(imposable);
      const net = Math.max(0, imposable - irg);
      const cnas26 = Math.round(brut * 0.26 * 100) / 100;

      const fiche = {
        name: `PAY-${per}-${e.name.replace("EMP-", "")}`,
        periode: per,
        employe: e.name,
        employe_nom: e.nom_complet || `${e.prenom} ${e.nom}`,
        departement: e.departement || "Hébergement",
        fonction: e.fonction || "Poste",
        salaire_base: base,
        total_primes: primes,
        salaire_brut: brut,
        retenue_cnas_salariale: cnas9,
        salaire_imposable: imposable,
        retenue_irg: irg,
        net_a_payer: net,
        cotisation_cnas_patronale: cnas26,
        cout_total_employeur: brut + cnas26,
        statut_paiement: "En attente de virement"
      };

      const idx = db["SE Fiche de Paie Mensuelle"].findIndex(x => x.name === fiche.name);
      if(idx >= 0) db["SE Fiche de Paie Mensuelle"][idx] = fiche;
      else db["SE Fiche de Paie Mensuelle"].push(fiche);
    });

    rhNotify(`⚡ Calcul terminé : ${emps.length} bulletins calculés pour ${per} (salariés sortis exclus)`, "success");
    rhRenderActiveView();
  };

  /* ==============================================================================
     4. VUE CNAS & CONGÉS
     ============================================================================== */
  function rhRenderCnasView(){
    const emps = rhGetRows("SE Employe").filter(rhIsEmployeEnPoste);
    const declarations = rhGetRows("SE Declaration CNAS");

    return `
      <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:18px;">
        <h3 style="margin:0 0 4px 0;font-size:16px;color:#0f172a;">Sécurité Sociale (CNAS) & Droits à Congés</h3>
        <div style="font-size:12px;color:#64748b;margin-bottom:16px;">Déclarations réglementaires et soldes de congés des salariés en activité.</div>

        <!-- Déclarations CNAS -->
        <div style="margin-bottom:24px;">
          <div style="font-size:13px;font-weight:800;color:#0f172a;margin-bottom:8px;">Bordereaux de Cotisation CNAS (35%)</div>
          <table style="width:100%;font-size:12px;border-collapse:collapse;border:1px solid #e2e8f0;">
            <thead>
              <tr style="background:#f1f5f9;color:#475569;text-align:left;">
                <th style="padding:8px;">Période</th>
                <th style="padding:8px;">Assiette Globale</th>
                <th style="padding:8px;">Part Ouvrière (9%)</th>
                <th style="padding:8px;">Part Patronale (26%)</th>
                <th style="padding:8px;font-weight:800;">Total à Verser (35%)</th>
                <th style="padding:8px;">Statut</th>
              </tr>
            </thead>
            <tbody>
              ${declarations.map(c => `
                <tr style="border-bottom:1px solid #f1f5f9;">
                  <td style="padding:8px;font-weight:700;">${c.periode}</td>
                  <td style="padding:8px;">${rhFmtMoney(c.assiette_globale)}</td>
                  <td style="padding:8px;">${rhFmtMoney(c.cotisation_salariale_9)}</td>
                  <td style="padding:8px;">${rhFmtMoney(c.cotisation_patronale_26)}</td>
                  <td style="padding:8px;font-weight:800;color:#0f172a;">${rhFmtMoney(c.montant_total_a_payer)}</td>
                  <td style="padding:8px;"><span style="background:#dcfce7;color:#166534;padding:2px 8px;border-radius:4px;font-weight:700;">${c.statut}</span></td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>

        <!-- Soldes Congés -->
        <div>
          <div style="font-size:13px;font-weight:800;color:#0f172a;margin-bottom:8px;">Soldes de Congés par Salarié (En activité)</div>
          <table style="width:100%;font-size:12px;border-collapse:collapse;border:1px solid #e2e8f0;">
            <thead>
              <tr style="background:#f1f5f9;color:#475569;text-align:left;">
                <th style="padding:8px;">Salarié</th>
                <th style="padding:8px;">Département</th>
                <th style="padding:8px;">Droits Acquis</th>
                <th style="padding:8px;">Congés Pris</th>
                <th style="padding:8px;font-weight:800;color:#0284c7;">Solde Restant</th>
              </tr>
            </thead>
            <tbody>
              ${emps.slice(0, 10).map(e => `
                <tr style="border-bottom:1px solid #f1f5f9;">
                  <td style="padding:8px;font-weight:700;">${e.nom_complet || (e.prenom + ' ' + e.nom)}</td>
                  <td style="padding:8px;">${e.departement || '—'}</td>
                  <td style="padding:8px;">${e.solde_conges_acquis || 30} jours</td>
                  <td style="padding:8px;">${e.solde_conges_pris || 0} jours</td>
                  <td style="padding:8px;font-weight:800;color:#0284c7;">${e.solde_conges_restant || 30} jours</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  /* ==============================================================================
     MODAL NOUVEAU SALARIÉ (Date d'Entrée & Date de Sortie)
     ============================================================================== */
  window.rhModalNouveauSalarie = function(){
    const curRole = (window.CURRENT_USER ? window.CURRENT_USER.role : "Administrateur");
    if (curRole === "Consultant") {
      alert("Action non autorisée : Le profil Consultant est en lecture seule.");
      return;
    }
    const modalId = "rh-modal-nouveau";
    let modal = document.getElementById(modalId);
    if(!modal){
      modal = document.createElement("div");
      modal.id = modalId;
      modal.style.cssText = "position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(15,23,42,0.7);z-index:999999;display:flex;align-items:center;justify-content:center;padding:20px;box-sizing:border-box;";
      document.body.appendChild(modal);
    }
    modal.style.display = "flex";

    const emps = rhGetRows("SE Employe");
    let maxId = 0;
    emps.forEach(e => {
      const m = String(e.name || "").match(/(\d+)$/);
      if(m) maxId = Math.max(maxId, parseInt(m[1], 10));
    });
    const nextMatricule = `EMP-${new Date().getFullYear()}-${String(maxId + 1).padStart(4, "0")}`;
    const todayStr = rhTodayDate();

    modal.innerHTML = `
      <div style="background:#fff;border-radius:12px;width:100%;max-width:620px;max-height:90vh;overflow-y:auto;padding:24px;box-shadow:0 20px 40px rgba(0,0,0,0.3);">
        <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #e2e8f0;padding-bottom:12px;margin-bottom:16px;">
          <div>
            <h3 style="margin:0;font-size:18px;color:#0f172a;">➕ Nouveau Salarié Hôtel</h3>
            <div style="font-size:12px;color:#64748b;">Matricule attribué : <strong style="color:#0284c7;">${nextMatricule}</strong></div>
          </div>
          <button onclick="document.getElementById('${modalId}').style.display='none'" style="background:none;border:none;font-size:20px;cursor:pointer;">✕</button>
        </div>
        <form id="form-simple-emp" onsubmit="window.rhSubmitNouveauSalarie(event, '${nextMatricule}')" style="display:grid;grid-template-columns:1fr 1fr;gap:12px;font-size:12px;">
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;">Nom de famille :</label>
            <input name="nom" required placeholder="Ex: Benali" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
          </div>
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;">Prénom :</label>
            <input name="prenom" required placeholder="Ex: Sami" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
          </div>

          <!-- DATE D'ENTRÉE -->
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;color:#059669;">📅 Date d'Entrée (Embauche) * :</label>
            <input name="date_embauche" type="date" required value="${todayStr}" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #059669;border-radius:6px;font-weight:600;">
          </div>

          <!-- DATE DE SORTIE (OPTIONNELLE) -->
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;color:#dc2626;">🚪 Date de Sortie (si départ) :</label>
            <input name="date_sortie" id="input_new_date_sortie" type="date" onchange="window.rhOnDateSortieChange(this.value, 'select_new_situation')" placeholder="Laisser vide si en poste" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #dc2626;border-radius:6px;">
            <div style="font-size:10px;color:#64748b;margin-top:2px;">* Renseigner cette date retire automatiquement l'employé de la masse salariale.</div>
          </div>

          <!-- SITUATION -->
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;color:#0284c7;">🏷️ Situation du Salarié :</label>
            <select name="statut_professionnel" id="select_new_situation" required style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #0284c7;border-radius:6px;font-weight:700;">
              <option value="Actif" selected>🟢 Actif (En poste)</option>
              <option value="Sorti">🔴 Sorti (A quitté l'hôtel - Exclu paie)</option>
              <option value="Non déclaré">🟠 Non déclaré (En attente CNAS)</option>
            </select>
          </div>

          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;">Département :</label>
            <select name="departement" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
              <option value="Hébergement">Hébergement</option>
              <option value="Restauration">Restauration</option>
              <option value="Administration & DAF">Administration & DAF</option>
              <option value="Technique & Sécurité">Technique & Sécurité</option>
              <option value="Commercial & Réception">Commercial & Réception</option>
            </select>
          </div>
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;">Fonction / Poste :</label>
            <input name="fonction" required placeholder="Ex: Réceptionniste" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
          </div>
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;">Type de Contrat :</label>
            <select name="type_contrat" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
              <option value="CDI">CDI (Indéterminé)</option>
              <option value="CDD">CDD (Déterminé)</option>
              <option value="Saisonnier">Saisonnier</option>
              <option value="Stage">Stage</option>
            </select>
          </div>
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;">Salaire Contractuel (DZD) :</label>
            <input name="salaire_base_contractuel" type="number" required value="50000" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
          </div>
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;">Numéro CNAS (si déclaré) :</label>
            <input name="n_assurance" placeholder="12 chiffres" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
          </div>
          <div style="grid-column:1/-1;">
            <label style="font-weight:700;display:block;margin-bottom:4px;">NIN (Identifiant National) :</label>
            <input name="nin" placeholder="18 chiffres" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
          </div>
          <div style="grid-column:1/-1;text-align:right;margin-top:14px;border-top:1px solid #e2e8f0;padding-top:14px;">
            <button type="button" onclick="document.getElementById('${modalId}').style.display='none'" style="background:#f1f5f9;color:#334155;border:1px solid #cbd5e1;border-radius:6px;padding:8px 16px;cursor:pointer;margin-right:8px;">Annuler</button>
            <button type="submit" style="background:#059669;color:#fff;border:none;border-radius:6px;padding:8px 22px;font-weight:700;cursor:pointer;font-size:13px;">💾 Enregistrer Salarié</button>
          </div>
        </form>
      </div>
    `;
  };

  // Synchronisation dynamique : Si date de sortie entrée, passer la situation en Sorti
  window.rhOnDateSortieChange = function(dateVal, selectId){
    const sel = document.getElementById(selectId);
    if(sel){
      if(dateVal && dateVal.trim() !== ""){
        sel.value = "Sorti";
      } else {
        if(sel.value === "Sorti") sel.value = "Actif";
      }
    }
  };

  window.rhSubmitNouveauSalarie = async function(e, matricule){
    e.preventDefault();
    const fd = new FormData(e.target);
    const nom = (fd.get("nom") || "").trim();
    const prenom = (fd.get("prenom") || "").trim();
    const salaire = Number(fd.get("salaire_base_contractuel")) || 50000;
    const dateEntree = fd.get("date_embauche") || rhTodayDate();
    const dateSortie = (fd.get("date_sortie") || "").trim();

    // Règle automatique : si date_sortie est présente => Situation = Sorti
    let situation = fd.get("statut_professionnel") || "Actif";
    if(dateSortie !== ""){
      situation = "Sorti";
    }

    const newEmp = {
      name: matricule,
      nom: nom,
      prenom: prenom,
      nom_complet: `${prenom} ${nom}`,
      departement: fd.get("departement"),
      fonction: fd.get("fonction"),
      type_contrat: fd.get("type_contrat") || "CDI",
      date_embauche: dateEntree,
      date_entree: dateEntree,
      date_recrutement: dateEntree,
      date_sortie: dateSortie,
      statut_professionnel: situation,
      situation: situation,
      salaire_base_contractuel: salaire,
      salaire_base_declare: situation === "Non déclaré" ? 0 : salaire,
      n_assurance: situation === "Non déclaré" ? "" : (fd.get("n_assurance") || ""),
      nin: fd.get("nin") || "",
      solde_conges_acquis: 30,
      solde_conges_pris: 0,
      solde_conges_restant: 30
    };

    document.getElementById("rh-modal-nouveau").style.display = "none";
    await rhSaveDoc("SE Employe", newEmp, true);
    RH_STATE.activeTab = "employees";
    rhRenderActiveView();
  };

  // Modification complète de la fiche salarié
  window.rhModalModifierEmploye = function(empId){
    const emps = rhGetRows("SE Employe");
    const e = emps.find(x => x.name === empId);
    if(!e) return;

    const modalId = "rh-modal-nouveau";
    let modal = document.getElementById(modalId);
    if(!modal){
      modal = document.createElement("div");
      modal.id = modalId;
      modal.style.cssText = "position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(15,23,42,0.7);z-index:999999;display:flex;align-items:center;justify-content:center;padding:20px;box-sizing:border-box;";
      document.body.appendChild(modal);
    }
    modal.style.display = "flex";

    const dateEntree = e.date_embauche || e.date_entree || e.date_recrutement || rhTodayDate();
    const dateSortie = e.date_sortie || "";
    const isEnPoste = rhIsEmployeEnPoste(e);
    const situation = !isEnPoste ? "Sorti" : (e.statut_professionnel || e.situation || "Actif");

    modal.innerHTML = `
      <div style="background:#fff;border-radius:12px;width:100%;max-width:620px;max-height:90vh;overflow-y:auto;padding:24px;">
        <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #e2e8f0;padding-bottom:12px;margin-bottom:16px;">
          <div>
            <h3 style="margin:0;font-size:18px;color:#0f172a;">✏️ Fiche Salarié — ${e.name}</h3>
            <div style="font-size:12px;color:#64748b;">Mise à jour des dates d'entrée et de sortie</div>
          </div>
          <button onclick="document.getElementById('${modalId}').style.display='none'" style="background:none;border:none;font-size:20px;cursor:pointer;">✕</button>
        </div>
        <form onsubmit="window.rhSaveModifEmp(event, '${e.name}')" style="display:grid;grid-template-columns:1fr 1fr;gap:12px;font-size:12px;">
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;">Nom Complet :</label>
            <input name="nom_complet" value="${e.nom_complet || (e.prenom + ' ' + e.nom)}" required style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
          </div>
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;">Fonction :</label>
            <input name="fonction" value="${e.fonction || ''}" required style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
          </div>

          <!-- DATE D'ENTRÉE -->
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;color:#059669;">📅 Date d'Entrée :</label>
            <input name="date_embauche" type="date" value="${dateEntree}" required style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #059669;border-radius:6px;font-weight:600;">
          </div>

          <!-- DATE DE SORTIE -->
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;color:#dc2626;">🚪 Date de Sortie (si départ) :</label>
            <input name="date_sortie" type="date" value="${dateSortie}" onchange="window.rhOnDateSortieChange(this.value, 'select_edit_situation')" placeholder="Laisser vide si en poste" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #dc2626;border-radius:6px;">
            <div style="font-size:10px;color:#64748b;margin-top:2px;">* Renseigner la date de sortie exclut l'employé de la masse salariale.</div>
          </div>

          <!-- SITUATION -->
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;color:#0284c7;">🏷️ Situation :</label>
            <select name="statut_professionnel" id="select_edit_situation" required style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #0284c7;border-radius:6px;font-weight:700;">
              <option value="Actif" ${situation === 'Actif' ? 'selected' : ''}>🟢 Actif (En poste)</option>
              <option value="Sorti" ${situation === 'Sorti' ? 'selected' : ''}>🔴 Sorti (A quitté l'hôtel - Exclu paie)</option>
              <option value="Non déclaré" ${situation === 'Non déclaré' ? 'selected' : ''}>🟠 Non déclaré</option>
            </select>
          </div>

          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;">Département :</label>
            <select name="departement" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
              <option value="Hébergement" ${e.departement === 'Hébergement' ? 'selected' : ''}>Hébergement</option>
              <option value="Restauration" ${e.departement === 'Restauration' ? 'selected' : ''}>Restauration</option>
              <option value="Administration & DAF" ${e.departement === 'Administration & DAF' ? 'selected' : ''}>Administration & DAF</option>
              <option value="Technique & Sécurité" ${e.departement === 'Technique & Sécurité' ? 'selected' : ''}>Technique & Sécurité</option>
              <option value="Commercial & Réception" ${e.departement === 'Commercial & Réception' ? 'selected' : ''}>Commercial & Réception</option>
            </select>
          </div>
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;">Type de Contrat :</label>
            <select name="type_contrat" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
              <option value="CDI" ${e.type_contrat === 'CDI' ? 'selected' : ''}>CDI</option>
              <option value="CDD" ${e.type_contrat === 'CDD' ? 'selected' : ''}>CDD</option>
              <option value="Saisonnier" ${e.type_contrat === 'Saisonnier' ? 'selected' : ''}>Saisonnier</option>
              <option value="Stage" ${e.type_contrat === 'Stage' ? 'selected' : ''}>Stage</option>
            </select>
          </div>
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;">Salaire de Base (DZD) :</label>
            <input name="salaire_base_contractuel" type="number" value="${e.salaire_base_contractuel || 45000}" required style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
          </div>
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;">N° CNAS :</label>
            <input name="n_assurance" value="${e.n_assurance || ''}" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
          </div>
          <div style="grid-column:1/-1;">
            <label style="font-weight:700;display:block;margin-bottom:4px;">NIN (Identifiant National) :</label>
            <input name="nin" value="${e.nin || ''}" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
          </div>
          <div style="grid-column:1/-1;text-align:right;margin-top:14px;border-top:1px solid #e2e8f0;padding-top:14px;">
            <button type="button" onclick="document.getElementById('${modalId}').style.display='none'" style="background:#f1f5f9;color:#334155;border:1px solid #cbd5e1;border-radius:6px;padding:8px 16px;cursor:pointer;margin-right:8px;">Annuler</button>
            <button type="submit" style="background:#0284c7;color:#fff;border:none;border-radius:6px;padding:8px 22px;font-weight:700;cursor:pointer;">💾 Mettre à jour</button>
          </div>
        </form>
      </div>
    `;
  };

  window.rhSaveModifEmp = async function(e, empId){
    e.preventDefault();
    const fd = new FormData(e.target);
    const emps = rhGetRows("SE Employe");
    const emp = emps.find(x => x.name === empId);
    if(emp){
      emp.nom_complet = fd.get("nom_complet");
      emp.fonction = fd.get("fonction");
      emp.departement = fd.get("departement");
      emp.type_contrat = fd.get("type_contrat") || emp.type_contrat;
      emp.date_embauche = fd.get("date_embauche") || emp.date_embauche;
      emp.date_entree = emp.date_embauche;
      emp.date_recrutement = emp.date_embauche;
      emp.date_sortie = (fd.get("date_sortie") || "").trim();

      // Règle automatique : si date_sortie renseignée => Situation = Sorti
      let situation = fd.get("statut_professionnel");
      if(emp.date_sortie !== ""){
        situation = "Sorti";
      }
      emp.statut_professionnel = situation;
      emp.situation = situation;

      emp.salaire_base_contractuel = Number(fd.get("salaire_base_contractuel")) || emp.salaire_base_contractuel;
      emp.n_assurance = emp.statut_professionnel === "Non déclaré" ? "" : (fd.get("n_assurance") || "");
      emp.nin = fd.get("nin") || "";
      document.getElementById("rh-modal-nouveau").style.display = "none";
      await rhSaveDoc("SE Employe", emp, false);
    }
  };

  // Impression individuelle du bulletin de paie format officiel 4★
  window.rhImprimerBulletin = function(bullId){
    const paies = rhGetRows("SE Fiche de Paie Mensuelle");
    const b = paies.find(x => x.name === bullId);
    if(!b){
      rhNotify("Bulletin introuvable", "error");
      return;
    }
    const win = window.open("", "_blank");
    win.document.write(`
      <!DOCTYPE html>
      <html>
      <head>
        <title>Bulletin de Paie — ${b.employe_nom} (${b.periode})</title>
        <style>
          body { font-family: 'Segoe UI', Tahoma, sans-serif; margin: 40px; color: #0f172a; font-size: 12px; }
          .header { border-bottom: 2px solid #0f172a; padding-bottom: 12px; margin-bottom: 20px; display: flex; justify-content: space-between; }
          .title { font-size: 18px; font-weight: 800; text-transform: uppercase; }
          table { width: 100%; border-collapse: collapse; margin-top: 15px; }
          th, td { border: 1px solid #cbd5e1; padding: 6px 8px; text-align: left; }
          th { background: #f1f5f9; }
          .net-box { background: #f8fafc; border: 2px solid #0f172a; padding: 12px; margin-top: 20px; text-align: right; font-size: 16px; font-weight: 800; }
          .footer { margin-top: 40px; display: flex; justify-content: space-between; }
          .sig-box { width: 200px; height: 80px; border: 1px dashed #94a3b8; padding: 6px; font-size: 11px; text-align: center; }
        </style>
      </head>
      <body>
        <div class="header">
          <div style="display:flex;align-items:center;gap:14px;">
            <img src="data:image/png;base64,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" alt="Logo Hôtel Saint Eugène" style="max-height:56px;width:auto;object-fit:contain;">
            <div>
              <div style="font-weight: 800; font-size: 16px;">HOTEL SAINT EUGENE <span style="font-size:12px;color:#d97706;">★★★★</span></div>
              <div style="font-size:11.5px;color:#475569;">04, Boulevard Omar LOUNAS, Bab El Oued, Alger</div>
              <div style="font-size:11px;color:#64748b;">SARL au capital de 70 000 000 DA • NIF : 001416099002973 • RC : 16/00-0990029B14 • NIS : 001416170291741 • AI : 16175066192</div>
            </div>
          </div>
          <div style="text-align: right;">
            <div class="title">BULLETIN DE PAIE</div>
            <div>Période : <strong>${b.periode}</strong></div>
            <div>Matricule Bulletin : <strong>${b.name}</strong></div>
          </div>
        </div>

        <div style="background: #f8fafc; border: 1px solid #e2e8f0; padding: 12px; border-radius: 6px; margin-bottom: 15px;">
          <div>Salarié : <strong>${b.employe_nom}</strong> (Matricule: ${b.employe})</div>
          <div>Fonction : <strong>${b.fonction || '—'}</strong> • Département : <strong>${b.departement || '—'}</strong></div>
        </div>

        <table>
          <thead>
            <tr>
              <th>Rubrique de Paie</th>
              <th>Base (DZD)</th>
              <th>Taux</th>
              <th>Gains (DZD)</th>
              <th>Retenues (DZD)</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>Salaire de Base</td><td>${b.salaire_base?.toLocaleString()}</td><td>—</td><td>${b.salaire_base?.toLocaleString()}</td><td>—</td></tr>
            <tr><td>Primes Forfaitaires (Panier & Transport)</td><td>—</td><td>Forfait</td><td>${b.total_primes?.toLocaleString() || '11,000.00'}</td><td>—</td></tr>
            <tr style="font-weight: 700; background: #f8fafc;">
              <td colspan="3">SALAIRE BRUT TOTAL</td>
              <td>${b.salaire_brut?.toLocaleString()} DZD</td>
              <td>—</td>
            </tr>
            <tr><td>Cotisation CNAS Salariale</td><td>${b.salaire_brut?.toLocaleString()}</td><td>9.00%</td><td>—</td><td>${b.retenue_cnas_salariale?.toLocaleString()}</td></tr>
            <tr><td>Retenue IRG (Barème Algérien)</td><td>${b.salaire_imposable?.toLocaleString()}</td><td>Barème</td><td>—</td><td>${b.retenue_irg?.toLocaleString()}</td></tr>
          </tbody>
        </table>

        <div class="net-box">
          NET À PAYER : ${b.net_a_payer?.toLocaleString()} DZD
        </div>

        <div class="footer">
          <div class="sig-box">
            Signature et Cachet Employeur<br><br>
            <em>Direction RH</em>
          </div>
          <div class="sig-box">
            Émargement Salarié<br>
            <em>Pour acquit</em>
          </div>
        </div>
      </body>
      </html>
    `);
    win.document.close();
    win.focus();
    setTimeout(() => win.print(), 500);
  };

  /* ==============================================================================
     DISPATCHEUR CENTRAL DES VUES DU MODULE RH
     ============================================================================== */
  function rhRenderActiveView(){
    const root = document.getElementById("rh-module-root");
    if(!root) return;

    let content = "";
    content += rhRenderHeader();

    const t = RH_STATE.activeTab;
    if(t === "dashboard") content += rhRenderDashboardView();
    else if(t === "employees") content += rhRenderEmployeesView();
    else if(t === "payroll") content += rhRenderPayrollView();
    else if(t === "cnas") content += rhRenderCnasView();
    else content += rhRenderDashboardView();

    root.innerHTML = content;
  }

  // Point d'entrée principal pour intégration dans l'interface ERP
  window.showRhModule = function(tabName="dashboard"){
    RH_STATE.activeTab = tabName;
    const target = document.getElementById("mainContent") || document.getElementById("content") || document.body;
    target.innerHTML = `<div id="rh-module-root" style="padding:16px;box-sizing:border-box;"></div>`;

    const viewTitle = document.getElementById("viewTitle");
    if(viewTitle){
      viewTitle.innerHTML = `<span>👥 RH & Paie 4★ — Hôtel Saint Eugène</span>`;
    }

    if(typeof renderSidebar === "function"){
      renderSidebar("rh_" + tabName);
    }

    rhRenderActiveView();
  };

})();
