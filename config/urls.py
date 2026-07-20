from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from portal.views import health_check

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", health_check, name="health-check"),
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/", include("apps.rides.urls")),
    path("api/v1/", include("apps.payments.urls")),
    path("api/v1/", include("apps.fleet.urls")),
    path("api/v1/", include("apps.geoloc.urls")),
    path("chauffeur/", include("apps.users.urls_web")),
    path("client/", include("apps.users.urls_client")),
    path("", include("portal.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [path("__reload__/", include("django_browser_reload.urls"))]
