import requests
import time
import math

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
    print("Connexion réussie.")
except Exception as e:
    print(f"Échec de la connexion: {e}")
    exit(1)

# 2. Simulation de déplacement ellipsoïdal
URL_PING = f"{BASE_URL}/api/v1/location-pings/"
HEADERS = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Centre de l'ellipse (Gombe)
center_lat, center_lng = -4.310000, 15.310000
# Rayons (en degrés)
a, b = 0.005, 0.003

print("Démarrage du déplacement ellipsoïdal (3 minutes)... Regardez la carte!")

# 3 minutes = 180 secondes. Envoi toutes les 5s => 36 itérations.
for i in range(36):
    t = i * 0.2  # Progression angulaire
    lat = center_lat + a * math.cos(t)
    lng = center_lng + b * math.sin(t)
    
    # Formatage strict pour le DecimalField (6 décimales)
    data = {"latitude": f"{lat:.6f}", "longitude": f"{lng:.6f}"}
    
    try:
        response = requests.post(URL_PING, json=data, headers=HEADERS)
        print(f"[{i+1}/36] Position envoyée: {data} - Status: {response.status_code}")
    except Exception as e:
        print(f"Erreur: {e}")
        
    time.sleep(5)

print("Simulation terminée.")
