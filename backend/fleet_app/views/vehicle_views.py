from rest_framework.decorators import api_view
from rest_framework.response import Response
from fleet_app.services.vehicle_service import list_vehicles
@api_view(['GET'])
def vehicles(request):
    return Response(list_vehicles())
