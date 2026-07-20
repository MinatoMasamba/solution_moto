import requests
import time
import random

# URL de base
BASE_URL = "http://127.0.0.1:8000"

# Identifiants
PHONE = "+243810000003"
PASSWORD = "motard1234"

# 1. Obtenir le token JWT
login_url = f"{BASE_URL}/api/v1/auth/login/"
data = {"phone_number": PHONE, "password": PASSWORD}

try:
    response = requests.post(login_url, json=data)
    response.raise_for_status()
    token = response.json()["access"]
    print(f"Connexion réussie. Token: {token[:10]}...")
except Exception as e:
    print(f"Échec de la connexion: {e}")
    if response is not None:
        print(f"Réponse: {response.text}")
    exit(1)

# 2. Simulation de l'envoi de position
URL_PING = f"{BASE_URL}/api/v1/location-pings/"
# Format correct pour DRF JWT
HEADERS = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

print(f"Headers utilisés: {HEADERS}")

# Coordonnées approximatives de Kinshasa
KIN_LAT_MIN, KIN_LAT_MAX = -4.52, -4.28
KIN_LNG_MIN, KIN_LNG_MAX = 15.15, 15.58

print("Démarrage de la simulation d'envoi de positions (durée: 1 minute)...")
end_time = time.time() + 60

while time.time() < end_time:
    lat = round(random.uniform(KIN_LAT_MIN, KIN_LAT_MAX), 6)
    lng = round(random.uniform(KIN_LNG_MIN, KIN_LNG_MAX), 6)
    
    data = {"latitude": lat, "longitude": lng}
    
    try:
        response = requests.post(URL_PING, json=data, headers=HEADERS)
        print(f"Position envoyée: {lat}, {lng} - Status: {response.status_code}")
        if response.status_code != 201:
            print(f"Réponse détaillée: {response.text}")
    except Exception as e:
        print(f"Erreur lors de l'envoi: {e}")
        
    time.sleep(5)

print("Simulation terminée.")
