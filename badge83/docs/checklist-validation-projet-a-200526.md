# Checklist de validation — Projet A Open Badges MODE83 — 20/05/2026

Date : 20/05/2026  
Projet : Badge83 — Open Badges MODE83  
Objet : correspondance entre le cahier des charges stagiaire et l'état actuel du Projet A

## 1. Synthèse

Le cahier des charges définit le **Projet A** comme le livrable obligatoire du stage : documenter et mettre en œuvre un système Open Badges 2.0 permettant d'émettre, remettre et vérifier des badges numériques MODE83.

Au 20/05/2026, Badge83 couvre les exigences obligatoires du Projet A et ajoute plusieurs fonctionnalités complémentaires utiles pour un usage interne MODE83 : constructeur de badges, QR code visible, registre SQLite, bureau de vérification et émission groupée CSV/XLSX.

## 2. Checklist cahier des charges

| Exigence Projet A | État Badge83 | Preuve / fichier |
|---|---:|---|
| Documentation de référence Open Badges MODE83 | OK | `docs/technical-baking-verification.md`, `docs/reference-obi-sample.md`, `docs/openbadges-validator-keys-reference.md` |
| Fichiers JSON Issuer et BadgeClass | OK | `data/issuer_template.json`, `data/issuer.json`, `data/badgeclass_template.json`, `data/badgeclass.json` |
| Script / code Python d'émission d'une Assertion | OK | `app/issuer.py`, routes `POST /issue`, `POST /issue-baked` |
| Badge signé / baked PNG avec métadonnées embarquées | OK | `app/baker.py`, dossier `data/baked/`, endpoint `POST /issue-baked` |
| Page ou endpoint de vérification publique | OK | `app/main.py`, `app/routes/verify.py`, templates `verify_badge.html`, `verify_qr.html` |
| Guide d'utilisation formateur MODE83 | OK | `docs/guide-formateur-mode83.md` |
| Dépôt Git documenté avec README | OK | `README.md`, branche `main` publiée sur GitHub |
| Tests du parcours complet | OK | `tests/`, `docs/test-report-projet-a-120526.md`, `docs/rapport-validation-projet-a-150526.md` |
| Validation formelle Projet A à présenter au référent | Prêt | Présente checklist + script de démonstration |

## 3. Éléments dépassant le périmètre minimal

Badge83 contient aussi des éléments au-delà du cahier des charges Projet A initial :

- constructeur opérateur de badges ;
- modèles visuels réutilisables ;
- QR code visible de vérification ;
- bureau de vérification administratif ;
- registre SQLite local ;
- recherche administrative par hash ;
- protection des routes administrateur ;
- garde-fous production ;
- limites d'upload configurables ;
- émission groupée CSV/XLSX ;
- archive ZIP batch avec PNG, rapport CSV et manifeste ;
- historisation des sessions batch.

Ces ajouts renforcent la démonstration mais ne doivent pas masquer le message principal : le Projet A obligatoire est validable indépendamment du Projet B.

## 4. Points de contrôle avant démonstration

Avant la présentation au référent, vérifier :

```bash
cd /home/ubuntu/projects/Mode83/badge83
/home/ubuntu/projects/Mode83/.venv/bin/python -m pytest tests -q
./badge83.sh status
```

Critère attendu : tests automatisés en succès et serveur démarrable via `./badge83.sh start` si une démonstration live est prévue.

## 5. Décision proposée

Décision à présenter :

```text
Projet A — Open Badges MODE83 : prêt pour validation référent.
Projet B — Blockchain : peut être préparé comme PoC séparé après validation formelle du Projet A.
```
