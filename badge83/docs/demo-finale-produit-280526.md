# Démonstration finale produit — Badge83 — 28/05/2026

Projet : Badge83 — Open Badges MODE83  
Objet : scénario de démonstration final pour présenter Badge83 à un public non technique

---

## 1. Objectif de la démonstration

La démonstration doit montrer que Badge83 est une plateforme utilisable pour :

1. préparer des modèles de badges MODE83 ;
2. émettre un badge individuel ;
3. remettre un PNG baked vérifiable ;
4. vérifier un badge par QR code, page publique ou upload ;
5. émettre une cohorte depuis CSV/XLSX ;
6. récupérer une archive ZIP avec badges et rapport ;
7. expliquer les garanties : Open Badges, traçabilité, confidentialité, sauvegarde et sécurité.

Le message principal à garder pendant toute la présentation :

> Badge83 couvre le Projet A obligatoire et dispose déjà des fonctions nécessaires pour une démonstration produit claire, exploitable par un opérateur MODE83.

---

## 2. Préparation avant présentation

### 2.1 Vérifications techniques

Depuis le projet :

```bash
cd /home/ubuntu/projects/Mode83/badge83
/home/ubuntu/projects/Mode83/.venv/bin/python -m pytest -q
./badge83.sh status
```

Si l'application est arrêtée et que la démonstration est locale :

```bash
./badge83.sh start
./badge83.sh status
```

À la fin de la démonstration locale :

```bash
./badge83.sh stop
```

### 2.2 URLs utiles

Adapter l'URL de base selon l'environnement :

```text
Local :      http://127.0.0.1:8000
Production : https://<domaine-mode83>
```

URLs à ouvrir pendant la démonstration :

```text
/auth/login
/
/issuers/main
/badges/blockchain-foundations
/assertions/<assertion_id>
/verify/badge/<assertion_id>
/verify/qr/<assertion_id>
```

Les identifiants opérateur ne doivent pas être écrits dans ce document. Ils doivent rester transmis hors Git.

### 2.3 Données de démonstration

Données individuelles proposées :

```text
Nom : Alice Validation
Email : alice.validation@example.org
Formation : Blockchain MODE83
```

Fichiers de cohorte disponibles :

```text
data/sample_batch_issue.csv
data/sample_batch_issue.xlsx
```

Pour une présentation publique, privilégier des adresses fictives `example.org` et éviter les données personnelles réelles.

---

## 3. Script de démonstration recommandé — 12 à 15 minutes

### Étape 1 — Introduction fonctionnelle

Durée indicative : 1 minute.

Présenter Badge83 comme une application MODE83 permettant d'émettre et vérifier des certifications numériques au format Open Badges 2.0.

Message à dire :

```text
Un badge n'est pas seulement une image : il contient ou référence des métadonnées vérifiables indiquant l'émetteur, la formation, le titulaire et la preuve de validité.
```

### Étape 2 — Connexion opérateur

Durée indicative : 1 minute.

1. Ouvrir `/auth/login`.
2. Se connecter avec le compte opérateur préparé.
3. Arriver sur l'interface principale.

À montrer :

- la séparation entre pages publiques et espace opérateur ;
- l'accès contrôlé aux fonctions d'administration.

### Étape 3 — Constructeur de badge

Durée indicative : 2 minutes.

Dans l'interface principale :

1. ouvrir la zone constructeur ;
2. montrer les schémas de champs ;
3. ouvrir un modèle existant ;
4. montrer les textes fixes et dynamiques ;
5. montrer la position du QR code ;
6. lancer une prévisualisation.

Message à dire :

```text
L'opérateur peut préparer un modèle visuel sans modifier manuellement les fichiers JSON. Le même modèle peut ensuite servir pour une émission individuelle ou groupée.
```

### Étape 4 — Émission individuelle

Durée indicative : 2 minutes.

1. Choisir un modèle ou utiliser le formulaire d'émission individuelle.
2. Saisir les données fictives d'Alice Validation.
3. Émettre le badge.
4. Noter l'`assertion_id` généré.
5. Télécharger ou ouvrir le PNG baked.

Résultat attendu :

- une assertion JSON est créée ;
- un PNG baked est généré ;
- le badge peut être remis au titulaire.

### Étape 5 — Vérification publique par QR et page complète

Durée indicative : 2 minutes.

Avec l'`assertion_id` obtenu :

```text
/verify/qr/<assertion_id>
/verify/badge/<assertion_id>
```

À montrer :

- statut de validité ;
- nom du titulaire si présent ;
- absence d'email complet par défaut ;
- résumé de conformité Open Badges ;
- QR code destiné au contrôle mobile.

Message à dire :

```text
La vérification est publique pour le badge, mais l'espace opérateur reste protégé. L'email complet n'est pas publié par défaut afin de réduire l'exposition des données personnelles.
```

### Étape 6 — Vérification par upload PNG

Durée indicative : 1 minute.

