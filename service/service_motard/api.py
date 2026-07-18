from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .logic import MotardHardwareService

@method_decorator(csrf_exempt, name='dispatch')
class TrackerPingView(View):
    """
    Endpoint for GPS trackers to send their current position.
    URL example: /geoloc/tracker/ping/?imei=123456789&lat=-4.32&lng=15.31&speed=20&batt=85
    """
    def get(self, request):
        # We support GET for simplicity with some trackers, 
        # but POST is preferred for security/standard.
        return self.handle_ping(request)

    def post(self, request):
        # For POST, we assume the tracker sends data in query params or simple form
        return self.handle_ping(request)

    def handle_ping(self, request):
        imei = request.GET.get('imei')
        lat = request.GET.get('lat')
        lng = request.GET.get('lng')
        speed = request.GET.get('speed')
        battery = request.GET.get('batt')

        if not all([imei, lat, lng]):
            return JsonResponse({
                "status": "error", 
                "message": "Missing required parameters: imei, lat, lng"
            }, status=400)

        try:
            result = MotardHardwareService.process_ping(
                device_id=imei, 
                latitude=float(lat), 
                longitude=float(lng), 
                speed=float(speed) if speed else None, 
                battery=int(battery) if battery else None
            )
            return JsonResponse(result)
        except ValueError:
            return JsonResponse({"status": "error", "message": "Invalid coordinate format"}, status=400)
