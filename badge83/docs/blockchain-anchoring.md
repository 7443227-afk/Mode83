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

## 10. File d'ancrage locale et providers

Badge83 dispose maintenant d'une file locale d'ancrage sans dépendance réseau :

```text
app/proofs/anchoring.py
app/proofs/anchoring_repository.py
app/proofs/anchoring_providers.py
app/proofs/anchoring_service.py
```

La table `anchoring_transactions` enregistre les demandes et leur cycle de vie :

```text
queued → pending → anchored
```

Statuts supportés :

```text
queued
pending
anchored
failed
retry_scheduled
```

Trois providers existent maintenant :

- `noop` : provider désactivé, retourne un échec contrôlé sans contacter de réseau ;
- `mock` : provider de démonstration, simule un ancrage réussi en local ;
- `evm` : provider optionnel, désactivable, qui publie uniquement le digest `bytes32` sur un contrat EVM compatible.

Le provider `mock` renseigne notamment :

```text
provider = mock
network = local-demo
tx_hash = mock:<fragment_hash>
block_number = <id_transaction_locale>
```

Ce provider ne publie rien sur une blockchain. Il sert uniquement à démontrer le cycle applicatif complet.

Le provider `evm` reste séparé du runtime principal : il importe `web3` uniquement au moment d'ancrer une transaction et retourne un échec contrôlé si la configuration ou la dépendance optionnelle manque.

Variables d'environnement prévues :

```text
BADGE83_ANCHORING_PROVIDER=mock
BADGE83_EVM_RPC_URL=
BADGE83_EVM_CHAIN_ID=
BADGE83_EVM_CONTRACT_ADDRESS=
BADGE83_EVM_PRIVATE_KEY=
BADGE83_EVM_NETWORK_LABEL=hardhat-local
BADGE83_EVM_CONFIRMATION_TIMEOUT_SECONDS=120
```

Les dépendances EVM ne sont pas dans `requirements.txt`. Elles s'installent seulement si l'opérateur active l'ancrage réel :

```bash
pip install -r requirements-blockchain.txt
```

En cas de succès, le provider retourne une référence compatible avec les transactions locales :

```json
{
  "status": "anchored",
  "provider": "evm",
  "network": "hardhat-local",
  "tx_hash": "0x...",
  "block_number": 123
}
```

En cas de configuration absente, de RPC indisponible ou de dépendance `web3` non installée, Badge83 ne casse pas au démarrage et la transaction passe en `failed` avec un message explicite.

---

## 11. Service d'ancrage et audit

Le service `AnchoringService` orchestre :

1. la récupération de la preuve locale ;
2. la création d'une transaction `queued` ;
3. le passage en `pending` ;
4. l'appel au provider ;
5. la transition finale `anchored` ou `failed` ;
6. l'enregistrement des événements d'audit.

Événements d'audit ajoutés :

```text
anchoring_requested
anchoring_completed
anchoring_failed
```

Une preuve absente provoque une erreur contrôlée : l'ancrage n'est pas demandé et le système ne casse pas l'émission ni la vérification existante.

---

## 12. API administrateur d'ancrage local

Endpoints ajoutés :

```text
POST /api/badges/{assertion_id}/anchor
GET /api/badges/{assertion_id}/anchoring
```

Accès : administrateur uniquement.

Le endpoint `POST` crée une demande d'ancrage locale et, par défaut, la traite immédiatement avec le provider demandé. Le provider recommandé pour la démonstration est `mock`. Si `provider` est omis, Badge83 utilise `BADGE83_ANCHORING_PROVIDER`, dont la valeur par défaut reste `mock`.

Exemple de corps :

```json
{
  "provider": "mock",
  "actor": "admin",
  "process": true
}
```

Pour demander explicitement un ancrage EVM réel, utiliser un corps séparé afin de ne pas confondre démonstration locale et transaction blockchain :

```json
{
  "provider": "evm",
  "actor": "admin",
  "process": true
}
```

Le provider EVM n'envoie au contrat que le digest converti en `bytes32`, jamais `assertion_id`, nom, email, assertion JSON, PNG, payload canonique ou données opérateur.

Réponse simplifiée attendue :

```json
{
  "assertion_id": "...",
  "transaction": {
    "status": "anchored",
    "provider": "mock",
    "network": "local-demo",
    "tx_hash": "mock:...",
    "block_number": 1
  }
}
```

---

## 13. Affichage public enrichi

Les pages publiques de vérification affichent maintenant un résumé de l'ancrage local :

```text
GET /verify/badge/{assertion_id}
GET /verify/qr/{assertion_id}
```

Informations affichées lorsque disponibles :

- statut local (`not_requested`, `queued`, `pending`, `anchored`, `failed`, `retry_scheduled`) ;
- libellé lisible ;
- provider ;
- réseau local simulé ;
- référence `tx_hash` mock.

Le libellé reste volontairement `Ancrage local` pour éviter de laisser croire à une publication blockchain réelle.

---

## 14. Limites actuelles

Ce qui est déjà présent :

- hash déterministe ;
- preuve locale ;
- stockage SQLite ;
- création automatique à l'émission ;
- endpoint administrateur ;
- affichage public du statut de preuve ;
- détection simple d'incohérence si l'assertion est modifiée après preuve ;
- révocation locale ;
- audit trail ;
- file d'attente d'ancrage locale ;
- provider `noop` ;
- provider `mock` ;
- smart contract minimal `Badge83Anchor` dans `blockchain/` ;
- provider `evm` optionnel avec imports `web3` lazy ;
- configuration EVM optionnelle ;
- tests unitaires du provider EVM sans réseau réel ;
- API administrateur d'ancrage local ;
- affichage public du statut d'ancrage local.

Ce qui n'est pas encore présent :

- transaction testnet ;
- vérification blockchain publique.

---

## 15. Étapes suivantes recommandées

1. Tester l'intégration locale complète avec Hardhat node, contrat déployé et variables `BADGE83_EVM_*`.
2. Documenter le flux EVM de bout en bout dans une page dédiée.
3. Ajouter une action UI distincte pour l'ancrage blockchain réel, sans remplacer le bouton local `mock`.
4. Préparer plus tard une vérification blockchain publique du hash, sans publier de donnée personnelle on-chain.
