# Rapport de test — Validation Projet A — 12/05/2026

Date : 12/05/2026  
Projet : Badge83 — Open Badges MODE83  
Objet : validation fonctionnelle de bout en bout du Projet A

## 1. Objectif

L'objectif de la journée est de vérifier que le **Projet A — Open Badges MODE83** fonctionne sur un parcours complet :

1. émission d'un badge ;
2. création d'une assertion JSON ;
3. génération d'un PNG baked ;
4. accès à la page publique de vérification ;
5. accès à la page QR ;
6. extraction et vérification des métadonnées Open Badges depuis le PNG ;
7. présence du badge dans le registre local.

Cette validation fait suite au travail de stabilisation du 11/05/2026, notamment la correction de l'erreur SQLite/threading observée sur les routes du constructeur.

## 2. Environnement de test

Répertoire projet :

```text
/home/ubuntu/projects/Mode83
```

État Git au démarrage :

```text
Dernier commit : 7037753 11/05
Fichier non suivi : badge83/docs/plan-validation-projet-a-120526.md
```

Serveur Badge83 lancé localement avec gestion firewall désactivée :

```bash
cd /home/ubuntu/projects/Mode83/badge83
BADGE83_ENABLE_FIREWALL_MANAGEMENT=false ./badge83.sh start
```

Statut observé :

```text
Statut     : ACTIF
PID        : 1912363
Écoute     : 127.0.0.1:8000
URL de base: https://mode83.ddns.net
Firewall   : gestion automatique = false ; ports publics = 80,443
```

Contrôles initiaux :

| Route | Résultat |
|---|---:|
| `/` | 200 |
| `/badge-constructor/schemas` | 200 |
| `/badge-constructor/templates` | 200 |

État du constructeur au moment du test :

```text
Schémas disponibles : 2
Modèles disponibles : 4
Modèle utilisé pour le scénario constructeur : Badge 83
ID modèle : 4197ef6c-d34f-4aed-8623-100b17b244d7
```

## 3. Résultat des tests automatisés

Commande exécutée avant la recette fonctionnelle :

```bash
cd /home/ubuntu/projects/Mode83/badge83
/home/ubuntu/projects/Mode83/.venv/bin/python -m pytest tests -q
```

Résultat :

```text
24 passed in 1.08s
```

Conclusion : la suite automatisée existante passe avant validation manuelle/API.

## 4. Scénarios exécutés

Les scénarios ont été exécutés contre le serveur local :

```text
http://127.0.0.1:8000
```

Les PNG de preuve générés pendant la recette ont aussi été copiés temporairement dans :

```text
/tmp/badge83-validation-120526
```

### 4.1 Scénario 1 — Badge standard simple

Données :

```text
Nom : Apprenant Test Standard
Email : test.standard@example.com
```

Résultat :

```text
Assertion ID : c7d55c93-ddbb-48d9-9aa4-461cfffb615f
PNG généré : oui, 23351 octets
```

Contrôles :

| Élément | Résultat |
|---|---:|
| Émission `/issue-baked` | 200 |
| JSON `/api/badges/{id}/json` | 200 |
| PNG `/api/badges/{id}/png` | 200 |
| Page vérification `/verify/badge/{id}` | 200 |
| Page QR `/verify/qr/{id}` | 200 |
| Inspection PNG `/api/badges/{id}/inspect` | 200 |
| Upload PNG `/verify-baked` | valide |

### 4.2 Scénario 2 — Badge émis depuis un modèle constructeur

Données :

```text
Nom : Apprenant Test Modèle
Email : test.modele@example.com
Modèle : Badge 83
ID modèle : 4197ef6c-d34f-4aed-8623-100b17b244d7
```

Valeurs de champs utilisées :

```json
{
  "course_name": "Validation Projet A",
  "certificate_number": "VAL-120526-001",
  "issue_date": "2026-05-12"
}
```

Résultat :

```text
Assertion ID : a051e23e-c0f8-467d-a120-b9e412930d61
PNG généré : oui, 25463 octets
Prévisualisation modèle : 200
```

Contrôles :

| Élément | Résultat |
|---|---:|
| Liste des modèles | 200 |
| Prévisualisation modèle | 200 |
| Émission `/templates/{template_id}/issue-baked` | 200 |
| JSON `/api/badges/{id}/json` | 200 |
| PNG `/api/badges/{id}/png` | 200 |
| Page vérification `/verify/badge/{id}` | 200 |
| Page QR `/verify/qr/{id}` | 200 |
| Inspection PNG `/api/badges/{id}/inspect` | 200 |
| Upload PNG `/verify-baked` | valide |

Conclusion : le constructeur reste fonctionnel après correction SQLite.

### 4.3 Scénario 3 — Vérification publique et page QR

Données :

```text
Nom : Apprenant Test QR
Email : test.qr@example.com
```

Résultat :

```text
Assertion ID : b4fe995e-bdc5-4317-8f3c-627f9cfc0310
PNG généré : oui, 23628 octets
```

Contrôles :

| Élément | Résultat |
|---|---:|
| Émission `/issue-baked` | 200 |
| Page vérification `/verify/badge/{id}` | 200 |
| Page QR `/verify/qr/{id}` | 200 |
| JSON | 200 |
| PNG | 200 |
| Upload PNG `/verify-baked` | valide |

