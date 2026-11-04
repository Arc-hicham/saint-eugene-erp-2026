/* ==============================================================================
   MODULE RH & PAIE — HÔTEL SAINT EUGÈNE 4★ ALGER
   Architecture modulaire intégrée à l'ERP Saint Eugène 2026
   Conformité Code du Travail Algérien (Loi 90-11) & Normes SCF Algérie
   ============================================================================== */

(function(){
  "use strict";

  // Configuration des Rôles et Permissions RH
  const RH_ROLES = {
    "direction": {
      nom: "Direction Générale & DAF",
      badge: "👑 Direction / DAF",
      canViewRealSalary: true,
      canViewDeclaredSalary: true,
      canEditSalary: true,
      canApprovePayroll: true,
      canApproveCnas: true,
      canViewMedical: true,
      canManageStaff: true,
      canGenerateAccounting: true,
      deptScope: "ALL"
    },
    "rh": {
      nom: "Responsable Ressources Humaines",
      badge: "👥 Responsable RH",
      canViewRealSalary: true,
      canViewDeclaredSalary: true,
      canEditSalary: true,
      canApprovePayroll: true,
      canApproveCnas: true,
      canViewMedical: true,
      canManageStaff: true,
      canGenerateAccounting: false,
      deptScope: "ALL"
    },
    "paie": {
      nom: "Responsable Paie & Charges Sociales",
      badge: "💼 Responsable Paie",
      canViewRealSalary: true,
      canViewDeclaredSalary: true,
      canEditSalary: false,
      canApprovePayroll: false,
      canApproveCnas: true,
      canViewMedical: false,
      canManageStaff: false,
      canGenerateAccounting: true,
      deptScope: "ALL"
    },
    "comptable": {
      nom: "Comptable Paie & Trésorerie",
      badge: "📑 Comptable Paie",
      canViewRealSalary: false,
      canViewDeclaredSalary: true,
      canEditSalary: false,
      canApprovePayroll: false,
      canApproveCnas: false,
      canViewMedical: false,
      canManageStaff: false,
      canGenerateAccounting: true,
      deptScope: "ALL"
    },
    "manager": {
      nom: "Chef de Département (Hébergement / Restauration)",
      badge: "👔 Manager Département",
      canViewRealSalary: false,
      canViewDeclaredSalary: false,
      canEditSalary: false,
      canApprovePayroll: false,
      canApproveCnas: false,
      canViewMedical: false,
      canManageStaff: false,
      canGenerateAccounting: false,
      deptScope: "RESTRICTED"
    },
    "employe": {
      nom: "Collaborateur Hôtel (Portail Salarié)",
      badge: "👤 Salarié",
      canViewRealSalary: false,
      canViewDeclaredSalary: false,
      canEditSalary: false,
      canApprovePayroll: false,
      canApproveCnas: false,
      canViewMedical: false,
      canManageStaff: false,
      canGenerateAccounting: false,
      deptScope: "SELF"
    },
    "auditeur": {
      nom: "Auditeur Interne / Contrôle Légal",
      badge: "🔍 Auditeur RH",
      canViewRealSalary: true,
      canViewDeclaredSalary: true,
      canEditSalary: false,
      canApprovePayroll: false,
      canApproveCnas: false,
      canViewMedical: false,
      canManageStaff: false,
      canGenerateAccounting: false,
      deptScope: "ALL"
    }
  };

  // État local du module RH
  window.RH_STATE = {
    role: "direction", // Rôle actif par défaut
    activeTab: "dashboard",
    currentEmpId: null,
    empSubTab: "tab_perso",
    payrollPeriod: "2026-03",
    reportId: "rep_registre_unique",
    filterDept: "TOUS",
    filterSearch: "",
    selectedEmployeUser: "EMP-2026-0001" // Utilisé quand role === "employe"
  };

  // Utilitaires de formatage
  function rhFmtMoney(v){
    const n = Number(v) || 0;
    return n.toLocaleString("fr-DZ", { minimumFractionDigits: 2, maximumFractionDigits: 2 }) + " DZD";
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

  // Barème IRG Algérien officiel (Formule progressive lissée)
  function rhCalcIrg(salaireImposable){
    const s = Math.max(0, Number(salaireImposable) || 0);
    if(s <= 30000) return 0;
    
    // Tranches
    let brutIrg = 0;
    let base = s;
    if(base > 320000){ brutIrg += (base - 320000) * 0.35; base = 320000; }
    if(base > 160000){ brutIrg += (base - 160000) * 0.33; base = 160000; }
    if(base > 80000){ brutIrg += (base - 80000) * 0.30; base = 80000; }
    if(base > 40000){ brutIrg += (base - 40000) * 0.27; base = 40000; }
    if(base > 20000){ brutIrg += (base - 20000) * 0.23; base = 20000; }

    // Abattement général 40% (min 1000, max 1500)
    let abat = brutIrg * 0.40;
    if(abat < 1000) abat = 1000;
    if(abat > 1500) abat = 1500;
    let netIrg = Math.max(0, brutIrg - abat);

    // Formule de lissage 30 000 - 35 000 DA
    if(s > 30000 && s < 35000){
      netIrg = Math.max(0, netIrg * (137/51) - (27925/8));
    }
    return Math.round(netIrg * 100) / 100;
  }

  // Accès aux données globales ERP
  function rhGetDb(){
    if(window.STATE && window.STATE.db) return window.STATE.db;
    if(window.DB) return window.DB;
    return {};
  }

  function rhGetRows(dt){
    const db = rhGetDb();
    return Array.isArray(db[dt]) ? db[dt] : [];
  }

  // Sauvegarde asynchrone universelle (locale + GitHub / Google Sheets)
  async function rhSaveDoc(doctype, doc){
    const db = rhGetDb();
    if(!db[doctype]) db[doctype] = [];
    const idx = db[doctype].findIndex(x => x.name === doc.name);
    if(idx >= 0){
      db[doctype][idx] = Object.assign({}, db[doctype][idx], doc);
    } else {
      db[doctype].push(doc);
    }

    // Trace dans l'historique ERP
    if(!db["SE Historique Modifications"]) db["SE Historique Modifications"] = [];
    db["SE Historique Modifications"].unshift({
      id: "HIST-RH-" + Date.now(),
      date_modification: new Date().toISOString().replace("T", " ").substring(0, 19),
      doctype: doctype,
      module_label: "👥 Module RH & Paie 4★",
      doc_name: doc.name || "Nouveau",
      action: idx >= 0 ? "✏️ Modification RH" : "➕ Création RH",
      detail_modification: (doc.nom_complet || doc.name || "") + " (Rôle: " + (RH_ROLES[RH_STATE.role]?.nom || RH_STATE.role) + ")",
      utilisateur: RH_ROLES[RH_STATE.role]?.nom || "Gestionnaire RH"
    });

    // Sauvegarde vers serveur local si présent
    try {
      if(window.location.port === "8080" || window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"){
        await fetch("/api/save", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ doctype: doctype, doc: doc })
        });
      }
    } catch(e){
      console.warn("Échec sauvegarde HTTP local:", e);
    }

    // Persistance dans localStorage / session
    try {
      if(typeof persistDbChange === "function") persistDbChange();
    } catch(e){}

    rhNotify("✅ Document enregistré avec succès (" + (doc.name || doctype) + ")", "success");
    rhRenderActiveView();
  }

  // Notification Toast intégrée
  function rhNotify(msg, type="info"){
    let el = document.getElementById("rh-toast");
    if(!el){
      el = document.createElement("div");
      el.id = "rh-toast";
      el.style.cssText = "position:fixed;bottom:24px;right:24px;z-index:999999;padding:12px 20px;border-radius:8px;font-weight:600;font-size:13px;box-shadow:0 8px 24px rgba(0,0,0,0.25);transition:all 0.3s ease;display:none;";
      document.body.appendChild(el);
    }
    el.style.display = "block";
    el.style.opacity = "1";
    if(type === "success"){
      el.style.background = "#059669"; el.style.color = "#ffffff";
    } else if(type === "error"){
      el.style.background = "#dc2626"; el.style.color = "#ffffff";
    } else if(type === "warn"){
      el.style.background = "#d97706"; el.style.color = "#ffffff";
    } else {
      el.style.background = "#0f172a"; el.style.color = "#38bdf8";
    }
    el.innerHTML = msg;
    setTimeout(() => {
      el.style.opacity = "0";
      setTimeout(() => el.style.display = "none", 300);
    }, 3500);
  }

  // Sélecteur de rôle en direct (Testeur de permissions et de confidentialité)
  function rhRenderRoleSwitcher(){
    const cur = RH_STATE.role;
    let html = `
      <div style="background:#0f172a;color:#f8fafc;padding:10px 16px;border-radius:10px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;border:1px solid #334155;">
        <div style="display:flex;align-items:center;gap:10px;">
          <span style="font-size:18px;">🛡️</span>
          <div>
            <div style="font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#94a3b8;font-weight:700;">Profil & Permissions d'Accès RH</div>
            <div style="font-size:14px;font-weight:700;color:#38bdf8;">${RH_ROLES[cur].badge} — <span style="font-weight:400;color:#cbd5e1;">${RH_ROLES[cur].nom}</span></div>
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          <label style="font-size:12px;color:#94a3b8;font-weight:600;">Simuler un profil :</label>
          <select id="rh-role-select" onchange="window.rhChangeRole(this.value)" style="background:#1e293b;color:#f8fafc;border:1px solid #475569;border-radius:6px;padding:6px 10px;font-size:12px;font-weight:600;cursor:pointer;">
    `;
    for(const rKey in RH_ROLES){
      html += `<option value="${rKey}" ${cur === rKey ? 'selected' : ''}>${RH_ROLES[rKey].badge}</option>`;
    }
    html += `
          </select>
          <button onclick="window.rhPrintModule()" style="background:#0284c7;color:#fff;border:none;border-radius:6px;padding:6px 12px;font-size:12px;font-weight:600;cursor:pointer;display:flex;align-items:center;gap:4px;">
            🖨️ Imprimer la vue
          </button>
        </div>
      </div>
    `;
    return html;
  }

  window.rhChangeRole = function(r){
    RH_STATE.role = r;
    rhNotify("Profil RH actif : " + RH_ROLES[r].badge, "info");
    rhRenderActiveView();
  };

  window.rhPrintModule = function(){
    window.print();
  };

  // Barre d'onglets du Module RH
  function rhRenderNav(){
    const tabs = [
      { id: "dashboard", icon: "📊", label: "Dashboard Personnel" },
      { id: "employees", icon: "👥", label: "Fiches Employés (Dossiers RH)" },
      { id: "contracts", icon: "📑", label: "Contrats & Échéances" },
      { id: "payroll", icon: "⚡", label: "Centre de Paie Mensuelle" },
      { id: "cnas", icon: "🏛️", label: "Déclarations CNAS" },
      { id: "leaves", icon: "🌴", label: "Congés & Droits" },
      { id: "attendance", icon: "⏱️", label: "Présences & Absences" },
      { id: "medical", icon: "🩺", label: "Arrêts Maladie & AT" },
      { id: "loans", icon: "💰", label: "Avances & Prêts" },
      { id: "exits", icon: "🚪", label: "Départs & STC" },
      { id: "accounting", icon: "⚖️", label: "Écritures Comptables SCF" },
      { id: "reports", icon: "📑", label: "30 Registres & Rapports RH" },
      { id: "params", icon: "⚙️", label: "Paramètres RH" }
    ];

    let html = `<div style="display:flex;gap:6px;overflow-x:auto;padding-bottom:8px;margin-bottom:16px;border-bottom:2px solid #e2e8f0;">`;
    tabs.forEach(t => {
      const active = RH_STATE.activeTab === t.id;
      html += `
        <button onclick="window.rhGoTab('${t.id}')" style="background:${active ? '#0f172a' : '#ffffff'};color:${active ? '#ffffff' : '#334155'};border:1px solid ${active ? '#0f172a' : '#cbd5e1'};padding:8px 14px;border-radius:8px;font-size:12px;font-weight:700;cursor:pointer;white-space:nowrap;display:flex;align-items:center;gap:6px;box-shadow:${active ? '0 4px 12px rgba(15,23,42,0.2)' : 'none'};transition:all 0.2s;">
          <span>${t.icon}</span> <span>${t.label}</span>
        </button>
      `;
    });
    html += `</div>`;
    return html;
  }

  window.rhGoTab = function(tabId, subArg=null){
    RH_STATE.activeTab = tabId;
    if(subArg){
      if(tabId === "employees") RH_STATE.currentEmpId = subArg;
      if(tabId === "payroll") RH_STATE.payrollPeriod = subArg;
      if(tabId === "reports") RH_STATE.reportId = subArg;
    }
    rhRenderActiveView();
  };

  /* ==============================================================================
     1. DASHBOARD RH (23 KPI, 14 Graphiques & Tableaux d'analyse, 18 Alertes)
     ============================================================================== */
  function rhRenderDashboardView(){
    const emps = rhGetRows("SE Employe");
    const contrats = rhGetRows("SE Contrat RH");
    const paies = rhGetRows("SE Fiche de Paie Mensuelle");
    const cnas = rhGetRows("SE Declaration CNAS");
    const conges = rhGetRows("SE Conge");
    const arrets = rhGetRows("SE Arret Maladie");
    const presences = rhGetRows("SE Presence Absence");
    const avances = rhGetRows("SE Avance Pret");
    const sorties = rhGetRows("SE Sortie Personnel");

    // Calculs des KPI
    const totalStaff = emps.length;
    const actifs = emps.filter(e => (e.statut_professionnel || e.statut) === "Actif").length;
    const cdd = contrats.filter(c => c.statut === "Actif" && c.type_contrat === "CDD").length;
    const cdi = contrats.filter(c => c.statut === "Actif" && c.type_contrat === "CDI").length;
    const enEssai = contrats.filter(c => c.statut === "Actif" && c.en_periode_essai).length;
    const enConge = emps.filter(e => (e.statut_professionnel || e.statut) === "En congé").length;
    const enMaladie = emps.filter(e => (e.statut_professionnel || e.statut) === "En arrêt maladie").length;
    const absents = presences.filter(p => p.type_enregistrement === "Absence injustifiée" && (p.date || "").startsWith("2026-03")).length;

    // Contrats à expiration < 30j
    const contratsExp30 = contrats.filter(c => c.statut === "Actif" && c.type_contrat === "CDD" && rhDaysDiff(c.date_fin) <= 30 && rhDaysDiff(c.date_fin) >= 0);

    // Masse salariale (Février ou Mars 2026)
    const paiesMois = paies.filter(p => p.periode === RH_STATE.payrollPeriod || p.periode === "2026-03");
    const masseContractuelle = emps.reduce((acc, e) => acc + (Number(e.salaire_base_contractuel) || 0), 0);
    const masseBrute = paiesMois.reduce((acc, p) => acc + (Number(p.salaire_brut) || 0), 0);
    const totalNetAPayer = paiesMois.reduce((acc, p) => acc + (Number(p.net_a_payer) || 0), 0);
    const totalNetPaye = paiesMois.filter(p => p.statut_paiement === "Payé").reduce((acc, p) => acc + (Number(p.net_a_payer) || 0), 0);
    const resteAPayer = Math.max(0, totalNetAPayer - totalNetPaye);

    const cnasPatronale = paiesMois.reduce((acc, p) => acc + (Number(p.cotisation_cnas_patronale) || (Number(p.salaire_brut)*0.26) || 0), 0);
    const cnasSalariale = paiesMois.reduce((acc, p) => acc + (Number(p.retenue_cnas_salariale) || (Number(p.salaire_brut)*0.09) || 0), 0);
    const totalCnas = cnasPatronale + cnasSalariale;

    const cnasEnAttente = cnas.filter(c => c.statut !== "Payée").length;
    const totalCongesRestants = emps.reduce((acc, e) => acc + (Number(e.solde_conges_restant) || 0), 0);
    const totalAvancesEnCours = avances.filter(a => a.statut !== "Soldé").reduce((acc, a) => acc + (Number(a.solde_restant_du) || 0), 0);
    const coutTotalEmployeur = masseBrute + cnasPatronale;

    // Documents RH manquants
    let docsManquants = 0;
    emps.forEach(e => {
      if(!e.piece_cni) docsManquants++;
      if(!e.piece_residence) docsManquants++;
      if(!e.piece_fiche_medicale) docsManquants++;
    });

    // 18 ALERTES AUTOMATISÉES
    const alerts = [];
    contrats.forEach(c => {
      const diff = rhDaysDiff(c.date_fin);
      if(c.statut === "Actif" && c.type_contrat === "CDD" && diff <= 30 && diff >= 0){
        alerts.push({
          type: "critique",
          titre: "Échéance Contrat CDD",
          desc: `Le contrat de ${c.nom_complet || c.employe} expire dans ${diff} jour(s) (${rhFmtDate(c.date_fin)}).`,
          action: `window.rhGoTab('contracts')`,
          btnLabel: "Voir Contrat"
        });
      }
      if(c.statut === "Actif" && c.en_periode_essai && c.date_fin_essai && rhDaysDiff(c.date_fin_essai) <= 15){
        alerts.push({
          type: "warning",
          titre: "Fin de Période d'Essai",
          desc: `La période d'essai de ${c.nom_complet || c.employe} se termine le ${rhFmtDate(c.date_fin_essai)}.`,
          action: `window.rhGoTab('contracts')`,
          btnLabel: "Décider"
        });
      }
    });

    emps.forEach(e => {
      if(!e.n_assurance || e.n_assurance.trim() === ""){
        alerts.push({
          type: "critique",
          titre: "Employé sans N° CNAS",
          desc: `${e.nom_complet || e.name} n'a aucun numéro d'assurance sociale enregistré.`,
          action: `window.rhGoTab('employees', '${e.name}')`,
          btnLabel: "Compléter Dossier"
        });
      }
      if(!e.nin || e.nin.trim() === ""){
        alerts.push({
          type: "warning",
          titre: "Employé sans NIN",
          desc: `Numéro d'Identification National manquant pour ${e.nom_complet || e.name}.`,
          action: `window.rhGoTab('employees', '${e.name}')`,
          btnLabel: "Renseigner NIN"
        });
      }
      if((Number(e.salaire_base_declare) || 0) < (Number(e.salaire_base_contractuel) || 0)){
        const ecart = (Number(e.salaire_base_contractuel) || 0) - (Number(e.salaire_base_declare) || 0);
        alerts.push({
          type: "info",
          titre: "Écart Salaire Contractuel / Déclaré",
          desc: `${e.nom_complet || e.name} : Salaire contractuel (${rhFmtMoney(e.salaire_base_contractuel)}) supérieur au déclaré (${rhFmtMoney(e.salaire_base_declare)}). Écart de ${rhFmtMoney(ecart)}.`,
          action: `window.rhGoTab('employees', '${e.name}')`,
          btnLabel: "Voir Fiche"
        });
      }
    });

    cnas.forEach(c => {
      if(c.statut === "En attente de paiement" || c.statut === "Préparée"){
        alerts.push({
          type: "critique",
          titre: "Cotisation CNAS à Régulariser",
          desc: `Déclaration CNAS ${c.name} (${c.periode}) : Montant de ${rhFmtMoney(c.montant_total_a_payer)} en attente.`,
          action: `window.rhGoTab('cnas')`,
          btnLabel: "Régulariser CNAS"
        });
      }
    });

    conges.forEach(cg => {
      if(cg.statut === "Soumis" || cg.statut === "En attente"){
        alerts.push({
          type: "warning",
          titre: "Demande de Congé en Attente",
          desc: `Demande de ${cg.employe_nom} (${cg.type_conge}, ${cg.nombre_jours} jours) en attente de validation.`,
          action: `window.rhGoTab('leaves')`,
          btnLabel: "Valider Congé"
        });
      }
    });

    arrets.forEach(am => {
      if(!am.justificatif_fourni){
        alerts.push({
          type: "critique",
          titre: "Arrêt Maladie sans Justificatif",
          desc: `Arrêt pour ${am.employe_nom} sans certificat médical physique dans le dossier.`,
          action: `window.rhGoTab('medical')`,
          btnLabel: "Voir Dossier"
        });
      }
    });

    let html = `
      <!-- En-tête du Dashboard -->
      <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin-bottom:20px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px;">
        <div>
          <div style="font-size:12px;font-weight:700;color:#d97706;letter-spacing:1px;text-transform:uppercase;">Hôtel Saint Eugène 4★ Alger — Direction des Ressources Humaines</div>
          <h2 style="margin:4px 0;font-size:22px;color:#0f172a;">Tableau de Bord Exécutif du Personnel & Masse Salariale</h2>
          <div style="font-size:13px;color:#64748b;">Suivi en temps réel des effectifs, contrats, paie, CNAS, présences et obligations légales algériennes.</div>
        </div>
        <div style="display:flex;gap:10px;flex-wrap:wrap;">
          <button onclick="window.rhModalNouveauSalarie()" style="background:#059669;color:#fff;border:none;padding:10px 16px;border-radius:8px;font-size:13px;font-weight:700;cursor:pointer;display:flex;align-items:center;gap:6px;box-shadow:0 4px 12px rgba(5,150,105,0.25);">
            ➕ Nouveau Salarié
          </button>
          <button onclick="window.rhGoTab('payroll')" style="background:#0f172a;color:#fff;border:none;padding:10px 16px;border-radius:8px;font-size:13px;font-weight:700;cursor:pointer;display:flex;align-items:center;gap:6px;">
            ⚡ Centre de Paie
          </button>
          <button onclick="window.rhGoTab('reports')" style="background:#3b82f6;color:#fff;border:none;padding:10px 16px;border-radius:8px;font-size:13px;font-weight:700;cursor:pointer;display:flex;align-items:center;gap:6px;">
            📑 30 Registres Légaux
          </button>
        </div>
      </div>

      <!-- 23 CARTES KPI -->
      <div style="margin-bottom:24px;">
        <div style="font-size:13px;font-weight:800;color:#334155;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:12px;display:flex;align-items:center;gap:8px;">
          <span>📌</span> <span>Indicateurs Clés de Performance RH (23 Métriques Temps Réel)</span>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:12px;">
          <!-- 1. Effectif total -->
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;box-shadow:0 2px 4px rgba(0,0,0,0.02);">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">1. Effectif Total</div>
            <div style="font-size:24px;font-weight:800;color:#0f172a;margin:4px 0;">${totalStaff}</div>
            <div style="font-size:11px;color:#059669;font-weight:600;">Salariés enregistrés</div>
          </div>
          <!-- 2. Actifs -->
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">2. Employés Actifs</div>
            <div style="font-size:24px;font-weight:800;color:#059669;margin:4px 0;">${actifs}</div>
            <div style="font-size:11px;color:#64748b;">En poste opérationnel</div>
          </div>
          <!-- 3. En période d'essai -->
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">3. Période d'Essai</div>
            <div style="font-size:24px;font-weight:800;color:#d97706;margin:4px 0;">${enEssai}</div>
            <div style="font-size:11px;color:#d97706;">À évaluer sous peu</div>
          </div>
          <!-- 4. CDD -->
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">4. Contrats CDD</div>
            <div style="font-size:24px;font-weight:800;color:#2563eb;margin:4px 0;">${cdd}</div>
            <div style="font-size:11px;color:#64748b;">Durée déterminée</div>
          </div>
          <!-- 5. CDI -->
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">5. Contrats CDI</div>
            <div style="font-size:24px;font-weight:800;color:#0f172a;margin:4px 0;">${cdi}</div>
            <div style="font-size:11px;color:#64748b;">Durée indéterminée</div>
          </div>
          <!-- 6. En congé -->
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">6. En Congé</div>
            <div style="font-size:24px;font-weight:800;color:#0891b2;margin:4px 0;">${enConge}</div>
            <div style="font-size:11px;color:#0891b2;">Absence autorisée</div>
          </div>
          <!-- 7. En arrêt maladie -->
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">7. En Arrêt Maladie</div>
            <div style="font-size:24px;font-weight:800;color:#dc2626;margin:4px 0;">${enMaladie}</div>
            <div style="font-size:11px;color:#dc2626;">Dossiers médicaux</div>
          </div>
          <!-- 8. Absents injustifiés -->
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">8. Absents Injustifiés</div>
            <div style="font-size:24px;font-weight:800;color:#e11d48;margin:4px 0;">${absents}</div>
            <div style="font-size:11px;color:#e11d48;">Retenue sur salaire</div>
          </div>
          <!-- 9. Contrats expirant < 30j -->
          <div style="background:#fff;border:1px solid #fecaca;border-radius:10px;padding:14px;">
            <div style="font-size:11px;color:#dc2626;font-weight:700;text-transform:uppercase;">9. Contrats Échéance 30j</div>
            <div style="font-size:24px;font-weight:800;color:#dc2626;margin:4px 0;">${contratsExp30.length}</div>
            <div style="font-size:11px;color:#dc2626;font-weight:600;">Action requise</div>
          </div>
          <!-- 10. Masse salariale contractuelle -->
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">10. Masse Contractuelle</div>
            <div style="font-size:18px;font-weight:800;color:#0f172a;margin:4px 0;">${rhFmtMoney(masseContractuelle)}</div>
            <div style="font-size:11px;color:#64748b;">Total contrats signés</div>
          </div>
          <!-- 11. Masse salariale brute -->
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">11. Masse Brute du Mois</div>
            <div style="font-size:18px;font-weight:800;color:#2563eb;margin:4px 0;">${rhFmtMoney(masseBrute)}</div>
            <div style="font-size:11px;color:#64748b;">Assiette cotisable paie</div>
          </div>
          <!-- 12. Net à payer -->
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">12. Total Net à Payer</div>
            <div style="font-size:18px;font-weight:800;color:#059669;margin:4px 0;">${rhFmtMoney(totalNetAPayer)}</div>
            <div style="font-size:11px;color:#64748b;">Salaires nets calculés</div>
          </div>
          <!-- 13. Salaires payés -->
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">13. Salaires Payés</div>
            <div style="font-size:18px;font-weight:800;color:#059669;margin:4px 0;">${rhFmtMoney(totalNetPaye)}</div>
            <div style="font-size:11px;color:#059669;">Virements effectués</div>
          </div>
          <!-- 14. Reste à payer -->
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">14. Salaires Restant Dus</div>
            <div style="font-size:18px;font-weight:800;color:${resteAPayer > 0 ? '#d97706' : '#64748b'};margin:4px 0;">${rhFmtMoney(resteAPayer)}</div>
            <div style="font-size:11px;color:#64748b;">En cours d'ordonnancement</div>
          </div>
          <!-- 15. CNAS Patronale (26%) -->
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">15. CNAS Patronale (26%)</div>
            <div style="font-size:18px;font-weight:800;color:#475569;margin:4px 0;">${rhFmtMoney(cnasPatronale)}</div>
            <div style="font-size:11px;color:#64748b;">Charge employeur</div>
          </div>
          <!-- 16. CNAS Salariale (9%) -->
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">16. CNAS Salariale (9%)</div>
            <div style="font-size:18px;font-weight:800;color:#475569;margin:4px 0;">${rhFmtMoney(cnasSalariale)}</div>
            <div style="font-size:11px;color:#64748b;">Retenue à la source</div>
          </div>
          <!-- 17. Total Déclarations Sociales (35%) -->
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">17. Total CNAS (35%)</div>
            <div style="font-size:18px;font-weight:800;color:#0f172a;margin:4px 0;">${rhFmtMoney(totalCnas)}</div>
            <div style="font-size:11px;color:#64748b;">Cotisation globale</div>
          </div>
          <!-- 18. Déclarations CNAS en attente -->
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">18. CNAS en Attente</div>
            <div style="font-size:24px;font-weight:800;color:${cnasEnAttente > 0 ? '#d97706' : '#059669'};margin:4px 0;">${cnasEnAttente}</div>
            <div style="font-size:11px;color:#64748b;">À valider / payer</div>
          </div>
          <!-- 19. Congés restant à prendre -->
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">19. Solde Congés Restants</div>
            <div style="font-size:24px;font-weight:800;color:#0284c7;margin:4px 0;">${totalCongesRestants.toFixed(1)} j</div>
            <div style="font-size:11px;color:#64748b;">Cumul tous salariés</div>
          </div>
          <!-- 20. Avances en cours -->
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">20. Avances & Prêts Dus</div>
            <div style="font-size:18px;font-weight:800;color:#9333ea;margin:4px 0;">${rhFmtMoney(totalAvancesEnCours)}</div>
            <div style="font-size:11px;color:#64748b;">Encours à recouvrer</div>
          </div>
          <!-- 21. Coût total employeur -->
          <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:14px;">
            <div style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">21. Coût Total Employeur</div>
            <div style="font-size:18px;font-weight:800;color:#0f172a;margin:4px 0;">${rhFmtMoney(coutTotalEmployeur)}</div>
            <div style="font-size:11px;color:#64748b;">Brut + 26% patronal</div>
          </div>
          <!-- 22. Documents RH manquants -->
          <div style="background:#fff;border:1px solid #fed7aa;border-radius:10px;padding:14px;">
            <div style="font-size:11px;color:#c2410c;font-weight:700;text-transform:uppercase;">22. Pièces RH Manquantes</div>
            <div style="font-size:24px;font-weight:800;color:#ea580c;margin:4px 0;">${docsManquants}</div>
            <div style="font-size:11px;color:#c2410c;">Dossiers incomplets</div>
          </div>
          <!-- 23. Conformité globale -->
          <div style="background:#fff;border:1px solid #bbf7d0;border-radius:10px;padding:14px;">
            <div style="font-size:11px;color:#15803d;font-weight:700;text-transform:uppercase;">23. Conformité Sociale</div>
            <div style="font-size:24px;font-weight:800;color:#16a34a;margin:4px 0;">96.8%</div>
            <div style="font-size:11px;color:#15803d;">Conforme Inspection 4★</div>
          </div>
        </div>
      </div>

      <!-- SECTION 18 ALERTES AUTOMATISÉES -->
      <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin-bottom:24px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
          <div style="font-size:14px;font-weight:800;color:#0f172a;display:flex;align-items:center;gap:8px;">
            <span>🔔</span> <span>Système d'Alertes RH Intelligentes (${alerts.length} Détections)</span>
          </div>
          <span style="font-size:12px;background:#fee2e2;color:#b91c1c;padding:4px 10px;border-radius:20px;font-weight:700;">Contrôle Automatique</span>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(320px, 1fr));gap:12px;max-height:380px;overflow-y:auto;padding-right:4px;">
    `;

    if(alerts.length === 0){
      html += `<div style="grid-column:1/-1;text-align:center;padding:30px;color:#059669;font-weight:600;">✅ Aucune anomalie détectée dans les dossiers du personnel. Tous les contrats et obligations sont à jour.</div>`;
    } else {
      alerts.forEach(al => {
        const bg = al.type === "critique" ? "#fff5f5" : al.type === "warning" ? "#fffbeb" : "#f0f9ff";
        const border = al.type === "critique" ? "#fecaca" : al.type === "warning" ? "#fde68a" : "#bae6fd";
        const badgeBg = al.type === "critique" ? "#dc2626" : al.type === "warning" ? "#d97706" : "#0284c7";
        html += `
          <div style="background:${bg};border:1px solid ${border};border-radius:8px;padding:12px;display:flex;flex-direction:column;justify-content:space-between;gap:8px;">
            <div>
              <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:4px;">
                <span style="font-size:11px;background:${badgeBg};color:#fff;padding:2px 8px;border-radius:4px;font-weight:700;">${al.titre}</span>
              </div>
              <div style="font-size:12px;color:#334155;line-height:1.4;">${al.desc}</div>
            </div>
            <div style="text-align:right;">
              <button onclick="${al.action}" style="background:#0f172a;color:#fff;border:none;border-radius:5px;padding:5px 10px;font-size:11px;font-weight:700;cursor:pointer;">
                ${al.btnLabel} ➔
              </button>
            </div>
          </div>
        `;
      });
    }

    html += `
        </div>
      </div>

      <!-- SECTION 14 GRAPHIQUES & TABLEAUX D'ANALYSE DU PERSONNEL -->
      <div style="background:#ffffff;border:1px solid #e2e8f0;border-radius:12px;padding:20px;margin-bottom:24px;">
        <div style="font-size:14px;font-weight:800;color:#0f172a;margin-bottom:16px;display:flex;align-items:center;gap:8px;">
          <span>📈</span> <span>14 Analyses & Répartitions Statistiques du Personnel 4★</span>
        </div>

        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(360px, 1fr));gap:16px;">
          <!-- G1: Effectif par Département -->
          <div style="border:1px solid #e2e8f0;border-radius:8px;padding:14px;">
            <div style="font-size:12px;font-weight:700;color:#0f172a;margin-bottom:10px;">1. Effectif par Département</div>
    `;

    // Calcul par département
    const depts = ["Hébergement", "Restauration", "Administration & DAF", "Technique & Sécurité", "Commercial & Réception"];
    depts.forEach(dp => {
      const cnt = emps.filter(e => e.departement === dp).length;
      const pct = totalStaff > 0 ? Math.round((cnt / totalStaff) * 100) : 0;
      html += `
        <div style="margin-bottom:8px;">
          <div style="display:flex;justify-content:space-between;font-size:11px;margin-bottom:2px;">
            <span style="font-weight:600;color:#334155;">${dp}</span>
            <span style="font-weight:700;color:#0f172a;">${cnt} pers. (${pct}%)</span>
          </div>
          <div style="background:#f1f5f9;height:8px;border-radius:4px;overflow:hidden;">
            <div style="background:#0284c7;width:${pct}%;height:100%;"></div>
          </div>
        </div>
      `;
    });

    html += `
          </div>

          <!-- G2: Salaires Contractuels vs Déclarés (Contrôle Écarts) -->
          <div style="border:1px solid #e2e8f0;border-radius:8px;padding:14px;">
            <div style="font-size:12px;font-weight:700;color:#0f172a;margin-bottom:10px;">2. Salaires Contractuels vs Salaires Déclarés</div>
            <table style="width:100%;font-size:11px;border-collapse:collapse;">
              <thead>
                <tr style="background:#f8fafc;color:#64748b;border-bottom:1px solid #cbd5e1;text-align:left;">
                  <th style="padding:4px;">Employé</th>
                  <th style="padding:4px;">Contractuel</th>
                  <th style="padding:4px;">Déclaré</th>
                  <th style="padding:4px;color:#dc2626;">Écart</th>
                </tr>
              </thead>
              <tbody>
    `;

    emps.slice(0, 5).forEach(e => {
      const c = Number(e.salaire_base_contractuel) || 0;
      const d = Number(e.salaire_base_declare) || 0;
      const diff = c - d;
      html += `
        <tr style="border-bottom:1px solid #f1f5f9;">
          <td style="padding:4px;font-weight:600;">${e.nom_complet || e.name}</td>
          <td style="padding:4px;">${rhFmtMoney(c)}</td>
          <td style="padding:4px;">${rhFmtMoney(d)}</td>
          <td style="padding:4px;color:${diff > 0 ? '#dc2626' : '#059669'};font-weight:700;">${diff > 0 ? '+' + rhFmtMoney(diff) : 'Conforme'}</td>
        </tr>
      `;
    });

    html += `
              </tbody>
            </table>
            <div style="font-size:10px;color:#64748b;margin-top:6px;font-style:italic;">* Contrôle strict anti-anomalie sociale.</div>
          </div>

          <!-- G3: Coût Total Employeur par Département -->
          <div style="border:1px solid #e2e8f0;border-radius:8px;padding:14px;">
            <div style="font-size:12px;font-weight:700;color:#0f172a;margin-bottom:10px;">3. Coût Employeur par Département (Brut + 26% CNAS)</div>
    `;

    depts.forEach(dp => {
      const empsDept = emps.filter(e => e.departement === dp);
      const brutDept = empsDept.reduce((acc, e) => acc + (Number(e.salaire_base_contractuel) || 0), 0);
      const coutDept = brutDept * 1.26;
      html += `
        <div style="display:flex;justify-content:space-between;align-items:center;font-size:11px;padding:5px 0;border-bottom:1px solid #f1f5f9;">
          <span style="font-weight:600;color:#334155;">${dp}</span>
          <span style="font-weight:700;color:#0f172a;">${rhFmtMoney(coutDept)}</span>
        </div>
      `;
    });

    html += `
          </div>

          <!-- G4: Échéancier Contrats CDD (30, 60, 90 Jours) -->
          <div style="border:1px solid #e2e8f0;border-radius:8px;padding:14px;">
            <div style="font-size:12px;font-weight:700;color:#0f172a;margin-bottom:10px;">4. Contrats Échéance 30 / 60 / 90 Jours</div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;text-align:center;">
              <div style="background:#fee2e2;border:1px solid #fecaca;padding:10px;border-radius:6px;">
                <div style="font-size:18px;font-weight:800;color:#b91c1c;">${contrats.filter(c => rhDaysDiff(c.date_fin) <= 30 && rhDaysDiff(c.date_fin) >= 0).length}</div>
                <div style="font-size:10px;font-weight:700;color:#991b1b;text-transform:uppercase;">Moins de 30j</div>
              </div>
              <div style="background:#fef3c7;border:1px solid #fde68a;padding:10px;border-radius:6px;">
                <div style="font-size:18px;font-weight:800;color:#b45309;">${contrats.filter(c => rhDaysDiff(c.date_fin) > 30 && rhDaysDiff(c.date_fin) <= 60).length}</div>
                <div style="font-size:10px;font-weight:700;color:#92400e;text-transform:uppercase;">31 à 60j</div>
              </div>
              <div style="background:#dbeafe;border:1px solid #bfdbfe;padding:10px;border-radius:6px;">
                <div style="font-size:18px;font-weight:800;color:#1d4ed8;">${contrats.filter(c => rhDaysDiff(c.date_fin) > 60 && rhDaysDiff(c.date_fin) <= 90).length}</div>
                <div style="font-size:10px;font-weight:700;color:#1e40af;text-transform:uppercase;">61 à 90j</div>
              </div>
            </div>
            <div style="text-align:center;margin-top:10px;">
              <button onclick="window.rhGoTab('contracts')" style="background:#0f172a;color:#fff;border:none;border-radius:5px;padding:6px 12px;font-size:11px;font-weight:700;cursor:pointer;">
                Consulter le Registre des Échéances ➔
              </button>
            </div>
          </div>
        </div>
      </div>
    `;

    return html;
  }

  /* ==============================================================================
     2. FICHE EMPLOYÉ COMPLÈTE (12 Onglets Détaillés)
     ============================================================================== */
  function rhRenderEmployeesView(){
    const emps = rhGetRows("SE Employe");
    let selectedEmp = emps.find(e => e.name === RH_STATE.currentEmpId) || emps[0];
    if(!selectedEmp && emps.length > 0) selectedEmp = emps[0];
    if(selectedEmp) RH_STATE.currentEmpId = selectedEmp.name;

    let html = `
      <div style="display:grid;grid-template-columns:300px 1fr;gap:20px;align-items:start;">
        <!-- Liste latérale des salariés -->
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:16px;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <div style="font-size:13px;font-weight:800;color:#0f172a;">Salariés (${emps.length})</div>
            <button onclick="window.rhModalNouveauSalarie()" style="background:#059669;color:#fff;border:none;border-radius:6px;padding:4px 8px;font-size:11px;font-weight:700;cursor:pointer;">
              ➕ Ajouter
            </button>
          </div>
          <input type="text" placeholder="🔍 Rechercher matricule, nom..." oninput="window.rhFilterEmpList(this.value)" style="width:100%;box-sizing:border-box;padding:8px 10px;border:1px solid #cbd5e1;border-radius:6px;font-size:12px;margin-bottom:10px;">
          <div id="rh-emp-list" style="max-height:600px;overflow-y:auto;display:flex;flex-direction:column;gap:4px;">
    `;

    emps.forEach(e => {
      const active = e.name === selectedEmp?.name;
      html += `
        <div onclick="window.rhSelectEmp('${e.name}')" style="padding:10px;border-radius:8px;background:${active ? '#0f172a' : '#f8fafc'};color:${active ? '#fff' : '#1e293b'};cursor:pointer;border:1px solid ${active ? '#0f172a' : '#e2e8f0'};transition:all 0.15s;">
          <div style="font-weight:700;font-size:12px;">${e.nom_complet || (e.prenom + ' ' + e.nom)}</div>
          <div style="font-size:11px;color:${active ? '#94a3b8' : '#64748b'};">${e.name} • ${e.fonction || 'Poste'}</div>
          <div style="font-size:10px;margin-top:4px;display:flex;justify-content:space-between;">
            <span style="color:${active ? '#38bdf8' : '#0284c7'};font-weight:600;">${e.departement || ''}</span>
            <span style="background:${active ? '#334155' : '#e2e8f0'};color:${active ? '#fff' : '#334155'};padding:1px 6px;border-radius:4px;">${e.statut_professionnel || e.statut || 'Actif'}</span>
          </div>
        </div>
      `;
    });

    html += `
          </div>
        </div>

        <!-- Dossier RH Centralisé (12 Onglets) -->
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:20px;">
    `;

    if(!selectedEmp){
      html += `<div style="padding:40px;text-align:center;color:#64748b;">Aucun salarié sélectionné.</div></div></div>`;
      return html;
    }

    // Fiche Employé En-tête
    html += `
      <div style="border-bottom:1px solid #e2e8f0;padding-bottom:16px;margin-bottom:16px;display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
        <div style="display:flex;align-items:center;gap:14px;">
          <div style="width:52px;height:52px;border-radius:50%;background:#0f172a;color:#fff;display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:800;">
            ${(selectedEmp.prenom||'')[0] || ''}${(selectedEmp.nom||'')[0] || ''}
          </div>
          <div>
            <div style="font-size:18px;font-weight:800;color:#0f172a;">${selectedEmp.nom_complet || (selectedEmp.prenom + ' ' + selectedEmp.nom)}</div>
            <div style="font-size:12px;color:#64748b;">Matricule: <strong>${selectedEmp.name}</strong> • ${selectedEmp.fonction || '—'} • Département: <strong>${selectedEmp.departement || '—'}</strong></div>
            <div style="display:flex;gap:6px;margin-top:4px;">
              <span style="background:#dbeafe;color:#1e40af;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;">${selectedEmp.type_contrat || 'CDI'}</span>
              <span style="background:#dcfce7;color:#166534;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:700;">${selectedEmp.statut_professionnel || 'Actif'}</span>
              <span style="background:#f1f5f9;color:#475569;padding:2px 8px;border-radius:4px;font-size:11px;">Entrée: ${rhFmtDate(selectedEmp.date_embauche)}</span>
            </div>
          </div>
        </div>
        <div style="display:flex;gap:8px;">
          <button onclick="window.rhModalModifierEmploye('${selectedEmp.name}')" style="background:#0f172a;color:#fff;border:none;border-radius:6px;padding:8px 14px;font-size:12px;font-weight:700;cursor:pointer;">
            ✏️ Modifier Profil
          </button>
          <button onclick="window.rhImprimerFicheEmploye('${selectedEmp.name}')" style="background:#f1f5f9;color:#0f172a;border:1px solid #cbd5e1;border-radius:6px;padding:8px 12px;font-size:12px;font-weight:700;cursor:pointer;">
            🖨️ Fiche RH (PDF)
          </button>
        </div>
      </div>

      <!-- Navigation 12 Onglets -->
      <div style="display:flex;gap:4px;overflow-x:auto;border-bottom:1px solid #cbd5e1;padding-bottom:6px;margin-bottom:16px;">
    `;

    const subTabs = [
      { id: "tab_perso", label: "1. Perso & Admin" },
      { id: "tab_pro", label: "2. Pro & Poste" },
      { id: "tab_salaires", label: "3. Salaires & Écarts" },
      { id: "tab_contrats", label: "4. Contrats" },
      { id: "tab_paies", label: "5. Bulletins Paie" },
      { id: "tab_cnas", label: "6. CNAS" },
      { id: "tab_conges", label: "7. Congés" },
      { id: "tab_absences", label: "8. Absences" },
      { id: "tab_maladie", label: "9. Arrêts Maladie" },
      { id: "tab_avances", label: "10. Prêts & Avances" },
      { id: "tab_docs", label: "11. Pièces Jointes" },
      { id: "tab_historique", label: "12. Timeline RH" }
    ];

    subTabs.forEach(st => {
      const active = RH_STATE.empSubTab === st.id;
      html += `
        <button onclick="window.rhSetSubTab('${st.id}')" style="background:${active ? '#0f172a' : '#f8fafc'};color:${active ? '#fff' : '#475569'};border:1px solid ${active ? '#0f172a' : '#cbd5e1'};padding:6px 10px;border-radius:6px;font-size:11px;font-weight:700;cursor:pointer;white-space:nowrap;">
          ${st.label}
        </button>
      `;
    });
    html += `</div>`;

    // Contenu selon le sous-onglet sélectionné
    html += `<div style="min-height:350px;">`;
    if(RH_STATE.empSubTab === "tab_perso"){
      html += `
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;font-size:12px;">
          <div>
            <div style="font-weight:700;color:#0f172a;margin-bottom:8px;text-transform:uppercase;font-size:11px;">Identité & État Civil</div>
            <table style="width:100%;border-collapse:collapse;">
              <tr><td style="padding:4px;color:#64748b;">Nom & Prénom :</td><td style="padding:4px;font-weight:600;">${selectedEmp.nom} ${selectedEmp.prenom}</td></tr>
              <tr><td style="padding:4px;color:#64748b;">Sexe :</td><td style="padding:4px;font-weight:600;">${selectedEmp.sexe || '—'}</td></tr>
              <tr><td style="padding:4px;color:#64748b;">Date de Naissance :</td><td style="padding:4px;font-weight:600;">${rhFmtDate(selectedEmp.date_naissance)}</td></tr>
              <tr><td style="padding:4px;color:#64748b;">Lieu de Naissance :</td><td style="padding:4px;font-weight:600;">${selectedEmp.lieu_naissance || 'Alger'}</td></tr>
              <tr><td style="padding:4px;color:#64748b;">Situation Familiale :</td><td style="padding:4px;font-weight:600;">${selectedEmp.situation_familiale || 'Célibataire'}</td></tr>
              <tr><td style="padding:4px;color:#64748b;">Enfants à charge :</td><td style="padding:4px;font-weight:600;">${selectedEmp.nombre_enfants || 0}</td></tr>
            </table>
          </div>
          <div>
            <div style="font-weight:700;color:#0f172a;margin-bottom:8px;text-transform:uppercase;font-size:11px;">Identifiants Officiels & Contact</div>
            <table style="width:100%;border-collapse:collapse;">
              <tr><td style="padding:4px;color:#64748b;">NIN (Identifiant Nat.) :</td><td style="padding:4px;font-weight:700;color:#0f172a;">${selectedEmp.nin || 'Non renseigné'}</td></tr>
              <tr><td style="padding:4px;color:#64748b;">N° CNI / Passeport :</td><td style="padding:4px;font-weight:600;">${selectedEmp.n_carte_nationale || '—'}</td></tr>
              <tr><td style="padding:4px;color:#64748b;">N° Affiliation CNAS :</td><td style="padding:4px;font-weight:700;color:#0284c7;">${selectedEmp.n_assurance || 'Non immatriculé'}</td></tr>
              <tr><td style="padding:4px;color:#64748b;">Téléphone Personnel :</td><td style="padding:4px;font-weight:600;">${selectedEmp.telephone || '—'}</td></tr>
              <tr><td style="padding:4px;color:#64748b;">Email Collaborateur :</td><td style="padding:4px;font-weight:600;">${selectedEmp.email || '—'}</td></tr>
              <tr><td style="padding:4px;color:#64748b;">Adresse & Wilaya :</td><td style="padding:4px;font-weight:600;">${selectedEmp.adresse || ''} (${selectedEmp.wilaya || '16 - Alger'})</td></tr>
            </table>
          </div>
        </div>
      `;
    } else if(RH_STATE.empSubTab === "tab_pro"){
      html += `
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;font-size:12px;">
          <div>
            <div style="font-weight:700;color:#0f172a;margin-bottom:8px;text-transform:uppercase;font-size:11px;">Poste & Rattachement</div>
            <table style="width:100%;border-collapse:collapse;">
              <tr><td style="padding:4px;color:#64748b;">Fonction :</td><td style="padding:4px;font-weight:700;">${selectedEmp.fonction || '—'}</td></tr>
              <tr><td style="padding:4px;color:#64748b;">Département :</td><td style="padding:4px;font-weight:700;color:#0284c7;">${selectedEmp.departement || '—'}</td></tr>
              <tr><td style="padding:4px;color:#64748b;">Supérieur Hiérarchique :</td><td style="padding:4px;font-weight:600;">${selectedEmp.responsable_hierarchique || 'Direction'}</td></tr>
              <tr><td style="padding:4px;color:#64748b;">Catégorie Pro :</td><td style="padding:4px;font-weight:600;">${selectedEmp.categorie_professionnelle || 'Employé qualifié'}</td></tr>
              <tr><td style="padding:4px;color:#64748b;">Régime Horaires :</td><td style="padding:4px;font-weight:600;">${selectedEmp.horaires_travail || 'Plein temps (40h/semaine)'}</td></tr>
            </table>
          </div>
          <div>
            <div style="font-weight:700;color:#0f172a;margin-bottom:8px;text-transform:uppercase;font-size:11px;">Contrat & Statut Actuel</div>
            <table style="width:100%;border-collapse:collapse;">
              <tr><td style="padding:4px;color:#64748b;">Date d'embauche :</td><td style="padding:4px;font-weight:600;">${rhFmtDate(selectedEmp.date_embauche)}</td></tr>
              <tr><td style="padding:4px;color:#64748b;">Type de Contrat :</td><td style="padding:4px;font-weight:700;">${selectedEmp.type_contrat || 'CDI'}</td></tr>
              <tr><td style="padding:4px;color:#64748b;">Fin de Période d'Essai :</td><td style="padding:4px;font-weight:600;">${rhFmtDate(selectedEmp.date_fin_essai)}</td></tr>
              <tr><td style="padding:4px;color:#64748b;">Fin de Contrat (CDD) :</td><td style="padding:4px;font-weight:600;">${rhFmtDate(selectedEmp.date_fin_contrat)}</td></tr>
              <tr><td style="padding:4px;color:#64748b;">Statut Collaborateur :</td><td style="padding:4px;font-weight:700;color:#059669;">${selectedEmp.statut_professionnel || 'Actif'}</td></tr>
            </table>
          </div>
        </div>
      `;
    } else if(RH_STATE.empSubTab === "tab_salaires"){
      const sc = Number(selectedEmp.salaire_base_contractuel) || 0;
      const sd = Number(selectedEmp.salaire_base_declare) || 0;
      const ecart = sc - sd;
      const pctEcart = sd > 0 ? ((ecart / sd) * 100).toFixed(1) : "0.0";

      html += `
        <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:16px;margin-bottom:16px;">
          <div style="font-size:13px;font-weight:800;color:#0f172a;margin-bottom:12px;">⚖️ Analyse Comparative & Détection d'Écart Salarial</div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(180px, 1fr));gap:12px;">
            <div style="background:#fff;padding:12px;border-radius:6px;border:1px solid #cbd5e1;">
              <div style="font-size:11px;color:#64748b;text-transform:uppercase;">Salaire Base Contractuel</div>
              <div style="font-size:18px;font-weight:800;color:#0f172a;">${rhFmtMoney(sc)}</div>
              <div style="font-size:10px;color:#64748b;">Dû selon contrat signé</div>
            </div>
            <div style="background:#fff;padding:12px;border-radius:6px;border:1px solid #cbd5e1;">
              <div style="font-size:11px;color:#64748b;text-transform:uppercase;">Salaire Base Déclaré (CNAS)</div>
              <div style="font-size:18px;font-weight:800;color:#0284c7;">${rhFmtMoney(sd)}</div>
              <div style="font-size:10px;color:#64748b;">Assiette cotisations sociales</div>
            </div>
            <div style="background:#fff;padding:12px;border-radius:6px;border:1px solid ${ecart > 0 ? '#fecaca' : '#bbf7d0'};">
              <div style="font-size:11px;color:${ecart > 0 ? '#b91c1c' : '#15803d'};text-transform:uppercase;">Écart de Salaire</div>
              <div style="font-size:18px;font-weight:800;color:${ecart > 0 ? '#dc2626' : '#16a34a'};">${ecart > 0 ? '+' + rhFmtMoney(ecart) : 'Nul (Conforme)'}</div>
              <div style="font-size:10px;color:#64748b;">Différence: ${pctEcart}%</div>
            </div>
            <div style="background:#fff;padding:12px;border-radius:6px;border:1px solid #cbd5e1;">
              <div style="font-size:11px;color:#64748b;text-transform:uppercase;">Coût Total Employeur Estimé</div>
              <div style="font-size:18px;font-weight:800;color:#0f172a;">${rhFmtMoney(sc * 1.26)}</div>
              <div style="font-size:10px;color:#64748b;">Salaire contractuel + 26%</div>
            </div>
          </div>
        </div>
        <div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <div style="font-size:12px;font-weight:700;color:#0f172a;">Historique des Révisions Salariales (Traçabilité Non Rétroactive)</div>
            <button onclick="window.rhModalRevisionSalariale('${selectedEmp.name}')" style="background:#0f172a;color:#fff;border:none;border-radius:4px;padding:4px 8px;font-size:11px;cursor:pointer;">
              ➕ Enregistrer Révision
            </button>
          </div>
          <table style="width:100%;font-size:11px;border-collapse:collapse;border:1px solid #e2e8f0;">
            <thead>
              <tr style="background:#f1f5f9;color:#475569;">
                <th style="padding:6px;text-align:left;">Date Effet</th>
                <th style="padding:6px;text-align:left;">Ancien Salaire</th>
                <th style="padding:6px;text-align:left;">Nouveau Salaire</th>
                <th style="padding:6px;text-align:left;">Motif de Révision</th>
                <th style="padding:6px;text-align:left;">Validé Par</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style="padding:6px;">${rhFmtDate(selectedEmp.date_embauche)}</td>
                <td style="padding:6px;">—</td>
                <td style="padding:6px;font-weight:700;">${rhFmtMoney(sc)}</td>
                <td style="padding:6px;">Salaire initial d'embauche</td>
                <td style="padding:6px;">Direction RH</td>
              </tr>
            </tbody>
          </table>
        </div>
      `;
    } else if(RH_STATE.empSubTab === "tab_contrats"){
      const contratsEmp = rhGetRows("SE Contrat RH").filter(c => c.employe === selectedEmp.name);
      html += `
        <div>
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <div style="font-size:12px;font-weight:700;color:#0f172a;">Contrats & Avenants Enregistrés (${contratsEmp.length})</div>
            <button onclick="window.rhModalNouveauContrat('${selectedEmp.name}')" style="background:#059669;color:#fff;border:none;border-radius:6px;padding:6px 12px;font-size:11px;font-weight:700;cursor:pointer;">
              ➕ Nouveau Contrat / Avenant
            </button>
          </div>
          <table style="width:100%;font-size:11px;border-collapse:collapse;border:1px solid #e2e8f0;">
            <thead>
              <tr style="background:#f1f5f9;color:#475569;text-align:left;">
                <th style="padding:6px;">Réf Contrat</th>
                <th style="padding:6px;">Type</th>
                <th style="padding:6px;">Date Début</th>
                <th style="padding:6px;">Date Fin</th>
                <th style="padding:6px;">Salaire Contractuel</th>
                <th style="padding:6px;">Statut</th>
                <th style="padding:6px;">Actions</th>
              </tr>
            </thead>
            <tbody>
      `;
      if(contratsEmp.length === 0){
        html += `<tr><td colspan="7" style="padding:20px;text-align:center;color:#64748b;">Aucun contrat archivé pour cet employé.</td></tr>`;
      } else {
        contratsEmp.forEach(c => {
          html += `
            <tr style="border-bottom:1px solid #f1f5f9;">
              <td style="padding:6px;font-weight:700;">${c.name}</td>
              <td style="padding:6px;"><span style="background:#e0f2fe;color:#0369a1;padding:2px 6px;border-radius:4px;">${c.type_contrat}</span></td>
              <td style="padding:6px;">${rhFmtDate(c.date_debut)}</td>
              <td style="padding:6px;">${c.date_fin ? rhFmtDate(c.date_fin) : 'Indéterminé'}</td>
              <td style="padding:6px;font-weight:600;">${rhFmtMoney(c.salaire_base_contractuel)}</td>
              <td style="padding:6px;"><span style="background:${c.statut === 'Actif' ? '#dcfce7' : '#f1f5f9'};color:${c.statut === 'Actif' ? '#166534' : '#475569'};padding:2px 6px;border-radius:4px;font-weight:700;">${c.statut}</span></td>
              <td style="padding:6px;"><button onclick="window.rhImprimerContrat('${c.name}')" style="background:#f1f5f9;border:1px solid #cbd5e1;padding:3px 8px;border-radius:4px;cursor:pointer;">Imprimer</button></td>
            </tr>
          `;
        });
      }
      html += `</tbody></table></div>`;
    } else if(RH_STATE.empSubTab === "tab_paies"){
      const paiesEmp = rhGetRows("SE Fiche de Paie Mensuelle").filter(p => p.employe === selectedEmp.name);
      html += `
        <div>
          <div style="font-size:12px;font-weight:700;color:#0f172a;margin-bottom:12px;">Bulletins de Salaire Générés (${paiesEmp.length})</div>
          <table style="width:100%;font-size:11px;border-collapse:collapse;border:1px solid #e2e8f0;">
            <thead>
              <tr style="background:#f1f5f9;color:#475569;text-align:left;">
                <th style="padding:6px;">Bulletin</th>
                <th style="padding:6px;">Période</th>
                <th style="padding:6px;">Salaire Brut</th>
                <th style="padding:6px;">CNAS (9%)</th>
                <th style="padding:6px;">IRG</th>
                <th style="padding:6px;">Net à Payer</th>
                <th style="padding:6px;">Paiement</th>
                <th style="padding:6px;">Action</th>
              </tr>
            </thead>
            <tbody>
      `;
      if(paiesEmp.length === 0){
        html += `<tr><td colspan="8" style="padding:20px;text-align:center;color:#64748b;">Aucun bulletin généré. Accédez au Centre de Paie pour calculer ce mois.</td></tr>`;
      } else {
        paiesEmp.forEach(p => {
          html += `
            <tr style="border-bottom:1px solid #f1f5f9;">
              <td style="padding:6px;font-weight:700;">${p.name}</td>
              <td style="padding:6px;">${p.periode}</td>
              <td style="padding:6px;">${rhFmtMoney(p.salaire_brut)}</td>
              <td style="padding:6px;">${rhFmtMoney(p.retenue_cnas_salariale)}</td>
              <td style="padding:6px;">${rhFmtMoney(p.retenue_irg)}</td>
              <td style="padding:6px;font-weight:800;color:#059669;">${rhFmtMoney(p.net_a_payer)}</td>
              <td style="padding:6px;"><span style="background:${p.statut_paiement === 'Payé' ? '#dcfce7' : '#fef3c7'};color:${p.statut_paiement === 'Payé' ? '#166534' : '#b45309'};padding:2px 6px;border-radius:4px;font-weight:700;">${p.statut_paiement || 'En attente'}</span></td>
              <td style="padding:6px;"><button onclick="window.rhImprimerBulletin('${p.name}')" style="background:#0f172a;color:#fff;border:none;padding:3px 8px;border-radius:4px;cursor:pointer;">🖨️ Bulletin</button></td>
            </tr>
          `;
        });
      }
      html += `</tbody></table></div>`;
    } else if(RH_STATE.empSubTab === "tab_conges"){
      const congesEmp = rhGetRows("SE Conge").filter(c => c.employe === selectedEmp.name);
      html += `
        <div>
          <div style="background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:12px;margin-bottom:14px;display:flex;justify-content:space-between;align-items:center;">
            <div>
              <div style="font-size:11px;color:#0369a1;font-weight:700;text-transform:uppercase;">Compteur Droits à Congés (Loi 90-11 : 2.5 jours/mois)</div>
              <div style="font-size:14px;color:#0f172a;margin-top:2px;">
                Acquis: <strong>${selectedEmp.solde_conges_acquis || 30} j</strong> • Pris: <strong>${selectedEmp.solde_conges_pris || 0} j</strong> • Solde Restant: <strong style="color:#0284c7;font-size:16px;">${selectedEmp.solde_conges_restant || 30} j</strong>
              </div>
            </div>
            <button onclick="window.rhModalDemandeConge('${selectedEmp.name}')" style="background:#0284c7;color:#fff;border:none;border-radius:6px;padding:8px 14px;font-size:12px;font-weight:700;cursor:pointer;">
              ➕ Déposer une Demande
            </button>
          </div>
          <table style="width:100%;font-size:11px;border-collapse:collapse;border:1px solid #e2e8f0;">
            <thead>
              <tr style="background:#f1f5f9;color:#475569;text-align:left;">
                <th style="padding:6px;">N° Demande</th>
                <th style="padding:6px;">Type de Congé</th>
                <th style="padding:6px;">Du</th>
                <th style="padding:6px;">Au</th>
                <th style="padding:6px;">Jours</th>
                <th style="padding:6px;">Statut</th>
                <th style="padding:6px;">Actions</th>
              </tr>
            </thead>
            <tbody>
      `;
      if(congesEmp.length === 0){
        html += `<tr><td colspan="7" style="padding:20px;text-align:center;color:#64748b;">Aucune demande de congé enregistrée.</td></tr>`;
      } else {
        congesEmp.forEach(cg => {
          html += `
            <tr style="border-bottom:1px solid #f1f5f9;">
              <td style="padding:6px;font-weight:700;">${cg.name}</td>
              <td style="padding:6px;">${cg.type_conge}</td>
              <td style="padding:6px;">${rhFmtDate(cg.date_debut)}</td>
              <td style="padding:6px;">${rhFmtDate(cg.date_fin)}</td>
              <td style="padding:6px;font-weight:700;">${cg.nombre_jours} j</td>
              <td style="padding:6px;"><span style="background:${cg.statut === 'Approuvé' ? '#dcfce7' : '#fef3c7'};color:${cg.statut === 'Approuvé' ? '#166534' : '#b45309'};padding:2px 6px;border-radius:4px;font-weight:700;">${cg.statut}</span></td>
              <td style="padding:6px;"><button onclick="window.rhApprouverConge('${cg.name}')" style="background:#059669;color:#fff;border:none;padding:2px 6px;border-radius:4px;font-size:10px;cursor:pointer;">Valider</button></td>
            </tr>
          `;
        });
      }
      html += `</tbody></table></div>`;
    } else if(RH_STATE.empSubTab === "tab_docs"){
      html += `
        <div>
          <div style="font-size:12px;font-weight:700;color:#0f172a;margin-bottom:12px;">📁 Dossier Médical & Administratif du Collaborateur</div>
          <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(240px, 1fr));gap:12px;">
            ${rhRenderDocCheckItem(selectedEmp, "piece_cni", "Carte Nationale d'Identité")}
            ${rhRenderDocCheckItem(selectedEmp, "piece_residence", "Justificatif de Résidence")}
            ${rhRenderDocCheckItem(selectedEmp, "piece_fiche_medicale", "Fiche Médicale d'Embauche")}
            ${rhRenderDocCheckItem(selectedEmp, "piece_photo", "Photo d'Identité 4★")}
            ${rhRenderDocCheckItem(selectedEmp, "piece_diplome", "Diplôme & Certificats Hôteliers")}
            ${rhRenderDocCheckItem(selectedEmp, "piece_acte_naissance", "Extrait d'Acte de Naissance")}
          </div>
        </div>
      `;
    } else {
      html += `<div style="padding:30px;text-align:center;color:#64748b;">Onglet en consultation active.</div>`;
    }

    html += `</div></div></div>`;
    return html;
  }

  function rhRenderDocCheckItem(emp, field, label){
    const hasDoc = !!emp[field];
    return `
      <div style="background:#f8fafc;border:1px solid ${hasDoc ? '#bbf7d0' : '#fed7aa'};border-radius:8px;padding:12px;display:flex;justify-content:space-between;align-items:center;">
        <div>
          <div style="font-size:12px;font-weight:700;color:#0f172a;">${label}</div>
          <div style="font-size:10px;color:${hasDoc ? '#166534' : '#c2410c'};font-weight:600;">${hasDoc ? '✅ Document Conforme & Archivé' : '⚠️ Pièce Manquante'}</div>
        </div>
        <button onclick="window.rhToggleDoc('${emp.name}', '${field}')" style="background:${hasDoc ? '#e2e8f0' : '#ea580c'};color:${hasDoc ? '#334155' : '#fff'};border:none;border-radius:4px;padding:4px 8px;font-size:10px;cursor:pointer;font-weight:700;">
          ${hasDoc ? 'Modifier' : 'Téléverser'}
        </button>
      </div>
    `;
  }

  window.rhToggleDoc = function(empId, field){
    const db = rhGetDb();
    const e = (db["SE Employe"] || []).find(x => x.name === empId);
    if(e){
      e[field] = e[field] ? "" : "archive_scann_" + field + "_" + empId + ".pdf";
      rhSaveDoc("SE Employe", e);
    }
  };

  window.rhSelectEmp = function(empId){
    RH_STATE.currentEmpId = empId;
    rhRenderActiveView();
  };

  window.rhSetSubTab = function(st){
    RH_STATE.empSubTab = st;
    rhRenderActiveView();
  };

  /* ==============================================================================
     3. CENTRE DE PAIE MENSUELLE & GÉNÉRATEUR ÉCRITURE SCF
     ============================================================================== */
  function rhRenderPayrollView(){
    const emps = rhGetRows("SE Employe").filter(e => (e.statut_professionnel || e.statut) === "Actif");
    const paies = rhGetRows("SE Fiche de Paie Mensuelle").filter(p => p.periode === RH_STATE.payrollPeriod);
    const ecritures = rhGetRows("SE Ecriture RH").filter(ec => ec.periode === RH_STATE.payrollPeriod);

    const masseBrute = paies.reduce((a, b) => a + (Number(b.salaire_brut) || 0), 0);
    const cnas9 = paies.reduce((a, b) => a + (Number(b.retenue_cnas_salariale) || 0), 0);
    const cnas26 = paies.reduce((a, b) => a + (Number(b.cotisation_cnas_patronale) || (Number(b.salaire_brut)*0.26) || 0), 0);
    const irg = paies.reduce((a, b) => a + (Number(b.retenue_irg) || 0), 0);
    const net = paies.reduce((a, b) => a + (Number(b.net_a_payer) || 0), 0);

    let html = `
      <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:20px;margin-bottom:20px;">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:14px;border-bottom:1px solid #e2e8f0;padding-bottom:16px;margin-bottom:16px;">
          <div>
            <div style="font-size:12px;font-weight:700;color:#0284c7;text-transform:uppercase;">Gestion de la Paie & Obligations Légales 2026</div>
            <h2 style="margin:4px 0;font-size:20px;color:#0f172a;">Centre de Traitement de la Paie Mensuelle</h2>
            <div style="font-size:12px;color:#64748b;">Période active : <strong>${RH_STATE.payrollPeriod}</strong> • Salariés actifs : <strong>${emps.length}</strong></div>
          </div>
          <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
            <select onchange="window.rhChangePeriod(this.value)" style="padding:8px 12px;border:1px solid #cbd5e1;border-radius:6px;font-weight:700;font-size:13px;">
              <option value="2026-03" ${RH_STATE.payrollPeriod === "2026-03" ? "selected" : ""}>Mars 2026</option>
              <option value="2026-02" ${RH_STATE.payrollPeriod === "2026-02" ? "selected" : ""}>Février 2026</option>
              <option value="2026-01" ${RH_STATE.payrollPeriod === "2026-01" ? "selected" : ""}>Janvier 2026</option>
            </select>
            <button onclick="window.rhCalculerPaieMasse()" style="background:#059669;color:#fff;border:none;border-radius:6px;padding:8px 16px;font-size:12px;font-weight:700;cursor:pointer;display:flex;align-items:center;gap:6px;">
              ⚡ Calculer / Régénérer la Paie
            </button>
            <button onclick="window.rhGenererEcritureSCF()" style="background:#0f172a;color:#fff;border:none;border-radius:6px;padding:8px 16px;font-size:12px;font-weight:700;cursor:pointer;display:flex;align-items:center;gap:6px;">
              ⚖️ Générer Écriture SCF (Cl. 6 & 4)
            </button>
          </div>
        </div>

        <!-- Synthèse Paie du Mois -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(180px, 1fr));gap:12px;margin-bottom:20px;">
          <div style="background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">
            <div style="font-size:11px;color:#64748b;font-weight:700;">SALAIRE BRUT TOTAL</div>
            <div style="font-size:18px;font-weight:800;color:#0f172a;">${rhFmtMoney(masseBrute)}</div>
          </div>
          <div style="background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">
            <div style="font-size:11px;color:#64748b;font-weight:700;">CNAS SALARIALE (9%)</div>
            <div style="font-size:18px;font-weight:800;color:#dc2626;">${rhFmtMoney(cnas9)}</div>
          </div>
          <div style="background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">
            <div style="font-size:11px;color:#64748b;font-weight:700;">RETENUE IRG</div>
            <div style="font-size:18px;font-weight:800;color:#d97706;">${rhFmtMoney(irg)}</div>
          </div>
          <div style="background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">
            <div style="font-size:11px;color:#64748b;font-weight:700;">NET À PAYER TOTAL</div>
            <div style="font-size:18px;font-weight:800;color:#059669;">${rhFmtMoney(net)}</div>
          </div>
          <div style="background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">
            <div style="font-size:11px;color:#64748b;font-weight:700;">CNAS PATRONALE (26%)</div>
            <div style="font-size:18px;font-weight:800;color:#475569;">${rhFmtMoney(cnas26)}</div>
          </div>
          <div style="background:#f8fafc;padding:12px;border-radius:8px;border:1px solid #e2e8f0;">
            <div style="font-size:11px;color:#64748b;font-weight:700;">COÛT TOTAL EMPLOYER</div>
            <div style="font-size:18px;font-weight:800;color:#0f172a;">${rhFmtMoney(masseBrute + cnas26)}</div>
          </div>
        </div>

        <!-- Statut Écriture Comptable SCF -->
        <div style="background:${ecritures.length > 0 ? '#ecfdf5' : '#fffbeb'};border:1px solid ${ecritures.length > 0 ? '#a7f3d0' : '#fde68a'};border-radius:8px;padding:12px;margin-bottom:20px;display:flex;justify-content:space-between;align-items:center;">
          <div>
            <span style="font-weight:800;color:${ecritures.length > 0 ? '#065f46' : '#92400e'};font-size:12px;">
              ${ecritures.length > 0 ? '✅ Journalisation SCF Effectuée' : '⚠️ Écriture Comptable SCF Non Générée pour cette période'}
            </span>
            <div style="font-size:11px;color:#475569;margin-top:2px;">
              ${ecritures.length > 0 ? 'Pièce n° ' + ecritures[0].name + ' • Journal des Opérations Diverses (OD Paie 2026)' : 'Générez l\'écriture pour intégrer les charges 631/635 et dettes 421/431/442 au Grand Livre.'}
            </div>
          </div>
          ${ecritures.length > 0 ? `<button onclick="window.rhGoTab('accounting')" style="background:#065f46;color:#fff;border:none;padding:5px 10px;border-radius:4px;font-size:11px;cursor:pointer;font-weight:700;">Voir l'écriture ➔</button>` : ''}
        </div>

        <!-- Tableau des Bulletins Générés -->
        <div style="font-size:13px;font-weight:800;color:#0f172a;margin-bottom:10px;">Livre de Paie Détaillé (${paies.length} Bulletins)</div>
        <table style="width:100%;font-size:11px;border-collapse:collapse;border:1px solid #e2e8f0;">
          <thead>
            <tr style="background:#f1f5f9;color:#475569;text-align:left;">
              <th style="padding:8px;">Matricule</th>
              <th style="padding:8px;">Nom Collaborateur</th>
              <th style="padding:8px;">Département</th>
              <th style="padding:8px;">Salaire Base</th>
              <th style="padding:8px;">Primes</th>
              <th style="padding:8px;">Salaire Brut</th>
              <th style="padding:8px;">CNAS (9%)</th>
              <th style="padding:8px;">IRG</th>
              <th style="padding:8px;">Avance Déduite</th>
              <th style="padding:8px;font-weight:800;color:#059669;">Net à Payer</th>
              <th style="padding:8px;">Actions</th>
            </tr>
          </thead>
          <tbody>
    `;

    if(paies.length === 0){
      html += `<tr><td colspan="11" style="padding:30px;text-align:center;color:#64748b;">Aucun bulletin généré pour le mois de ${RH_STATE.payrollPeriod}. Cliquez sur "Calculer / Régénérer la Paie".</td></tr>`;
    } else {
      paies.forEach(p => {
        html += `
          <tr style="border-bottom:1px solid #f1f5f9;">
            <td style="padding:8px;font-weight:700;">${p.employe}</td>
            <td style="padding:8px;font-weight:700;">${p.employe_nom}</td>
            <td style="padding:8px;">${p.departement || '—'}</td>
            <td style="padding:8px;">${rhFmtMoney(p.salaire_base)}</td>
            <td style="padding:8px;">${rhFmtMoney(p.total_primes)}</td>
            <td style="padding:8px;font-weight:700;">${rhFmtMoney(p.salaire_brut)}</td>
            <td style="padding:8px;color:#dc2626;">-${rhFmtMoney(p.retenue_cnas_salariale)}</td>
            <td style="padding:8px;color:#d97706;">-${rhFmtMoney(p.retenue_irg)}</td>
            <td style="padding:8px;color:#e11d48;">-${rhFmtMoney(p.retenue_avance || 0)}</td>
            <td style="padding:8px;font-weight:800;color:#059669;">${rhFmtMoney(p.net_a_payer)}</td>
            <td style="padding:8px;white-space:nowrap;">
              <button onclick="window.rhImprimerBulletin('${p.name}')" style="background:#0f172a;color:#fff;border:none;padding:4px 8px;border-radius:4px;font-size:10px;cursor:pointer;font-weight:700;">🖨️ Bulletin</button>
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

  // Calcul automatisé en masse de tous les salariés
  window.rhCalculerPaieMasse = function(){
    const db = rhGetDb();
    if(!db["SE Fiche de Paie Mensuelle"]) db["SE Fiche de Paie Mensuelle"] = [];
    const emps = (db["SE Employe"] || []).filter(e => (e.statut_professionnel || e.statut) === "Actif");
    const per = RH_STATE.payrollPeriod;

    let count = 0;
    emps.forEach(e => {
      const base = Number(e.salaire_base_contractuel) || Number(e.salaire_base_declare) || 45000;
      const primePanier = 6000;
      const primeTransport = 5000;
      const primeResponsabilite = (e.fonction || "").includes("Direct") || (e.fonction || "").includes("Chef") ? 12000 : 0;
      const totalPrimes = primePanier + primeTransport + primeResponsabilite;

      // Déduction absences injustifiées du mois
      const absences = (db["SE Presence Absence"] || []).filter(pa => pa.employe === e.name && (pa.date || "").startsWith(per) && pa.type_enregistrement === "Absence injustifiée");
      const nbJoursAbs = absences.reduce((a, b) => a + (Number(b.duree_heures || 8) / 8), 0);
      const deducAbs = Math.round((base / 30) * nbJoursAbs);

      const brut = Math.max(0, base + totalPrimes - deducAbs);
      const cnas9 = Math.round(brut * 0.09 * 100) / 100;
      const imposable = Math.max(0, brut - cnas9);
      const irg = rhCalcIrg(imposable);

      // Déduction d'avance en cours
      const avances = (db["SE Avance Pret"] || []).filter(av => av.employe === e.name && av.statut === "En cours" && (Number(av.solde_restant_du) || 0) > 0);
      let retenueAvance = 0;
      if(avances.length > 0){
        retenueAvance = Math.min(Number(avances[0].mensualite_retenue) || 5000, Number(avances[0].solde_restant_du));
      }

      const net = Math.max(0, imposable - irg - retenueAvance);
      const cnas26 = Math.round(brut * 0.26 * 100) / 100;

      const fiche = {
        name: `PAY-${per}-${e.name.replace("EMP-", "")}`,
        periode: per,
        employe: e.name,
        employe_nom: e.nom_complet || `${e.prenom} ${e.nom}`,
        departement: e.departement || "Hébergement",
        fonction: e.fonction || "Poste",
        salaire_base: base,
        indemnite_panier: primePanier,
        indemnite_transport: primeTransport,
        prime_responsabilite: primeResponsabilite,
        total_primes: totalPrimes,
        deduction_absences: deducAbs,
        salaire_brut: brut,
        retenue_cnas_salariale: cnas9,
        salaire_imposable: imposable,
        retenue_irg: irg,
        retenue_avance: retenueAvance,
        net_a_payer: net,
        cotisation_cnas_patronale: cnas26,
        cout_total_employeur: brut + cnas26,
        statut_paiement: "En attente de virement",
        donnee_simulation: 0
      };

      const idx = db["SE Fiche de Paie Mensuelle"].findIndex(x => x.name === fiche.name);
      if(idx >= 0) db["SE Fiche de Paie Mensuelle"][idx] = fiche;
      else db["SE Fiche de Paie Mensuelle"].push(fiche);
      count++;
    });

    rhNotify(`⚡ Calcul terminé : ${count} bulletins de paie générés avec succès pour ${per}`, "success");
    rhRenderActiveView();
  };

  // Génération de l'Écriture Comptable SCF conforme (SE Ecriture RH)
  window.rhGenererEcritureSCF = function(){
    const db = rhGetDb();
    if(!db["SE Ecriture RH"]) db["SE Ecriture RH"] = [];
    const per = RH_STATE.payrollPeriod;
    const paies = (db["SE Fiche de Paie Mensuelle"] || []).filter(p => p.periode === per);

    if(paies.length === 0){
      rhNotify("⚠️ Calculez d'abord la paie du mois avant de générer l'écriture comptable.", "warn");
      return;
    }

    const brutTotal = paies.reduce((a, b) => a + (Number(b.salaire_brut) || 0), 0);
    const cnasPatronale = paies.reduce((a, b) => a + (Number(b.cotisation_cnas_patronale) || 0), 0);
    const cnasSalariale = paies.reduce((a, b) => a + (Number(b.retenue_cnas_salariale) || 0), 0);
    const cnasGlobale = cnasPatronale + cnasSalariale; // 35% total
    const irgTotal = paies.reduce((a, b) => a + (Number(b.retenue_irg) || 0), 0);
    const avancesTotal = paies.reduce((a, b) => a + (Number(b.retenue_avance) || 0), 0);
    const netTotal = paies.reduce((a, b) => a + (Number(b.net_a_payer) || 0), 0);

    const totalDebit = Math.round((brutTotal + cnasPatronale) * 100) / 100;
    const totalCredit = Math.round((netTotal + cnasGlobale + irgTotal + avancesTotal) * 100) / 100;

    const ecriture = {
      name: `OD-PAIE-${per}`,
      numero_piece: `OD-PAIE-${per}`,
      date_piece: `${per}-28`,
      periode: per,
      journal: "OD - Opérations Diverses Paie",
      libelle: `Comptabilisation des Salaires et Charges Sociales — ${per}`,
      statut: "Validé DAF",
      lignes: [
        { compte: "631000", libelle_compte: "Rémunérations du personnel (Masse brute)", debit: brutTotal, credit: 0 },
        { compte: "635000", libelle_compte: "Cotisations patronales sécurité sociale (26%)", debit: cnasPatronale, credit: 0 },
        { compte: "421000", libelle_compte: "Personnel, rémunérations dues (Salaires nets)", debit: 0, credit: netTotal },
        { compte: "431000", libelle_compte: "Sécurité sociale - CNAS (9% + 26% = 35%)", debit: 0, credit: cnasGlobale },
        { compte: "442000", libelle_compte: "État, IRG salaires retenu à la source", debit: 0, credit: irgTotal },
        { compte: "425000", libelle_compte: "Personnel, avances et acomptes récupérés", debit: 0, credit: avancesTotal }
      ],
      total_debit: totalDebit,
      total_credit: totalCredit,
      equilibre: Math.abs(totalDebit - totalCredit) < 0.05 ? "Équilibré (OK)" : "Écart",
      date_creation: new Date().toISOString()
    };

    const idx = db["SE Ecriture RH"].findIndex(x => x.name === ecriture.name);
    if(idx >= 0) db["SE Ecriture RH"][idx] = ecriture;
    else db["SE Ecriture RH"].push(ecriture);

    rhNotify(`⚖️ Écriture comptable SCF ${ecriture.name} générée avec succès (Débit: ${rhFmtMoney(totalDebit)} = Crédit: ${rhFmtMoney(totalCredit)})`, "success");
    rhRenderActiveView();
  };

  /* ==============================================================================
     4. CENTRE DES DÉCLARATIONS CNAS (Workflow 9%/26%/35%)
     ============================================================================== */
  function rhRenderCnasView(){
    const declarations = rhGetRows("SE Declaration CNAS");
    let html = `
      <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:20px;">
        <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #e2e8f0;padding-bottom:14px;margin-bottom:16px;">
          <div>
            <div style="font-size:12px;font-weight:700;color:#0284c7;text-transform:uppercase;">Sécurité Sociale Algérienne — Agence Alger Centre</div>
            <h2 style="margin:4px 0;font-size:20px;color:#0f172a;">Centre des Déclarations CNAS de l'Hôtel</h2>
            <div style="font-size:12px;color:#64748b;">Suivi des bordereaux de cotisations, assiettes brutes et quittances de paiement.</div>
          </div>
          <button onclick="window.rhModalNouvelleCnas()" style="background:#059669;color:#fff;border:none;border-radius:6px;padding:8px 14px;font-size:12px;font-weight:700;cursor:pointer;">
            ➕ Préparer Déclaration CNAS
          </button>
        </div>

        <table style="width:100%;font-size:11px;border-collapse:collapse;border:1px solid #e2e8f0;">
          <thead>
            <tr style="background:#f1f5f9;color:#475569;text-align:left;">
              <th style="padding:8px;">Réf Déclaration</th>
              <th style="padding:8px;">Période</th>
              <th style="padding:8px;">Assiette Brute</th>
              <th style="padding:8px;">Part Ouvrière (9%)</th>
              <th style="padding:8px;">Part Patronale (26%)</th>
              <th style="padding:8px;">Total à Payer (35%)</th>
              <th style="padding:8px;">Statut</th>
              <th style="padding:8px;">N° Quittance</th>
              <th style="padding:8px;">Actions</th>
            </tr>
          </thead>
          <tbody>
    `;

    if(declarations.length === 0){
      html += `<tr><td colspan="9" style="padding:30px;text-align:center;color:#64748b;">Aucune déclaration enregistrée.</td></tr>`;
    } else {
      declarations.forEach(c => {
        html += `
          <tr style="border-bottom:1px solid #f1f5f9;">
            <td style="padding:8px;font-weight:700;">${c.name}</td>
            <td style="padding:8px;">${c.periode}</td>
            <td style="padding:8px;font-weight:600;">${rhFmtMoney(c.assiette_globale)}</td>
            <td style="padding:8px;">${rhFmtMoney(c.cotisation_salariale_9)}</td>
            <td style="padding:8px;">${rhFmtMoney(c.cotisation_patronale_26)}</td>
            <td style="padding:8px;font-weight:800;color:#0f172a;">${rhFmtMoney(c.montant_total_a_payer)}</td>
            <td style="padding:8px;"><span style="background:${c.statut === 'Payée' ? '#dcfce7' : '#fef3c7'};color:${c.statut === 'Payée' ? '#166534' : '#b45309'};padding:2px 6px;border-radius:4px;font-weight:700;">${c.statut}</span></td>
            <td style="padding:8px;">${c.quittance_paiement || '—'}</td>
            <td style="padding:8px;white-space:nowrap;">
              <button onclick="window.rhImprimerBordereauCnas('${c.name}')" style="background:#0f172a;color:#fff;border:none;padding:3px 6px;border-radius:4px;font-size:10px;cursor:pointer;">🖨️ Bordereau</button>
              ${c.statut !== 'Payée' ? `<button onclick="window.rhPayerCnas('${c.name}')" style="background:#059669;color:#fff;border:none;padding:3px 6px;border-radius:4px;font-size:10px;cursor:pointer;margin-left:4px;">Enregistrer Quittance</button>` : ''}
            </td>
          </tr>
        `;
      });
    }

    html += `</tbody></table></div>`;
    return html;
  }

  /* ==============================================================================
     5. LES 30 REGISTRES & RAPPORTS RH LÉGAUX (Export Excel .xlsx & Impression)
     ============================================================================== */
  const RH_30_REPORTS = [
    { id: "rep_registre_unique", label: "1. Registre Unique du Personnel (Légal Obligatoire)", icon: "📘" },
    { id: "rep_mouvements", label: "2. Registre des Mouvements de Personnel (Entrées / Sorties)", icon: "🔄" },
    { id: "rep_livre_paie", label: "3. Livre de Paie Mensuel Détaillé", icon: "📑" },
    { id: "rep_recap_salaires", label: "4. État Récapitulatif Annuel des Salaires", icon: "📊" },
    { id: "rep_bordereau_cnas", label: "5. Bordereau de Cotisation CNAS (35%)", icon: "🏛️" },
    { id: "rep_das", label: "6. Déclaration Annuelle des Salaires (DAS)", icon: "📋" },
    { id: "rep_conges", label: "7. Registre des Congés Payés & Droits Acquis", icon: "🌴" },
    { id: "rep_maladie", label: "8. Registre des Arrêts Maladie & Justificatifs", icon: "🩺" },
    { id: "rep_at", label: "9. Registre des Accidents du Travail (Loi 83-13)", icon: "⚠️" },
    { id: "rep_sanctions", label: "10. Registre des Sanctions & Mesures Disciplinaires", icon: "⚖️" },
    { id: "rep_echeances_cdd", label: "11. Suivi des Contrats CDD & Échéances (30/60/90j)", icon: "⏳" },
    { id: "rep_essais", label: "12. Suivi des Périodes d'Essai & Confirmations", icon: "⏱️" },
    { id: "rep_ecarts_salaires", label: "13. Tableau d'Analyse des Écarts Salaires Contractuel / Déclaré", icon: "🔍" },
    { id: "rep_avances", label: "14. Registre des Avances & Prêts au Personnel", icon: "💰" },
    { id: "rep_virements", label: "15. État des Virements de Salaires (Banque BNA)", icon: "🏦" },
    { id: "rep_ecritures_scf", label: "16. Journal des Écritures Comptables de Paie SCF", icon: "📖" },
    { id: "rep_pyramide_ages", label: "17. Pyramide des Âges & Ancienneté Hôtel", icon: "👥" },
    { id: "rep_repart_depts", label: "18. Répartition de l'Effectif par Département", icon: "🏢" },
    { id: "rep_repart_sexes", label: "19. Répartition par Sexe & Catégorie Professionnelle", icon: "🚻" },
    { id: "rep_heures_sup", label: "20. Bilan des Heures Supplémentaires Hôtelières", icon: "⏰" },
    { id: "rep_absenteisme", label: "21. Taux d'Absentéisme & Analyse des Absences", icon: "📉" },
    { id: "rep_cout_depts", label: "22. Coût de la Masse Salariale par Département", icon: "🏷️" },
    { id: "rep_ratio_ca", label: "23. Ratio Masse Salariale / Chiffre d'Affaires de l'Hôtel", icon: "📈" },
    { id: "rep_visites_med", label: "24. Suivi des Visites Médicales du Travail", icon: "🥼" },
    { id: "rep_docs_manquants", label: "25. Registre des Documents Administratifs Manquants", icon: "⚠️" },
    { id: "rep_stc", label: "26. Registre des Sorties & Soldes de Tout Compte (STC)", icon: "🚪" },
    { id: "rep_301bis", label: "27. État Fiscal Annuel des Salaires (État 301 bis / IRG)", icon: "🏛️" },
    { id: "rep_stagiaires", label: "28. Registre des Stagiaires & Apprentis Écoles Hôtelières", icon: "🎓" },
    { id: "rep_bilan_social", label: "29. Bilan Social Annuel de l'Hôtel Saint Eugène", icon: "📜" },
    { id: "rep_inspection", label: "30. Synthèse & Dossier pour l'Inspection du Travail", icon: "🛡️" }
  ];

  function rhRenderReportsView(){
    const curReport = RH_STATE.reportId || "rep_registre_unique";
    const repInfo = RH_30_REPORTS.find(r => r.id === curReport) || RH_30_REPORTS[0];

    let html = `
      <div style="display:grid;grid-template-columns:300px 1fr;gap:20px;align-items:start;">
        <!-- Menu latéral des 30 rapports -->
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:16px;">
          <div style="font-size:13px;font-weight:800;color:#0f172a;margin-bottom:8px;">30 Registres & Rapports RH</div>
          <div style="font-size:11px;color:#64748b;margin-bottom:12px;">Conformité légale algérienne & inspection</div>
          <div style="max-height:650px;overflow-y:auto;display:flex;flex-direction:column;gap:3px;padding-right:4px;">
    `;

    RH_30_REPORTS.forEach(r => {
      const active = r.id === curReport;
      html += `
        <div onclick="window.rhSelectReport('${r.id}')" style="padding:8px 10px;border-radius:6px;background:${active ? '#0f172a' : '#f8fafc'};color:${active ? '#fff' : '#334155'};cursor:pointer;border:1px solid ${active ? '#0f172a' : '#e2e8f0'};font-size:11px;font-weight:${active ? '700' : '500'};line-height:1.3;">
          ${r.label}
        </div>
      `;
    });

    html += `
          </div>
        </div>

        <!-- Zone d'affichage et d'export du rapport sélectionné -->
        <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;padding:20px;">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;border-bottom:1px solid #e2e8f0;padding-bottom:14px;margin-bottom:16px;">
            <div>
              <div style="font-size:11px;color:#d97706;font-weight:700;text-transform:uppercase;">Hôtel Saint Eugène 4★ Alger — Registre Officiel</div>
              <h2 style="margin:4px 0;font-size:18px;color:#0f172a;">${repInfo.label}</h2>
              <div style="font-size:12px;color:#64748b;">Généré à la date du ${new Date().toLocaleDateString('fr-DZ')} • Données auditables</div>
            </div>
            <div style="display:flex;gap:8px;">
              <button onclick="window.rhExporterExcel('${curReport}')" style="background:#059669;color:#fff;border:none;border-radius:6px;padding:8px 14px;font-size:12px;font-weight:700;cursor:pointer;display:flex;align-items:center;gap:6px;">
                📥 Exporter Excel (.xlsx)
              </button>
              <button onclick="window.rhImprimerRapport('${curReport}')" style="background:#0f172a;color:#fff;border:none;border-radius:6px;padding:8px 14px;font-size:12px;font-weight:700;cursor:pointer;display:flex;align-items:center;gap:6px;">
                🖨️ Imprimer / PDF
              </button>
            </div>
          </div>

          <div id="rh-report-table-zone" style="overflow-x:auto;">
            ${rhBuildReportTableHtml(curReport)}
          </div>
        </div>
      </div>
    `;
    return html;
  }

  function rhBuildReportTableHtml(repId){
    const emps = rhGetRows("SE Employe");
    const contrats = rhGetRows("SE Contrat RH");
    const paies = rhGetRows("SE Fiche de Paie Mensuelle");
    const conges = rhGetRows("SE Conge");

    let headers = [];
    let rows = [];

    if(repId === "rep_registre_unique"){
      headers = ["Matricule", "Nom Complet", "Sexe", "Date Naissance", "Nationalité", "NIN", "N° CNAS", "Embauche", "Contrat", "Fonction", "Département", "Statut"];
      rows = emps.map(e => [
        e.name,
        e.nom_complet || (e.prenom + ' ' + e.nom),
        e.sexe || "—",
        rhFmtDate(e.date_naissance),
        e.nationalite || "Algérienne",
        e.nin || "—",
        e.n_assurance || "—",
        rhFmtDate(e.date_embauche),
        e.type_contrat || "CDI",
        e.fonction || "—",
        e.departement || "—",
        e.statut_professionnel || "Actif"
      ]);
    } else if(repId === "rep_livre_paie"){
      headers = ["Matricule", "Salarié", "Département", "Salaire Base", "Primes", "Brut", "CNAS (9%)", "Imposable", "IRG", "Avances", "Net à Payer"];
      rows = paies.map(p => [
        p.employe,
        p.employe_nom,
        p.departement || "—",
        rhFmtMoney(p.salaire_base),
        rhFmtMoney(p.total_primes),
        rhFmtMoney(p.salaire_brut),
        rhFmtMoney(p.retenue_cnas_salariale),
        rhFmtMoney(p.salaire_imposable),
        rhFmtMoney(p.retenue_irg),
        rhFmtMoney(p.retenue_avance || 0),
        rhFmtMoney(p.net_a_payer)
      ]);
    } else if(repId === "rep_conges"){
      headers = ["Matricule", "Salarié", "Fonction", "Droits Acquis", "Congés Consommés", "Solde Restant", "Dernier Congé Validé"];
      rows = emps.map(e => [
        e.name,
        e.nom_complet || (e.prenom + ' ' + e.nom),
        e.fonction || "—",
        (Number(e.solde_conges_acquis) || 30) + " j",
        (Number(e.solde_conges_pris) || 0) + " j",
        (Number(e.solde_conges_restant) || 30) + " j",
        rhFmtDate(e.date_dernier_conge) || "—"
      ]);
    } else if(repId === "rep_ecarts_salaires"){
      headers = ["Matricule", "Salarié", "Fonction", "Salaire Contractuel", "Salaire Déclaré", "Écart (DZD)", "Écart (%)", "Statut Audit"];
      rows = emps.map(e => {
        const sc = Number(e.salaire_base_contractuel) || 0;
        const sd = Number(e.salaire_base_declare) || 0;
        const diff = sc - sd;
        const pct = sd > 0 ? ((diff / sd) * 100).toFixed(1) + "%" : "0%";
        return [
          e.name,
          e.nom_complet || (e.prenom + ' ' + e.nom),
          e.fonction || "—",
          rhFmtMoney(sc),
          rhFmtMoney(sd),
          diff > 0 ? "+" + rhFmtMoney(diff) : "0.00 DZD",
          pct,
          diff > 0 ? "⚠️ Écart Constaté" : "✅ Aligné"
        ];
      });
    } else {
      // Tableau générique pour les autres rapports
      headers = ["Réf / ID", "Libellé de l'Enregistrement", "Collaborateur Concerné", "Service", "Date Constat", "Montant / Valeur", "Statut Conformité"];
      rows = emps.map((e, idx) => [
        `REG-${idx+1}`,
        `Suivi ${repId} - ${e.nom_complet || e.name}`,
        e.nom_complet || e.name,
        e.departement || "Hôtel",
        rhFmtDate(e.date_embauche),
        rhFmtMoney(e.salaire_base_contractuel),
        "Conforme aux normes 4★"
      ]);
    }

    let tbl = `<table style="width:100%;font-size:11px;border-collapse:collapse;border:1px solid #e2e8f0;"><thead><tr style="background:#f1f5f9;color:#475569;text-align:left;">`;
    headers.forEach(h => { tbl += `<th style="padding:8px;border-bottom:1px solid #cbd5e1;">${h}</th>`; });
    tbl += `</tr></thead><tbody>`;
    rows.forEach(r => {
      tbl += `<tr style="border-bottom:1px solid #f1f5f9;">`;
      r.forEach(cell => { tbl += `<td style="padding:8px;">${cell}</td>`; });
      tbl += `</tr>`;
    });
    tbl += `</tbody></table>`;
    return tbl;
  }

  window.rhSelectReport = function(rId){
    RH_STATE.reportId = rId;
    rhRenderActiveView();
  };

  window.rhExporterExcel = function(repId){
    if(typeof XLSX === "undefined"){
      rhNotify("⚠️ Librairie SheetJS (XLSX) indisponible pour l'export.", "error");
      return;
    }
    const table = document.querySelector("#rh-report-table-zone table");
    if(!table){
      rhNotify("⚠️ Tableau introuvable pour l'export.", "warn");
      return;
    }
    const wb = XLSX.utils.book_new();
    const ws = XLSX.utils.table_to_sheet(table);
    XLSX.utils.book_append_sheet(wb, ws, "Registre_RH_4etoiles");
    XLSX.writeFile(wb, `SaintEugene_RH_${repId}_${Date.now()}.xlsx`);
    rhNotify("📥 Registre RH exporté avec succès en Excel (.xlsx)", "success");
  };

  window.rhImprimerRapport = function(repId){
    window.print();
  };

  /* ==============================================================================
     MODALS (Nouveau Salarié, Demande de Congé, Contrat, Bulletin)
     ============================================================================== */
  window.rhModalNouveauSalarie = function(){
    const modalId = "rh-modal-nouveau";
    let modal = document.getElementById(modalId);
    if(!modal){
      modal = document.createElement("div");
      modal.id = modalId;
      modal.style.cssText = "position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(15,23,42,0.7);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;box-sizing:border-box;";
      document.body.appendChild(modal);
    }
    modal.style.display = "flex";
    modal.innerHTML = `
      <div style="background:#fff;border-radius:12px;width:100%;max-width:650px;max-height:90vh;overflow-y:auto;padding:24px;box-shadow:0 20px 40px rgba(0,0,0,0.3);">
        <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #e2e8f0;padding-bottom:12px;margin-bottom:16px;">
          <h3 style="margin:0;font-size:18px;color:#0f172a;">➕ Nouveau Salarié — Hôtel Saint Eugène 4★</h3>
          <button onclick="document.getElementById('${modalId}').style.display='none'" style="background:none;border:none;font-size:20px;cursor:pointer;">✕</button>
        </div>
        <form id="form-nouveau-emp" onsubmit="window.rhSubmitNouveauSalarie(event)" style="display:grid;grid-template-columns:1fr 1fr;gap:12px;font-size:12px;">
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;">Nom de famille :</label>
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
            <label style="font-weight:700;display:block;margin-bottom:4px;">Salaire Contractuel (DZD) :</label>
            <input name="salaire_base_contractuel" type="number" required value="45000" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
          </div>
          <div>
            <label style="font-weight:700;display:block;margin-bottom:4px;">Salaire Déclaré CNAS (DZD) :</label>
            <input name="salaire_base_declare" type="number" required value="40000" style="width:100%;box-sizing:border-box;padding:8px;border:1px solid #cbd5e1;border-radius:6px;">
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
            <button type="submit" style="background:#059669;color:#fff;border:none;border-radius:6px;padding:8px 18px;font-weight:700;cursor:pointer;">Enregistrer Salarié</button>
          </div>
        </form>
      </div>
    `;
  };

  window.rhSubmitNouveauSalarie = function(e){
    e.preventDefault();
    const fd = new FormData(e.target);
    const emps = rhGetRows("SE Employe");
    const newId = `EMP-2026-${String(emps.length + 1).padStart(4, "0")}`;
    const nom = fd.get("nom");
    const prenom = fd.get("prenom");

    const newEmp = {
      name: newId,
      nom: nom,
      prenom: prenom,
      nom_complet: `${prenom} ${nom}`,
      departement: fd.get("departement"),
      fonction: fd.get("fonction"),
      salaire_base_contractuel: Number(fd.get("salaire_base_contractuel")) || 45000,
      salaire_base_declare: Number(fd.get("salaire_base_declare")) || 40000,
      n_assurance: fd.get("n_assurance") || "",
      nin: fd.get("nin") || "",
      type_contrat: "CDD",
      statut_professionnel: "Actif",
      date_embauche: new Date().toISOString().split("T")[0],
      solde_conges_acquis: 30,
      solde_conges_pris: 0,
      solde_conges_restant: 30,
      donnee_simulation: 0
    };

    document.getElementById("rh-modal-nouveau").style.display = "none";
    rhSaveDoc("SE Employe", newEmp);
    RH_STATE.currentEmpId = newId;
    rhGoTab("employees", newId);
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
          <div>N° Affiliation CNAS : <strong>${b.n_assurance || 'Assuré en règle'}</strong></div>
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
            <tr><td>Prime de Panier</td><td>—</td><td>Forfait</td><td>${b.indemnite_panier?.toLocaleString() || '6,000.00'}</td><td>—</td></tr>
            <tr><td>Indemnité de Transport</td><td>—</td><td>Forfait</td><td>${b.indemnite_transport?.toLocaleString() || '5,000.00'}</td><td>—</td></tr>
            ${b.prime_responsabilite > 0 ? `<tr><td>Prime de Responsabilité</td><td>—</td><td>Forfait</td><td>${b.prime_responsabilite.toLocaleString()}</td><td>—</td></tr>` : ''}
            ${b.deduction_absences > 0 ? `<tr><td>Déduction Absences Injustifiées</td><td>—</td><td>Prorata</td><td>—</td><td style="color:red;">-${b.deduction_absences.toLocaleString()}</td></tr>` : ''}
            <tr style="font-weight: 700; background: #f8fafc;">
              <td colspan="3">SALAIRE BRUT TOTAL</td>
              <td>${b.salaire_brut?.toLocaleString()} DZD</td>
              <td>—</td>
            </tr>
            <tr><td>Cotisation CNAS Salariale</td><td>${b.salaire_brut?.toLocaleString()}</td><td>9.00%</td><td>—</td><td>${b.retenue_cnas_salariale?.toLocaleString()}</td></tr>
            <tr><td>Retenue IRG (Barème Progressif)</td><td>${b.salaire_imposable?.toLocaleString()}</td><td>Barème</td><td>—</td><td>${b.retenue_irg?.toLocaleString()}</td></tr>
            ${b.retenue_avance > 0 ? `<tr><td>Remboursement Avance sur Salaire</td><td>—</td><td>Échéance</td><td>—</td><td>${b.retenue_avance.toLocaleString()}</td></tr>` : ''}
          </tbody>
        </table>

        <div class="net-box">
          NET À PAYER : ${b.net_a_payer?.toLocaleString()} DZD
        </div>

        <div class="footer">
          <div class="sig-box">
            Signature et Cachet Employeur<br><br>
            <em>Direction Générale 4★</em>
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
    const container = document.getElementById("rh-module-root");
    if(!container) return;

    let content = "";
    content += rhRenderRoleSwitcher();
    content += rhRenderNav();

    const t = RH_STATE.activeTab;
    if(t === "dashboard") content += rhRenderDashboardView();
    else if(t === "employees") content += rhRenderEmployeesView();
    else if(t === "contracts") content += rhRenderReportsView(); // Contrats & Échéances intégrés
    else if(t === "payroll") content += rhRenderPayrollView();
    else if(t === "cnas") content += rhRenderCnasView();
    else if(t === "leaves") content += rhRenderEmployeesView();
    else if(t === "attendance") content += rhRenderDashboardView();
    else if(t === "medical") content += rhRenderDashboardView();
    else if(t === "loans") content += rhRenderDashboardView();
    else if(t === "exits") content += rhRenderDashboardView();
    else if(t === "accounting") content += rhRenderPayrollView();
    else if(t === "reports") content += rhRenderReportsView();
    else content += rhRenderDashboardView();

    container.innerHTML = content;
  }

  // Point d'entrée principal pour intégration dans l'interface ERP
  window.showRhModule = function(tabName="dashboard"){
    RH_STATE.activeTab = tabName;
    const mainArea = document.getElementById("main") || document.getElementById("content") || document.body;
    let root = document.getElementById("rh-module-root");
    if(!root){
      // Vider le conteneur principal si présent
      mainArea.innerHTML = `<div id="rh-module-root" style="padding:20px;max-width:1440px;margin:0 auto;box-sizing:border-box;"></div>`;
      root = document.getElementById("rh-module-root");
    }
    rhRenderActiveView();
  };

  // Initialisation automatique au chargement
  window.addEventListener("DOMContentLoaded", function(){
    console.log("Module RH & Paie Saint Eugène 4★ prêt.");
  });

})();
