from rest_framework.decorators import api_view
from rest_framework.response import Response
from fleet_app.services.dispatch_service import create_order, list_orders
@api_view(['GET', 'POST'])
def dispatch_orders(request):
    if request.method == 'POST':
        return Response(create_order(request.data), status=201)
    return Response(list_orders())