Conclusion : le parcours de vérification publique et QR est accessible pour le badge généré.

### 4.4 Scénario 4 — Vérification du PNG baked

Données :

```text
Nom : Apprenant Test PNG
Email : test.png@example.com
```

Résultat :

```text
Assertion ID : 41a9d0e6-952c-4542-a6bd-93ce8ff593ce
PNG généré : oui, 23492 octets
```

Contrôles :

| Élément | Résultat |
|---|---:|
| Émission `/issue-baked` | 200 |
| Inspection PNG `/api/badges/{id}/inspect` | 200 |
| Upload PNG `/verify-baked` | valide |
| Assertion extraite | `https://mode83.ddns.net/assertions/41a9d0e6-952c-4542-a6bd-93ce8ff593ce` |

Conclusion : le PNG baked contient bien des métadonnées Open Badges récupérables.

### 4.5 Scénario 5 — Variantes de données et registre local

Données :

```text
Nom : Apprenant Test Registre
Email : test.registre@example.com
```

Résultat :

```text
Assertion ID : 523855ba-82c1-481a-bcb9-ba6d0b57d0ee
PNG généré : oui, 23166 octets
```

Contrôles :

| Élément | Résultat |
|---|---:|
| Émission `/issue-baked` | 200 |
| JSON | 200 |
| PNG | 200 |
| Page vérification | 200 |
| Page QR | 200 |
| Upload PNG `/verify-baked` | valide |
| Total registre après test | 90 badges |
| Badge présent dans `/api/badges` | oui |
| Recherche par email | 1 résultat |
| Badge trouvé par recherche email | oui |

Conclusion : le registre local est cohérent pour le badge de test et la recherche par email fonctionne.

## 5. Tableau de synthèse

| Scénario | Assertion JSON | PNG baked | QR/page QR | Page vérification | Vérification PNG | Résultat | Notes |
|---|---|---|---|---|---|---|---|
| 1 — Badge standard | OK | OK | OK | OK | OK | OK | Parcours standard validé |
| 2 — Modèle constructeur | OK | OK | OK | OK | OK | OK | Modèle `Badge 83`, prévisualisation OK |
| 3 — QR/public | OK | OK | OK | OK | OK | OK | Page QR et page publique accessibles |
| 4 — PNG baked | OK | OK | OK | OK | OK | OK | Métadonnées extraites depuis le PNG |
| 5 — Registre local | OK | OK | OK | OK | OK | OK | Présent dans registre et recherche email OK |

## 6. Contrôle des logs

Commande exécutée après les scénarios :

```bash
cd /home/ubuntu/projects/Mode83/badge83
tail -n 180 server.log | grep -E "sqlite3\.ProgrammingError|SQLite objects created in a thread|Internal Server Error|Traceback|ERROR" -C 2 || true
```

Résultat : aucune occurrence critique trouvée dans le bloc de logs inspecté.

Éléments recherchés :

```text
sqlite3.ProgrammingError
SQLite objects created in a thread
Internal Server Error
Traceback
ERROR
```

Conclusion : pas de régression visible de l'erreur SQLite/threading pendant les scénarios de validation.

## 7. Anomalies observées

### 7.1 Point mineur corrigé — résumé `/verify-baked`

Pendant la recette, le résumé retourné par `/verify-baked` affichait initialement :

```text
recipient_name : unknown
```

Cause : le vérificateur lisait `recipient.name`, alors que Badge83 stocke volontairement l'identité Open Badges standard sous forme hashée dans `recipient` :

```text
recipient.type = email
recipient.hashed = true
recipient.identity = sha256$...
```

Le nom opérateur est conservé dans le bloc interne `admin_recipient`.

Correction appliquée dans :

```text
badge83/app/verifier.py
```

Le résumé utilise maintenant `admin_recipient.name` en priorité, puis `recipient.name` si disponible, puis `unknown` en dernier recours.

Vérification après correction :

```text
pytest : 24 passed in 1.04s
verify_baked_badge(...).summary.recipient_name : Apprenant Test Standard
```

Gravité résiduelle : aucune pour ce point.

### 7.2 Point de suivi Git

Le fichier suivant existe comme plan de travail mais n'était pas encore suivi par Git au démarrage :

```text
badge83/docs/plan-validation-projet-a-120526.md
```

Action proposée : l'ajouter au prochain commit avec le présent rapport si l'on souhaite conserver la trace de planification.

## 8. Conclusion de validation Projet A

La validation fonctionnelle du **Projet A — Open Badges MODE83** est concluante sur les scénarios testés le 12/05/2026.

Les fonctions principales sont opérationnelles :

- émission de badges ;
- génération d'assertions JSON ;
- génération de PNG baked ;
- vérification du PNG baked ;
- pages publiques de vérification ;
- pages QR ;
- routes du constructeur ;
- émission depuis un modèle constructeur ;
- registre local et recherche.

Les tests automatisés passent et aucune nouvelle erreur SQLite/threading n'a été observée dans les logs après les scénarios.

Décision recommandée : considérer le Projet A comme fonctionnellement validé pour les parcours principaux, puis poursuivre la semaine avec :

1. la rédaction du guide formateur MODE83 ;
2. les finitions UX opérateur prioritaires ;
3. le rapport final de validation Projet A ;
4. seulement ensuite la décision de cadrage du Projet B blockchain.