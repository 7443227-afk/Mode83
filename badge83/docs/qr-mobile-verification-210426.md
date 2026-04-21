# Documentation technique — QR mobile verification Badge83

## Objectif

Cette évolution ajoute un **QR code visible** sur les badges PNG baked afin de permettre une vérification immédiate depuis un smartphone.

Le principe retenu est le suivant :

- le QR code est un **point d’entrée UX** ;
- il ne remplace pas l’assertion Open Badges embarquée ;
- il ouvre une **page mobile dédiée**, courte, lisible et orientée preuve visuelle ;
- le baking Open Badges reste assuré séparément par le chunk `tEXt` `openbadges`.

---

## Décision produit retenue

Le QR ne pointe pas vers :

- l’assertion JSON brute ;
- la page admin ;
- le bureau de vérification par upload.

Il pointe vers une route dédiée de type :

```text
<BADGE83_BASE_URL>/verify/qr/<assertion_id>
```

Exemple :

```text
http://mode83.ddns.net:8000/verify/qr/8cf3e60f-51e0-4b07-bcf6-c28f7ece1c04
```

Cette route est pensée pour un usage mobile, avec :

- un statut immédiatement lisible ;
- une couleur forte ;
- un message court ;
- un nombre limité d’informations.

---

## Architecture retenue

### 1. Génération du lien QR

Fichier concerné :

- `badge83/app/qr.py`

Fonction :

- `make_verification_qr_url(base_url, assertion_id)`

Elle construit l’URL mobile finale :

```text
<base_url>/verify/qr/<assertion_id>
```

### 2. Génération visuelle du QR

Fichier concerné :

- `badge83/app/qr.py`

Fonction :

- `overlay_qr_on_badge(png_data, qr_text)`

Cette fonction :

- charge le PNG du badge avec Pillow ;
- génère un QR code avec `qrcode` ;
- le redimensionne ;
- lui ajoute une zone blanche de protection (*quiet zone*) ;
- le place dans l’angle inférieur droit du badge ;
- renvoie un nouveau PNG contenant le QR visuel.

### 3. Intégration dans le pipeline d’émission

Fichier concerné :

- `badge83/app/issuer.py`

Fonction concernée :

- `issue_baked_badge(...)`

Pipeline appliqué :

1. création de l’assertion Open Badges ;
2. calcul de l’URL mobile de vérification ;
3. génération du QR ;
4. apposition du QR sur l’image du badge ;
5. baking Open Badges classique via `bake_badge_from_bytes(...)` ;
6. sauvegarde du PNG final dans `data/baked/`.

Autrement dit :

- **QR dans l’image** ;
- **assertion dans les métadonnées PNG**.

Cette séparation évite de mélanger la preuve visuelle et la structure standard Open Badges.

---

## Route mobile de vérification

Fichier concerné :

- `badge83/app/main.py`

Nouvelle route :

```text
GET /verify/qr/{assertion_id}
```

Template associé :

- `badge83/templates/verify_qr.html`

### Rôle de cette page

Cette page est conçue pour être ouverte après un scan QR sur smartphone.

Elle affiche uniquement :

- le statut global de vérification ;
- le nom du badge ;
- l’issuer / organisation ;
- la date de délivrance ;
- l’Assertion ID.

Elle propose en plus :

- un lien vers l’assertion brute ;
- un lien secondaire vers la page de vérification complète.

---

## Logique de vérification affichée

La page mobile s’appuie sur :

- `_collect_badge_record(assertion_id)` ;
- `_build_issuer_check(assertion)` ;
- `_format_display_date(...)`.

### États visuels retenus

#### 1. Badge valide MODE83

- couleur : **vert** ;
- message : `Badge vérifié` ;
- sous-message : `Badge valide et émis par MODE83.`

Condition :

- assertion trouvée dans le registre local ;
- issuer reconnu comme MODE83.

#### 2. Badge valide mais externe

- couleur : **orange** ;
- message : `Badge valide` ;
- sous-message : `Badge valide, mais émis par un autre organisme.`

Condition :

- assertion trouvée ;
- issuer différent de MODE83.

#### 3. Badge introuvable / vérification incomplète

- couleur : **rouge** ;
- message d’erreur explicite.

Cas couverts :

- badge absent du registre local ;
- informations locales incomplètes.

---

## Structure du badge résultant

