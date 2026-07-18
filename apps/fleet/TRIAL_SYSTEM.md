# Système de Période d'Essai et de Contrats (Trial & Agreement System)

Ce document décrit la logique métier et l'implémentation technique du processus d'intégration des motards et de la gestion des contrats de location/acquisition.

## 1. Flux de Travail (Workflow)

Le parcours d'un motard suit trois étapes distinctes :

### Étape A : L'Essai (Trial Period)
Avant d'obtenir un contrat définitif, tout motard doit passer par une phase de probation.
- **Statut** : `MotardProfile.SubscriptionStatus.TRIAL` ("En essai").
- **Attribution** : Une moto est affectée temporairement via un objet `MotardTrial`.
- **Suivi Quotidien** : Chaque soir, le gérant remplit un `TrialDailyLog` lors de la remise de la moto.
- **Validation** : À la fin de la période, le gérant juge le motard sur :
    - La ponctualité (Heures de retour).
    - La fiabilité financière (Versements complets).
    - Le soin apporté au matériel (Note d'état /10).
    - La performance (Nombre de courses et note moyenne).

### Étape B : La Validation
Si le résultat de `MotardTrial` est `VALIDATED` :
1. Le statut du motard passe à `ACTIVE`.
2. Un `Agreement` (Contrat) est créé et signé.

### Étape C : Le Contrat Définitif (`Agreement`)
Le motard est affecté à l'un des deux types de contrats selon son profil et son accord avec la direction.

---

## 2. Détails des Contrats

### A. Location Simple (`RENTAL`)
Le motard loue la moto pour une durée indéterminée.
- **Paiement** : Versement périodique (Journalier ou Hebdomadaire).
- **Entretien** : 
    - **Samedi** : Jour libre pour le motard (pas de versement).
    - **Dimanche** : La moto est remise au gérant pour l'entretien technique.
- **Propriété** : La moto reste la propriété exclusive de Go-Mboka ou du Propriétaire.

### B. Location-Vente (`HIRE_PURCHASE`)
Le motard loue la moto avec l'objectif d'en devenir propriétaire.
- **Paiement** : Versement périodique cumulé vers un `target_total_amount`.
- **Entretien** : 
    - Le motard est responsable de l'entretien de sa moto.
    - **Dimanche** : Le motard effectue lui-même l'entretien.
    - **Pas de jour libre le samedi**.
- **Propriété** : Dès que `amount_already_paid` $\ge$ `target_total_amount`, la moto est transférée au nom du motard.

---

## 3. Spécifications Techniques (Modèles)

### `Motorcycle` (L'Objet)
Considéré comme un actif physique avec :
- `brand`, `model_style`, `color` : Identification visuelle.
- `chassis_number` (VIN) : Identification légale unique.
- `general_condition` : Note de 1 à 10 sur l'état global.

### `MotardTrial` & `TrialDailyLog`
L'essai est un processus itératif :
- `MotardTrial` définit le cadre (dates, objectifs de performance).
- `TrialDailyLog` capture la réalité terrain quotidienne :
    - `return_time` : Vérification de la ponctualité.
    - `amount_paid` & `is_payment_complete` : Rigueur financière.
    - `bike_condition_score` : Responsabilité vis-à-vis du matériel.
    - `motard_explanation` : Espace pour les plaintes et justifications.

### `Agreement`
Le contrat lie le motard à la moto avec des règles financières strictes :
- `periodic_amount` : Le montant dû selon la `frequency`.
- `target_total_amount` : Le prix de rachat (uniquement pour `HIRE_PURCHASE`).
- `amount_already_paid` : Le compteur de progression vers la propriété.

---

## 4. Matrice de Maintenance

| Type de Contrat | Samedi | Dimanche | Responsable Entretien |
| :--- | :--- | :--- | :--- |
| **Rental** | Jour Libre Motard | Entretien Gérant | Gérant |
| **Hire Purchase** | Travail | Entretien Motard | Motard |
