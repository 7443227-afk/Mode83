# Plan de travail — Nginx sécurisé comme passerelle QR vers Badge83

## Objectif

Mettre en place **Nginx comme point d’entrée unique, sécurisé et extensible** pour Badge83, avec une exposition publique strictement limitée au flux de vérification QR.

L’idée n’est pas seulement de placer un reverse proxy devant FastAPI, mais de transformer Nginx en **passerelle de contrôle d’accès** :

- HTTPS obligatoire ;
- exposition publique minimale ;
- ouverture externe limitée à la page de vérification QR ;
- blocage de l’accès direct aux autres routes ;
- possibilité d’ouvrir ensuite le portail de gestion uniquement après une vérification jugée conforme.

---

## 1. Rôle cible de Nginx

Nginx doit devenir la **façade réseau unique** de la machine pour Badge83, et potentiellement pour d’autres services à venir.

### Rôle attendu

- terminer les connexions HTTPS ;
- servir de reverse proxy vers le serveur FastAPI local ;
- masquer les ports applicatifs internes ;
- appliquer les premières règles de filtrage d’accès ;
- préparer une architecture réutilisable pour plusieurs applications sur le même hôte.

### Architecture visée

```text
Internet
   ↓
Nginx : 443 (HTTPS)
   ↓
FastAPI / Uvicorn : 127.0.0.1:8000
```

Dans cette logique :

- le port `443` devient l’unique point d’entrée public ;
- le port `8000` n’a plus vocation à être utilisé directement depuis Internet ;
- l’application FastAPI reste joignable localement par Nginx.

---

## 2. Exigence de sécurité réseau

### 2.1 HTTPS obligatoire

Le service public doit être publié derrière un certificat valide.

Option naturelle :

- Nginx + Let’s Encrypt.

Objectifs :

- chiffrement du trafic ;
- compatibilité mobile et navigateur ;
- suppression des avertissements de sécurité lors d’un scan QR.

### 2.2 Réduction de la surface exposée

Une fois Nginx en place :

- le trafic externe doit passer par Nginx ;
- le port applicatif `8000` doit être restreint à l’usage local ou privé ;
- le firewall doit être cohérent avec cette logique.

---

## 3. Politique d’exposition publique

Le principe retenu est :

> **La seule route publique d’entrée doit être la vérification QR.**

### Route à exposer publiquement

```text
/verify/qr/<assertion_id>
```

### Routes à ne pas exposer directement

Par défaut, l’accès externe doit être bloqué pour :

- `/`
- `/verify-desk`
- `/verify/badge/...`
- `/api/...`
- `/issue`
- `/issue-baked`
- les endpoints de gestion ou d’administration
- toute autre page interne non explicitement autorisée.

### Comportement attendu côté Nginx

Pour ces routes internes, plusieurs politiques sont possibles :

- retour `403 Forbidden` ;
- retour `404 Not Found` ;
- redirection vers une page publique neutre ;
- ou exposition sélective depuis un réseau privé uniquement.

Pour un premier déploiement, un **blocage explicite** est le plus simple et le plus robuste.

---

## 4. QR page comme passerelle contrôlée

La page mobile QR ne doit plus être pensée comme une simple page informative, mais comme une **passerelle de décision**.

### Rôle attendu

Après scan du QR :

1. l’utilisateur ouvre `/verify/qr/<assertion_id>` ;
2. le serveur évalue le badge ;
3. si le badge est jugé conforme, la page peut proposer un accès supplémentaire ;
4. sinon, l’accès reste limité à l’information de vérification.

Autrement dit, la page QR devient un **sas de filtrage fonctionnel**.

---

## 5. Condition d’ouverture vers le portail de gestion

Le besoin exprimé est le suivant :

- si la vérification montre un **bon QR** ;
- et si certaines conditions sont remplies ;
- alors la page peut ouvrir ensuite l’accès à un **portail de gestion**.

### Règles à formaliser

La notion de “bon QR” doit être définie côté serveur. Une base raisonnable serait :

- l’assertion existe ;
- le badge est considéré comme valide ;
- l’issuer est reconnu ;
- éventuellement : le badge est bien MODE83 ;
- éventuellement : le badge dispose bien de toutes les métadonnées attendues.

### Comportement souhaité

#### Si vérification positive

La page QR peut afficher :

- un signal visuel positif ;
- l’adresse email de l’administrateur ;
- un bouton ou lien vers le portail de gestion.

#### Si vérification négative

La page QR ne doit pas :

- montrer de lien vers le portail ;
- laisser croire qu’un accès de gestion est autorisé.

