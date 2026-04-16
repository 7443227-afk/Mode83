# Analyse de conformité de Badge83 à la méthodologie Open Badges (PNG baked)

## Sources prises en compte

### Spécification Open Badges v2.0

- Open Badges v2.0 — IMS / 1EdTech Final Release
- section générale sur les images PNG / SVG et le baking

### Baking Specification

Éléments identifiés dans la documentation officielle :

- pour les PNG, un chunk **`iTXt`** doit être inséré ;
- le keyword doit être **`openbadges`** ;
- le texte doit contenir soit le JSON de l’assertion, soit une signature ;
- la compression ne doit pas être utilisée ;
- un seul chunk `openbadges` doit être présent ;
- le parsing peut s’arrêter au premier chunk `openbadges` trouvé ;
- les anciens PNG baked en `tEXt` sont considérés comme **legacy PNGs**.

## Algorithme actuel de Badge83

### Production

Badge83 :

- charge un PNG source ;
- retire un éventuel chunk `openbadges` existant ;
- sérialise l’assertion en JSON compact UTF-8 ;
- construit un chunk **`tEXt`** avec keyword `openbadges` ;
- insère ce chunk avant `IEND`.

### Lecture

Badge83 sait lire :

- `tEXt`
- `iTXt`

Cela est bon pour l’interopérabilité.

## Conformité par point

| Exigence / recommandation | Badge83 | Évaluation |
|---------------------------|---------|-----------|
| PNG valide | Oui | Conforme |
| Keyword `openbadges` | Oui | Conforme |
| Une seule injection Open Badges | Oui | Conforme |
| Texte JSON UTF-8 | Oui | Conforme |
| Parsing des badges baked | Oui | Conforme |
| Support lecture `iTXt` | Oui | Conforme |
| Usage de `iTXt` à l’écriture | Non | À améliorer |
| Compression du chunk baked | Non | Conforme par simplicité |
| HostedBadge résolvable | Oui | Conforme |

## Interprétation

Badge83 est **fonctionnellement conforme** pour un usage HostedBadge moderne avec validation externe, mais **n’est pas encore parfaitement aligné sur la recommandation de baking PNG v2**, car il écrit encore en `tEXt` plutôt qu’en `iTXt`.

## Recommandation technique

### Évolution conseillée

1. ajouter un mode de sortie `iTXt` ;
2. idéalement basculer la production par défaut sur `iTXt` ;
3. conserver la rétrocompatibilité de lecture `tEXt` et `iTXt` ;
4. documenter clairement ce changement dans le projet.

### Ce qu’il ne faut pas surinterpréter

Le fait qu’un badge externe soit beaucoup plus gros ou contienne énormément de chunks `IDAT` ne signifie pas qu’il est “plus conforme”. Cela traduit surtout :

- une image plus lourde ;
- une autre chaîne d’export graphique ;
- éventuellement un autre pipeline applicatif.

La vraie différence méthodologique utile est surtout :

- **`iTXt` recommandé** vs **`tEXt` legacy**.