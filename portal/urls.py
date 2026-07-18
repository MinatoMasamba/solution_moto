from django.urls import path

from . import views

app_name = "portal"

urlpatterns = [
    # Portail public
    path("", views.HomeView.as_view(), name="home"),
    path("inscription/", views.RegisterPageView.as_view(), name="register"),
    path("connexion/", views.LoginPageView.as_view(), name="login"),
    path("deconnexion/", views.LogoutView.as_view(), name="logout"),

    # Direction Générale (opérateur)
    path("direction/connexion/", views.DirectionLoginView.as_view(), name="direction_login"),
    path("direction/", views.DirectionDashboardView.as_view(), name="direction_dashboard"),
    path("direction/console/", views.DirectionConsoleView.as_view(), name="direction_console"),

    # Gérance (gérant de flotte)
    path("gerance/connexion/", views.GeranceAuthView.as_view(), name="gerance_auth"),
    path("gerance/", views.GeranceDashboardView.as_view(), name="gerance_dashboard"),

    # API tableaux de bord
    path("api/dashboard/operator/", views.OperatorDashboardView.as_view(), name="operator_dashboard"),
    path("api/dashboard/operator/clients/", views.OperatorClientsView.as_view(), name="operator_clients"),
    path("api/dashboard/operator/gerants/", views.OperatorGerantsView.as_view(), name="operator_gerants"),
    path("api/dashboard/operator/commissions/", views.OperatorCommissionsView.as_view(), name="operator_commissions"),
    path("api/dashboard/owner/", views.OwnerDashboardView.as_view(), name="owner_dashboard"),
    path("api/dashboard/fleet-manager/", views.FleetManagerDashboardView.as_view(), name="fleet_manager_dashboard"),
    path("api/dashboard/fleet-manager/performance/", views.ManagerPerformanceView.as_view(), name="fleet_manager_performance"),
    path("api/dashboard/notifications/", views.NotificationsView.as_view(), name="notifications"),
    path("api/account/password/", views.PasswordChangeView.as_view(), name="password_change"),
]
