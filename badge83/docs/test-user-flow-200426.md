# Test user flow — 20/04/26

## 1. Contexte

Cette note documente le **nouveau scénario de démonstration utilisateur** mis en place dans Badge83 en réponse aux remarques du tuteur sur l’usage concret du projet.

L’objectif n’est plus seulement de prouver que l’application sait :

- émettre une assertion Open Badges ;
- stocker un JSON et éventuellement un PNG baked ;
- exposer des endpoints techniques ;

mais aussi de montrer qu’un **utilisateur non technique** peut suivre un parcours crédible :

1. un badge est émis ;
2. il apparaît dans un registre ;
3. il peut être consulté via une page dédiée ;
4. cette page fournit des éléments de confiance lisibles ;
5. cette URL peut ensuite devenir une cible naturelle pour un QR code.

---

## 2. Objectif du test

Valider un scénario simple, démontrable et réutilisable lors d’une capture vidéo ou d’une soutenance courte.

Le scénario retenu est volontairement minimal :

- **cas d’usage** : badge de formation ;
- **acteur principal** : administrateur / émetteur ;
- **acteur secondaire** : tiers vérificateur (recruteur, formateur, évaluateur, employeur) ;
- **sortie attendue** : une page de vérification claire à partir d’un identifiant de badge.

---

## 3. Éléments implémentés

### 3.1. Nouvelle page de vérification publique orientée humain

Une nouvelle route HTML a été ajoutée :

- `/verify/badge/{assertion_id}`

Cette page n’est pas pensée comme une sortie brute d’API, mais comme une **vue de confiance lisible par un humain**.

Elle affiche :

- le statut du badge ;
- l’identifiant de l’assertion ;
- le nom du badge ;
- le nom de l’émetteur ;
- la date d’émission ;
- l’identité du recipient quand elle est présente dans les données ;
- la présence d’un JSON local ;
- la présence éventuelle d’un PNG baked ;
- l’URL d’assertion hébergée ;
- les actions rapides vers JSON / PNG / raw assertion.

### 3.2. Liaison depuis le registre

Le registre existant a été enrichi avec :

- un bouton `Verify` dans chaque ligne du tableau ;
- un lien `Open verification page` dans la zone inspecteur ;
- un rappel de l’URL de vérification dans les métadonnées du badge sélectionné.

Ainsi, le flow devient immédiat :

- on trouve un badge ;
- on le sélectionne ;
- on ouvre la page publique correspondante ;
- on bascule d’un usage admin vers un usage démonstratif / public.

### 3.3. Recherche et filtres dans le registre

Le registre a aussi été renforcé pour répondre à l’idée de recherche et filtrage évoquée dans le retour du tuteur.

Les améliorations ajoutées sont :

- recherche texte libre ;
- filtre `JSON uniquement` ;
- filtre `PNG uniquement` ;
- filtre `Hosted ready uniquement`.

La recherche est faite côté interface sur les données déjà retournées par `/api/badges`.

Champs exploitables dans la recherche :

- `assertion_id` ;
- `badge_name` ;
- `issuer_name` ;
- `recipient.identity` ;
- plus généralement tout le contenu utile de l’objet de badge déjà chargé côté client.

---

## 4. Parcours utilisateur documenté

## 4.1. Scénario de départ

Exemple retenu :

- badge de formation ;
- émis pour un apprenant fictif ;
- consulté ensuite par un tiers.

Exemple de données :

- `name = Alice Martin`
- `email = alice@example.org`

### 4.2. Étape 1 — Émission du badge

Depuis le `Control Center`, l’administrateur remplit le formulaire d’émission.

Deux modes restent disponibles :

- émission d’une assertion JSON ;
- émission d’un PNG baked.

Résultat attendu :

- création d’une assertion dans `data/issued/` ;
- création éventuelle d’un PNG dans `data/baked/` ;
- apparition immédiate du badge dans le registre après rafraîchissement automatique.

### 4.3. Étape 2 — Consultation dans le registre

Le badge apparaît dans la table avec :

- son identifiant ;
- sa date ;
- son type de badge ;
- le recipient ;
- les assets disponibles.

À ce stade, l’utilisateur admin peut :

