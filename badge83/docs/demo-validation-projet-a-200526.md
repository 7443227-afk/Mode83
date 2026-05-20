# Script de démonstration — Validation Projet A — Badge83 — 20/05/2026

Date : 20/05/2026  
Projet : Badge83 — Open Badges MODE83  
Objet : scénario de démonstration de 10 à 15 minutes pour valider le Projet A du cahier des charges

## 1. Objectif de la démonstration

Montrer que Badge83 permet bien de :

1. représenter MODE83 comme émetteur Open Badges ;
2. émettre une assertion pour un apprenant ;
3. générer un badge PNG baked ;
4. remettre ce badge à l'apprenant ;
5. vérifier publiquement le badge ;
6. consulter les métadonnées Open Badges associées.

## 2. Préparation

Commandes de contrôle :

```bash
cd /home/ubuntu/projects/Mode83/badge83
/home/ubuntu/projects/Mode83/.venv/bin/python -m pytest tests -q
./badge83.sh status
```

Si le serveur est arrêté et qu'une démonstration live est prévue :

```bash
./badge83.sh start
./badge83.sh status
```

URL de démonstration locale ou publique selon configuration :

```text
http://127.0.0.1:8000
https://mode83.ddns.net
```

## 3. Démonstration principale Projet A

### Étape 1 — Présenter le standard Open Badges

Montrer rapidement les trois objets du standard :

- Issuer : MODE83 ;
- BadgeClass : formation / certification ;
- Assertion : badge remis à un apprenant.

Preuves dans le projet :

```text
badge83/data/issuer_template.json
badge83/data/badgeclass_template.json
badge83/app/issuer.py
```

### Étape 2 — Montrer les endpoints publics HostedBadge

Ouvrir ou tester :

```text
/issuers/main
/badges/blockchain-foundations
```

Message à transmettre : les validateurs externes peuvent résoudre les URLs publiques contenues dans les assertions.

### Étape 3 — Émettre un badge individuel

Depuis l'interface ou via API, émettre un badge pour un apprenant fictif.

Exemple de données :

```text
Nom : Alice Validation
Email : alice.validation@example.org
Formation : Blockchain MODE83
```

Résultat attendu : création d'une assertion JSON et d'un PNG baked.

### Étape 4 — Télécharger ou ouvrir le PNG baked

Montrer que le badge est une image PNG utilisable par l'apprenant.

Message à transmettre : le badge contient visuellement l'attestation et techniquement les métadonnées Open Badges.

### Étape 5 — Vérifier le PNG par upload

Utiliser la vérification baked :

```text
POST /verify-baked
```

ou l'interface de vérification.

Résultat attendu : badge valide, informations apprenant, issuer MODE83, date, statut.

### Étape 6 — Vérifier par QR code / page publique

Scanner ou ouvrir l'URL :

```text
/verify/qr/<assertion_id>
/verify/badge/<assertion_id>
```

Résultat attendu : page lisible de vérification humaine.

### Étape 7 — Montrer l'assertion publique

Ouvrir :

```text
/assertions/<assertion_id>
```

Message à transmettre : l'assertion suit la structure Open Badges 2.0 et référence Issuer / BadgeClass par URL.

## 4. Démonstration bonus hors cahier des charges

Si le temps le permet, montrer que Badge83 dépasse le Projet A minimal.

### Bonus A — Constructeur de badges

Montrer :

- schéma de champs ;
- modèle visuel ;
- textes dynamiques ;
- position QR ;
- preview.

### Bonus B — Émission groupée CSV/XLSX

Scénario court :

1. sélectionner un modèle ;
2. télécharger le modèle Excel adapté ;
3. importer un fichier CSV/XLSX ;
4. afficher la preview ;
5. confirmer l'émission ;
6. télécharger l'archive ZIP ;
7. montrer `rapport_emission.csv`, `manifest.json` et `badges/*.png`.

Message à transmettre : ce module facilite l'usage réel par promotions ou sessions de formation.

## 5. Conclusion à prononcer

Conclusion proposée :

```text
Le Projet A demandé par le cahier des charges est opérationnel : Badge83 émet des badges Open Badges MODE83, génère des PNG baked, expose les métadonnées publiques et permet la vérification. Le projet est prêt pour validation référent. Les fonctionnalités CSV/XLSX, constructeur et registre constituent des améliorations au-delà du périmètre obligatoire.
```
