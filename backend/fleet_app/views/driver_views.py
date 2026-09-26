from rest_framework.decorators import api_view
from rest_framework.response import Response

from fleet_app.services import driver_service
from fleet_app.services.exceptions import BadRequest


@api_view(['GET'])
def drivers(request):
    with_schedule = request.query_params.get('withSchedule') in ('1', 'true', 'True')
    return Response(driver_service.list_drivers(with_schedule=with_schedule))


@api_view(['GET', 'PATCH'])
def driver_detail(request, driver_id):
    if request.method == 'PATCH':
        return Response(driver_service.update_compliance(int(driver_id), request.data))
    driver = driver_service.get_driver(int(driver_id))
    if driver is None:
        raise BadRequest(f'司机不存在：{driver_id}')
    return Response(driver)
