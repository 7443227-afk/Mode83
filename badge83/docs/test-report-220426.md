# Rapport de tests Badge83 — 22/04/2026

## 1. Objet

Ce document présente les tests effectivement mis en place aujourd'hui sur le projet **Badge83**, ainsi que la méthode utilisée pour préparer une base de test reproductible sans impacter les données déjà émises dans le projet.

L'objectif de cette première itération n'était pas encore de couvrir l'ensemble de l'application, mais de :

- mettre en place une infrastructure de test locale simple ;
- isoler les tests des répertoires métier réels (`data/issued`, `data/baked`) ;
- valider les premières fonctions critiques du noyau applicatif ;
- confirmer que le projet peut désormais être testé automatiquement avec `pytest` ;
- inscrire ces tests dans un environnement de travail Python stable et reproductible ;
- commencer à réduire la dispersion de la configuration technique.

---

## 2. Périmètre testé

Les tests ajoutés aujourd'hui couvrent principalement deux modules :

- `badge83/app/issuer.py`
- `badge83/app/baker.py`

Ils s'appuient sur une infrastructure de test créée dans :

- `badge83/tests/conftest.py`
- `badge83/tests/unit/test_issuer.py`
- `badge83/tests/unit/test_baker.py`

---

## 3. Méthodologie retenue

### 3.1. Isolation de l'environnement de test

Un point important de la méthode a été de **ne pas exécuter les tests sur les données réelles du projet**.

Pour cela, les tests utilisent :

- des répertoires temporaires créés par `pytest` ;
- un PNG de test généré en mémoire ;
- des templates JSON minimaux créés dynamiquement pendant l'exécution.

Cette approche permet de vérifier le comportement du code sans :

- modifier les badges déjà émis ;
- écrire dans les dossiers de production ;
- dépendre d'un état préalable du projet.

### 3.2. Utilisation de fixtures

Le fichier `conftest.py` fournit notamment :

- une fixture `sample_png_bytes` qui génère un PNG valide en mémoire ;
- une fixture `isolated_issuer_env` qui redirige les chemins du module `issuer` et du module `verifier` vers un environnement temporaire.

La logique utilisée consiste à **monkeypatcher** les constantes de chemins et certaines variables d'environnement, notamment :

- `BADGE83_BASE_URL`
- `BADGE83_SEARCH_PEPPER`

De cette manière, les tests vérifient la logique fonctionnelle tout en restant déterministes.

### 3.3. Environnement d'exécution

Le système Python global étant protégé par un environnement géré de type PEP 668, l'installation de `pytest` n'a pas été faite au niveau système.

Une solution propre a donc été retenue :

- création d'un environnement virtuel local : `/home/ubuntu/projects/Mode83/.venv`
- installation des dépendances du projet dans cet environnement
- exécution des tests via le Python de ce virtualenv

Cette méthode évite toute pollution du système et rend le lancement des tests reproductible.

Au-delà du simple besoin de test, ce virtualenv doit désormais être considéré comme **l'environnement de travail standard du projet** : il sert à installer les dépendances, à lancer le serveur et à exécuter les tests.

### 3.4. Centralisation initiale de la configuration

Dans le prolongement de ce travail, une première couche de configuration commune a été introduite dans :

- `badge83/app/config.py`

Ce module centralise désormais :

- les répertoires `data`, `issued` et `baked` ;
- les chemins vers les templates JSON ;
- le chemin vers l'image de badge par défaut ;
- la construction de l'URL publique du projet ;
- le `BADGE83_SEARCH_PEPPER`.

Cette évolution améliore la cohérence de l'application et simplifie les tests, qui peuvent s'appuyer sur un point de configuration plus explicite.

---

## 4. Tests réalisés

### 4.1. Tests sur `issuer.py`

Les points suivants ont été vérifiés :

1. **Normalisation des entrées**
   - `normalize_email`
   - `normalize_name`

   Vérification : suppression des espaces parasites, homogénéisation de la casse, réduction des espaces multiples.

2. **Métadonnées de recherche**
   - `make_search_metadata`

   Vérification : calcul cohérent des hash à partir des valeurs normalisées.

