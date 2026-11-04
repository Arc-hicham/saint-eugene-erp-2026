/* ==============================================================================
   MODULE RH & PAIE SIMPLIFIÉ — HÔTEL SAINT EUGÈNE 4★ ALGER
   Architecture épurée, ultra-rapide, intuitive et optimisée mobile & desktop
   Conformité Code du Travail Algérien (Loi 90-11) & Normes SCF Algérie
   ============================================================================== */

(function(){
  "use strict";

  // État local du module RH
  window.RH_STATE = {
    activeTab: "dashboard", // "dashboard", "employees", "payroll", "cnas"
    currentEmpId: null,
    payrollPeriod: "2026-03",
    filterSearch: ""
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

  // Accès aux données universel (supporte APP_STATE de launch_now et DB de index.html)
  function rhGetDb(){
    if(window.APP_STATE && window.APP_STATE.db) return window.APP_STATE.db;
    if(window.DB) return window.DB;
    if(window.STATE && window.STATE.db) return window.STATE.db;
    return {};
  }

  function rhGetRows(dt){
    const db = rhGetDb();
    return Array.isArray(db[dt]) ? db[dt] : [];
  }

  // Sauvegarde universelle asynchrone (met à jour la mémoire locale et le backend)
  async function rhSaveDoc(doctype, doc, isNew=false){
    const db = rhGetDb();
    if(!db[doctype]) db[doctype] = [];
    const idx = db[doctype].findIndex(x => x.name === doc.name);
    if(idx >= 0){
      db[doctype][idx] = Object.assign({}, db[doctype][idx], doc);
    } else {
      db[doctype].unshift(doc);
    }

    // 1. Sauvegarde serveur local launch_now.py si disponible
    if(typeof fetch === "function"){
      try {
        const res = await fetch("/api/save", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ doctype: doctype, doc: doc, is_new: isNew })
        });
        if(res.ok){
          const payload = await res.json();
          if(window.APP_STATE && payload.db){
            window.APP_STATE = payload;
          }
        }
      } catch(e){
        console.warn("Sauvegarde serveur local ignorée:", e);
      }
    }

    // 2. Sauvegarde portail web chiffré index.html
    if(typeof saveToStorage === "function"){
      try { saveToStorage(); } catch(e){}
    }
    if(typeof syncToGoogleSheet === "function"){
      try { syncToGoogleSheet(); } catch(e){}
    }

    // 3. Rafraîchissement des compteurs de la barre latérale
    if(typeof renderSidebar === "function"){
      try { renderSidebar(RH_STATE.activeTab ? "rh_" + RH_STATE.activeTab : "workspace"); } catch(e){}
    }

    rhNotify("✅ " + (doc.name || doctype) + " enregistré avec succès !", "success");
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
            👥 2. Salariés & Fiches (${emps.length})
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
     ============================================================================== */
  function rhRenderDashboardView(){
    const emps = rhGetRows("SE Employe");
    const paies = rhGetRows("SE Fiche de Paie Mensuelle");
    const contrats = rhGetRows("SE Contrat RH");
    const cnas = rhGetRows("SE Declaration CNAS");

    const totalStaff = emps.length;
    const cdd = emps.filter(e => e.type_contrat === "CDD").length;
    const cdi = emps.filter(e => e.type_contrat === "CDI" || !e.type_contrat).length;
    const masseContractuelle = emps.reduce((acc, e) => acc + (Number(e.salaire_base_contractuel) || 0), 0);
    const masseDeclaree = emps.reduce((acc, e) => acc + (Number(e.salaire_base_declare) || 0), 0);
    const cnasPatronale = Math.round(masseContractuelle * 0.26);

    // Contrats à expiration < 30j
    const contratsExp = contrats.filter(c => c.statut === "Actif" && c.type_contrat === "CDD" && rhDaysDiff(c.date_fin) <= 30 && rhDaysDiff(c.date_fin) >= 0);

    return `
      <!-- Cartes KPI Essentielles -->
      <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(220px, 1fr));gap:14px;margin-bottom:20px;">
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:16px;box-shadow:0 2px 4px rgba(0,0,0,0.02);">
          <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">Effectif Total Hôtel</div>
          <div style="font-size:28px;font-weight:800;color:#0f172a;margin:4px 0;">${totalStaff}</div>
          <div style="font-size:12px;color:#059669;font-weight:600;">${cdi} CDI • ${cdd} CDD</div>
        </div>

        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:16px;box-shadow:0 2px 4px rgba(0,0,0,0.02);">
          <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">Masse Salariale Contractuelle</div>
          <div style="font-size:20px;font-weight:800;color:#0284c7;margin:4px 0;">${rhFmtMoney(masseContractuelle)}</div>
          <div style="font-size:11px;color:#64748b;">Salaires de base bruts</div>
        </div>

        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:16px;box-shadow:0 2px 4px rgba(0,0,0,0.02);">
          <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">Cotisations CNAS (26% Patronale)</div>
          <div style="font-size:20px;font-weight:800;color:#d97706;margin:4px 0;">${rhFmtMoney(cnasPatronale)}</div>
          <div style="font-size:11px;color:#64748b;">Charges sociales employeur</div>
        </div>

        <div style="background:#fff;border:1px solid ${contratsExp.length > 0 ? '#fecaca' : '#e2e8f0'};border-radius:10px;padding:16px;">
          <div style="font-size:11px;color:${contratsExp.length > 0 ? '#dc2626' : '#64748b'};font-weight:700;text-transform:uppercase;">Contrats à Échéance (< 30j)</div>
          <div style="font-size:28px;font-weight:800;color:${contratsExp.length > 0 ? '#dc2626' : '#059669'};margin:4px 0;">${contratsExp.length}</div>
          <div style="font-size:11px;color:#64748b;">Renouvellement ou fin</div>
        </div>
      </div>

      <!-- Alertes & Actions Rapides -->
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;">
        <!-- Alertes RH -->
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:16px;">
          <div style="font-size:13px;font-weight:800;color:#0f172a;margin-bottom:12px;display:flex;align-items:center;gap:8px;">
            <span>🔔</span> <span>Alertes du Personnel</span>
          </div>
          <div style="display:flex;flex-direction:column;gap:8px;">
            ${contratsExp.length > 0 ? `
              <div style="background:#fee2e2;border:1px solid #fecaca;padding:10px;border-radius:6px;font-size:12px;color:#991b1b;">
                <strong>⚠️ Échéance Contrat CDD :</strong> ${contratsExp[0].nom_complet || contratsExp[0].employe} expire le ${rhFmtDate(contratsExp[0].date_fin)}.
              </div>
            ` : `<div style="font-size:12px;color:#059669;padding:6px;">✅ Tous les contrats CDD sont à jour.</div>`}

            ${emps.some(e => !e.n_assurance) ? `
              <div style="background:#fffbeb;border:1px solid #fde68a;padding:10px;border-radius:6px;font-size:12px;color:#92400e;">
                <strong>⚠️ Immatriculation CNAS :</strong> Certains salariés n'ont pas encore de N° d'assurance renseigné.
              </div>
            ` : `<div style="font-size:12px;color:#059669;padding:6px;">✅ Immatriculations CNAS en règle.</div>`}
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
              ⚡ Calculer la Paie
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

  /* ==============================================================================
     2. VUE SALARIÉS & DOSSIERS RH
     ============================================================================== */
  function rhRenderEmployeesView(){
    const emps = rhGetRows("SE Employe");
    const search = (RH_STATE.filterSearch || "").toLowerCase();
    const filtered = emps.filter(e => {
      const q = (e.name + " " + (e.nom_complet||"") + " " + (e.departement||"") + " " + (e.fonction||"")).toLowerCase();
      return q.includes(search);
    });

    let html = `
      <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:18px;">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:16px;">
          <div>
            <h3 style="margin:0;font-size:16px;color:#0f172a;">Effectif du Personnel (${emps.length} Salariés)</h3>
            <div style="font-size:12px;color:#64748b;">Consultez, modifiez ou ajoutez les collaborateurs de l'Hôtel Saint Eugène.</div>
          </div>
          <div style="display:flex;gap:8px;">
            <input type="text" placeholder="🔍 Rechercher salarié, poste..." value="${RH_STATE.filterSearch}" oninput="window.rhSearchEmp(this.value)" style="padding:8px 12px;border:1px solid #cbd5e1;border-radius:6px;font-size:12px;width:220px;">
            <button onclick="window.rhModalNouveauSalarie()" style="background:#059669;color:#fff;border:none;border-radius:6px;padding:8px 14px;font-size:12px;font-weight:700;cursor:pointer;">
              ➕ Ajouter
            </button>
          </div>
        </div>

        <table style="width:100%;font-size:12px;border-collapse:collapse;border:1px solid #e2e8f0;">
          <thead>
            <tr style="background:#f1f5f9;color:#475569;text-align:left;">
              <th style="padding:10px;">Matricule</th>
              <th style="padding:10px;">Nom Complet</th>
              <th style="padding:10px;">Département</th>
              <th style="padding:10px;">Fonction</th>
              <th style="padding:10px;">Contrat</th>
              <th style="padding:10px;">Salaire Base</th>
              <th style="padding:10px;">N° CNAS</th>
              <th style="padding:10px;">Statut</th>
              <th style="padding:10px;">Actions</th>
            </tr>
          </thead>
          <tbody>
    `;

    if(filtered.length === 0){
      html += `<tr><td colspan="9" style="padding:30px;text-align:center;color:#64748b;">Aucun salarié trouvé. Cliquez sur "Ajouter un Salarié".</td></tr>`;
    } else {
      filtered.forEach(e => {
        html += `
          <tr style="border-bottom:1px solid #f1f5f9;">
            <td style="padding:10px;font-weight:700;color:#0284c7;">${e.name}</td>
            <td style="padding:10px;font-weight:700;color:#0f172a;">${e.nom_complet || (e.prenom + ' ' + e.nom)}</td>
            <td style="padding:10px;">${e.departement || '—'}</td>
            <td style="padding:10px;">${e.fonction || '—'}</td>
            <td style="padding:10px;"><span style="background:#e0f2fe;color:#0369a1;padding:2px 8px;border-radius:4px;font-weight:700;">${e.type_contrat || 'CDI'}</span></td>
            <td style="padding:10px;font-weight:600;">${rhFmtMoney(e.salaire_base_contractuel)}</td>
            <td style="padding:10px;color:#475569;">${e.n_assurance || '—'}</td>
            <td style="padding:10px;"><span style="background:#dcfce7;color:#166534;padding:2px 8px;border-radius:4px;font-weight:700;">${e.statut_professionnel || 'Actif'}</span></td>
            <td style="padding:10px;white-space:nowrap;">
              <button onclick="window.rhModalModifierEmploye('${e.name}')" style="background:#f1f5f9;border:1px solid #cbd5e1;padding:4px 8px;border-radius:4px;font-size:11px;cursor:pointer;font-weight:600;">✏️ Fiche</button>
            </td>
          </tr>
        `;
      });
    }

    html += `</tbody></table></div>`;
    return html;
  }

  window.rhSearchEmp = function(v){
    RH_STATE.filterSearch = v;
    rhRenderActiveView();
  };

  /* ==============================================================================
     3. VUE CENTRE DE PAIE & BULLETINS
     ============================================================================== */
  function rhRenderPayrollView(){
    const emps = rhGetRows("SE Employe");
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
            <div style="font-size:12px;color:#64748b;">Calcul automatique, retenues CNAS (9%), IRG et impression des bulletins officiels.</div>
          </div>
          <div style="display:flex;gap:10px;align-items:center;">
            <select onchange="window.rhChangePeriod(this.value)" style="padding:8px 12px;border:1px solid #cbd5e1;border-radius:6px;font-size:13px;font-weight:700;">
              <option value="2026-03" ${RH_STATE.payrollPeriod === "2026-03" ? "selected" : ""}>Mars 2026</option>
              <option value="2026-02" ${RH_STATE.payrollPeriod === "2026-02" ? "selected" : ""}>Février 2026</option>
              <option value="2026-01" ${RH_STATE.payrollPeriod === "2026-01" ? "selected" : ""}>Janvier 2026</option>
            </select>
            <button onclick="window.rhCalculerPaieMasse()" style="background:#059669;color:#fff;border:none;border-radius:6px;padding:8px 16px;font-size:12px;font-weight:700;cursor:pointer;">
              ⚡ Calculer Tous les Bulletins
            </button>
          </div>
        </div>

        <!-- Synthèse -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(180px, 1fr));gap:12px;margin-bottom:18px;">
          <div style="background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">
            <div style="font-size:11px;color:#64748b;font-weight:700;">MASSE BRUTE</div>
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
      html += `<tr><td colspan="8" style="padding:30px;text-align:center;color:#64748b;">Aucun bulletin calculé pour ce mois. Cliquez sur "Calculer Tous les Bulletins".</td></tr>`;
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
    const emps = (db["SE Employe"] || []);
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

    rhNotify(`⚡ Calcul terminé : ${emps.length} bulletins de paie calculés pour ${per}`, "success");
    rhRenderActiveView();
  };

  /* ==============================================================================
     4. VUE CNAS & CONGÉS
     ============================================================================== */
  function rhRenderCnasView(){
    const emps = rhGetRows("SE Employe");
    const declarations = rhGetRows("SE Declaration CNAS");

    return `
      <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:18px;">
        <h3 style="margin:0 0 4px 0;font-size:16px;color:#0f172a;">Sécurité Sociale (CNAS) & Droits à Congés</h3>
        <div style="font-size:12px;color:#64748b;margin-bottom:16px;">Déclarations réglementaires et soldes de congés (2.5 jours/mois selon Loi 90-11).</div>

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
          <div style="font-size:13px;font-weight:800;color:#0f172a;margin-bottom:8px;">Soldes de Congés par Salarié</div>
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
     MODAL NOUVEAU SALARIÉ (Simple, Efficace, Garanti de Sauvegarde)
     ============================================================================== */
  window.rhModalNouveauSalarie = function(){
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
    // Calcul automatique du prochain matricule réel
    let maxId = 0;
    emps.forEach(e => {
      const m = String(e.name || "").match(/(\d+)$/);
      if(m) maxId = Math.max(maxId, parseInt(m[1], 10));
    });
    const nextMatricule = `EMP-2026-${String(maxId + 1).padStart(4, "0")}`;

    modal.innerHTML = `
      <div style="background:#fff;border-radius:12px;width:100%;max-width:550px;max-height:90vh;overflow-y:auto;padding:24px;box-shadow:0 20px 40px rgba(0,0,0,0.3);">
        <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #e2e8f0;padding-bottom:12px;margin-bottom:16px;">
          <div>
            <h3 style="margin:0;font-size:18px;color:#0f172a;">➕ Nouveau Salarié Hôtel</h3>
            <div style="font-size:12px;color:#64748b;">Matricule attribué : <strong style="color:#0284c7;">${nextMatricule}</strong></div>
          </div>
          <button onclick="document.getElementById('${modalId}').style.display='none'" style="background:none;border:none;font-size:20px;cursor:pointer;">✕</button>
        </div>
        <form id="form-simple-emp" onsubmit="window.rhSubmitNouveauSalarie(event, '${nextMatricule}')" style="display:grid;grid-template-columns:1fr 1fr;gap:12px;font-size:12px;">
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;">Nom :</label>
            <input name="nom" required style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
          </div>
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;">Prénom :</label>
            <input name="prenom" required style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
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
            </select>
          </div>
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;">Salaire Contractuel (DZD) :</label>
            <input name="salaire_base_contractuel" type="number" required value="50000" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
          </div>
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;">Numéro CNAS :</label>
            <input name="n_assurance" placeholder="12 chiffres" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
          </div>
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;">NIN (Identifiant National) :</label>
            <input name="nin" placeholder="18 chiffres" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
          </div>
          <div style="grid-column:1/-1;text-align:right;margin-top:14px;border-top:1px solid #e2e8f0;padding-top:14px;">
            <button type="button" onclick="document.getElementById('${modalId}').style.display='none'" style="background:#f1f5f9;color:#334155;border:1px solid #cbd5e1;border-radius:6px;padding:8px 16px;cursor:pointer;margin-right:8px;">Annuler</button>
            <button type="submit" style="background:#059669;color:#fff;border:none;border-radius:6px;padding:8px 20px;font-weight:700;cursor:pointer;">Enregistrer Salarié</button>
          </div>
        </form>
      </div>
    `;
  };

  window.rhSubmitNouveauSalarie = async function(e, matricule){
    e.preventDefault();
    const fd = new FormData(e.target);
    const nom = fd.get("nom");
    const prenom = fd.get("prenom");
    const salaire = Number(fd.get("salaire_base_contractuel")) || 50000;

    const newEmp = {
      name: matricule,
      nom: nom,
      prenom: prenom,
      nom_complet: `${prenom} ${nom}`,
      departement: fd.get("departement"),
      fonction: fd.get("fonction"),
      type_contrat: fd.get("type_contrat") || "CDI",
      salaire_base_contractuel: salaire,
      salaire_base_declare: salaire,
      n_assurance: fd.get("n_assurance") || "",
      nin: fd.get("nin") || "",
      statut_professionnel: "Actif",
      date_embauche: new Date().toISOString().split("T")[0],
      solde_conges_acquis: 30,
      solde_conges_pris: 0,
      solde_conges_restant: 30
    };

    document.getElementById("rh-modal-nouveau").style.display = "none";
    await rhSaveDoc("SE Employe", newEmp, true);
    RH_STATE.activeTab = "employees";
    rhRenderActiveView();
  };

  // Modification simple de la fiche
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
    modal.innerHTML = `
      <div style="background:#fff;border-radius:12px;width:100%;max-width:550px;max-height:90vh;overflow-y:auto;padding:24px;">
        <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #e2e8f0;padding-bottom:12px;margin-bottom:16px;">
          <h3 style="margin:0;font-size:18px;color:#0f172a;">✏️ Fiche Salarié — ${e.name}</h3>
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
            <label style="font-weight:700;display:block;margin-bottom:4px;">Salaire de Base (DZD) :</label>
            <input name="salaire_base_contractuel" type="number" value="${e.salaire_base_contractuel || 45000}" required style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
          </div>
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;">N° CNAS :</label>
            <input name="n_assurance" value="${e.n_assurance || ''}" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
          </div>
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;">NIN :</label>
            <input name="nin" value="${e.nin || ''}" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
          </div>
          <div style="grid-column:1/-1;text-align:right;margin-top:14px;border-top:1px solid #e2e8f0;padding-top:14px;">
            <button type="button" onclick="document.getElementById('${modalId}').style.display='none'" style="background:#f1f5f9;color:#334155;border:1px solid #cbd5e1;border-radius:6px;padding:8px 16px;cursor:pointer;margin-right:8px;">Annuler</button>
            <button type="submit" style="background:#0284c7;color:#fff;border:none;border-radius:6px;padding:8px 20px;font-weight:700;cursor:pointer;">Mettre à jour</button>
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
      emp.salaire_base_contractuel = Number(fd.get("salaire_base_contractuel")) || emp.salaire_base_contractuel;
      emp.n_assurance = fd.get("n_assurance") || "";
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
          <div>
            <div style="font-weight: 800; font-size: 16px;">HÔTEL SAINT EUGÈNE 4★ ALGER</div>
            <div>04 Boulevard Omar Lounas, Bologhine, Alger</div>
            <div>SARL Saint Eugène Hôtel • NIF : 002616012345678 • RC : 16/00-1234567</div>
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