À l’issue de cette évolution, un badge baked Badge83 combine désormais **deux couches complémentaires**.

### 1. Couche visuelle

Le PNG visible contient :

- le design du badge ;
- le QR code visible en bas à droite.

Le QR contient uniquement une URL de vérification mobile.

### 2. Couche Open Badges embarquée

Le PNG contient toujours un chunk PNG :

- type : `tEXt`
- mot-clé : `openbadges`
- contenu : assertion JSON Open Badges

Structure observée côté assertion :

```json
{
  "@context": "https://w3id.org/openbadges/v2",
  "id": "http://mode83.ddns.net:8000/assertions/<uuid>",
  "type": "Assertion",
  "url": "http://mode83.ddns.net:8000/assertions/<uuid>",
  "recipient": {
    "type": "email",
    "hashed": true,
    "salt": "<salt>",
    "identity": "sha256$..."
  },
  "issuedOn": "<ISO8601>",
  "verification": {
    "type": "HostedBadge",
    "url": "http://mode83.ddns.net:8000/assertions/<uuid>"
  },
  "badge": "http://mode83.ddns.net:8000/badges/blockchain-foundations",
  "issuer": "http://mode83.ddns.net:8000/issuers/main",
  "admin_recipient": {
    "name": "...",
    "email": "..."
  },
  "search": {
    "name_hash": "sha256$...",
    "email_hash": "sha256$..."
  }
}
```

### Important

Le QR ne contient donc **pas** l’assertion elle-même.

Il contient seulement une URL de consultation.

L’assertion standard reste stockée dans le PNG baked et peut toujours être :

- extraite par `unbake_badge(...)` ;
- vérifiée par les flux baked existants ;
- exposée comme HostedBadge.

---

## Comment la vérification est testée

### Vérification 1 — compilation Python

Commande :

```bash
python3 -m py_compile badge83/app/*.py
```

Objectif :

- s’assurer que les nouveaux modules et routes sont syntaxiquement valides.

### Vérification 2 — installation des dépendances dans le virtualenv

Commande :

```bash
/home/ubuntu/projects/Mode83/badge83/.venv/bin/python -m pip install -r badge83/requirements.txt
```

Objectif :

- installer `qrcode` et `Pillow` dans l’environnement du projet.

### Vérification 3 — émission d’un badge avec QR

Test réalisé via :

- `issue_baked_badge(...)`

Points contrôlés :

- création d’un nouvel `assertion_id` ;
- production d’une nouvelle URL QR ;
- écriture du PNG dans `data/baked/`.

### Vérification 4 — conservation du baking Open Badges

Test réalisé via :

- `unbake_badge(result["baked_png_bytes"])`

Point contrôlé :

- l’assertion extraite depuis le PNG correspond bien à l’assertion émise.

### Vérification 5 — disponibilité HTML de la page mobile

Commande de contrôle :

```bash
curl -s http://127.0.0.1:8000/verify/qr/<assertion_id>
```

Point contrôlé :

- la route QR renvoie bien une page HTML exploitable.

### Vérification 6 — accessibilité réseau

Contrôles réalisés :

- service écoutant sur `0.0.0.0:8000` ;
- règles `iptables` montrant des `ACCEPT tcp dpt:8000`.

---

## Dépendances ajoutées

Fichier :

- `badge83/requirements.txt`

Nouvelles dépendances :

- `qrcode==8.2`
- `Pillow==11.2.1`

---

## Points d’attention

### 1. Importance du `BADGE83_BASE_URL`

Les liens du QR dépendent directement de `BADGE83_BASE_URL`.

Pour éviter les incohérences, `issuer.py` lit désormais cette valeur dynamiquement via :

- `get_base_url()`

Cela évite qu’un ancien `BASE_URL` sans port reste figé en mémoire lors de nouveaux badges.

### 2. Compatibilité standard conservée

L’ajout du QR n’altère pas le mécanisme de baking.

Le badge reste :

- un PNG valide ;
- un badge Open Badges baked ;
- un fichier compatible avec l’unbaking local existant.

---

## Résumé

Cette évolution transforme le QR en **porte d’entrée mobile vers une preuve lisible**, tout en conservant la structure Open Badges standard en arrière-plan.

Le résultat final est donc un badge qui est à la fois :

- plus crédible en usage terrain ;
- plus rapide à vérifier sur smartphone ;
- toujours compatible avec le flux baked Open Badges existant.