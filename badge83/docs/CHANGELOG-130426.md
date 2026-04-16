# Journal des modifications — 13/04/26

## Résumé

Implémentation des **endpoints publics HostedBadge** permettant la validation externe des badges par des tiers (ex. `validator.openbadges.org`). Les assertions générées contiennent désormais des URLs HTTP publiques au lieu d'objets imbriqués.

---

## Changements détaillés

### 1. Configuration dynamique via variable d'environnement

**Fichiers** : `app/main.py`, `app/issuer.py`

- Lecture de l'URL du serveur depuis la variable d'environnement `BADGE83_BASE_URL`
- Fallback par défaut : `http://127.0.0.1:8000`
- Aucune adresse IP hardcodée dans le code source

**Exemple d'utilisation** :
```bash
export BADGE83_BASE_URL=http://145.241.167.34:8000
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2. Middleware CORS

**Fichier** : `app/main.py`

- Ajout du middleware `CORSMiddleware` avec `allow_origins=["*"]` et `allow_methods=["GET"]`
- Permet aux validateurs externes de faire des requêtes cross-origin vers les endpoints publics

### 3. Nouveaux endpoints publics

**Fichier** : `app/main.py`

| Endpoint | Méthode | Description | Content-Type |
|----------|---------|-------------|--------------|
| `/issuers/main` | `GET` | Profil de l'émetteur (Issuer) | `application/ld+json; profile="https://w3id.org/openbadges/v2"` |
| `/badges/blockchain-foundations` | `GET` | Définition du badge (BadgeClass) | `application/ld+json; profile="https://w3id.org/openbadges/v2"` |
| `/assertions/{uuid}` | `GET` | Assertion individuelle | `application/ld+json; profile="https://w3id.org/openbadges/v2"` |
| `/assets/{fichier}` | `GET` | Assets statiques (PNG, logos) | `image/png` |

### 4. Templates JSON dynamiques

**Fichiers ajoutés** :
- `data/issuer_template.json`
- `data/badgeclass_template.json`

- Remplacement du placeholder `${BASE_URL}` par la valeur réelle au moment de la requête
- Les fichiers de données ne contiennent plus d'adresse IP → **pas de fuite dans git**
- Fichier `.env` ajouté au `.gitignore`
- Fichier `.env.example` fourni comme référence

### 5. Assertions au format HostedBadge

**Fichier** : `app/issuer.py`

Les assertions générées utilisent désormais des **URLs de référence** au lieu d'objets imbriqués :

**Avant** :
```json
{
  "badge": { "id": "...", "name": "...", "issuer": { ... } },
  "issuer": { "id": "...", "name": "..." }
}
```

**Après** :
```json
{
  "id": "http://<BASE_URL>/assertions/<uuid>",
  "url": "http://<BASE_URL>/assertions/<uuid>",
  "badge": "http://<BASE_URL>/badges/blockchain-foundations",
  "issuer": "http://<BASE_URL>/issuers/main"
}
```

### 6. Compatibilité du vérificateur

**Fichier** : `app/verifier.py`

- Mise à jour de `verify_badge()` et `verify_baked_badge()` pour gérer les deux formats :
  - URLs de référence (chaînes de caractères)
  - Objets imbriqués (dictionnaires) — rétrocompatibilité

---

## Chaîne de vérification complète

Après ces modifications, un validateur externe suit cette chaîne :

```
Badge PNG (baked)
  │
  ├── Extraction du chunk tEXt → Assertion JSON
  │
  ├── assertion.badge → "http://<IP>:8000/badges/blockchain-foundations"
  │     └── GET → BadgeClass JSON avec Content-Type Open Badges
  │           └── badgeClass.issuer → "http://<IP>:8000/issuers/main"
  │                 └── GET → Issuer JSON avec Content-Type Open Badges
  │
  ├── assertion.issuer → "http://<IP>:8000/issuers/main"
  │     └── GET → Issuer JSON (vérification croisée)
  │
  └── assertion.id → "http://<IP>:8000/assertions/<uuid>"
        └── GET → Assertion JSON (résolvable)
```

---

## Fichiers modifiés

| Fichier | Type | Description |
|---------|------|-------------|
| `app/main.py` | Modifié | + BASE_URL, + CORS, + 4 endpoints publics |
| `app/issuer.py` | Modifié | + BASE_URL, + templates, assertion avec URLs |
| `app/verifier.py` | Modifié | Gestion URLs + objets imbriqués |
| `data/issuer_template.json` | Ajouté | Template du profil émetteur |
| `data/badgeclass_template.json` | Ajouté | Template du badge |
| `.gitignore` | Modifié | + exclusion `.env` |
| `.env.example` | Ajouté | Exemple de configuration |
| `README.md` | Modifié | Documentation des endpoints HostedBadge |
| `docs/plan-hosted-verification.md` | Ajouté | Plan détaillé de l'implémentation |

---

## Tests effectués

| Test | Résultat |
|------|----------|
| `GET /issuers/main` → JSON avec URLs résolues | Oui / |
| `GET /badges/blockchain-foundations` → JSON avec URLs résolues | Oui / |
| `GET /assertions/<uuid>` → assertion valide | Oui / |
| `POST /issue` → assertion avec URLs publiques | Oui / |
| `POST /issue-baked` → PNG baked avec assertion URLs | Oui / |
| `POST /verify-baked` → vérification réussie | Oui / |

---

## Prochaines étapes

1. **Ouvrir le port 8000** dans le firewall du serveur pour accès externe
2. **Tester avec `validator.openbadges.org`** en uploadant un badge baked
3. **Configurer HTTPS** (Let's Encrypt) pour la production
4. **Configurer un domaine** (`badges.mode83.fr` ou équivalent)
