# Documentation technique — Injection et vérification de badges Open Badges dans des fichiers PNG

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Structure de l'assertion Open Badges](#structure-de-lassertion-open-badges)
3. [Format PNG et chunks](#format-png-et-chunks)
4. [Analyse de la vérification PNG par openbadges-validator-core](#analyse-de-la-vérification-png-par-openbadges-validator-core)
5. [Processus d'injection (Baking)](#processus-dinjection-baking)
6. [Processus d'extraction (Unbaking)](#processus-dextraction-unbaking)
7. [Gestion des doublons](#gestion-des-doublons)
8. [Outils et bibliothèques utilisés](#outils-et-bibliothèques-utilisés)
9. [Flux complet d'émission et vérification](#flux-complet-démission-et-vérification)
10. [Exemples concrets](#exemples-concrets)
11. [Limites et perspectives](#limites-et-perspectives)

---

## Vue d'ensemble

Ce document décrit le mécanisme technique d'**injection** (*baking*) et d'**extraction** (*unbaking*) d'une assertion Open Badges 2.0 dans un fichier PNG. Le projet Badge83 implémente une version légère de la spécification Open Badges 2.0 en utilisant FastAPI, avec un stockage local des assertions au format JSON, des endpoints publics de type **HostedBadge**, et une capacité d'intégration directe dans des images PNG.

### Principe

Le **baking** consiste à embarquer l'assertion JSON (qui contient les informations du badge, de l'émetteur et du destinataire) directement dans le fichier PNG, via un **chunk `tEXt`** conforme à la spécification PNG. Le chunk utilise le mot-clé `openbadges`, tel que défini par la spécification Open Badges 2.0.

L'image reste **visuellement identique** à l'originale. Les données sont stockées dans une section métadonnée du fichier, invisible pour l'utilisateur final.

---

## Structure de l'assertion Open Badges

L'assertion est un objet JSON conforme au modèle **Open Badges 2.0 Assertion**. Voici la structure actuellement produite par Badge83 :

```json
{
  "@context": "https://w3id.org/openbadges/v2",
  "id": "http://<serveur>:8000/assertions/<uuid-v4>",
  "type": "Assertion",
  "url": "http://<serveur>:8000/assertions/<uuid-v4>",
  "recipient": {
    "type": "email",
    "hashed": true,
    "salt": "<sel-aléatoire>",
    "identity": "sha256$<sha256(email-normalisé+salt)>"
  },
  "issuedOn": "2025-04-13T10:30:00+00:00",
  "verification": {
    "type": "HostedBadge",
    "url": "http://<serveur>:8000/assertions/<uuid-v4>"
  },
  "badge": "http://<serveur>:8000/badges/blockchain-foundations",
  "issuer": "http://<serveur>:8000/issuers/main"
}
```

### Champs principaux

| Champ | Description |
|-------|-------------|
| `@context` | URI du contexte Open Badges 2.0 |
| `id` | Identifiant public de l'assertion (`http://.../assertions/<uuid>`) |
| `type` | Toujours `"Assertion"` |
| `url` | URL publique de l'assertion, utilisée pour la vérification hébergée |
| `recipient` | Destinataire du badge (email haché SHA-256) |
| `issuedOn` | Date d'émission au format ISO 8601 |
| `verification` | Mécanisme de vérification (`HostedBadge`) avec URL de l'assertion |
| `badge` | URL publique du `BadgeClass` |
| `issuer` | URL publique du profil `Issuer` |

### Hachage de l'email

L'email du destinataire est haché via **SHA-256** (normalisé : minuscules, espaces supprimés) :

```python
from hashlib import sha256
identity = sha256(email.strip().lower().encode("utf-8")).hexdigest()
```

Cela permet de vérifier l'appartenance du badge sans exposer l'email en clair dans le champ `identity`. Le préfixe `sha256$` est conservé afin de respecter le format attendu par le validateur Open Badges.

### Usage du `salt`

Badge83 ajoute désormais un `salt` aléatoire par assertion dans `recipient`.

- le hash est calculé sur `email_normalisé + salt` ;
- deux badges émis pour le même email produisent ainsi des `identity` différentes ;
- cela limite la corrélation entre badges et complique les attaques par dictionnaire.

Le champ `salt` est optionnel dans le validateur, mais recommandé pour améliorer la confidentialité des destinataires.

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

## Analyse de la vérification PNG par openbadges-validator-core

Le validateur `openbadges-validator-core` ne réimplémente pas lui-même un parseur PNG complet pour retrouver l'assertion. Pour l'entrée de type fichier image, il délègue l'extraction des métadonnées Open Badges à la bibliothèque **`openbadges_bakery`** via l'appel `unbake(...)`.

### Ce que le validateur vérifie côté image

L'analyse du code montre trois niveaux distincts :

1. **Détection d'une entrée fichier baked**
   - dans `openbadges/verifier/verifier.py`, la fonction `verification_store()` appelle `unbake(badge_input)` quand l'entrée est un fichier ;
   - si aucune assertion n'est retrouvée dans l'image, la vérification échoue immédiatement.

2. **Traitement d'une ressource image distante ou embarquée**
   - dans `openbadges/verifier/tasks/input.py`, `process_baked_resource()` accepte uniquement des images déclarées en `image/png` ou `image/svg+xml` ;
   - le contenu est ensuite passé à `openbadges_bakery.unbake(...)` pour extraire l'assertion éventuelle.

3. **Validation du champ `image` des objets Open Badges**
   - dans `openbadges/verifier/tasks/images.py`, le validateur contrôle surtout le **type MIME** et la capacité à récupérer l'image ;
   - pour un `BadgeClass.image`, il accepte PNG et SVG ;
   - pour une `Assertion.image`, les `data:` URI ne sont pas autorisées ;
   - cette étape ne valide pas la présence d'un chunk `openbadges` dans l'image décorative du badge, elle vérifie seulement que la ressource image est acceptable.

### Conséquence pratique

Pour un badge PNG baked, l'exigence principale du validateur est donc la suivante :

- le fichier doit être un **PNG valide** ;
- il doit contenir une métadonnée Open Badges que `openbadges_bakery.unbake(...)` sait extraire ;
- le JSON extrait doit ensuite être valide au regard du modèle Open Badges 2.0.

Autrement dit, la vérification se fait en deux temps :

1. **structure binaire du PNG suffisamment correcte pour permettre l'unbake** ;
2. **structure sémantique de l'assertion JSON** conforme à Open Badges.

### Structure réellement observée dans un PNG produit par Badge83

L'inspection d'un fichier généré par Badge83 (`data/baked/8eca1166-162f-4761-96fe-8f8366b709be.png`) donne la séquence de chunks suivante :

| Ordre | Chunk | Longueur | Observation |
|------:|-------|---------:|-------------|
| 1 | `IHDR` | 13 | En-tête PNG standard |
| 2 | `IDAT` | 6436 | Données image compressées |
| 3 | `tEXt` | 658 | Keyword `openbadges`, payload JSON UTF-8 |
| 4 | `IEND` | 0 | Fin de fichier PNG |

Contrôles observés :

- signature PNG valide (`89 50 4E 47 0D 0A 1A 0A`) ;
- présence d'un unique chunk `tEXt` avec le mot-clé **`openbadges`** ;
- chunk inséré juste avant `IEND`, ce qui respecte la structure générale du fichier PNG ;
- JSON embarqué décodable et contenant les clés :
  `@context`, `id`, `type`, `url`, `recipient`, `issuedOn`, `verification`, `badge`, `issuer`.

### Correspondance avec les attentes du validateur

Le PNG produit par Badge83 est cohérent avec la façon dont `openbadges-validator-core` traite une image baked :

- ✅ **format binaire PNG valide** ;
- ✅ **métadonnée Open Badges présente** dans un chunk texte `openbadges` ;
- ✅ **assertion extraite sous forme de JSON valide** ;
- ✅ **assertion Open Badges 2.0 hosted** exploitable ensuite par le pipeline JSON-LD du validateur.

### Point d'attention

Le code de Badge83 sait lire à la fois `tEXt` et `iTXt` lors de l'unbaking local, alors que les PNG actuellement produits utilisent exclusivement **`tEXt`**. C'est un bon choix de compatibilité :

- production simple et compatible ;
- lecture tolérante vis-à-vis de badges plus anciens ou d'autres producteurs.

---

## Processus d'injection (Baking)

### Étapes

1. **Chargement du PNG source** — Lecture des octets du fichier PNG original (`data/badge.png` ou upload utilisateur).
2. **Suppression d'un chunk `openbadges` existant** — Pour éviter les doublons, on parcourt tous les chunks du PNG et on retire tout chunk `tEXt` dont le keyword est `openbadges`.
3. **Sérialisation de l'assertion** — L'assertion est convertie en JSON compact UTF-8.
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
3. **Recherche du chunk `openbadges`** — Pour chaque chunk `tEXt` ou `iTXt`, on extrait le keyword et on vérifie s'il correspond à `openbadges`.
4. **Extraction du JSON** — Le texte est décodé en UTF-8 puis parsé comme JSON.
5. **Retour de l'assertion** — L'objet JSON est retourné pour vérification locale ou distante.

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

Lors du baking, si le PNG source contient **déjà** un chunk `tEXt` ou `iTXt` avec le keyword `openbadges` (par exemple, un badge qui a été rebaké), ce chunk est **supprimé** avant l'insertion du nouveau.

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
| Modèles de données | **Pydantic** | Modèles applicatifs et validation de certaines entrées |
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
    │   issuer.py │ ← Charge les templates `issuer_template.json` et `badgeclass_template.json`
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

### Vérification hébergée (`POST /verify-online`)

``` 
URL d'assertion ou PNG baked
         │
         ▼
    ┌─────────────┐
    │ main.py     │ ← Récupère l'assertion puis résout `badge` et `issuer`
    └──────┬──────┘
           │
           ├── GET /badges/blockchain-foundations
           ├── GET /issuers/main
           └── contrôle de cohérence de la chaîne
           ▼
    JSON de synthèse de validation
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
| Vérification externe | Endpoints publics disponibles + test `openbadges-validator-core` réussi | Généraliser les tests publics HTTPS |
| Signature cryptographique | Aucune (JSON en clair dans le PNG) | Signature JWS (JSON Web Signature) |
| Stockage | Fichiers JSON locaux | Base de données ou stockage cloud |
| Ancrage temporel | Date d'émission système | Ancrage blockchain pour preuve d'immutabilité |
| Validation IMS | Compatibilité démontrée avec `openbadges-validator-core` | Vérifications complémentaires sur le validateur public IMS |

### Prochaines étapes

1. **HTTPS et domaine dédié** — Publier les ressources sur un domaine stable et sécurisé.
2. **Signature JWS** — Signer les assertions avec une clé privée pour garantir leur intégrité et authenticité.
3. **Campagne de validation externe** — Tester régulièrement les badges produits avec plusieurs validateurs compatibles Open Badges.
4. **Nettoyage documentaire** — Harmoniser les anciens exemples encore fondés sur des objets imbriqués ou des URN.
