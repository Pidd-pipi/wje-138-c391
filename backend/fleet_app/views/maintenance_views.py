from rest_framework.decorators import api_view
from rest_framework.response import Response
from fleet_app.services.maintenance_service import list_records
@api_view(['GET'])
def maintenance_records(request):
    return Response(list_records())
