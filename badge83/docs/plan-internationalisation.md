# Plan d'implémentation du support multi-langue pour Badge83

## Objectif
Ajouter la possibilité de spécifier la langue lors de l'émission des badges Open Badges, en remplaçant la valeur hardcodée "fr-FR" par une langue configurable.

## Étapes d'implémentation

### 1. Configuration de la langue par défaut
- Ajouter une nouvelle variable d'environnement `BADGE83_DEFAULT_LANGUAGE` dans `badge83.env.exemple` et `badge83.sh`
- Valeur par défaut : "fr-FR" pour maintenir la compatibilité
- Exemple : `BADGE83_DEFAULT_LANGUAGE=fr-FR`

### 2. Modification du noyau d'émission (`app/issuer.py`)
- Dans la fonction `build_assertion()` :
  * Remplacer `"@language": "fr-FR"` par `"@language": get_language()` 
  * Créer une fonction `get_language()` qui :
    - Vérifie d'abord un paramètre optionnel `language` dans la requête API
    - Puis utilise la variable d'environnement `BADGE83_DEFAULT_LANGUAGE`
    - Enfin retourne "fr-FR" comme fallback

### 3. Mise à jour des endpoints API
- Dans `app/routes/issue.py` et `app/routes/issue_baked.py` :
  * Ajouter un paramètre optionnel `language: str = None` aux fonctions POST
  * Passer ce paramètre à la fonction `build_assertion()`
  * Documenter ce nouveau paramètre dans les docstrings

### 4. Mise à jour des templates JSON
- Modifier `data/issuer_template.json` et `data/badgeclass_template.json` :
  * Remplacer `"@language": "fr-FR"` par `"@language": "${LANGUAGE}"`
  * Le script de démarrage remplacera `${LANGUAGE}` par la valeur configurée
  * Alternative : laisser les templates tels quels et remplacer la valeur pendant la génération (plus simple)

### 5. Mise à jour du script de démarrage (`badge83.sh`)
- Exporter la nouvelle variable d'environnement :
  ```bash
  export BADGE83_DEFAULT_LANGUAGE="${BADGE83_DEFAULT_LANGUAGE:-fr-FR}"
  ```
- Utiliser cette variable pour remplacer les placeholders dans les templates si nécessaire

### 6. Mise à jour de la documentation
- Dans `README.md` :
  * Ajouter une section "Configuration de la langue"
  * Documenter la nouvelle variable d'environnement `BADGE83_DEFAULT_LANGUAGE`
  * Mentionner le nouveau paramètre API `language` pour les endpoints `/issue` et `/issue-baked`
  * Exemple d'utilisation :
    ```bash
    # Émission en anglais
    curl -X POST -F "name=Alice" -F "email=alice@example.org" -F "language=en" http://localhost:8000/issue-baked --output badge.png
    ```

### 7. Tests
- Ajouter des tests dans `tests/` pour vérifier :
  * Que la langue par défaut est bien "fr-FR"
  * Que la variable d'environnement override la langue par défaut
  * Que le paramètre API override à la fois la variable d'environnement et le défaut
  * Que la langue est correctement présente dans l'assertion générée

## Impact
- Changement rétrocompatible : la valeur par défaut reste "fr-FR"
- Aucune modification nécessaire des badges déjà émis
- Le standard Open Badges 2.0 supporte n'importe quel code de langue valide (BCP 47)

## Langues supportées
Toute chaîne de langue valide selon la norme BCP 47 (ex: "en", "en-US", "es", "de", "fr", "fr-FR", etc.)

## Sécurité
- Validation basique du code de langue (optionnel) : vérifier qu'il correspond au pattern [a-z]{2}(-[A-Z]{2})?
- Pas d'injection possible car la valeur est utilisée dans un champ JSON spécifique