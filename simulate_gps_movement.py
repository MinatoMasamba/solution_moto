import requests
import time

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
    print(f"Connexion réussie.")
except Exception as e:
    print(f"Échec de la connexion: {e}")
    exit(1)

# 2. Simulation de déplacement
URL_PING = f"{BASE_URL}/api/v1/location-pings/"
HEADERS = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Point de départ (Gombe)
lat, lng = -4.3100, 15.3100

print("Démarrage du déplacement simulé (1 minute)... Regardez la carte!")

for _ in range(12): # 12 étapes * 5s = 1 minute
    lat += 0.002
    lng += 0.002
    
    data = {"latitude": lat, "longitude": lng}
    
    try:
        response = requests.post(URL_PING, json=data, headers=HEADERS)
        print(f"Position envoyée: {lat:.4f}, {lng:.4f} - Status: {response.status_code}")
    except Exception as e:
        print(f"Erreur: {e}")
        
    time.sleep(5)

print("Simulation terminée.")
