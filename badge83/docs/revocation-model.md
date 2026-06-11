# Badge83 — Modèle de révocation locale

Date : 11/06/2026  
Statut : modèle local, sans blockchain obligatoire

---

## Objectif

Badge83 distingue maintenant trois notions :

- l'existence de l'assertion Open Badges ;
- la cohérence de la preuve locale par hash ;
- le statut de révocation locale du credential.

La révocation locale permet d'indiquer qu'un badge précédemment émis ne doit
plus être considéré comme actif, sans supprimer l'historique et sans modifier la
logique Open Badges existante.

---

## Suppression vs révocation

La suppression retire un fichier ou une entrée du registre. Elle est utile pour
des opérations techniques ou des erreurs de gestion, mais elle détruit une partie
de la traçabilité.

La révocation conserve le credential vérifiable et ajoute un statut explicite :

```text
credential actif
credential révoqué
```

Une credential révoquée peut donc rester consultable afin d'expliquer son état.
C'est important pour les vérificateurs : ils peuvent confirmer que le badge a
bien existé, mais qu'il n'est plus actif.

---

## Données stockées

La table locale `credential_revocations` stocke uniquement :

```text
assertion_id
revoked
reason_category
actor
created_at
updated_at
```

Les catégories publiques autorisées sont :

```text
erreur_emission
demande_titulaire
expiration_admin
fraude
autre
```

La raison détaillée ne doit pas être publiée dans cette table. Elle peut contenir
des informations personnelles, disciplinaires ou administratives sensibles. La
page publique affiche seulement une catégorie contrôlée.

---

## Affichage public

Les pages suivantes affichent le statut local :

```text
/verify/badge/{assertion_id}
/verify/qr/{assertion_id}
```

Le statut de révocation est additionnel. Il ne remplace pas :

- la validité Open Badges ;
- la preuve locale Badge83 ;
- l'état d'ancrage blockchain.

Exemple de lecture attendue :

```text
Statut credential : actif / révoqué
Preuve locale : cohérente / incohérente / absente
Ancrage blockchain : not_requested / unavailable / anchored plus tard
```

---

## API administrateur

Endpoints locaux protégés par authentification admin :

```text
POST /api/badges/{assertion_id}/revoke
GET /api/badges/{assertion_id}/revocation
```

Le `POST` accepte une charge JSON minimale :

```json
{
  "reason_category": "erreur_emission",
  "actor": "admin"
}
```

Si la catégorie n'est pas reconnue, elle est normalisée en `autre`.

---

## Relation future avec la blockchain

La révocation locale reste la source de vérité immédiate dans Badge83. Une future
révocation blockchain pourra ancrer un hash ou un événement de révocation, mais
elle ne doit pas publier :

- le nom du titulaire ;
- l'email ;
- la raison détaillée ;
- le contenu complet de l'assertion.

Le futur modèle blockchain devra donc ancrer uniquement des empreintes ou des
événements non personnels.
