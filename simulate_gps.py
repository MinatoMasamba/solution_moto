import requests
import time
import random

# URL de l'API de ping de localisation
URL = "http://127.0.0.1:8000/api/v1/location-pings/"

# Coordonnées approximatives de Kinshasa pour la simulation
KIN_LAT_MIN, KIN_LAT_MAX = -4.52, -4.28
KIN_LNG_MIN, KIN_LNG_MAX = 15.15, 15.58

# En-têtes (vous devrez peut-être ajuster l'authentification si requis)
# Pour ce test, je pars du principe que l'API est accessible.
# Si une authentification est nécessaire, ajoutez le token ici :
HEADERS = {"Authorization": "Bearer VOTRE_TOKEN_JWT", "Content-Type": "application/json"}

print("Démarrage de la simulation d'envoi de positions (durée: 2 minutes)...")

end_time = time.time() + 120  # 2 minutes

while time.time() < end_time:
    lat = random.uniform(KIN_LAT_MIN, KIN_LAT_MAX)
    lng = random.uniform(KIN_LNG_MIN, KIN_LNG_MAX)
    
    data = {"latitude": lat, "longitude": lng}
    
    try:
        response = requests.post(URL, json=data, headers=HEADERS)
        print(f"Position envoyée: {lat:.4f}, {lng:.4f} - Status: {response.status_code}")
    except Exception as e:
        print(f"Erreur lors de l'envoi: {e}")
        
    time.sleep(5)  # Envoi toutes les 5 secondes

print("Simulation terminée.")
