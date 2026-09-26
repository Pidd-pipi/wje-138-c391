from rest_framework.decorators import api_view
from rest_framework.response import Response
from fleet_app.services.fuel_analytics_service import list_fuel_records
@api_view(['GET'])
def fuel_records(request):
    return Response(list_fuel_records())
