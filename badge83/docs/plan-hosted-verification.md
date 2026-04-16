# État d'implémentation — Endpoints publics pour la vérification en ligne (HostedBadge)

## Contexte

Les assertions Open Badges émises par Badge83 utilisent le type de vérification **`HostedBadge`**. Un validateur externe (ex. `validator.openbadges.org`) doit pouvoir accéder aux URLs référencées dans l'assertion via HTTP/HTTPS.

**État actuel** : l'implémentation a été réalisée. Les badges émis utilisent `BADGE83_BASE_URL` comme base pour toutes les URLs publiques (`Issuer`, `BadgeClass`, `Assertion`).

---

## Problème initial

| Ressource | Ancien format | Problème |
|-----------|-------------|-------------|
| Issuer | `https://mode83.example/issuers/main` | Domaine fictif non résolvable |
| BadgeClass | `https://mode83.example/badges/blockchain-foundations` | Domaine fictif non résolvable |
| Assertion | `urn:uuid:<uuid>` | URN non résolvable pour HostedBadge |

---

## Implémentation réalisée

### 1. Endpoints publics dans `main.py`

Les endpoints publics suivants servent les ressources JSON :

| Endpoint | Méthode | Retour |
|----------|---------|--------|
| `/issuers/main` | `GET` | `issuer_template.json` avec `${BASE_URL}` résolu |
| `/badges/blockchain-foundations` | `GET` | `badgeclass_template.json` avec `${BASE_URL}` résolu |
| `/assertions/{assertion_id}` | `GET` | `data/issued/{id}.json` |
| `/assets/{asset_name}` | `GET` | Image du badge ou autre ressource statique |

Content-Type : `application/ld+json; profile="https://w3id.org/openbadges/v2"`

### 2. Fichiers de référence dynamiques

Les fichiers de référence sont désormais des **templates** :

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

Le même principe s'applique à `badgeclass_template.json`.

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

### 3. Génération des assertions (`issuer.py`)

L'assertion générée utilise des **URLs de référence** (pas d'objets imbriqués) :

```json
{
  "@context": "https://w3id.org/openbadges/v2",
  "id": "http://<SERVEUR_IP>:8000/assertions/<uuid>",
  "type": "Assertion",
  "url": "http://<SERVEUR_IP>:8000/assertions/<uuid>",
  "recipient": {
    "type": "email",
    "hashed": true,
    "identity": "sha256..."
  },
  "issuedOn": "2025-04-13T10:30:00+00:00",
  "verification": {
    "type": "HostedBadge",
    "url": "http://<SERVEUR_IP>:8000/assertions/<uuid>"
  },
  "badge": "http://<SERVEUR_IP>:8000/badges/blockchain-foundations",
  "issuer": "http://<SERVEUR_IP>:8000/issuers/main"
}
```

Points effectivement implémentés dans `issuer.py` :
- `issuer` → URL string (au lieu de l'objet complet)
- `badge` → URL string (au lieu de l'objet imbriqué)
- `id` → URL complète (`http://<IP>:8000/assertions/<uuid>`)
- Ajouter `verification.url`

### 4. CORS

Le middleware CORS est en place dans `main.py` pour autoriser les requêtes cross-origin des validateurs externes :

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)
```

### 5. Endpoint pour l'image du badge

Le champ `image` dans BadgeClass pointe vers une ressource HTTP, servie via `/assets/{asset_name}`.

```python
@app.get("/assets/mode83-badge.png")
async def get_badge_image():
    return FileResponse(DATA_BASE / "badge.png", media_type="image/png")
```

### 6. Configuration du serveur

FastAPI doit être démarré en écoute sur toutes les interfaces pour une validation externe :

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Vérifier que :
- Le port 8000 est ouvert dans le firewall du serveur
- L'IP publique est accessible depuis internet

---

## Résumé des fichiers concernés

| Fichier | Rôle actuel |
|---------|--------------|
| `main.py` | Expose les endpoints publics, les assets, CORS et la vérification en ligne |
| `issuer.py` | Génère des assertions HostedBadge avec URLs de référence |
| `data/issuer_template.json` | Template dynamique de profil émetteur |
| `data/badgeclass_template.json` | Template dynamique de BadgeClass |

---

## Chaîne de vérification actuelle

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

## Tests recommandés

1. **Émettre un badge** : `POST /issue-baked` avec `name` + `email`
2. **Vérifier les URLs** : extraire l'assertion du PNG, curl chaque URL
   ```bash
   curl http://<IP>:8000/issuers/main
   curl http://<IP>:8000/badges/blockchain-foundations
   curl http://<IP>:8000/assertions/<uuid>
   ```
3. **Soumettre au validateur compatible** : utiliser `openbadges-validator-core` ou un validateur public compatible

---

## Prochaines améliorations

Pour une mise en production durable :
1. Configurer un domaine (`badges.mode83.fr`)
2. Mettre en place HTTPS (Let's Encrypt)
3. Remplacer `http://<IP>:8000` → `https://badges.mode83.fr` dans `issuer.json` et `badgeclass.json`
4. Redéployer — les anciens badges restent valides (leurs URLs pointent vers l'ancien domaine, donc prévoir redirection 301)
