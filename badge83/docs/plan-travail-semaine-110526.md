# Plan de travail Badge83 — semaine du 11/05/2026

Date de préparation : 11/05/2026  
Projet : Badge83 — Open Badges MODE83  
Référence principale : `formation/cahier_charges_stagiaire_mode83.pdf`

## 1. État général du projet au 11/05/2026

Badge83 n'est plus seulement un prototype technique. Le projet dispose déjà d'un noyau Open Badges fonctionnel et d'une interface opérateur avancée : émission d'assertions, génération de PNG baked, QR code visible, vérification publique, registre local, constructeur de modèles, édition de modèles et premières protections d'accès.

Par rapport au cahier des charges stagiaire, le **Projet A — Open Badges MODE83** est presque entièrement réalisé sur le plan fonctionnel. Le travail restant concerne surtout la stabilisation, la validation formelle, la documentation utilisateur et la préparation d'une décision claire sur le démarrage du **Projet B — Ancrage Blockchain**.

## 2. Correspondance avec le cahier des charges

### 2.1 Projet A — Open Badges MODE83

| Livrable demandé | État actuel | Priorité |
|---|---|---|
| Documentation de référence Open Badges MODE83 | README, documents techniques, plans et rapports existants | À consolider |
| Fichiers JSON Issuer et BadgeClass | Présents dans `badge83/data/` avec endpoints publics | Fait |
| Émission d'une Assertion | Routes `/issue` et `/issue-baked`, logique dans `app/issuer.py` | Fait |
| Badge PNG baked | Baking PNG avec chunk `openbadges` | Fait |
| Page ou endpoint de vérification publique | Routes `/verify`, `/verify/badge`, `/verify/qr`, `/verify-desk` | Fait |
| Guide formateur MODE83 | Guides partiels existants, mais pas encore guide final unique | À faire |
| Dépôt Git documenté | README et historique de commits existants | Fait |
| Tests sur plusieurs badges/formations | Tests automatisés existants ; parcours complet final à documenter | À faire |
| Validation officielle Open Badges / IMS | Validation partielle documentée ; vérification officielle à poursuivre | À faire |

**Conclusion Projet A :** environ 85–90 % réalisé. La priorité est de transformer l'état fonctionnel en livrable validable : tests finaux, documentation formateur, rapport de validation et correction des anomalies visibles.

### 2.2 Projet B — Ancrage Blockchain

Le Projet B n'est pas encore engagé dans le code.

Éléments encore absents :

- calcul et workflow dédiés au hash SHA-256 d'une assertion pour ancrage blockchain ;
- smart contract Solidity ;
- environnement Hardhat ;
- déploiement testnet Polygon ;
- connexion Python ↔ smart contract via `web3.py` ;
- vérification on-chain depuis la page de vérification.

**Conclusion Projet B :** ne pas démarrer avant stabilisation et validation formelle du Projet A.

### 2.3 Projet C — Vision professionnelle

Badge83 dépasse déjà le minimum du Projet A sur plusieurs points :

- interface d'administration ;
- registre SQLite local ;
- recherche et consultation des badges ;
- constructeur de modèles visuels ;
- personnalisation des fonds PNG ;
- modification, duplication et suppression de modèles ;
- page QR mobile ;
- protection par authentification côté Nginx/auth_request ;
- réflexion sur l'émission groupée CSV/XLSX.

Ces éléments sont utiles, mais ils ne doivent pas détourner la semaine de l'objectif principal : livrer et valider proprement le Projet A.

## 3. Risques et points d'attention

### 3.1 Erreur SQLite observée dans les logs

Le fichier `server.log` montre des erreurs intermittentes :

```text
sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread
```

Routes concernées observées :

```text
/badge-constructor/schemas
/badge-constructor/templates
```

C'est le principal risque technique immédiat. Même si l'erreur ne bloque pas tous les usages, elle doit être corrigée avant une démonstration ou une validation formelle.

### 3.2 Documentation formateur incomplète

Le cahier des charges demande un guide lisible par un formateur ou un opérateur non technique. La documentation existante est riche, mais encore dispersée.

### 3.3 Risque de dispersion fonctionnelle

Les pistes suivantes sont utiles mais ne doivent pas devenir prioritaires avant la clôture Projet A :

- émission groupée Excel/CSV ;
- BadgeClass dynamique par programme ;
- intégration blockchain complète ;
- refonte complète de l'interface.

## 4. Objectif principal de la semaine

**Stabiliser Badge83 et fermer le Projet A comme livrable démontrable, testable et documenté.**

Critères de réussite de la semaine :

1. les tests automatisés passent ;
2. l'erreur SQLite/threading est corrigée ou documentée avec solution ;
3. un parcours complet d'émission et vérification est testé sur plusieurs badges ;
4. un guide formateur v1 est rédigé ;
5. un rapport de validation Projet A est prêt ;
6. la décision de démarrage Projet B peut être prise avec le référent.

## 5. Plan de travail de la semaine

### Lundi 11/05 — Stabilisation technique

Objectif : corriger ou isoler le principal risque technique.

Actions :

1. Vérifier l'état du serveur Badge83 avec `./badge83.sh status`.
2. Lancer la suite de tests automatisés :

   ```bash
   cd /home/ubuntu/projects/Mode83/badge83
   /home/ubuntu/projects/Mode83/.venv/bin/python -m pytest tests -q
   ```

3. Analyser les fichiers liés à l'erreur SQLite :

   ```text
   badge83/app/database.py
   badge83/app/routes/badge_constructor/schemas.py
   badge83/app/routes/badge_constructor/templates.py
   ```

4. Corriger la gestion des connexions SQLite si nécessaire.
5. Relancer les tests et vérifier les routes du constructeur.
6. Rédiger un court rapport de stabilisation.