- chercher le badge par ID ;
- filtrer le registre ;
- ouvrir le détail technique ;
- ouvrir directement la page de vérification publique.

### 4.4. Étape 3 — Ouverture de la verification page

L’utilisateur clique sur :

- `Verify` dans la ligne du registre ;
ou
- `Open verification page` depuis l’inspecteur.

Le navigateur ouvre :

- `/verify/badge/{assertion_id}`

### 4.5. Étape 4 — Lecture par un tiers

Sur cette page, un tiers doit pouvoir comprendre rapidement :

- qu’il s’agit bien d’une page de vérification officielle du projet ;
- si le badge existe dans le registre ;
- quel badge est concerné ;
- qui l’a émis ;
- quand il a été émis ;
- quels fichiers ou ressources brutes sont disponibles.

Cette page sert donc de **point d’entrée de vérification lisible**, en complément des endpoints plus techniques.

---

## 5. Informations visibles sur la page de vérification

La page de vérification a été pensée autour de deux catégories d’information.

### 5.1. Informations de synthèse

Informations visibles immédiatement :

- `Verification status`
- `Assertion ID`
- `Badge`
- `Issuer`
- `Issued on`
- `Recipient identity`

Ces informations répondent à la question :

> « Quel badge est-ce, qui l’a émis, et cette page confirme-t-elle son existence ? »

### 5.2. Signaux de confiance

Une section `Trust signals` présente des éléments plus interprétables :

- assertion enregistrée localement ou non ;
- disponibilité d’un PNG baked ;
- présence d’une URL d’assertion hébergée ;
- URL exacte de la verification page.

Ces éléments sont utiles pour justifier la crédibilité de la page, même si cette étape ne remplace pas encore une validation cryptographique complète.

### 5.3. Actions rapides

La page donne aussi accès à des actions simples :

- téléchargement du JSON ;
- téléchargement du PNG s’il existe ;
- ouverture de la raw assertion.

Cela permet de combiner :

- une lecture simple pour un humain ;
- et un accès plus technique si nécessaire.

---

## 6. Gestion des cas d’erreur

Un cas `badge not found` a été prévu.

Si l’identifiant demandé n’existe pas dans le registre local :

- la route retourne une page HTML dédiée ;
- le statut HTTP renvoyé est `404` ;
- le message affiché indique clairement que le badge n’a pas été trouvé.

Cela est important pour éviter qu’une URL invalide renvoie simplement une erreur technique peu lisible.

---

## 7. Intérêt produit / démonstration

Cette évolution apporte plusieurs bénéfices concrets.

### 7.1. Réponse directe au retour du tuteur

Elle répond explicitement aux axes mentionnés :

- vérifier un badge simplement ;
- préparer un usage par lien ou QR code ;
- clarifier les informations visibles ;
- enrichir le registre avec recherche et filtrage ;
- raisonner en parcours utilisateur.

### 7.2. Meilleur support pour une capture vidéo

Le scénario est maintenant plus naturel à montrer :

1. émission ;
2. apparition dans le registre ;
3. ouverture de la page de vérification ;
4. lecture des informations de confiance.

Le résultat est plus convaincant visuellement qu’une démonstration limitée à des réponses JSON brutes.

### 7.3. Base claire pour le QR code

La page `/verify/badge/{id}` devient une **cible MVP idéale** pour un futur QR code.

Le QR pourra ensuite pointer vers :

- une URL stable ;
- une page compréhensible ;
- une interface cohérente avec le parcours réel de vérification.

---

## 8. Vérification technique réalisée

Validation effectuée dans l’environnement virtuel du projet :

- chargement de l’application FastAPI via `.venv/bin/python` ;
- test de l’endpoint `/api/badges` ;
- récupération d’un badge existant ;
- ouverture de `/verify/badge/{id}` ;
- vérification de la présence du titre de page et de l’identifiant dans la réponse HTML.

Résultat observé :

- `/api/badges` répond avec succès ;
- la nouvelle page de vérification répond avec le statut `200` sur un badge existant ;
- l’identifiant du badge est bien visible dans la page rendue.

---

## 9. Limites actuelles

Cette étape reste un **MVP fonctionnel**, pas encore une vérification avancée complète.

Limites actuelles :

