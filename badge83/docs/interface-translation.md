# Documentation de la traduction de l'interface Badge83

## Aperçu
L'interface web d'administration de Badge83 possède une implémentation complète de multi-langue côté client, permettant aux utilisateurs de basculer dynamiquement entre différentes langues sans rechargement de page.

## Fonctionnement technique

### 1. Sélecteur de langue dans l'interface
L'interface comprend un sélecteur de langue situé dans la barre d'en-tête :
```html
<select id="languageSelect" class="form-select" style="min-width: 180px;">
  <option value="fr">Français</option>
  <option value="en">English</option>
  <option value="ru">Русский</option>
</select>
```

### 2. Système de traduction JavaScript
Toutes les chaînes de l'interface sont définies dans un objet `translations` dans le fichier `badge83/templates/index.html` :

```javascript
const translations = {
  fr: {
    pageTitle: 'Espace de travail administrateur et élément courant',
    // ... des centaines de chaînes traduites
  },
  en: {
    pageTitle: 'Admin workspace and current item',
    // ... traductions anglaises
  },
  ru: {
    pageTitle: 'Админ-пространство и текущий элемент',
    // ... traductions russes
  }
};
```

### 3. Fonctions de traduction
- `t(key)` : fonction helper qui retourne la traduction pour une clé donnée dans la langue courante
- `applyTranslations()` : parcourt tous les éléments traduisibles de l'interface et met à jour leur contenu avec la traduction appropriée

### 4. Mécanisme de commutation
Lorsque l'utilisateur change la langue dans le sélecteur :
1. Un écouteur d'événement détecte le changement (ligne 1242-1245)
2. La variable `currentLang` est mise à jour avec la nouvelle valeur
3. `applyTranslations()` est appelée pour rafraîchir toute l'interface
4. L'attribut `lang` de l'élément `<html>` est mis à jour pour l'accessibilité

## Langues actuellement supportées
| Code | Langue | Statut |
|------|--------|--------|
| `fr` | Français | Langue par défaut |
| `en` | Anglais | Complètement supportée |
| `ru` | Russe | Complètement supportée |

## Où trouver le code de traduction
Toute la logique de traduction se trouve dans le fichier :
```
badge83/templates/index.html
```

Sections clés :
- Lignes 660-862 : Objet `translations` contenant toutes les chaînes
- Lignes 864-911 : Fonctions `t()` et `applyTranslations()`
- Lignes 1242-1245 : Gestion du changement de langue
- Lignes 1247-1250 : Initialisation au chargement de la page

## Comment ajouter une nouvelle langue
Pour ajouter une nouvelle langue à l'interface :

1. **Ajouter une entrée dans le sélecteur de langue** :
   ```html
   <option value="xx">Nom de la langue</option>
   ```

2. **Étendre l'objet `translations`** :
   ```javascript
   const translations = {
     // ... langues existantes
     xx: {
       pageTitle: 'Titre de la page en nouvelle langue',
       // ... traduire TOUTES les chaînes présentes dans les autres langues
       // Astuce : copiez-collez l'objet "fr" ou "en" et traduisez les valeurs
     }
   };
   ```

3. **Vérifier la couverture** :
   Assurez-vous que votre nouvel objet de langue contient exactement les mêmes clés que les autres langues pour éviter les affichages manquants.

## Points importants concernant la traduction de l'interface

### Ce qui est traduit
- Tous les textes statiques de l'interface (labels, boutons, titres, messages)
- Les placeholders des champs de formulaire
- Les messages système et de statut
- Les infobulles et textes d'aide
- Les libellés des colonnes du tableau des badges

### Ce qui N'EST PAS traduit (et pourquoi)
- **Les données des badges elles-mêmes** : Le contenu des assertions Open Badges (nom, email, etc.) reste dans la langue originale de l'émission car il s'agit de données utilisateur, pas de texte d'interface
- **Les métadonnées Open Badges** : Comme discuté dans d'autres documents, le champ `@language` des assertions reste pour l'instant hardcodé en "fr-FR" (voir plan-internationalisation.md pour les améliorations prévues)
- **Les URLs et chemins** : Ils restent inchangés pour préserver la fonctionnalité

## Interaction avec l'API
La traduction de l'interface est totalement indépendante de l'API backend :
- Le sélecteur de langue n'affecte PAS les appels API
- Les endpoints comme `/issue`, `/verify`, etc. fonctionnent dans la langue de leur implémentation (actuellement principalement français pour les messages d'erreur API)
- Une future amélioration pourrait consister à faire reconnaître à l'API l'en-tête `Accept-Language` pour retourner les messages d'erreur dans la langue de l'utilisateur

## Exemples d'utilisation
1. **Changer la langue** : Sélectionnez simplement la langue souhaitée dans le menu déroulant en haut de l'interface
2. **Développeur** : Pour tester une nouvelle traduction, modifiez directement l'objet `translations` dans `index.html` et rechargez la page
3. **Utilisation en production** : La dernière langue sélectionnée est conservée dans la session du navigateur jusqu'à ce qu'elle soit changée manuellement

## Limitations actuelles
- Aucune persistance côté serveur du choix de langue (réinitialisé à "fr" en cas de nettoyage du cache)
- Pas de détection automatique basée sur les préférences du navigateur (Accept-Language header)
- L'implémentation est purement côté serveur dans le template HTML (pas de fichiers de traduction séparés .json ou .po)

## Prochaines étapes possibles
1. Externaliser les traductions dans des fichiers JSON séparés pour faciliter la maintenance
2. Ajouter la persistance du choix de langue dans le stockage local du navigateur
3. Implémenter la détection automatique de la langue via l'en-tête Accept-Language
4. Étendre le système pour supporter les paramètres régionaux (ex: "fr-CA", "en-GB")