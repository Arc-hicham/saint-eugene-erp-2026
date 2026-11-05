// =============================================================================
// 👥 LISTE DES UTILISATEURS & MOTS DE PASSE — HÔTEL SAINT EUGÈNE 4★
// =============================================================================
// Exactement 3 Rôles Officiels :
// 1. Administrateur (Accès Total & Supervision)
// 2. Utilisateur Normal (Création & Édition de ses propres documents, Sans Suppression)
// 3. Consultant (Lecture Seule & Impression A4 / PDF)
// =============================================================================

window.UTILISATEURS_CONFIG = [
  {
    "id": "USR-001",
    "name": "USR-001",
    "identifiant": "admin",
    "nom": "Hicham Bakir",
    "role": "Administrateur",
    "mot_de_passe": "1234",
    "email": "general.manager@sainteugenehotel.com"
  },
  {
    "id": "USR-002",
    "name": "USR-002",
    "identifiant": "user1",
    "nom": "Réception & Facturation",
    "role": "Utilisateur Normal",
    "mot_de_passe": "user2026",
    "email": "reception@sainteugenehotel.com"
  },
  {
    "id": "USR-003",
    "name": "USR-003",
    "identifiant": "consultant",
    "nom": "Audit & Contrôle Financier",
    "role": "Consultant",
    "mot_de_passe": "consultant2026",
    "email": "consultant@sainteugenehotel.com"
  }
];
