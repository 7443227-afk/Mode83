# Test de Validation Open Badges — 15 Avril 2026

## Contexte

Ce document décrit la procédure de test de validation d'un badge MODE83 (Badge83) 
à l'aide du validateur **openbadges-validator-core** d'IMS Global.

## Environnement

### Services déployés

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| Badge83 (FastAPI) | 8000 | `http://mode83.ddns.net:8000` | Serveur d'émission et d'hébergement de badges Open Badges 2.0 |
| Open Badges Validator Core (Flask) | 5000 | `http://mode83.ddns.net:5000` | Validateurs officiel IMS Global pour Open Badges 2.0 |

### Configuration réseau

Le serveur Badge83 est configuré avec `BADGE83_BASE_URL=http://mode83.ddns.net:8000` 
pour que les badges émis contiennent des URLs publiques résolubles.

### Configuration iptables

Les règles suivantes ont été ajoutées pour autoriser l'accès distant :

```bash
sudo iptables -I INPUT 5 -p tcp --dport 8000 -j ACCEPT  # Badge83
sudo iptables -I INPUT 6 -p tcp --dport 5000 -j ACCEPT  # Validator
```

## Procédure de Test

### Étape 1 — Émission d'un badge (Badge83)

Un badge a été émis via l'API Badge83 :

```bash
curl -X POST http://mode83.ddns.net:8000/issue \
  -d "name=TestUser" -d "email=test@example.org"
```

**Résultat :** Assertion JSON créée avec ID `8eca1166-162f-4761-96fe-8f8366b709be`  
**URL publique :** `http://mode83.ddns.net:8000/assertions/8eca1166-162f-4761-96fe-8f8366b709be`

### Étape 2 — Validation via openbadges-validator-core

L'assertion émise a été soumise au validateur :

```bash
curl -X POST http://mode83.ddns.net:5000/results \
  -d "data=http://mode83.ddns.net:8000/assertions/8eca1166-162f-4761-96fe-8f8366b709be"
```

### Étape 3 — Résultat initial (ÉCHEC)

**Premier résultat :** `valid: false`

**Erreur rencontrée :**
```
JsonLdError: Could not expand input before compaction.
Type: jsonld.CompactError
Cause: Could not perform JSON-LD expansion.
...
'CachedSession' object has no attribute 'remove_expired_responses'
```

**Diagnostic :** La méthode `remove_expired_responses()` a été supprimée dans 
les versions récentes de `requests_cache` (≥ 1.0). Le validator utilisait une 
ancienne API incompatible avec Python 3.12 et `requests_cache` 1.3.1.

**Localisation du bug :** 
`openbadges/verifier/utils.py`, ligne 56, dans la classe `CachableDocumentLoader`.

### Étape 4 — Correction appliquée

**Fichier :** `openbadges/verifier/utils.py`

**Avant :**
```python
if self.use_cache:
    doc['from_cache'] = response.from_cache
    self.session.remove_expired_responses()
```

**Après :**
```python
if self.use_cache:
    doc['from_cache'] = getattr(response, 'from_cache', False)
```

**Explication :** 
- Suppression de l'appel à `remove_expired_responses()` (n'existe plus dans requests_cache ≥ 1.0)
- Utilisation de `getattr()` avec valeur par défaut pour la compatibilité avec les 
  nouvelles versions de `requests_cache` où l'attribut `from_cache` peut varier

### Étape 5 — Redémarrage et re-validation

Après correction, le serveur validator a été redémarré :

```bash
pkill -f "openbadges.verifier.server"
cd /home/ubuntu/projects/Mode83/openbadges-validator-core
source .venv/bin/activate
python -c "from openbadges.verifier.server.app import app; app.run(host='0.0.0.0', port=5000)"
```

### Étape 6 — Résultat final (SUCCÈS ✅)

La validation a été relancée avec le **même badge** et a réussi.

**Réponse du validateur :**
```json
{
    "report": {
        "valid": true,
        "errorCount": 0,
        "warningCount": 0
    },
    "input": {
        "value": "http://mode83.ddns.net:8000/assertions/8eca1166-162f-4761-96fe-8f8366b709be"
    },
    "graph": [...]
}
```

## Conclusion

Le badge MODE83 émis par Badge83 a **validé avec succès** les tests de conformité 
Open Badges 2.0 d'IMS Global.

### Points validés

- ✅ Structure de l'assertion conforme Open Badges 2.0
- ✅ URLs publiques résolubles (HostedBadge)
- ✅ Chaîne de validation complète : Assertion → BadgeClass → Issuer
- ✅ Identité du destinataire hachée (sha256)
- ✅ Vérification de l'émetteur (Issuer)
- ✅ Compatibilité JSON-LD et contexte Open Badges

### Bug corrigé dans openbadges-validator-core

Un bug de compatibilité Python 3.12 / requests_cache ≥ 1.0 a été identifié et 
corrigé dans `openbadges/verifier/utils.py`. La correction remplace l'appel à 
`remove_expired_responses()` par une approche compatible avec les versions récentes.

## Notes techniques

### Dépendances mises à jour

| Package | Ancienne version | Nouvelle version | Raison |
|---------|-----------------|------------------|--------|
| `future` | 0.16.0 | 1.0.0 | Compatibilité Python 3.12 (module `imp` supprimé) |
| `requests_cache` | — | 1.3.1 | Version installée, API modifiée |

### Fichiers modifiés

- `openbadges/verifier/utils.py` — Correction de `CachableDocumentLoader.__call__()`

---

**Date du test :** 15 Avril 2026  
**Statut :** ✅ VALIDATION RÉUSSIE
