from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .views import ClientSummaryView
from django.test import RequestFactory

@login_required
def client_dashboard_view(request):
    # Appel interne de l'API de synthèse pour obtenir les données
    factory = RequestFactory()
    api_request = factory.get('/api/users/client-summary/')
    api_request.user = request.user
    
    # Appel direct de la vue API
    summary_view = ClientSummaryView.as_view()
    response = summary_view(api_request)
    
    context = {
        'user_data': response.data,
        'user': request.user,
    }
    
    return render(request, 'client_dashboard.html', context)