- la page repose sur l’état du registre local ;
- elle ne remplace pas une validation cryptographique ;
- elle n’intègre pas encore de QR code visuel ;
- elle ne présente pas encore d’informations étendues comme `evidence`, `expires`, `alignment` ou `endorsement`.

---

## 10. Prochaines étapes recommandées

### Priorité 1 — QR code

Ajouter un QR code qui pointe vers :

- `/verify/badge/{assertion_id}`

### Priorité 2 — Enrichissement de la page

Afficher, si présents :

- `expires` ;
- `evidence` ;
- `alignment` ;
- éventuellement le type de vérification Open Badges.

### Priorité 3 — Export du registre

Ajouter un export :

- JSON ;
- puis CSV si nécessaire.

### Priorité 4 — Scénario utilisateur plus complet

Tester explicitement un flow de type :

- création ;
- émission ;
- consultation titulaire ;
- vérification par un tiers.

### Priorité 5 — Réflexion sur une base de données locale

Préparer une réflexion technique sur l’introduction d’une **base de données locale** pour remplacer progressivement une partie du stockage par fichiers.

Points à étudier :

- quels objets doivent rester en fichiers et lesquels doivent passer en base ;
- si une base légère de type SQLite suffit pour la suite du prototype ;
- comment stocker les métadonnées admin, les index de recherche et l’historique d’émission ;
- comment conserver la compatibilité avec les assertions JSON et les PNG baked déjà présents ;
- comment préparer une migration simple depuis `data/issued/` et `data/baked/`.

---

## 11. Résumé court

Le projet dispose maintenant d’un **chemin de démonstration cohérent et crédible** :

- un badge est émis ;
- il apparaît dans le registre ;
- il peut être retrouvé par recherche / filtres ;
- il possède une page de vérification publique lisible ;
- cette page peut servir de base directe à une future intégration QR.

En termes de produit, c’est une amélioration importante car elle relie enfin les capacités techniques du prototype à un usage compréhensible par un humain non spécialiste.

---

## 12. Extension récente — Bureau de vérification pour secrétariat

Une seconde couche UX a été ajoutée après le scénario initial :

- une page spécifique `/verify-desk`

Cette page a été conçue pour un usage administratif simple, par exemple par une secrétaire ou une personne chargée d’un contrôle documentaire rapide.

### Objectif

Réduire la vérification à un parcours très court :

1. charger un badge PNG ;
2. voir immédiatement l’aperçu du badge ;
3. lancer la vérification ;
4. lire les informations essentielles ;
5. voir s’il existe d’autres certificats liés.

### Informations affichées

Le *Bureau de vérification* affiche désormais :

- l’aperçu du PNG chargé ;
- l’identifiant de l’assertion ;
- le nom / prénom ;
- l’email ;
- le nom du badge ;
- l’issuer simplifié (`mode83` ou `autre organisme`) ;
- l’organisation émettrice simplifiée (`mode83` ou `autre organisme`) ;
- la date de délivrance au format `JJ/MM/AAAA`.

### Comportement vis-à-vis de l’issuer

Le système distingue deux cas :

#### Cas 1 — badge émis par MODE83

La page indique :

- `Issuer : mode83`
- `Organisation émettrice : mode83`
- message : `Badge émis par mode83`

#### Cas 2 — badge valide mais émis par un autre organisme

La page indique :

- `Issuer : autre organisme`
- `Organisation émettrice : autre organisme`
- message : `Badge valide, mais émis par un autre organisme`

Cela permet d’éviter un faux négatif dans le cas où le badge serait correct, mais externe à MODE83.

### Certificats liés

Le bloc `Autres certificats liés` a été enrichi pour afficher, quand l’information est disponible :

- l’identifiant ;
- le nom ;
- l’email ;
- le badge ;
- l’issuer ;
- la date au format `JJ/MM/AAAA` ;
- le type de rapprochement (`email`, `name` ou les deux).

### Nommage des PNG baked

Le nom du fichier PNG téléchargé lors de l’émission baked suit désormais la convention :

- `{numéro}_mode83_{jjmmaaa}.png`

Exemple :

- `37_mode83_200426.png`

Cette convention facilite :

- l’archivage ;
- la lecture humaine ;
- l’identification rapide d’un badge émis par MODE83.