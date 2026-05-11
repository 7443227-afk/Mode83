# Rapport de debug — Badge83 — erreur SQLite threading

Date : 11/05/2026  
Projet : Badge83 — Open Badges MODE83  
Objet : correction et validation d'une erreur SQLite sur le constructeur de badges

## 1. Contexte

Lors de l'analyse du projet Badge83, le fichier `badge83/server.log` montrait des erreurs intermittentes sur les routes du constructeur de badges.

Routes concernées observées :

```text
/badge-constructor/schemas
/badge-constructor/templates
```

Erreur observée :

```text
sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread.
```

Cette erreur apparaissait au moment de la fermeture de la connexion SQLite dans les dépendances FastAPI `get_db()` des routes du constructeur.

## 2. Diagnostic

Fichiers analysés :

```text
badge83/app/database.py
badge83/app/routes/badge_constructor/schemas.py
badge83/app/routes/badge_constructor/templates.py
```

Dans les routes du constructeur, la connexion SQLite est fournie par une dépendance FastAPI de type generator :

```python
def get_db():
    conn = init_db_schema()
    try:
        yield conn
    finally:
        close_connection(conn)
```

La connexion était créée dans `badge83/app/database.py` avec :

```python
conn = sqlite3.connect(str(resolved_path))
```

Par défaut, SQLite impose qu'un objet connexion soit utilisé et fermé dans le même thread que celui où il a été créé. Or, avec FastAPI / Starlette / AnyIO, l'exécution d'une route synchrone et la finalisation de la dépendance peuvent passer par des worker threads différents.

Conclusion du diagnostic :

- la logique métier Open Badges n'était pas en cause ;
- le registre SQLite n'était pas corrompu ;
- le problème venait du lifecycle de la connexion SQLite dans un contexte FastAPI multi-thread.

## 3. Correction appliquée

Fichier modifié :

```text
badge83/app/database.py
```

Modification dans `init_database()` :

```python
conn = sqlite3.connect(
    str(resolved_path),
    timeout=10,
    check_same_thread=False,
)
```

Effet de la correction :

- `check_same_thread=False` permet à la connexion SQLite d'être fermée même si le finalizer FastAPI s'exécute dans un autre thread ;
- `timeout=10` donne à SQLite un délai raisonnable en cas de verrouillage temporaire de la base ;
- le format des données, les assertions Open Badges, le baking PNG et les routes fonctionnelles ne sont pas modifiés.

## 4. Tests automatisés

Commande exécutée :

```bash
cd /home/ubuntu/projects/Mode83/badge83
/home/ubuntu/projects/Mode83/.venv/bin/python -m pytest tests -q
```

Résultat :

```text
24 passed in 1.05s
```

La suite automatisée Badge83 passe après correction.

## 5. Vérification API sans serveur externe

Une vérification rapide a été faite avec `FastAPI TestClient` sur les deux routes concernées :

```text
/badge-constructor/schemas -> 200
/badge-constructor/templates -> 200
```

Cette vérification confirme que les routes répondent correctement dans le contexte applicatif Python.

## 6. Vérification sur serveur Uvicorn réel

Le serveur Badge83 a ensuite été lancé sur :

```text
127.0.0.1:8000
PID 1843745
```

Les routes problématiques ont été appelées 20 fois chacune sur le serveur réellement démarré :

```text
/badge-constructor/schemas   -> 200 OK, 20/20
/badge-constructor/templates -> 200 OK, 20/20
```

Les logs frais du processus serveur ont été inspectés pour rechercher :

```text
sqlite3.ProgrammingError
SQLite objects created in a thread
Internal Server Error
Traceback
```

Résultat : aucune nouvelle erreur SQLite/threading n'a été observée après le redémarrage et les appels répétés.

Le serveur a ensuite été arrêté proprement :

```text
Statut : ARRÊTÉ
```

## 7. Point d'attention secondaire observé et corrigé

Lors du lancement de test, la commande avait été appelée avec :

```bash
BADGE83_ENABLE_FIREWALL_MANAGEMENT=false ./badge83.sh start
```

Mais le fichier `badge83/badge83.env` contient :

