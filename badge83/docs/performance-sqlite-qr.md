# Badge83 — Optimisations performance SQLite et QR

Date : 17/06/2026  
Périmètre : backend Badge83, constructeur de badges, génération QR/PNG.

## Objectif

Cette note documente la première passe d'optimisation réalisée après la fusion de la base blockchain `Badge83Registry`.

Les objectifs étaient volontairement limités :

1. réduire le coût d'ouverture des connexions SQLite utilisées par le constructeur ;
2. améliorer le comportement SQLite en cas d'accès concurrents légers ;
3. éviter de recharger les polices à chaque rendu de texte sur PNG ;
4. conserver le comportement fonctionnel existant et la compatibilité des tests.

## Changements SQLite

Le module `badge83/app/database.py` applique maintenant les PRAGMA suivants à chaque connexion SQLite :

```sql
PRAGMA journal_mode=WAL;
PRAGMA busy_timeout=10000;
PRAGMA synchronous=NORMAL;
```

Effet attendu :

- `WAL` améliore la cohabitation lecture/écriture sur SQLite ;
- `busy_timeout=10000` évite certains échecs immédiats lorsque la base est temporairement verrouillée ;
- `synchronous=NORMAL` réduit le coût d'écriture tout en gardant un compromis acceptable pour l'usage Badge83.

## Initialisation du schéma

Avant cette optimisation, les dépendances FastAPI du constructeur ouvraient la base via `init_db_schema()`.

Cela relançait toute la séquence `CREATE TABLE IF NOT EXISTS` / `CREATE INDEX IF NOT EXISTS` à chaque requête du constructeur de badges.

Désormais :

- `get_database_connection()` ouvre une connexion configurée ;
- le schéma est créé une seule fois par chemin de base connu dans le processus courant ;
- `init_db_schema()` reste disponible pour l'initialisation explicite au démarrage, les tests et les scripts.

Fichiers concernés :

```text
badge83/app/database.py
badge83/app/routes/badge_constructor/schemas.py
badge83/app/routes/badge_constructor/templates.py
```

## Cache des polices QR/PNG

Le rendu de texte sur badge PNG passe par `overlay_text_on_badge()` dans `badge83/app/qr.py`.

Le chargement des polices TrueType est maintenant centralisé dans :

```python
_load_text_overlay_font(font_family, font_size)
```

Ce helper utilise `functools.lru_cache(maxsize=64)`, ce qui évite de relire les fichiers TTF pour chaque overlay ou chaque badge d'un lot lorsque les mêmes couples police/taille sont utilisés.

## Validation

Tests ciblés :

```bash
cd badge83
.venv/bin/python -m pytest tests/unit/test_database.py tests/unit/test_qr.py tests/unit/test_badge_constructor_api.py
```

Résultat :

```text
29 passed
```

Suite complète :

```bash
cd badge83
.venv/bin/python -m pytest tests/unit
```

Résultat :

```text
186 passed, 22 warnings
```

Les warnings restants concernent l'ordre des paramètres `TemplateResponse` côté Starlette et ne sont pas introduits par cette optimisation.

## Points non traités dans cette passe

Restent à faire dans une passe ultérieure :

- ajouter un debounce côté preview du constructeur ;
- charger le background PNG une seule fois par batch lorsque le même template est utilisé ;
- envisager les read-models SQLite pour `/api/badges` et `/api/badges/search`.