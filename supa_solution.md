**Livrable : CLAUDE.md pour un projet SaaS Next.js + SQLite**

**Introduction**

Bienvenue dans ce projet de création d'un modèle de code (CLAUDE.md) pour un projet SaaS réalisé avec Next.js 15 App Router et SQLite (better-sqlite3 ou Turbo). Notre objectif est de fournir une solution opiniée, production-prête et personnalisable pour les développeurs qui cherchent à créer des applications web robustes et maintenables.

**Structure du projet**

```markdown
claudé/
├── config/
│   ├── db.js
│   └── apiRoutes.js
├── components/
│   ├── Layout.js
│   └── ...
├── models/
│   ├── user.js
│   └── ...
├── pages/
│   ├── index.js
│   └── ...
├── public/
│   ├── images/
│   └── ...
├── scripts/
│   ├── db-migrate.js
│   └── ...
└── utils/
    ├── auth.js
    └── ...
```

**Nomenclature et conventions**

* Les noms de fichiers et de dossiers suivent le modèle de PascalCase (FirstLetterCapital).
* Les variables et les fonctions sont définies avec du nom minuscule et séparées par des underscore.
* Les erreurs sont traitées avec des messages explicites et des codes HTTP appropriés.

**Règles de migration**

```markdown
# Règles de migration

* Lorsqu'une table est modifiée, la nouvelle version est mise à jour dans la base de données avant d'appliquer les changements.
* Les migrations sont appliquées en fonction de l'ordre de modification (ASC).
```

**Commandes de développement**

```markdown
# Commandes de développement

* `npm run dev`: démarrage du serveur de développement avec les fichiers modifiés
* `npm run build`: construction des fichiers statiques pour le serveur de production
* `npm run db-migrate`: application des migrations à la base de données
```

**Anti-pattes à éviter**

* Utiliser `const` au lieu de `let` pour les variables qui ne sont pas modifiées.
* Utiliser des fonctions anonymes pour les traitements de données complexes.
* Utiliser des bibliothèques non mises à jour régulièrement.

**Conclusion**

Le présent modèle de code CLAUDE.md fournit une base solide pour la création d'applications web robustes et maintenables avec Next.js 15 App Router et SQLite. Les règles de migration, les commandes de développement et les anti-pattes à éviter contribuent à garantir la qualité et la sécurité des applications.

**Tests**

Pour tester ce modèle de code, vous pouvez créer un nouveau projet Next.js 15 et copier le contenu du fichier `claudé.md` dans le répertoire `.gitignore`. Ensuite, exécutez les commandes suivantes :

```bash
npm run dev
```

```bash
npm run build
```

```bash
npm run db-migrate
```

Si tout fonctionne correctement, vous devriez voir la page de votre application web avec les données stockées dans la base de données.

**Note**

Le présent modèle de code est une solution opiniée et peut être personnalisé en fonction des besoins spécifiques de votre projet. Il est recommandé de faire preuve de flexibilité et d'adapter les règles à vos besoins pour maximiser l'efficacité et la sécurité de votre application.