# Rapport de comparaison PNG baked

## Fichiers comparés

- `7443227_gmail-com-52da.png` — badge émis par un service externe
- `badge-baked 15.png` — badge généré par Badge83

## Résumé exécutif

Les deux fichiers sont des **PNG valides** contenant une injection Open Badges. En revanche, ils n'utilisent pas exactement la même méthode de baking ni le même profil d'image.

- Le badge externe suit plus fidèlement la **méthode PNG baked recommandée par la spécification Open Badges v2.0**, en utilisant un chunk **`iTXt`** avec keyword `openbadges`, sans compression.
- Le badge Badge83 utilise un chunk **`tEXt`** avec keyword `openbadges`, ce qui reste lisible par nos outils et compatible avec le validateur utilisé, mais correspond plutôt au **mode legacy** mentionné dans la spécification de baking.
- Le badge externe embarque aussi un objet assertion plus riche (`image`, `narrative`, `extensions`, `verify`) alors que Badge83 produit une assertion plus compacte, plus simple à maintenir, et mieux alignée avec notre architecture HostedBadge actuelle (`url`, `verification.url`, `badge`, `issuer`).

## Tableau de similitudes et différences

| Critère | PNG externe | PNG Badge83 | Analyse |
|--------|-------------|-------------|---------|
| Signature PNG | Valide | Valide | Conforme dans les deux cas |
| Chunk Open Badges | `iTXt` | `tEXt` | Différence majeure de méthodologie |
| Keyword | `openbadges` | `openbadges` | Conforme dans les deux cas |
| Compression du texte baked | Non compressé | n/a (`tEXt`) | Conforme côté externe à la spec v2 baking |
| Nombre de chunks `IDAT` | Très élevé (centaines) | 1 | Différence liée au poids/encodage de l'image, pas à Open Badges lui-même |
| Taille du fichier | ~1.3 MB | ~7 KB | Notre badge est beaucoup plus léger |
| Assertion embarquée | Oui | Oui | Les deux embarquent bien des données Open Badges |
| Contexte | `https://w3id.org/openbadges/v2` | `https://w3id.org/openbadges/v2` | Conforme dans les deux cas |
| Identité hachée | Oui | Oui | Conforme dans les deux cas |
| Salt | Oui | Oui | Conforme dans les deux cas |
| Référence badge | Oui | Oui | Conforme dans les deux cas |
| Référence issuer | Implicite via badge / structure externe | Oui, explicite | Notre modèle est plus explicite |
| Champ image assertion | Oui | Non | Le badge externe est plus riche fonctionnellement |
| Extensions | Oui | Non | Le badge externe exploite des extensions Open Badges |
| Style de vérification | `verify.type = hosted` | `verification.type = HostedBadge` | Différence de forme, liée à l’écosystème / mode de sérialisation |

## Détail structurel

### 1. Badge externe

Structure observée :

1. `IHDR`
2. `iTXt(openbadges)`
3. très nombreux chunks `IDAT`
4. `IEND`

Points notables :

- le chunk baked apparaît très tôt dans le fichier ;
- il contient un JSON Open Badges v2 lisible ;
- il utilise un chunk `iTXt`, explicitement recommandé par la spécification de baking Open Badges v2 ;
- l'image elle-même est beaucoup plus lourde.

### 2. Badge Badge83

Structure observée :

1. `IHDR`
2. `IDAT`
3. `tEXt(openbadges)`
4. `IEND`

Points notables :

- structure extrêmement compacte ;
- insertion claire et facile à auditer ;
- payload JSON propre, avec modèle HostedBadge explicite ;
- utilisation de `tEXt`, qui reste opérationnel mais n’est pas le format recommandé le plus récent pour PNG baked v2.

## Recommandations Open Badges identifiées

À partir de la spécification IMS / 1EdTech Open Badges v2.0 Baking :

1. Pour les **PNG**, un chunk **`iTXt`** devrait être utilisé.
2. Le keyword doit être **`openbadges`**.
3. Le texte doit contenir soit l’assertion JSON, soit une signature.
4. La compression **ne doit pas** être utilisée pour ce chunk `iTXt`.
5. Il ne doit y avoir **qu’un seul** chunk `openbadges`.
6. Les badges peuvent aussi être baked en **SVG**.
7. La spécification mentionne explicitement qu’un usage `tEXt` avec hosted URL correspond à un mode **legacy PNGs**.

## Évaluation de conformité des algorithmes Badge83

### Ce que Badge83 fait bien

- produit un PNG valide ;
- n’insère qu’une seule injection Open Badges ;
- utilise bien le keyword `openbadges` ;
- embarque une assertion Open Badges v2 cohérente ;
- sait lire à la fois `tEXt` et `iTXt` au moment de l’unbaking ;
- génère une assertion HostedBadge cohérente pour la validation externe.

### Ce qui est partiellement aligné / à améliorer

- la production actuelle utilise **`tEXt`** et non **`iTXt`** ;
- la spécification v2 recommande `iTXt` pour les PNG baked modernes ;
- Badge83 produit une assertion compacte mais n’exploite pas encore des champs enrichis comme `image`, `extensions`, `evidence`, etc.

## Conclusion sur la pertinence de reprendre les méthodes externes

### À ne pas copier tel quel

- la **taille** du PNG externe ;
- la multiplication des `IDAT`, qui reflète surtout le poids de l’image source et non une meilleure conformité Open Badges ;
- l’intégralité de son payload applicatif sans étude fonctionnelle.

### À envisager sérieusement

1. **Ajouter un mode de baking `iTXt` en production**
   - idéalement comme nouveau défaut ou comme option configurable ;
   - car c’est le mode recommandé par la spécification v2 pour PNG baked.

2. **Conserver la lecture des deux formats (`tEXt` + `iTXt`)**
   - ce qui est déjà le cas dans Badge83 ;
   - cela garantit une bonne interopérabilité.

3. **Étudier séparément les champs enrichis**
   - `image`
   - `narrative`
   - `extensions`
   - éventuellement `evidence`

### Recommandation finale

Pour la production, il est **pertinent de s’inspirer partiellement du badge externe**, mais **pas de le copier intégralement**.

La meilleure stratégie serait :

- conserver notre architecture compacte et notre modèle HostedBadge ;
- migrer progressivement de `tEXt` vers **`iTXt`** pour le baking PNG ;
- ajouter ensuite, de manière contrôlée, certains champs enrichis réellement utiles à notre cas d’usage.

Autrement dit :

- **oui** à l’adoption de la méthodologie `iTXt` recommandée ;
- **non** à la reproduction brute de la structure lourde du PNG externe.