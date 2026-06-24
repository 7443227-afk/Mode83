# Badge83 — Documentation maintenue

Ce dossier contient uniquement la documentation finale conservée dans Git pour le projet Badge83. Les notes de travail, plans, rapports, brouillons, documents datés et supports de formation internes sont archivés localement dans `formation/`, dossier ignoré par Git.

## Guides utilisateur et opérateur

| Document | Public | Contenu |
| --- | --- | --- |
| [`guide-formateur-mode83.md`](guide-formateur-mode83.md) | Formateur, opérateur, secrétariat pédagogique | Parcours courant : émettre, vérifier, transmettre et contrôler un badge MODE83. |
| [`guide-edition-modele-constructeur.md`](guide-edition-modele-constructeur.md) | Opérateur avancé, référent pédagogique | Création et modification des modèles de badges, champs dynamiques, QR et prévisualisation. |
| [`guide-emission-groupee-csv.md`](guide-emission-groupee-csv.md) | Opérateur, référent import | Préparer un CSV/XLSX, prévisualiser, émettre un lot, comprendre les rapports et statuts. |
| [`bureau-verification-mode83.md`](bureau-verification-mode83.md) | Opérateur, support, recruteur interne | Utilisation du bureau de vérification pour contrôler un PNG et lire les informations essentielles. |

## Documentation technique

| Document | Public | Contenu |
| --- | --- | --- |
| [`technical-baking-verification.md`](technical-baking-verification.md) | Développeur, intégrateur | Injection/extraction Open Badges dans PNG, vérification baked, compatibilité. |
| [`openbadges-validator-keys-reference.md`](openbadges-validator-keys-reference.md) | Développeur, référent conformité | Clés Open Badges importantes et points contrôlés par les validateurs. |
| [`revocation-model.md`](revocation-model.md) | Développeur, administrateur technique | Modèle de révocation locale et affichage public contrôlé. |
| [`blockchain-anchoring.md`](blockchain-anchoring.md) | Développeur, architecte | Preuve locale par hash, audit, providers d'ancrage et modèle fonctionnel. |
| [`blockchain-evm-anchoring.md`](blockchain-evm-anchoring.md) | Développeur blockchain | Configuration EVM, contrat `Badge83Registry`, scripts Hardhat et vérification externe. |

## Règles de maintien

- Garder ici seulement les documents utiles au projet final.
- Ne pas ajouter de plans de travail, rapports datés, TODO, brouillons ou notes de formation dans `docs/`.
- Placer les documents non publiables ou historiques dans `formation/`.
- Vérifier que les liens depuis `README.md` pointent vers des fichiers existants.
- Mettre à jour cet index lorsqu'un document final est ajouté, renommé ou supprimé.
