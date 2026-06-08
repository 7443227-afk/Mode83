# Badge83 — Modèle d'ancrage par hash et preuve locale

Date : 08/06/2026  
Projet : Badge83  
Objet : documentation du mécanisme de preuve locale préparant un ancrage blockchain optionnel

---

## 1. Principe général

Badge83 reste d'abord une plateforme Open Badges : l'émission, le PNG baked, la vérification QR et les endpoints HostedBadge doivent fonctionner sans blockchain.

Le mécanisme ajouté introduit une couche de preuve locale :

```text
Assertion Open Badges
  ↓
Payload canonique stable
  ↓
Hash SHA-256
  ↓
Preuve locale SQLite
  ↓ plus tard, optionnellement
Ancrage blockchain du hash uniquement
```

La blockchain n'est pas une dépendance nécessaire pour émettre ou vérifier un badge. Elle devient seulement une couche de preuve d'existence ou d'immutabilité si un opérateur décide de l'activer plus tard.

Principe de conception :

> Hash d'abord. Ancrage plus tard. Vérification toujours possible. Dégradation gracieuse.

---

## 2. Données on-chain et off-chain

### Données qui restent off-chain

Badge83 ne doit jamais publier sur blockchain :

- nom du titulaire ;
- email ;
- assertion JSON complète ;
- PNG du badge ;
- détails pédagogiques personnels ;
- raison de révocation détaillée ;
- notes opérateur ;
- secrets applicatifs ou clés privées.

### Donnée qui peut être ancrée plus tard

La seule donnée prévue pour un ancrage blockchain est une empreinte opaque :

```text
sha256:<hexadecimal_digest>
```

Ce hash est calculé à partir d'un payload canonique. Il ne permet pas, à lui seul, de retrouver le nom ou l'email du titulaire.

---

## 3. Canonicalisation

Le service de canonicalisation se trouve dans :

```text
app/proofs/canonical.py
```

Il construit une représentation JSON stable avec clés triées, séparateurs compacts et encodage UTF-8.

Champs retenus si présents :

```text
@context
schema_version
id
type
recipient
badge
issuer
issuedOn
expires
verification
field_values
badge83_template
```

Champs volontairement exclus :

```text
admin_recipient
search
canonical_payload
credential_hash
anchoring_status
```

Cette séparation évite de mélanger données publiques, données opérateur et métadonnées de preuve.

---

## 4. Hash déterministe

Le service de hash se trouve dans :

```text
app/proofs/hash_service.py
```

Algorithme :

```text
SHA-256(UTF-8(JSON canonique))
```

Format retourné :

```text
sha256:<digest_hexadécimal>
```

Propriétés attendues :

- la même assertion produit le même hash ;
- l'ordre des clés JSON ne change pas le hash ;
- changer `admin_recipient` ne change pas le hash ;
- changer `search` ne change pas le hash ;
- changer `recipient.identity` change le hash ;
- changer `issuedOn` change le hash.

---

## 5. Modèle de preuve locale

Le modèle se trouve dans :

```text
app/proofs/models.py
```

Structure logique :

```json
{
  "assertion_id": "<uuid>",
  "proof_version": "badge83-proof-v1",
  "hash_algorithm": "sha256",
  "canonicalization": "json-rfc8785-lite-v1",
  "credential_hash": "sha256:...",
  "canonical_payload": "{...}",
  "anchoring_status": "not_requested",
  "created_at": "..."
}
```

Le champ `canonical_payload` est conservé localement pour audit technique, mais il n'est pas exposé sur les pages publiques ni par l'endpoint admin ajouté.

---

## 6. Persistance SQLite

La table ajoutée au registre local est :

```sql
credential_proofs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  assertion_id TEXT UNIQUE NOT NULL,
  proof_version TEXT NOT NULL,
  hash_algorithm TEXT NOT NULL,
  canonicalization TEXT NOT NULL,
  credential_hash TEXT UNIQUE NOT NULL,
  canonical_payload TEXT NOT NULL,
  anchoring_status TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

Le repository se trouve dans :

```text
app/proofs/repository.py
```

Il permet la sauvegarde d'une preuve, la mise à jour par `assertion_id`, la recherche par `assertion_id` et la recherche par `credential_hash`.

---

## 7. Création automatique lors de l'émission

Lorsqu'un badge est émis, Badge83 crée maintenant une preuve locale pour :

- `issue_badge` ;
- `issue_baked_badge` ;
- `issue_baked_badge_from_template`.

La création est volontairement non bloquante. Si le registre de preuve est indisponible, Badge83 journalise l'erreur et continue l'émission du badge.

---

## 8. API administrateur

Endpoint ajouté :

```text
GET /api/badges/{assertion_id}/proof
```

Accès : administrateur uniquement.

Réponse :

```json
{
  "assertion_id": "...",
  "proof_version": "badge83-proof-v1",
  "hash_algorithm": "sha256",
  "canonicalization": "json-rfc8785-lite-v1",
  "credential_hash": "sha256:...",
  "anchoring_status": "not_requested",
  "created_at": "...",
  "updated_at": "..."
}
```

Le payload canonique n'est pas retourné pour éviter une exposition inutile.

---

## 9. Affichage public de la preuve

Les pages publiques suivantes affichent maintenant un résumé de preuve locale :

```text
GET /verify/badge/{assertion_id}
GET /verify/qr/{assertion_id}
```

États possibles :

| Statut | Signification |
|--------|---------------|
| `matches` | le hash courant de l'assertion correspond à la preuve stockée |
| `mismatch` | l'assertion a changé depuis la création de la preuve |
| `missing` | aucune preuve locale n'existe encore pour cette assertion |
| `unavailable` | le registre de preuve n'est pas accessible |

Le statut Open Badges existant n'est pas remplacé. La preuve locale est une information supplémentaire.

---

## 10. Limites actuelles

Ce qui est déjà présent :

- hash déterministe ;
- preuve locale ;
- stockage SQLite ;
- création automatique à l'émission ;
- endpoint administrateur ;
- affichage public du statut de preuve ;
- détection simple d'incohérence si l'assertion est modifiée après preuve.

Ce qui n'est pas encore présent :

- révocation locale ;
- audit trail complet ;
- file d'attente d'ancrage ;
- smart contract ;
- transaction testnet ;
- vérification blockchain publique.

---

## 11. Étapes suivantes recommandées

1. Ajouter un modèle de révocation locale.
2. Ajouter un journal d'audit pour émission, preuve, révocation et ancrage.
3. Ajouter une table `anchoring_transactions` sans dépendance blockchain.
4. Ajouter un provider `noop` puis un provider `mock`.
5. Créer un smart contract isolé hors du runtime Badge83.
6. Ajouter un provider EVM derrière feature flag uniquement après validation.