# GO-MBOKA — Application du personnel

Application Flutter commune prévue pour Linux, Android et Windows. Première interface : Direction Générale. Les autres interfaces seront ouvertes selon les rôles attribués par le serveur, sans auto-attribution de rôle.

## Structure

- `lib/core/api.dart` : transport JSON et authentification JWT en mémoire, partagé entre les futures interfaces.
- `lib/features/direction/dashboard.dart` : coque DG, navigation, disposition bureau/mobile, indicateurs, carte de référence et tableau.
- `lib/main.dart` : application et thème Nocturne.
- `assets/dg_reference.html` : maquette originale extraite du ZIP racine, pour traçabilité.
- `test/visual_test.dart` : captures reproductibles 1440 × 1000 et 412 × 915, avec détection des débordements.
- `linux`, `android`, `windows` : lanceurs natifs.

## Lancement

```bash
flutter pub get
flutter run -d linux
flutter run -d windows
flutter run -d <identifiant-android>
```

Windows nécessite une machine Windows avec la chaîne de compilation Flutter appropriée.

Le démarrage montre explicitement les données fictives du ZIP pour la comparaison. Le bouton Connexion demande l'adresse du serveur et les identifiants existants. L'API DG conserve son contrôle d'accès côté Django. Le téléphone doit joindre l'adresse réseau du serveur ; `127.0.0.1` désigne le téléphone lui-même. Utiliser HTTPS pour le serveur de production.

## État de la première tranche

Vue d'ensemble, navigation fixe, adaptation étroite, recherche dans le tableau et connexion JWT implémentées. Le mode serveur remplace les indicateurs et le classement par `/api/dashboard/operator/`. La carte GPS réelle, les écrans secondaires métier, les mutations, le renouvellement de session et les autres rôles restent à réaliser. Aucun chiffre de maquette n'est substitué aux réponses serveur.

```bash
flutter analyze
flutter test
flutter build linux
flutter build apk
```

La boucle visuelle n'est validée qu'après inspection des PNG de `verification/`, comparaison au ZIP et essais sur les plateformes réelles. Une capture au format téléphone ne constitue pas un essai Android.
