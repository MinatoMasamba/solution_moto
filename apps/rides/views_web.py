from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Ride

@login_required
def create_ride_view(request):
    # Logique simplifiée pour afficher le formulaire de demande de course
    # Le client demande une course et le backend crée le Ride
    return render(request, 'rides/create_ride.html')