```text
BADGE83_ENABLE_FIREWALL_MANAGEMENT=true
```

Comme `badge83.sh` charge ensuite le fichier `badge83.env`, la valeur du fichier a repris le dessus et le script a ouvert puis refermé les ports publics 80/443.

Ce n'était pas le bug SQLite, mais c'était un point d'amélioration du script : les variables passées explicitement en ligne de commande devaient avoir priorité sur les valeurs du fichier de configuration.

Correction appliquée dans :

```text
badge83/badge83.sh
```

Le script conserve maintenant les variables `BADGE83_*` déjà présentes dans l'environnement shell avant de charger `badge83.env`, puis les restaure après le chargement du fichier.

L'ordre de priorité retenu est donc :

1. variables passées explicitement dans le shell ;
2. valeurs de `badge83.env` ;
3. valeurs par défaut internes à `badge83.sh`.

Vérification syntaxique :

```bash
bash -n badge83/badge83.sh
```

Résultat : OK.

Vérification du cas problématique :

```bash
cd badge83 && BADGE83_ENABLE_FIREWALL_MANAGEMENT=false ./badge83.sh status | grep 'Firewall'
```

Résultat :

```text
Firewall   : gestion automatique = false ; ports publics = 80,443
```

La vérification a été réalisée avec `status`, sans ouvrir ni fermer de ports firewall.

## 8. Conclusion

Le bug SQLite identifié dans les logs est corrigé dans le scénario testé.

État après correction :

- tests automatisés : OK ;
- routes constructeur via TestClient : OK ;
- routes constructeur sur serveur Uvicorn réel : OK ;
- nouvelles erreurs SQLite/threading dans les logs frais : aucune ;
- serveur arrêté proprement après test ;
- priorité des variables d'environnement dans `badge83.sh` : corrigée et vérifiée avec `status`.

## 9. Plan de travail restant pour aujourd'hui

### Priorité 1 — Sécuriser la correction dans Git


1. Vérifier le diff complet :

   ```bash
   cd /home/ubuntu/projects/Mode83
   git diff -- badge83/app/database.py formation/110526_rapport_debug_sqlite_badge83.md
   ```

2. Vérifier l'état Git :

   ```bash
   git status --short
   ```

3. Préparer un commit clair si demandé :

   ```text
   fix(badge83): allow sqlite connection finalization across FastAPI worker threads
   ```

### Priorité 2 — Tester un parcours opérateur court


Relancer temporairement le serveur, puis vérifier dans le navigateur ou via API :

1. ouverture de l'interface principale ;
2. liste des schémas ;
3. liste des modèles ;
4. prévisualisation d'un modèle ;
5. émission d'un badge depuis un modèle si un modèle de test est disponible ;
6. consultation de la page QR du badge généré.

Objectif : confirmer que la correction technique ne se limite pas aux routes de liste, mais soutient le flux opérateur.

### Priorité 3 — Corriger le comportement de priorité des variables d'environnement


Statut : fait.

Le script `badge83.sh` a été ajusté pour que les variables déjà présentes dans l'environnement shell gardent priorité sur le fichier `badge83.env`.

La vérification sûre suivante confirme que le paramètre explicite est bien conservé :

```bash
cd badge83 && BADGE83_ENABLE_FIREWALL_MANAGEMENT=false ./badge83.sh status | grep 'Firewall'
```

Résultat :

```text
Firewall   : gestion automatique = false ; ports publics = 80,443
```

### Priorité 4 — Préparer le rapport de stabilisation dans `badge83/docs`


Statut : fait.

Rapport créé et complété :

```text
badge83/docs/rapport-travail-110526-stabilisation.md
```

Contenu :

- bug initial ;
- correction appliquée ;
- tests ;
- résultat serveur ;
- point d'attention firewall/env ;
- prochaines tâches Projet A.

### Priorité 5 — Continuer la clôture Projet A


Si le temps reste disponible aujourd'hui :

1. commencer le guide formateur MODE83 ;
2. préparer le test de parcours complet sur plusieurs badges ;
3. lister les captures ou preuves à produire pour la validation Projet A.