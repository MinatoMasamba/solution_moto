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
    print(f"Connexion réussie. Token obtenu.")
except Exception as e:
    print(f"Échec de la connexion: {e}")
    exit(1)

# 2. Simulation de l'envoi de position
URL_PING = f"{BASE_URL}/api/v1/location-pings/"
HEADERS = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Coordonnées approximatives de Kinshasa
KIN_LAT_MIN, KIN_LAT_MAX = -4.52, -4.28
KIN_LNG_MIN, KIN_LNG_MAX = 15.15, 15.58

print("Démarrage de la simulation d'envoi de positions (durée: 2 minutes)...")

end_time = time.time() + 120

while time.time() < end_time:
    lat = random.uniform(KIN_LAT_MIN, KIN_LAT_MAX)
    lng = random.uniform(KIN_LNG_MIN, KIN_LNG_MAX)
    
    data = {"latitude": lat, "longitude": lng}
    
    try:
        response = requests.post(URL_PING, json=data, headers=HEADERS)
        print(f"Position envoyée: {lat:.4f}, {lng:.4f} - Status: {response.status_code}")
    except Exception as e:
        print(f"Erreur lors de l'envoi: {e}")
        
    time.sleep(5)

print("Simulation terminée.")
