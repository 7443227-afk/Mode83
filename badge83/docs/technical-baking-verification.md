# Documentation technique — Injection et vérification de badges Open Badges dans des fichiers PNG

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Structure de l'assertion Open Badges](#structure-de-lassertion-open-badges)
3. [Format PNG et chunks](#format-png-et-chunks)
4. [Processus d'injection (Baking)](#processus-dinjection-baking)
5. [Processus d'extraction (Unbaking)](#processus-dextraction-unbaking)
6. [Gestion des doublons](#gestion-des-doublons)
7. [Outils et bibliothèques utilisés](#outils-et-bibliothèques-utilisés)
8. [Flux complet d'émission et vérification](#flux-complet-démission-et-vérification)
9. [Exemples concrets](#exemples-concrets)
10. [Limites et perspectives](#limites-et-perspectives)

---

## Vue d'ensemble

Ce document décrit le mécanisme technique d'**injection** (*baking*) et d'**extraction** (*unbaking*) d'une assertion Open Badges 2.0 dans un fichier PNG. Le projet Badge83 implémente une version légère de la spécification Open Badges 2.0 en utilisant FastAPI, avec un stockage local des assertions au format JSON et une capacité d'intégration directe dans des images PNG.

### Principe

Le **baking** consiste à embarquer l'assertion JSON (qui contient les informations du badge, de l'émetteur et du destinataire) directement dans le fichier PNG, via un **chunk `tEXt`** conforme à la spécification PNG. Le chunk utilise le mot-clé `openbadges`, tel que défini par la spécification Open Badges 2.0.

L'image reste **visuellement identique** à l'originale. Les données sont stockées dans une section métadonnée du fichier, invisible pour l'utilisateur final.

---

## Structure de l'assertion Open Badges

L'assertion est un objet JSON conforme au modèle **Open Badges 2.0 Assertion**. Voici la structure produite par Badge83 :

```json
{
  "@context": "https://w3id.org/openbadges/v2",
  "id": "urn:uuid:<uuid-v4>",
  "type": "Assertion",
  "recipient": {
    "type": "email",
    "hashed": true,
    "identity": "<sha256(email)>",
    "plaintext_email": "utilisateur@example.org",
    "name": "Alice"
  },
  "issuedOn": "2025-04-13T10:30:00+00:00",
  "verification": {
    "type": "HostedBadge"
  },
  "badge": {
    "id": "https://mode83.example/badges/badge-83",
    "name": "Badge 83",
    "description": "Badge pédagogique pour démontrer les digital credentials.",
    "issuer": {
      "id": "https://mode83.example/issuers/main",
      "name": "MODE83",
      "url": "https://mode83.example"
    }
  },
  "issuer": {
    "id": "https://mode83.example/issuers/main",
    "name": "MODE83",
    "url": "https://mode83.example"
  }
}
```

### Champs principaux

| Champ | Description |
|-------|-------------|
| `@context` | URI du contexte Open Badges 2.0 |
| `id` | Identifiant unique de l'assertion (`urn:uuid:<v4>`) |
| `type` | Toujours `"Assertion"` |
| `recipient` | Destinataire du badge (email haché SHA-256 + données en clair) |
| `issuedOn` | Date d'émission au format ISO 8601 |
| `verification` | Mécanisme de vérification (`HostedBadge` = vérification via URL hébergée) |
| `badge` | Définition du badge (`BadgeClass`) avec son émetteur imbriqué |
| `issuer` | Profil de l'émetteur (répliqué à la racine pour conformité) |

### Hachage de l'email

L'email du destinataire est haché via **SHA-256** (normalisé : minuscules, espaces supprimés) :

```python
from hashlib import sha256
identity = sha256(email.strip().lower().encode("utf-8")).hexdigest()
```

Cela permet de vérifier l'appartenance du badge sans exposer l'email en clair dans le champ `identity`.

---

## Format PNG et chunks

Un fichier PNG est structuré en une série de **chunks** (blocs). Chaque chunk suit le format suivant :

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|   Length (4 octets, big-endian)                |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|   Chunk Type (4 octets ASCII)                  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|   Chunk Data (Length octets)                   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|   CRC (4 octets, CRC-32)                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Signature PNG

Tout fichier PNG valide commence par une **signature fixe** de 8 octets :

```
89 50 4E 47 0D 0A 1A 0A   (.PNG....)
```

### Chunks obligatoires

| Chunk | Description |
|-------|-------------|
| `IHDR` | En-tête de l'image (dimensions, couleur, etc.) — **doit être le premier chunk** |
| `IDAT` | Données de l'image compressées (peut y en avoir plusieurs) |
| `IEND` | Marqueur de fin — **doit être le dernier chunk** |

### Chunk `tEXt`

Le chunk `tEXt` est un chunk **auxiliaire** utilisé pour stocker des paires clé-valeur texte. Son format interne est :

```
<keyword>\x00<text>
```

- **keyword** : chaîne ASCII (latin-1), sans caractère nul
- **séparateur** : un octet nul (`\x00`)
- **text** : chaîne UTF-8 (peut contenir n'importe quel caractère UTF-8)

Dans le cadre d'Open Badges, le keyword est toujours **`openbadges`** et le text contient l'assertion JSON.

---

## Processus d'injection (Baking)

### Étapes

1. **Chargement du PNG source** — Lecture des octets du fichier PNG original (`data/badge.png` ou upload utilisateur).
2. **Suppression d'un chunk `openbadges` existant** — Pour éviter les doublons, on parcourt tous les chunks du PNG et on retire tout chunk `tEXt` dont le keyword est `openbadges`.
3. **Sérialisation de l'assertion** — L'assertion est convertie en JSON indenté (UTF-8).
4. **Construction du chunk `tEXt`** — On fabrique le chunk avec le keyword `openbadges` et le JSON comme payload, puis on calcule le CRC-32.
5. **Insertion avant `IEND`** — Le chunk est inséré juste avant le chunk `IEND` du PNG.
6. **Sauvegarde** — Le PNG baké est écrit dans `data/baked/<assertion_id>.png`.

### Détail de la construction du chunk

```python
import struct
import zlib

def _make_text_chunk(keyword: str, text: str) -> bytes:
    payload = keyword.encode("latin-1") + b"\x00" + text.encode("utf-8")
    chunk_type = b"tEXt"
    crc = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + chunk_type + payload + struct.pack(">I", crc)
```

- `struct.pack(">I", len(payload))` — Encode la longueur du payload en **big-endian** sur 4 octets.
- `zlib.crc32(chunk_type + payload) & 0xFFFFFFFF` — Calcule le **CRC-32** sur le type du chunk + le payload (la spécification PNG exige que le CRC couvre ces deux éléments).

### Insertion avant `IEND`

```python
def _insert_chunk_before_iend(png_data: bytes, chunk: bytes) -> bytes:
    idx = png_data.rfind(b"IEND")
    if idx == -1:
        return png_data + chunk
    insert_pos = idx - 4  # 4 octets avant IEND = champ Length de IEND
    return png_data[:insert_pos] + chunk + png_data[insert_pos:]
```

Le chunk est inséré juste avant le champ `Length` du chunk `IEND`, ce qui préserve la structure du fichier PNG.

---

## Processus d'extraction (Unbaking)

### Étapes

1. **Validation de la signature PNG** — Vérification que les 8 premiers octets correspondent à la signature PNG valide.
2. **Parcours des chunks** — Lecture séquentielle de chaque chunk (length → type → data → CRC).
3. **Recherche du chunk `openbadges`** — Pour chaque chunk `tEXt`, on extrait le keyword et on vérifie s'il correspond à `openbadges`.
4. **Extraction du JSON** — Le texte après le séparateur nul est décodé en UTF-8 et parsé comme JSON.
5. **Retour de l'assertion** — L'objet JSON est retourné pour vérification.

### Détail de l'extraction

```python
def unbake_badge(png_data: bytes) -> dict:
    if png_data[:8] != PNG_SIGNATURE:
        raise ValueError("Not a valid PNG file (bad signature)")

    pos = 8
    while pos + 8 <= len(png_data):
        length = struct.unpack(">I", png_data[pos:pos + 4])[0]
        chunk_type = png_data[pos + 4:pos + 8]
        chunk_end = pos + 4 + 4 + length + 4

        if chunk_type == b"tEXt":
            data = png_data[pos + 8:pos + 8 + length]
            nul_idx = data.find(b"\x00")
            if nul_idx != -1:
                kw = data[:nul_idx].decode("latin-1")
                if kw == OB_KEYWORD:  # "openbadges"
                    text = data[nul_idx + 1:].decode("utf-8")
                    return json.loads(text)

        pos = chunk_end

    raise ValueError("No Open Badges assertion found in this PNG")
```

---

## Gestion des doublons

Lors du baking, si le PNG source contient **déjà** un chunk `tEXt` avec le keyword `openbadges` (par exemple, un badge qui a été rebaké), ce chunk est **supprimé** avant l'insertion du nouveau.

Cela garantit qu'un PNG ne contient **jamais plus d'un seul chunk `openbadges`**, évitant les ambiguïtés lors de la vérification.

```python
def _remove_existing_ob_chunk(png_data: bytes) -> bytes:
    # Parcourt tous les chunks, saute le premier chunk tEXt avec keyword "openbadges"
    # Reconstruit le PNG sans ce chunk
```

---

## Outils et bibliothèques utilisés

| Composant | Outil / Bibliothèque | Rôle |
|-----------|---------------------|------|
| Framework API | **FastAPI** + **Uvicorn** | Serveur HTTP asynchrone, génération automatique de l'API OpenAPI |
| Modèles de données | **Pydantic** | Validation et typage des assertions (`Issuer`, `BadgeClass`, `Assertion`) |
| Manipulation PNG | **Python standard** (`struct`, `zlib`) | Construction et lecture des chunks PNG — **aucune dépendance externe** |
| Sérialisation JSON | **json** (stdlib) | Encodage/décodage des assertions |
| Hachage | **hashlib** (stdlib) | SHA-256 pour l'identité du destinataire |
| Templates | **Jinja2** | Page web d'interface utilisateur |
| Upload de fichiers | **python-multipart** | Parsing des formulaires `multipart/form-data` |

### Dépendances (`requirements.txt`)

```
fastapi
uvicorn
pydantic
jinja2
python-multipart
```

---

## Flux complet d'émission et vérification

### Émission (`POST /issue-baked`)

```
Utilisateur (name, email)
         │
         ▼
    ┌─────────────┐
    │   issuer.py │ ← Charge issuer.json et badgeclass.json
    └──────┬──────┘
           │ Crée l'assertion JSON
           ▼
    ┌─────────────┐
    │   baker.py  │ ← Bake l'assertion dans le PNG (chunk tEXt)
    └──────┬──────┘
           │ Retourne le PNG baké
           ▼
    Téléchargement du fichier `badge-<uuid>.png`
```

### Vérification locale (`POST /verify-baked`)

```
Fichier PNG uploadé
         │
         ▼
    ┌─────────────┐
    │   baker.py  │ ← Extrait l'assertion du chunk tEXt (unbake)
    └──────┬──────┘
           │ Vérifie le type "Assertion"
           ▼
    ┌──────────────┐
    │  verifier.py │ ← Retourne valid=true + résumé de l'assertion
    └──────┬───────┘
           ▼
    JSON de réponse
```

### Vérification par ID (`GET /verify/{badge_id}`)

```
badge_id
    │
    ▼
Recherche dans data/issued/{badge_id}.json
    │
    ▼
Si existe et type == "Assertion" → valid=true + données
Sinon → valid=false
```

---

## Exemples concrets

### 1. Émettre un badge baked

```bash
curl -X POST \
  -F "name=Alice" \
  -F "email=alice@example.org" \
  http://127.0.0.1:8000/issue-baked \
  --output badge-alice.png
```

Le fichier `badge-alice.png` est un PNG valide contenant l'assertion injectée.

### 2. Vérifier un badge baked

```bash
curl -X POST \
  -F "badge=@badge-alice.png" \
  http://127.0.0.1:8000/verify-baked
```

Réponse attendue :

```json
{
  "valid": true,
  "assertion": { ... },
  "summary": {
    "assertion_id": "...",
    "badge_name": "Badge 83",
    "issuer_name": "MODE83",
    "recipient_name": "Alice",
    "issued_on": "2025-04-13T10:30:00+00:00"
  }
}
```

### 3. Inspecter manuellement un chunk PNG

```python
from app.baker import unbake_badge

with open("badge-alice.png", "rb") as f:
    assertion = unbake_badge(f.read())

print(assertion["recipient"]["name"])  # → Alice
```

---

## Limites et perspectives

### Limites actuelles

| Aspect | Situation actuelle | Amélioration prévue |
|--------|-------------------|---------------------|
| Vérification externe | Locale uniquement (fichier PNG ou ID local) | Endpoints HTTP publics pour `HostedBadge` |
| Signature cryptographique | Aucune (JSON en clair dans le PNG) | Signature JWS (JSON Web Signature) |
| Stockage | Fichiers JSON locaux | Base de données ou stockage cloud |
| Ancrage temporel | Date d'émission système | Ancrage blockchain pour preuve d'immutabilité |
| Validation IMS | Non testée | Passage par `validator.openbadges.org` |

### Prochaines étapes

1. **Exposition d'endpoints publics** — Rendre les assertions accessibles via des URLs HTTP (ex. `https://mode83.example/badges/{id}`) pour permettre la validation externe.
2. **Signature JWS** — Signer les assertions avec une clé privée pour garantir leur intégrité et authenticité.
3. **Compatibilité validateur IMS** — Tester les badges produits avec le validateur officiel [validator.openbadges.org](https://validator.openbadges.org).
4. **Hébergement sécurisé** — Mettre en place HTTPS, CORS, et contrôle d'accès pour les endpoints sensibles.
