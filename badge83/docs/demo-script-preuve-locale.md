# Badge83 — Script de démonstration de la preuve locale

Date : 08/06/2026  
Objet : scénario de démonstration du hash déterministe et de la preuve locale

---

## 1. Objectif de la démonstration

Montrer que Badge83 peut produire une preuve cryptographique locale pour chaque credential émis, sans stocker de donnée personnelle sur blockchain et sans rendre la blockchain obligatoire.

Message à faire passer :

> Badge83 reste une plateforme Open Badges fonctionnelle. Le hash local prépare un futur ancrage blockchain optionnel, mais l'émission et la vérification continuent de fonctionner sans blockchain.

---

## 2. Préparation

Depuis le dossier `badge83` :

```bash
.venv/bin/python -m pytest tests/unit -q
```

Résultat attendu :

```text
101 passed
```

Lancer ensuite l'application selon le mode habituel :

```bash
./badge83.sh start
```

ou, en développement :

```bash
.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 3. Scénario opérateur

### Étape 1 — Connexion

1. Ouvrir l'interface Badge83.
2. Se connecter avec le compte opérateur.
3. Vérifier que le centre de contrôle est accessible.

Point à expliquer : les routes administrateur sont protégées, alors que les pages publiques de vérification restent accessibles.

### Étape 2 — Émettre un badge

1. Émettre un badge simple ou un badge PNG baked.
2. Noter l'identifiant d'assertion généré.
3. Vérifier que le JSON existe dans `data/issued/`.
4. Vérifier que le PNG existe dans `data/baked/` si l'émission baked a été utilisée.

Point à expliquer : le flux Open Badges reste inchangé.

### Étape 3 — Consulter la preuve administrateur

Appeler l'endpoint protégé :

```text
GET /api/badges/{assertion_id}/proof
```

Réponse attendue :

```json
{
  "assertion_id": "...",
  "proof_version": "badge83-proof-v1",
  "hash_algorithm": "sha256",
  "canonicalization": "json-rfc8785-lite-v1",
  "credential_hash": "sha256:...",
  "anchoring_status": "not_requested",
  "created_at": "...",
  "updated_at": "..."
}
```

Point à expliquer : le hash est prêt pour un ancrage ultérieur, mais aucun appel blockchain n'est encore nécessaire.

### Étape 4 — Vérification publique complète

Ouvrir :

```text
/verify/badge/{assertion_id}
```

Montrer le bloc :

```text
Preuve locale Badge83
```

Résultat attendu :

```text
Preuve locale cohérente
Ancrage : not_requested
Hash credential : sha256:...
```

Point à expliquer : la page vérifie le hash courant de l'assertion contre le hash stocké localement.

### Étape 5 — Vérification QR mobile

Ouvrir ou scanner :

```text
/verify/qr/{assertion_id}
```

Résultat attendu :

```text
Badge vérifié
Preuve locale cohérente
```

Point à expliquer : un tiers peut vérifier le badge publiquement sans accéder à l'interface administrateur.

---

## 4. Démonstration d'incohérence contrôlée

Cette étape est optionnelle et doit être réalisée uniquement sur un badge de test.

1. Copier l'assertion JSON de test.
2. Modifier un champ stable, par exemple `issuedOn`.
3. Recharger `/verify/badge/{assertion_id}`.

Résultat attendu :

```text
Preuve locale incohérente
```

Point à expliquer : Badge83 détecte que le contenu actuel de l'assertion ne correspond plus à la preuve locale enregistrée.

---

## 5. Messages clés pour la présentation

- Les credentials restent off-chain.
- Les données personnelles ne sont pas publiées sur blockchain.
- Le hash local prépare un ancrage futur.
- La blockchain reste optionnelle.
- L'émission ne dépend pas du proof layer : en cas d'erreur, Badge83 continue d'émettre le badge.
- La vérification publique affiche maintenant une preuve locale cohérente ou incohérente.

---

## 6. Limites à annoncer clairement

- Le hash local n'est pas encore une transaction blockchain.
- Il ne remplace pas la conformité Open Badges.
- Il ne remplace pas une révocation officielle.
- Il prépare la couche d'ancrage, qui devra être ajoutée dans une itération séparée.

---

## 7. Captures recommandées

1. Centre de contrôle Badge83.
2. Badge émis.
3. Réponse `/api/badges/{id}/proof`.
4. Page `/verify/badge/{id}` avec preuve cohérente.
5. Page `/verify/qr/{id}` sur format mobile.
6. Résultat des tests unitaires.