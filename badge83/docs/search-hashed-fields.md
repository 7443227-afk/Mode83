# Recherche sur champs hashés — Badge83

## But

Permettre la recherche en admin sur :

- un email ;
- un nom ;

sans stocker ces valeurs en clair dans l’interface de registre.

## Principe

Badge83 utilise maintenant deux mécanismes :

1. `recipient.identity` avec `salt` aléatoire par badge pour la compatibilité Open Badges ;
2. `search.name_hash` et `search.email_hash` pour la recherche admin locale.

## Pourquoi deux hash différents

Le hash Open Badges du recipient email varie d’un badge à l’autre car il dépend d’un `salt` aléatoire.
Il n’est donc pas adapté à une recherche stable multi-badges.

Pour la recherche admin, Badge83 calcule donc des hash stables à partir de :

- `normalized_name + BADGE83_SEARCH_PEPPER`
- `normalized_email + BADGE83_SEARCH_PEPPER`

## Limite importante

Les anciens badges ne contiennent pas forcément `search.name_hash` / `search.email_hash`.

- pour l’email, Badge83 peut encore faire un fallback via `recipient.salt` et `recipient.identity` ;
- pour le nom, il n’y a pas de récupération possible si le nom n’a jamais été stocké auparavant.

## Recommandation

En production, définir explicitement :

```bash
export BADGE83_SEARCH_PEPPER="long-random-secret"
```

et conserver cette valeur stable dans le temps.

## Mise en œuvre dans Badge83

La recherche par valeurs hashées est utilisée dans deux cas d’usage principaux :

1. la **recherche dans le registre admin** ;
2. la **recherche de certificats liés** depuis le *Bureau de vérification*.

### 1. Champs ajoutés lors de l’émission

Pour chaque nouveau badge émis, Badge83 enregistre désormais :

- `search.name_hash`
- `search.email_hash`

Ces champs sont calculés à partir de versions normalisées des valeurs :

- nom : minuscules, espaces nettoyés ;
- email : minuscules, espaces supprimés en bordure.

Le calcul utilise ensuite un `pepper` stable côté serveur :

- `BADGE83_SEARCH_PEPPER`

Ce mécanisme permet de faire une recherche cohérente dans le temps sans dépendre du `salt` aléatoire utilisé pour `recipient.identity`.

### 2. Compatibilité avec Open Badges

Le champ standard Open Badges :

- `recipient.identity`

continue d’exister et d’être calculé avec :

- un email normalisé ;
- un `salt` aléatoire propre à chaque badge.

Ce hash est nécessaire pour la compatibilité du badge, mais il n’est pas adapté à une recherche multi-badges stable.

### 3. Fallback pour les badges plus anciens

Pour les anciens badges qui ne possèdent pas encore `search.email_hash` :

- Badge83 peut encore tenter un rapprochement via `recipient.salt` + `recipient.identity`.

En revanche, pour les anciens badges sans nom stocké localement :

- il n’est pas possible de reconstruire une recherche fiable par nom.

## Conséquences fonctionnelles

Grâce à ce mécanisme, l’application peut maintenant :

- rechercher si un badge a déjà été émis pour un email donné ;
- rechercher si plusieurs badges sont liés au même nom ;
- afficher, dans le *Bureau de vérification*, d’autres certificats liés au même profil quand les hash correspondants existent.

## Bonnes pratiques recommandées

Pour un environnement de démonstration avancée ou de production légère, il est recommandé de :

1. définir explicitement `BADGE83_SEARCH_PEPPER` ;
2. conserver cette valeur stable dans le temps ;
3. éviter d’utiliser la valeur par défaut en production ;
4. documenter le fait que les anciens badges ne disposent pas tous des mêmes capacités de recherche.