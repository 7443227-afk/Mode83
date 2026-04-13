# Plan — Endpoints publics pour la vérification en ligne (HostedBadge)

## Contexte

Les assertions Open Badges émises par Badge83 utilisent le type de vérification **`HostedBadge`**. Un validateur externe (ex. `validator.openbadges.org`) doit pouvoir accéder aux URLs référencées dans l'assertion via HTTP/HTTPS.

**État actuel** : les URLs pointent vers `https://mode83.example` — un domaine fictif non accessible.

**Solution temporaire** : utiliser l'IP du serveur de test comme base de toutes les URLs.

---

## Problème

| Ressource | URL actuelle | Accessible ? |
|-----------|-------------|-------------|
| Issuer | `https://mode83.example/issuers/main` | ❌ |
| BadgeClass | `https://mode83.example/badges/blockchain-foundations` | ❌ |
| Assertion | `urn:uuid:<uuid>` | ❌ (URN non résolvable) |

---

## Plan d'implémentation

### Étape 1 — Endpoints publics dans `main.py`

Ajouter 3 nouveaux endpoints qui servent les ressources JSON :

| Endpoint | Méthode | Retour |
|----------|---------|--------|
| `/issuers/main` | `GET` | `data/issuer.json` |
| `/badges/blockchain-foundations` | `GET` | `data/badgeclass.json` |
| `/assertions/{assertion_id}` | `GET` | `data/issued/{id}.json` |

Content-Type : `application/ld+json; profile="https://w3id.org/openbadges/v2"`

### Étape 2 — Mettre à jour les fichiers de référence

**`data/issuer.json`** — remplacer toutes les URLs :

```json
{
  "@context": "https://w3id.org/openbadges/v2",
  "id": "http://<SERVEUR_IP>:8000/issuers/main",
  "type": "Issuer",
  "name": "MODE83",
  "url": "http://<SERVEUR_IP>:8000",
  "email": "contact@mode83.example",
  "description": "Profil de l'émetteur MODE83 pour l'émission de badges Open Badges 2.0.",
  "image": "http://<SERVEUR_IP>:8000/assets/mode83-badge.png"
}
```

**`data/badgeclass.json`** — idem :

```json
{
  "@context": "https://w3id.org/openbadges/v2",
  "id": "http://<SERVEUR_IP>:8000/badges/blockchain-foundations",
  "type": "BadgeClass",
  "name": "MODE83 Fondamentaux Blockchain",
  "description": "Badge Open Badges émis par MODE83.",
  "image": "http://<SERVEUR_IP>:8000/assets/mode83-badge.png",
  "criteria": {
    "narrative": "L'apprenant a validé les exigences pédagogiques MODE83."
  },
  "issuer": "http://<SERVEUR_IP>:8000/issuers/main"
}
```

### Étape 3 — Modifier la génération des assertions (`issuer.py`)

L'assertion doit utiliser des **URLs de référence** (pas d'objets imbriqués) :

```json
{
  "@context": "https://w3id.org/openbadges/v2",
  "id": "http://<SERVEUR_IP>:8000/assertions/<uuid>",
  "type": "Assertion",
  "url": "http://<SERVEUR_IP>:8000/assertions/<uuid>",
  "recipient": {
    "type": "email",
    "hashed": true,
    "identity": "sha256...",
    "plaintext_email": "alice@example.org",
    "name": "Alice"
  },
  "issuedOn": "2025-04-13T10:30:00+00:00",
  "verification": {
    "type": "HostedBadge"
  },
  "badge": "http://<SERVEUR_IP>:8000/badges/blockchain-foundations",
  "issuer": "http://<SERVEUR_IP>:8000/issuers/main"
}
```

Changements dans `issuer.py` :
- `issuer` → URL string (au lieu de l'objet complet)
- `badge` → URL string (au lieu de l'objet imbriqué)
- `id` → URL complète (`http://<IP>:8000/assertions/<uuid>`)
- Ajouter le champ `url`

### Étape 4 — CORS

Ajouter le middleware CORS dans `main.py` pour autoriser les requêtes cross-origin du validateur IMS :

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)
```

### Étape 5 — Endpoint pour l'image du badge

Le champ `image` dans BadgeClass pointe vers une ressource HTTP. Ajouter un endpoint :

```python
@app.get("/assets/mode83-badge.png")
async def get_badge_image():
    return FileResponse(DATA_BASE / "badge.png", media_type="image/png")
```

### Étape 6 — Configuration du serveur

Démarrer FastAPI en écoute sur toutes les interfaces :

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Vérifier que :
- Le port 8000 est ouvert dans le firewall du serveur
- L'IP publique est accessible depuis internet

---

## Résumé des fichiers à modifier

| Fichier | Modifications |
|---------|--------------|
| `main.py` | + 3 endpoints (`/issuers/`, `/badges/`, `/assertions/`), + endpoint image, + CORS middleware |
| `issuer.py` | Assertion avec URLs de référence au lieu d'objets imbriqués |
| `data/issuer.json` | Remplacer `mode83.example` → `<SERVEUR_IP>:8000` |
| `data/badgeclass.json` | Remplacer `mode83.example` → `<SERVEUR_IP>:8000` |

---

## Chaîne de vérification (après implémentation)

```
Badge PNG (baked)
  │
  ├── chunk tEXt → Assertion JSON
  │
  ├── GET http://<IP>:8000/badges/blockchain-foundations
  │     → BadgeClass JSON
  │     └── GET http://<IP>:8000/issuers/main
  │           → Issuer JSON
  │
  ├── GET http://<IP>:8000/issuers/main
  │     → Issuer JSON (vérification croisée)
  │
  └── issuedOn → Date vérifiée
```

---

## Tests

1. **Émettre un badge** : `POST /issue-baked` avec `name` + `email`
2. **Vérifier les URLs** : extraire l'assertion du PNG, curl chaque URL
   ```bash
   curl http://<IP>:8000/issuers/main
   curl http://<IP>:8000/badges/blockchain-foundations
   curl http://<IP>:8000/assertions/<uuid>
   ```
3. **Soumettre au validateur IMS** : uploader le badge PNG sur [validator.openbadges.org](https://validator.openbadges.org)

---

## Migration future vers HTTPS / domaine

Quand on passe en production :
1. Configurer un domaine (`badges.mode83.fr`)
2. Mettre en place HTTPS (Let's Encrypt)
3. Remplacer `http://<IP>:8000` → `https://badges.mode83.fr` dans `issuer.json` et `badgeclass.json`
4. Redéployer — les anciens badges restent valides (leurs URLs pointent vers l'ancien domaine, donc prévoir redirection 301)
