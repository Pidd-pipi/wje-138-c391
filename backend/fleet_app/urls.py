from django.urls import path
from rest_framework.response import Response
from rest_framework.decorators import api_view
from fleet_app.views.vehicle_views import vehicles
from fleet_app.views.driver_views import drivers, driver_detail
from fleet_app.views.dispatch_views import (
    dispatch_orders, dispatch_order_start, dispatch_assign_precheck,
)
from fleet_app.views.maintenance_views import maintenance_records
from fleet_app.views.fuel_views import fuel_records

@api_view(['GET'])
def health(request):
    return Response({'status': 'ok', 'service': 'fleet-dispatch'})

urlpatterns = [
    path('health/', health),
    path('vehicles/', vehicles),
    path('drivers/', drivers),
    path('drivers/<int:driver_id>/', driver_detail),
    path('dispatch-orders/', dispatch_orders),
    path('dispatch-orders/<int:order_id>/start/', dispatch_order_start),
    path('dispatch-orders/precheck/', dispatch_assign_precheck),
    path('maintenance-records/', maintenance_records),
    path('fuel-records/', fuel_records),
]
