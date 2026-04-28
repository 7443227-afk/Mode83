# Référence externe : `csev/obi-sample`

Le dépôt [`csev/obi-sample`](https://github.com/csev/obi-sample) a été cloné hors du dépôt principal MODE83 pour étude :

```text
/home/ubuntu/projects/_external/obi-sample
```

Il ne fait donc pas partie du dépôt Git `Mode83` et ne sera pas poussé vers le GitHub du projet.

## Pourquoi cette référence est utile

`obi-sample` est un exemple volontairement minimal d'Open Badges en PHP. Il montre un flux complet très simple :

```text
email → assertion → PNG baked → extraction → vérification hosted
```

Les fichiers les plus utiles pour Badge83 sont :

| Fichier | Intérêt pour Badge83 |
|---|---|
| `index.php` | Démo très simple d'émission, upload et vérification d'un badge baked. |
| `assert.php` | Exemple d'assertion hosted résolue par URL. |
| `badge-info.php` | Exemple de `BadgeClass` accessible publiquement. |
| `badge-issuer.php` | Exemple d'`Issuer` accessible publiquement. |
| `baker.php` | Génération d'un PNG baked depuis une assertion. |
| `baker-lib.php` | Manipulation bas niveau des chunks PNG `openbadges` (`tEXt` / `iTXt`). |

## Ce qui a été retenu pour Badge83

### 1. Vérification profonde d'un PNG baked

Badge83 dispose désormais d'un mode de vérification approfondie inspiré de `obi-sample` :

```http
POST /verify-baked?deep=true
```

Ce mode :

1. extrait l'assertion du chunk PNG `openbadges` ;
2. récupère l'assertion hébergée via `verification.url`, `id` ou `url` ;
3. compare les champs stables de l'assertion embedded et hosted ;
4. récupère le `BadgeClass` ;
5. récupère l'`Issuer` ;
6. retourne un rapport structuré avec les contrôles effectués.

La fonction applicative correspondante est :

```python
deep_verify_baked_badge(png_data: bytes) -> dict
```

### 2. Tests de compatibilité baking / unbaking

Les tests de `badge83/tests/unit/test_baker.py` couvrent désormais :

- roundtrip bake / unbake ;
- remplacement d'un chunk `openbadges` existant sans duplication ;
- lecture d'un ancien chunk `iTXt` ;
- rejet d'un PNG sans assertion Open Badges ;
- rejet d'un fichier non-PNG ;
- résolution simulée de la chaîne hosted `Assertion → BadgeClass → Issuer`.

## Ce qui ne doit pas être repris de `obi-sample`

`obi-sample` est utile comme référence pédagogique, mais certains choix ne doivent pas être repris en production :

- chiffrement DES-EDE3-CBC obsolète ;
- IV statique ;
- désactivation de la vérification TLS dans `curl` ;
- absence de stockage/index local ;
- architecture PHP monolithique pensée pour la démonstration.

Badge83 conserve donc son architecture FastAPI actuelle :

- assertions JSON canoniques dans `data/issued/` ;
- PNG baked dans `data/baked/` ;
- registre SQLite local pour l'administration ;
- URLs HostedBadge publiques ;
- QR code de vérification humaine ;
- support de lecture `tEXt` et `iTXt`.

## Usage recommandé

`obi-sample` doit rester une référence externe pour :

- comparer les comportements de baking PNG ;
- documenter le modèle minimal Open Badges ;
- créer de nouveaux tests de compatibilité ;
- expliquer simplement la chaîne `PNG → Assertion → BadgeClass → Issuer`.