3. **Émission d'une assertion JSON**
   - `issue_badge`

   Vérification :
   - création d'un `assertion_id` ;
   - structure de l'assertion de type `Assertion` ;
   - présence d'une `verification` de type `HostedBadge` ;
   - présence des métadonnées administratives ;
   - persistance correcte du fichier JSON dans le répertoire temporaire.

4. **Émission d'un badge baked**
   - `issue_baked_badge`

   Vérification :
   - création du PNG baked ;
   - sauvegarde du fichier dans le dossier temporaire ;
   - génération correcte de l'URL de vérification QR ;
   - production d'un nom de téléchargement cohérent.

### 4.2. Tests sur `baker.py`

Les points suivants ont été validés :

1. **Cycle complet baking / unbaking**
   - `bake_badge_from_bytes`
   - `unbake_badge`

   Vérification : l'assertion injectée dans le PNG est correctement relue sans perte.

2. **Re-baking d'un PNG déjà baké**

   Vérification : si un badge contient déjà un chunk `openbadges`, celui-ci est bien remplacé, et non dupliqué.

3. **Gestion des entrées invalides**

   Vérification : un contenu non-PNG provoque bien une erreur explicite.

---

## 5. Résultat d'exécution

Commande utilisée :

```bash
/home/ubuntu/projects/Mode83/.venv/bin/python -m pytest /home/ubuntu/projects/Mode83/badge83/tests -q
```

Résultat obtenu :

```text
.......                                                                  [100%]
7 passed in 0.07s
```

Cette exécution confirme que la première base de tests automatisés est opérationnelle.

Elle confirme également que la centralisation initiale de la configuration n'a pas cassé le socle de tests déjà en place.

---

## 6. Limites actuelles

Cette première série de tests reste volontairement ciblée.

À ce stade, ne sont pas encore couverts automatiquement :

- `badge83/app/verifier.py`
- `badge83/app/qr.py`
- les routes FastAPI de `badge83/app/main.py`
- les scénarios d'intégration complets émission → baking → vérification HTTP
- les tests de conformité externe avec un validateur Open Badges tiers

Autrement dit, le socle est prêt, mais la campagne de test n'en est qu'à sa première étape.

Il faut donc lire ce document comme le rapport d'une **première base de qualité** et non comme un achèvement complet de la stratégie de test.

---

## 7. Évaluation de la méthode

La méthode choisie est satisfaisante pour une première montée en qualité, pour plusieurs raisons :

- elle est **non destructive** ;
- elle est **rapide à exécuter** ;
- elle cible d'abord le **noyau métier** ;
- elle prépare proprement l'extension vers les tests API et les tests d'intégration.

Le principal bénéfice obtenu aujourd'hui est donc moins le nombre brut de tests que la mise en place d'un **cadre de test fiable et extensible**, désormais mieux aligné avec le fonctionnement réel du projet.

---

## 8. Prochaines étapes recommandées

Les prolongements naturels sont les suivants :

1. ajouter des tests unitaires pour `verifier.py` ;
2. ajouter des tests unitaires pour `qr.py` ;
3. créer les premiers tests API avec `FastAPI TestClient` ;
4. mettre en place au moins un scénario d'intégration complet ;
5. documenter ensuite une matrice claire entre fonctionnalités et fichiers de test.

En parallèle, il est recommandé de poursuivre la migration des autres modules vers la configuration centralisée lorsque cela apportera un bénéfice clair en lisibilité ou en testabilité.

---

## 9. Conclusion

La séance du 22/04/2026 a permis de transformer le plan de test théorique en une **première base de validation automatique réellement exécutable**.

Le résultat est modeste en volume, mais solide sur le plan méthodologique : le projet dispose désormais d'un point d'entrée concret pour industrialiser ses tests sans perturber le fonctionnement actuel de Badge83.

En complément, le projet dispose maintenant d'un environnement de travail Python explicitement standardisé et d'une première couche de configuration centralisée, deux éléments qui renforcent directement la robustesse de la suite des travaux.