# Plan de travail — Validation fonctionnelle Projet A — 12/05/2026

Date prévue : 12/05/2026  
Projet : Badge83 — Open Badges MODE83  
Objectif : vérifier et documenter le fonctionnement complet du parcours Open Badges, de l'émission à la vérification.

## 1. Objectif de la journée

La journée du 12/05 doit servir à prouver que le **Projet A — Open Badges MODE83** est fonctionnel de bout en bout.

Le travail de stabilisation du 11/05 a corrigé le principal risque technique immédiat : l'erreur SQLite/threading sur les routes du constructeur. La suite logique est donc de tester le parcours utilisateur complet sur plusieurs badges.

Livrable principal à produire demain :

```text
badge83/docs/test-report-projet-a-120526.md
```

Ce rapport devra contenir :

- les scénarios exécutés ;
- les commandes ou actions réalisées ;
- les badges créés ;
- les fichiers JSON/PNG générés ;
- les vérifications QR et pages publiques ;
- les anomalies éventuelles ;
- une conclusion claire sur l'état de validation du Projet A.

## 2. Critères de réussite

La validation de demain sera considérée comme concluante si :

1. les tests automatisés passent avant la recette manuelle ;
2. le serveur Badge83 démarre sans régression visible ;
3. au moins cinq scénarios de badges sont exécutés ;
4. pour chaque scénario, une assertion JSON est créée ;
5. pour chaque scénario, un PNG baked est généré ;
6. pour chaque scénario, une page publique de vérification est consultable ;
7. pour chaque scénario, la page QR ou le QR code permet d'accéder à la vérification ;
8. les résultats sont documentés dans le rapport ;
9. les anomalies restantes sont listées sans bloquer la compréhension du livrable.

## 3. Préparation avant tests

### 3.1 Vérifier l'état du dépôt et du serveur

Si le commit est géré manuellement, commencer par vérifier que l'espace de travail est dans l'état attendu.

Commandes utiles :

```bash
cd /home/ubuntu/projects/Mode83
git status --short
```

Puis vérifier Badge83 :

```bash
cd /home/ubuntu/projects/Mode83/badge83
BADGE83_ENABLE_FIREWALL_MANAGEMENT=false ./badge83.sh status
```

### 3.2 Lancer les tests automatisés

```bash
cd /home/ubuntu/projects/Mode83/badge83
/home/ubuntu/projects/Mode83/.venv/bin/python -m pytest tests -q
```

Résultat attendu : tous les tests passent.

À noter dans le rapport :

```text
Tests automatisés : OK / KO
Résultat exact : ...
```

### 3.3 Démarrer le serveur en mode local sûr

```bash
cd /home/ubuntu/projects/Mode83/badge83
BADGE83_ENABLE_FIREWALL_MANAGEMENT=false ./badge83.sh start
```

Vérifier ensuite :

```bash
./badge83.sh status
```

Points à contrôler :

- statut actif ;
- host/port attendus ;
- `Firewall : gestion automatique = false` si test local ;
- URL de base cohérente.

## 4. Structure du rapport à créer demain

Créer le fichier :

```text
badge83/docs/test-report-projet-a-120526.md
```

Structure recommandée :

```markdown
# Rapport de test — Validation Projet A — 12/05/2026

## 1. Objectif

## 2. Environnement de test

## 3. Résultat des tests automatisés

## 4. Scénarios exécutés

## 5. Tableau de synthèse

## 6. Anomalies observées

## 7. Conclusion de validation Projet A
```

Tableau de synthèse recommandé :

| Scénario | Assertion JSON | PNG baked | QR/page QR | Page vérification | Vérification PNG | Résultat | Notes |
|---|---|---|---|---|---|---|---|
| 1 | OK/KO | OK/KO | OK/KO | OK/KO | OK/KO | OK/KO | ... |
| 2 | OK/KO | OK/KO | OK/KO | OK/KO | OK/KO | OK/KO | ... |
| 3 | OK/KO | OK/KO | OK/KO | OK/KO | OK/KO | OK/KO | ... |
| 4 | OK/KO | OK/KO | OK/KO | OK/KO | OK/KO | OK/KO | ... |
| 5 | OK/KO | OK/KO | OK/KO | OK/KO | OK/KO | OK/KO | ... |

