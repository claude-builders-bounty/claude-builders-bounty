# Résumé hebdo — claude-builders-bounty (1–7 sept. 2026)

> Exemple de sortie Claude `claude-sonnet-4-20250514` postée sur Discord par ce workflow. Données GitHub simulées.

**Faits saillants**
- 4 commits sur `main`, dont le déclencheur planifié et les nœuds de lecture GitHub.
- Issue #5 (ce bounty) : 6 nouveaux commentaires ; 2 anciennes issues clôturées.
- PR #12 mergée : squelette du workflow de résumé hebdomadaire.

**Commits (4)**
- `abc1234` feat : déclencheur planifié (cron ven. 17h)
- `def5678` feat : lecture commits/issues/PRs via API GitHub publique
- `9012abc` feat : prompt Claude EN/FR
- `3456def` fix : troncature webhook Discord à 1800 caractères

**Issues clôturées (2)**
- #3 Docs d'installation n8n en local — clôturée par @alice
- #4 Choix Discord vs email — clôturée, Discord retenu par défaut

**PRs mergées (1)**
- #12 Ajout du workflow de résumé hebdomadaire — mergée le 5 sept. par @alice

**Risques / Prochaines étapes**
- Surveiller le quota GitHub non authentifié (60 req/h) ; ajouter un token si l'activité augmente.
- Ensuite : capturer la capture d'import 2 minutes et activer la planification.
