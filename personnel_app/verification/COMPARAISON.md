# Première vue DG — comparaison au ZIP

Référence : `assets/reference-desktop.png`, rendu Chrome de `GO-MBOKA DG.dc.html` du ZIP racine, 1440 × 1000.

Captures Flutter : `dg-1440.png` et `dg-412.png`, produites par `flutter test test/visual_test.dart` avec Inter et les icônes Material chargées.

## Corrections effectuées après visualisation

- Police Inter embarquée, disponible hors ligne.
- Routes secondaires de la carte rétablies.
- Courbe verte des revenus superposée à l'histogramme.
- Suppression du bandeau qui décalait le contenu ; indication du mode maquette dans l'en-tête.
- Hauteur de carte réduite sur téléphone pour éviter son étirement.
- Hauteur uniforme des indicateurs, augmentée sur téléphone après détection d'un débordement.

## Conformité observée

Palette Nocturne, menu de 252 pixels, en-tête fixe, quatre indicateurs, carte à gauche, activité et classement à droite, tableau inférieur. Sur petit écran, navigation dans un tiroir et indicateurs sur deux colonnes.

## Écarts encore ouverts — validation non acquise

Les icônes Material diffèrent des Phosphor de la maquette. L'en-tête, la légende GPS, les badges, les espacements fins et la présentation du tableau ne sont pas encore identiques. La carte actuelle est un dessin de référence, sans GPS serveur. Les écrans métier secondaires et les autres rôles restent à implémenter. La connexion réelle nécessite un serveur joignable et un compte autorisé ; son parcours complet n'a pas été vérifié. Les captures de test ne remplacent pas un essai sur Android et Windows.

Ne pas passer à un autre rôle en considérant cette vue comme totalement validée.

## Vérifications

`flutter analyze` : aucune anomalie. `flutter test --timeout 45s` : 3 tests réussis après les corrections, dont les deux formats sans débordement. Première compilation Linux réussie et lancement natif observé. Android et Windows ne sont pas déclarés validés.