## 5. Scénario 1 — Badge standard simple

### Objectif

Vérifier que Badge83 peut émettre un badge simple avec le modèle standard et produire les éléments attendus : JSON, PNG baked, QR et page de vérification.

### Données de test proposées

```text
Nom : Apprenant Test Standard
Email : test.standard@example.com
Badge / formation : Badge standard MODE83
```

### Étapes

1. Ouvrir l'interface Badge83.
2. Aller vers le formulaire d'émission de badge.
3. Renseigner les données de test.
4. Émettre le badge.
5. Noter l'identifiant de l'assertion générée.
6. Vérifier qu'un fichier JSON correspondant existe dans :

   ```text
   badge83/data/issued/
   ```

7. Vérifier qu'un PNG baked correspondant existe dans :

   ```text
   badge83/data/baked/
   ```

8. Ouvrir la page publique de vérification du badge.
9. Ouvrir la page QR associée.
10. Si possible, scanner le QR avec un téléphone ou vérifier que l'URL du QR mène à la bonne page.
11. Noter le résultat dans le rapport.

### Résultat attendu

- assertion JSON créée ;
- PNG baked créé ;
- page de vérification accessible ;
- QR ou page QR accessible ;
- aucune erreur serveur visible.

## 6. Scénario 2 — Badge émis depuis un modèle constructeur existant

### Objectif

Vérifier que le constructeur de badges reste fonctionnel après la correction SQLite et qu'un badge peut être émis à partir d'un modèle existant.

### Données de test proposées

```text
Nom : Apprenant Test Modèle
Email : test.modele@example.com
Badge / formation : Badge via modèle constructeur
```

### Étapes

1. Ouvrir Badge83.
2. Aller dans la partie constructeur ou sélection de modèles.
3. Charger la liste des schémas.
4. Vérifier que la route ou l'interface des schémas répond correctement.
5. Charger la liste des modèles.
6. Sélectionner un modèle existant.
7. Ouvrir la prévisualisation du modèle.
8. Vérifier que les textes, le fond et la position du QR sont cohérents.
9. Utiliser ce modèle pour émettre un badge avec les données de test.
10. Vérifier la création du JSON dans `badge83/data/issued/`.
11. Vérifier la création du PNG baked dans `badge83/data/baked/`.
12. Ouvrir la page de vérification publique.
13. Ouvrir la page QR du badge.
14. Noter toute anomalie d'affichage ou de placement.

### Résultat attendu

- les routes du constructeur ne produisent plus d'erreur SQLite ;
- le modèle se charge ;
- la prévisualisation est utilisable ;
- l'émission depuis modèle fonctionne ;
- le badge généré reste vérifiable.

## 7. Scénario 3 — Vérification publique et page QR

### Objectif

Se concentrer sur l'expérience de vérification côté utilisateur externe : ouverture de la page publique, lisibilité du résultat et accès par QR.

### Données de test proposées

```text
Nom : Apprenant Test QR
Email : test.qr@example.com
Badge / formation : Badge vérification QR
```

### Étapes

1. Émettre un badge dédié au test QR.
2. Ouvrir la page de résultat après émission.
3. Identifier le lien de vérification publique.
4. Ouvrir ce lien dans le navigateur.
5. Vérifier que le statut du badge est compréhensible.
6. Vérifier les informations affichées : titulaire, badge, émetteur, date si disponible.
7. Ouvrir la page QR associée.
8. Vérifier que le QR est visible et suffisamment lisible.
9. Si un smartphone est disponible, scanner le QR.
10. Confirmer que le scan mène à la page attendue.
11. Noter les éventuelles limites UX : texte trop technique, JSON trop visible, message peu clair.

### Résultat attendu

- la page publique s'ouvre ;
- le QR est lisible ;
- le scan ou lien QR mène au bon badge ;
- les informations humaines sont compréhensibles.

## 8. Scénario 4 — Vérification du PNG baked

### Objectif

Vérifier que le PNG généré contient bien les métadonnées Open Badges attendues et qu'il peut être utilisé comme preuve portable.

### Données de test proposées

```text
Nom : Apprenant Test PNG
Email : test.png@example.com
Badge / formation : Badge PNG baked
```