1. Ouvrir l'interface de vérification.
2. Importer le PNG baked généré.
3. Montrer le résultat de vérification.

Message à dire :

```text
Même si l'image circule séparément, les métadonnées embarquées permettent de retrouver et contrôler le badge.
```

### Étape 7 — Endpoints Open Badges publics

Durée indicative : 1 minute.

Ouvrir rapidement :

```text
/issuers/main
/badges/blockchain-foundations
/assertions/<assertion_id>
```

À expliquer simplement :

- `Issuer` décrit MODE83 comme émetteur ;
- `BadgeClass` décrit la certification ;
- `Assertion` décrit le badge remis à un titulaire.

### Étape 8 — Émission groupée CSV/XLSX

Durée indicative : 3 minutes.

1. Ouvrir le module d'émission groupée.
2. Télécharger ou montrer le modèle Excel si nécessaire.
3. Importer `data/sample_batch_issue.csv` ou `data/sample_batch_issue.xlsx`.
4. Montrer la prévisualisation :
   - lignes prêtes ;
   - lignes non validées ;
   - doublons ;
   - erreurs.
5. Confirmer l'émission partielle contrôlée.
6. Télécharger l'archive ZIP.
7. Ouvrir la structure attendue :

```text
badges/*.png
rapport_emission.csv
manifest.json
source.csv ou source.xlsx
```

Message à dire :

```text
Le rapport permet de comprendre quelles lignes ont été émises, ignorées ou rejetées. Cela rend l'usage par cohorte plus sûr pour un formateur.
```

### Étape 9 — Historique et traçabilité

Durée indicative : 1 minute.

Montrer l'historique des sessions d'émission groupée si la page est disponible dans l'interface.

À mentionner :

- chaque émission groupée possède un `session_id` ;
- le manifeste ZIP et l'historique local facilitent le suivi ;
- le registre SQLite est une donnée runtime à sauvegarder et protéger.

### Étape 10 — Exploitation Docker, sauvegarde et limites

Durée indicative : 1 minute.

Conclure avec les points d'exploitation :

- Docker local pour démonstration ;
- Docker production derrière Nginx HTTPS ;
- sauvegarde de `runtime-data/`, `.env` hors Git et certificats TLS ;
- restauration documentée ;
- Projet B blockchain possible ensuite, séparé et optionnel.

---

## 4. Liste de contrôle pendant la démonstration

Cocher mentalement ou sur papier :

- [ ] l'application démarre et répond ;
- [ ] l'opérateur peut se connecter ;
- [ ] un modèle est visible dans le constructeur ;
- [ ] un badge individuel est émis ;
- [ ] le PNG baked est généré ;
- [ ] la page QR fonctionne ;
- [ ] la vérification par upload fonctionne ;
- [ ] les endpoints Open Badges répondent ;
- [ ] une cohorte CSV/XLSX est prévisualisée ;
- [ ] une archive ZIP est générée ;
- [ ] le rapport et le manifeste sont compréhensibles ;
- [ ] les limites privacy/sécurité sont expliquées honnêtement.

---

## 5. Risques connus à mentionner honnêtement

### 5.1 Données personnelles

- Les badges anciens peuvent contenir `admin_recipient.email` s'ils ont été émis avant la minimisation RGPD.
- La configuration actuelle n'intègre plus l'email complet dans le PNG baked par défaut.
- Un opérateur peut encore afficher un email sur le visuel s'il ajoute volontairement un champ dynamique correspondant dans le modèle.

### 5.2 Données runtime

- Le registre SQLite, les PNG générés et les logs sont des données d'exploitation.
- Ces éléments ne doivent pas être commités.
- Ils doivent être sauvegardés selon la procédure Docker/exploitation.

### 5.3 Vérification Open Badges

- Le rapport local de conformité est explicatif et utile pour Badge83.
- Il ne remplace pas un validateur externe officiel si MODE83 veut une certification de conformité indépendante.

### 5.4 Vérifications distantes

- Les protections SSRF bloquent volontairement les URLs locales ou privées.
- Pour une exposition publique, ce comportement est attendu.
- Pour des tests locaux avancés, utiliser les tests unitaires ou les endpoints locaux sans vérification distante.

### 5.5 Blockchain

- Le Projet B n'est pas nécessaire pour valider le Projet A.
- Si un PoC blockchain est lancé, seules des empreintes cryptographiques doivent être ancrées, jamais des données personnelles.

---

## 6. Conclusion proposée

Conclusion courte à prononcer :

```text
Badge83 permet aujourd'hui à MODE83 de créer, émettre, remettre et vérifier des badges numériques Open Badges. Le Projet A est démontrable de bout en bout : badge individuel, PNG baked, QR code, pages publiques, endpoints Open Badges, émission groupée, rapport ZIP et documentation d'exploitation. Les sujets privacy, sécurité et sauvegarde sont identifiés et documentés, ce qui rend la plateforme présentable et exploitable pour une validation finale.
```
