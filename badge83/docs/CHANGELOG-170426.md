# Journal des modifications — 17/04/26

## Résumé

Cette intervention a porté sur la **compaction de l’en-tête du Control Center Badge83** afin de mieux exploiter la hauteur utile de l’écran, en particulier sur tablette et sur les résolutions intermédiaires.

---

## Changements applicatifs

### 1. Simplification du bloc supérieur

**Fichier** : `templates/index.html`

- suppression du texte descriptif long situé sous le titre principal ;
- suppression des boutons rapides `Issuer` et `BadgeClass` dans la zone d’actions de droite ;
- conservation des éléments d’usage courant : sélecteur de langue et accès `Legacy page`.

### 2. Réduction visuelle de la шапка

Les éléments suivants ont été réduits et resserrés :

- taille du titre principal ;
- badges visuels `Badge83` / `Admin Workspace` ;
- hauteur et padding des chips de statut ;
- hauteur et padding des cartes statistiques ;
- taille des boutons et du sélecteur de langue ;
- espacement vertical entre les lignes du header.

### 3. Mise en ligne compacte

Pour limiter l’encombrement horizontal et vertical :

- les contrôles de droite restent sur une seule ligne sur écran large ;
- les valeurs des statuts et des cartes métriques sont forcées en ligne unique ;
- l’overflow est géré par `ellipsis` pour éviter les retours à la ligne intempestifs ;
- le comportement responsive est conservé sur les largeurs plus faibles.

---

## Effet fonctionnel

- l’en-tête prend moins de place au-dessus du menu latéral ;
- la lecture des statuts principaux reste immédiate ;
- la zone utile visible pour le registre et les panneaux fonctionnels augmente ;
- l’interface devient plus adaptée au format montré sur la capture annotée.

---

## Documentation / périmètre

Cette mise à jour concerne uniquement **la présentation et la densité visuelle** de l’interface d’administration.

Elle ne modifie pas :

- les routes backend ;
- la logique d’émission ;
- la logique de vérification ;
- la structure des assertions ou des PNG baked.

---

## Fichier impacté

- `badge83/templates/index.html`
