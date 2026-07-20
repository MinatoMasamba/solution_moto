# App: Fleet

Ce module gère le parc de motos, les affectations, les périodes d'essai et les contrats de location.

## Responsabilités
- Gestion des actifs physiques (`Motorcycle`) : Marque, châssis, état général.
- Gestion du flux d'intégration :
    - `MotardTrial` & `TrialDailyLog` : Suivi quotidien de la période de probation.
- Gestion contractuelle :
    - `Agreement` : Gestion des contrats `RENTAL` (Location) et `HIRE_PURCHASE` (Location-Vente).
- Gestion financière des flottes :
    - `FleetRemittance` : Calcul et suivi des reversements aux propriétaires.

## Modèles Principaux
- `Motorcycle` : L'objet moto.
- `MotardTrial` : Période d'essai.
- `TrialDailyLog` : Journal quotidien d'essai.
- `Agreement` : Contrat définitif.
- `FleetRemittance` : Reversements.

## Architecture Front-end
Cette application contribue à l'écosystème front-end dynamique. Les données liées aux flottes et au rendement fournis par ses services sont consommées en temps réel par les tableaux de bord pour garantir une interface réactive et sans données statiques.
