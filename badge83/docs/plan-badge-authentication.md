# Plan de travail — Badge-based authentication

## Idée

Étudier la possibilité d’utiliser un **badge correctement émis et vérifié** comme mécanisme d’accès à certaines pages du projet Badge83.

L’idée générale est la suivante :

- l’utilisateur charge un badge ;
- le système extrait ou lit l’assertion ;
- le backend vérifie que le badge est valide et correspond à une politique d’accès ;
- si les conditions sont remplies, l’utilisateur obtient un accès à une zone donnée.

---

## Formats d’entrée envisageables

### 1. PNG baked

Scénario :

- l’utilisateur téléverse un fichier PNG ;
- le système exécute un `unbake` pour extraire l’assertion Open Badges ;
- l’assertion est ensuite vérifiée comme un HostedBadge classique.

Avantages :

- expérience utilisateur simple ;
- cohérent avec la logique native de Badge83.

Limites :

- la possession d’un fichier PNG ne prouve pas toujours à elle seule l’identité réelle de la personne ;
- attention au risque de partage/copier-coller du badge.

### 2. Assertion JSON

Scénario :

- l’utilisateur fournit un fichier JSON d’assertion ;
- le système vérifie la structure, l’issuer, le recipient, la politique `verification` et l’état de validité.

Avantages :

- plus direct pour le traitement ;
- plus simple à inspecter côté backend.

Limites :

- moins ergonomique qu’un PNG pour un usage non technique.

### 3. Assertion URL / HostedBadge URL

Scénario :

- l’utilisateur fournit l’URL publique de son assertion ;
- le backend recharge l’assertion et la valide à distance.

Avantages :

- très propre conceptuellement ;
- bien aligné avec le modèle HostedBadge.

Limites :

- dépend de la disponibilité réseau et de la résolution publique ;
- nécessite de bien gérer les délais, erreurs HTTP et politiques d’origine.

---

## Cas d’usage possibles

### A. Accès à un espace utilisateur simple

Exemple :

- accès à une page personnelle de consultation ;
- accès à une page “voir mon badge / vérifier mon statut”.

➡️ Cas relativement sûr pour un MVP.

### B. Accès à des ressources réservées à certains détenteurs de badge

Exemple :

- page réservée aux titulaires d’un badge spécifique ;
- contenu débloqué par niveau / parcours / certification.

➡️ Cas intéressant et naturel pour Badge83.

### C. Accès à l’interface d’administration

Exemple :

- connexion au backoffice via un badge “admin” ou “staff”.

➡️ Cas beaucoup plus sensible.

Pour l’administration, le simple upload d’un badge ne doit pas être considéré comme suffisamment sûr sans mécanisme complémentaire.

---

## Risques de sécurité

### 1. Possession du fichier ≠ preuve d’identité

Un badge PNG ou JSON peut être copié, transféré ou partagé.

Donc :

- un badge peut servir de **preuve de droit potentiel** ;
- mais pas nécessairement de **preuve forte d’identité**.

### 2. Rejeu / réutilisation

Sans challenge temporaire, un même badge peut être réutilisé plusieurs fois pour ouvrir une session.

### 3. Badge valide mais contexte d’accès non autorisé

Il faut distinguer :

- badge valide ;
- badge valide et émis par le bon issuer ;
- badge valide et appartenant à la bonne classe ;
- badge valide et autorisé pour la page concernée.

### 4. Admin = exigence plus élevée

Pour l’admin, il faudrait idéalement ajouter au moins l’un des éléments suivants :

- challenge email ;
- lien magique envoyé au destinataire ;
- second facteur ;
- session courte avec contrôle côté serveur.

---

## Recommandation MVP

Le scénario recommandé pour un premier prototype serait :

1. **ne pas viser l’admin d’abord** ;
2. cibler une page protégée simple ;
3. accepter d’abord **assertion URL** ou **assertion JSON** ;
4. ajouter ensuite le support **PNG baked** ;
5. lier les droits à :
   - `issuer.id`
   - `badge.id`
   - statut de validation
   - éventuelle date d’expiration

---

## Architecture possible

### Backend

Ajouter un module ou service dédié, par exemple :

- `app/auth_badge.py`

Responsabilités :

- accepter un badge/JSON/URL ;
- extraire l’assertion si nécessaire ;
- valider la structure Open Badges ;
- vérifier la conformité HostedBadge ;
- appliquer une politique d’autorisation ;
- créer une session locale courte.

### Frontend

Ajouter une page dédiée, par exemple :

- `/badge-login`

Avec :

- upload PNG ;
- upload JSON ;
- saisie URL ;
- message de résultat clair ;
- redirection éventuelle vers la ressource autorisée.

### Politique d’accès

Exemples de règles :

- seul un badge d’une `BadgeClass` donnée ouvre la page ;
- seuls les badges émis par `Main` sont acceptés ;
- les badges expirés ou supprimés sont refusés.

---

## Questions ouvertes

Avant implémentation, il faudra trancher :

1. quelle page doit être protégée par badge ;
2. si l’usage vise un espace utilisateur, une ressource réservée ou l’admin ;
3. quel format doit être supporté en premier ;
4. si la possession du badge suffit, ou s’il faut un second facteur ;
5. comment persister la session côté serveur.

---

## Décision actuelle

Cette idée est **retenue comme piste produit / sécurité**, mais **pas implémentée pour le moment**.

Le document sert de point de reprise pour une future itération.