Livrable attendu :

```text
badge83/docs/rapport-travail-110526-stabilisation.md
```

### Mardi 12/05 — Validation fonctionnelle Projet A

Objectif : prouver le fonctionnement complet du parcours Open Badges.

Actions :

1. Tester au moins cinq émissions de badges ou scénarios de badges.
2. Pour chaque badge, vérifier :
   - assertion JSON créée ;
   - PNG baked généré ;
   - QR code lisible ;
   - page publique de vérification ;
   - extraction/vérification du PNG baked.
3. Documenter les résultats, commandes et anomalies.
4. Vérifier si possible avec un validateur Open Badges externe.

Livrable attendu :

```text
badge83/docs/test-report-projet-a-120526.md
```

### Mercredi 13/05 — Guide formateur MODE83

Objectif : produire le guide utilisateur demandé dans le cahier des charges.

Contenu recommandé :

1. accès à Badge83 ;
2. choix ou création d'un modèle ;
3. émission d'un badge individuel ;
4. téléchargement et remise du PNG à l'apprenant ;
5. vérification par page publique ;
6. vérification par QR code ;
7. vérification par dépôt de PNG ;
8. erreurs fréquentes et actions à faire ;
9. limites à ne pas modifier sans référent technique.

Livrable attendu :

```text
badge83/docs/guide-formateur-mode83.md
```

### Jeudi 14/05 — Finitions interface opérateur

Objectif : améliorer uniquement les points UX prioritaires pour un usage réel.

Actions prioritaires :

1. rendre le registre plus lisible : titulaire, email, badge, date, état PNG/JSON ;
2. améliorer la carte de résultat après émission ;
3. masquer les détails JSON bruts derrière une zone “détails techniques” ;
4. vérifier la page QR mobile sur smartphone ou écran étroit ;
5. documenter les changements.

Livrable attendu :

```text
badge83/docs/rapport-travail-140526-ux-operateur.md
```

### Vendredi 15/05 — Rapport de validation et décision Projet B

Objectif : préparer la revue avec le référent.

Actions :

1. Rédiger un rapport de validation Projet A.
2. Lister clairement :
   - fonctionnalités livrées ;
   - tests passés ;
   - limites connues ;
   - risques résiduels ;
   - démonstration prévue.
3. Décider avec le référent si le Projet B est engagé.
4. Si Projet B est validé, préparer seulement un cadrage technique initial : architecture, outils, sécurité des clés, stockage du hash uniquement.

Livrable attendu :

```text
badge83/docs/rapport-validation-projet-a-150526.md
```

## 6. Plan détaillé pour aujourd'hui — lundi 11/05/2026

### Priorité 1 — Vérifier l'état réel du projet

Commandes proposées :

```bash
cd /home/ubuntu/projects/Mode83
git status --short
```

```bash
cd /home/ubuntu/projects/Mode83/badge83
./badge83.sh status
```

Résultat attendu : connaître l'état Git, savoir si le serveur tourne et confirmer la configuration utilisée.

### Priorité 2 — Relancer les tests automatisés

Commande :

```bash
cd /home/ubuntu/projects/Mode83/badge83
/home/ubuntu/projects/Mode83/.venv/bin/python -m pytest tests -q
```

Résultat attendu : confirmer que la base existante reste stable avant correction.

### Priorité 3 — Corriger l'erreur SQLite/threading

Fichiers à examiner :

```text
badge83/app/database.py
badge83/app/routes/badge_constructor/schemas.py
badge83/app/routes/badge_constructor/templates.py
```

Hypothèse principale : une connexion SQLite est créée dans un thread puis fermée dans un autre par la gestion des dépendances FastAPI.

Solutions possibles à évaluer :

1. créer une connexion par requête ;
2. utiliser `check_same_thread=False` lors de `sqlite3.connect` si l'architecture le justifie ;
3. éviter toute connexion SQLite globale partagée ;
4. protéger les écritures concurrentes si nécessaire.

Critère de réussite : les routes du constructeur ne produisent plus d'erreur 500 liée à SQLite dans le scénario courant.

### Priorité 4 — Vérifier manuellement les routes critiques

Routes à contrôler après correction :

```text
/
/api/badges
/badge-constructor/schemas
/badge-constructor/templates
/verify/qr/{assertion_id}
```

Selon la configuration d'authentification, certains tests peuvent être faits via navigateur plutôt que `curl`.

### Priorité 5 — Documenter la journée

Créer un rapport court :

```text
badge83/docs/rapport-travail-110526-stabilisation.md
```

Structure recommandée :

1. objectif du jour ;
2. état initial ;
3. erreur observée ;
4. correction appliquée ;
5. tests exécutés ;
6. résultat ;
7. prochaines actions.

## 7. Ce qu'il ne faut pas faire aujourd'hui

Pour rester aligné avec le cahier des charges et sécuriser la livraison Projet A, il est déconseillé aujourd'hui de :

- commencer l'intégration blockchain complète ;
- implémenter l'émission groupée Excel/CSV ;
- modifier le format des assertions Open Badges ;
- refondre entièrement l'interface ;
- ajouter des dépendances sans besoin immédiat ;
- exposer davantage de données personnelles dans les pages publiques.

## 8. Décision recommandée

La semaine doit être traitée comme une semaine de **consolidation Projet A**.

La bonne séquence est :

1. stabiliser ;
2. tester ;
3. documenter ;
4. valider ;
5. seulement ensuite démarrer Projet B.

Si l'erreur SQLite est corrigée rapidement et que les tests Projet A sont concluants, Badge83 pourra être présenté comme livrable principal conforme au cahier des charges, avec une option réaliste de démarrage blockchain en fin de semaine.