### Étapes

1. Émettre un badge dédié au test PNG.
2. Télécharger ou localiser le PNG baked généré.
3. Vérifier que le fichier PNG s'ouvre correctement comme image.
4. Utiliser la fonction de vérification PNG disponible dans Badge83 si elle est accessible via l'interface.
5. Sinon, utiliser l'outil interne ou la route existante permettant l'extraction/vérification du PNG baked.
6. Contrôler que l'assertion extraite correspond au badge émis.
7. Vérifier que l'identité du titulaire et le badge correspondent aux données de test.
8. Vérifier que le PNG renvoie vers une assertion ou une URL cohérente.
9. Noter le résultat dans le rapport.

### Résultat attendu

- le PNG baked est généré ;
- le PNG reste une image valide ;
- les données Open Badges sont présentes ou récupérables ;
- la vérification du PNG ne contredit pas la page publique.

## 9. Scénario 5 — Variantes de données et registre local

### Objectif

Vérifier que Badge83 supporte plusieurs émissions avec des données différentes et que le registre local reste cohérent.

### Données de test proposées

```text
Nom : Apprenant Test Registre
Email : test.registre@example.com
Badge / formation : Badge registre local
```

Variante possible : utiliser un autre intitulé de formation ou un autre modèle pour vérifier que le registre distingue correctement les badges.

### Étapes

1. Émettre un badge avec les données de test.
2. Vérifier que le badge apparaît dans le registre ou la liste des badges si l'interface le permet.
3. Contrôler les informations affichées : nom, email, badge, date, présence JSON/PNG.
4. Ouvrir le détail du badge si disponible.
5. Ouvrir la page de vérification depuis le registre.
6. Vérifier que les fichiers JSON et PNG existent.
7. Si une recherche est disponible, rechercher par nom ou email.
8. Noter les incohérences éventuelles : doublons, absence d'entrée, mauvais lien, donnée manquante.

### Résultat attendu

- le badge est enregistré ;
- les informations principales sont retrouvables ;
- les liens vers JSON/PNG/vérification sont cohérents ;
- aucune régression visible du registre local.

## 10. Contrôles transverses à faire après les cinq scénarios

Après les scénarios, vérifier rapidement les logs :

```bash
cd /home/ubuntu/projects/Mode83/badge83
tail -n 80 server.log
```

Rechercher notamment :

```text
sqlite3.ProgrammingError
SQLite objects created in a thread
Internal Server Error
Traceback
```

Si rien de critique n'apparaît, le noter dans le rapport.

Arrêter ensuite le serveur :

```bash
./badge83.sh stop
```

## 11. Anomalies à documenter proprement

Pour chaque anomalie, utiliser ce format :

```text
Anomalie :
Scénario concerné :
Étape :
Résultat attendu :
Résultat obtenu :
Gravité : bloquant / gênant / mineur
Capture ou preuve : oui / non
Action proposée :
```

## 12. Décision attendue en fin de journée

À la fin du 12/05, il faut pouvoir écrire l'une des conclusions suivantes :

### Cas favorable

```text
La validation fonctionnelle Projet A est concluante sur les scénarios testés. Les fonctions principales d'émission, génération PNG baked, QR code et vérification publique sont opérationnelles. Les anomalies restantes ne bloquent pas la démonstration.
```

### Cas partiellement favorable

```text
La validation fonctionnelle Projet A est globalement positive, mais certaines anomalies doivent être corrigées avant démonstration ou remise finale.
```

### Cas défavorable

```text
La validation Projet A révèle encore un ou plusieurs blocages fonctionnels. La priorité doit rester à la correction avant de démarrer le Projet B blockchain.
```

## 13. Priorité si le temps manque

Si la journée est trop courte, respecter cet ordre :

1. pytest ;
2. démarrage serveur local sûr ;
3. scénario 1 badge standard ;
4. scénario 2 badge via modèle constructeur ;
5. scénario 3 QR/page publique ;
6. rapport `test-report-projet-a-120526.md` même incomplet ;
7. scénario 4 PNG baked ;
8. scénario 5 registre local ;
9. guide formateur seulement si la validation est suffisamment avancée.