---

## 6. Email administrateur affiché après validation

Le besoin précise qu’en cas de bonne vérification, la page doit afficher **l’email de l’administrateur**, défini côté serveur.

### Recommandation

Ajouter une variable d’environnement, par exemple :

```text
BADGE83_ADMIN_EMAIL
```

Cette valeur serait :

- lue côté backend ;
- injectée dans le contexte de la page QR ;
- affichée uniquement si les conditions de validation sont remplies.

Cela évite :

- le hardcode dans le template ;
- la duplication de configuration ;
- les erreurs en cas de changement d’adresse.

---

## 7. Portail de gestion : lien direct ou accès conditionnel

Le besoin mentionne qu’après une bonne vérification, “s’ouvre déjà la page du portail de gestion”.

Deux niveaux de mise en œuvre sont possibles.

### Niveau 1 — MVP simple

La page QR affiche seulement :

- l’email admin ;
- un lien / bouton vers le portail.

Avantage :

- mise en place rapide.

Limite :

- la sécurité reste surtout ergonomique, pas forte.

### Niveau 2 — accès mieux contrôlé

La page QR peut déclencher :

- un lien signé ;
- un token temporaire ;
- une session de transition ;
- une redirection conditionnelle à durée limitée.

Avantage :

- meilleure séparation entre consultation publique et accès privilégié.

Pour un premier jalon, le **niveau 1** peut suffire, mais l’architecture devrait rester ouverte à une évolution vers le **niveau 2**.

---

## 8. Variables de configuration à prévoir

Pour rendre cette architecture propre et portable, il serait utile d’introduire au minimum :

- `BADGE83_BASE_URL`
- `BADGE83_ADMIN_EMAIL`
- `BADGE83_PORTAL_URL`

Éventuellement plus tard :

- `BADGE83_TRUSTED_ISSUER_ONLY`
- `BADGE83_REQUIRE_LOCAL_BADGE_FOR_PORTAL`
- `BADGE83_QR_GATEWAY_MODE`

Ces variables doivent être centralisées côté backend pour piloter le comportement sans modifier le code ou les templates à chaque fois.

---

## 9. Plan d’implémentation proposé

### Étape 1 — Installer et configurer Nginx

- installer Nginx sur la machine ;
- créer un `server` dédié au domaine public ;
- faire proxy vers FastAPI local ;
- préparer une structure extensible pour plusieurs services.

### Étape 2 — Activer HTTPS

- obtenir un certificat valide ;
- forcer la redirection HTTP → HTTPS ;
- vérifier que le scan QR ouvre bien une page sans alerte de sécurité.

### Étape 3 — Restreindre les routes publiques

- autoriser uniquement `/verify/qr/` ;
- bloquer les routes admin / API / dashboard ;
- vérifier les réponses réseau route par route.

### Étape 4 — Ajouter la logique de gateway dans le backend

- formaliser la notion de badge valide pour le portail ;
- injecter `BADGE83_ADMIN_EMAIL` et `BADGE83_PORTAL_URL` ;
- afficher ces éléments uniquement si la vérification est positive.

### Étape 5 — Durcir l’accès au serveur applicatif

- limiter l’exposition de `8000` ;
- s’assurer que l’entrée publique passe uniquement par Nginx ;
- vérifier la cohérence firewall / iptables / cloud rules.

### Étape 6 — Tester le flux complet

- scan QR → page mobile HTTPS ;
- QR valide → email admin + ouverture portail ;
- QR invalide → pas de lien portail ;
- accès direct aux routes internes → refusé.

---

## 10. Critères de réussite

La mise en place sera considérée comme réussie si :

- le domaine public répond en HTTPS ;
- seule la page QR est accessible publiquement ;
- les autres pages ne sont pas directement accessibles depuis Internet ;
- la page QR affiche un état visuel clair ;
- en cas de badge conforme, l’email administrateur est affiché ;
- l’accès au portail de gestion n’est proposé qu’après validation ;
- l’architecture reste compatible avec l’hébergement futur d’autres services sur la même machine.

---

## Résumé

Ce plan vise à faire de Nginx non seulement un reverse proxy, mais une **couche de sécurité et d’orchestration d’accès**.

Le résultat attendu est une architecture dans laquelle :

- le QR ouvre une page publique très maîtrisée ;
- le reste de l’application n’est pas exposé directement ;
- l’accès au portail de gestion devient conditionnel ;
- la machine est prête à héberger plusieurs services derrière un point d’entrée HTTPS unique.

   functi