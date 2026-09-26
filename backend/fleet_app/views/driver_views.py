from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from fleet_app.serializers.driver_serializer import DriverComplianceSerializer
from fleet_app.services import compliance_service
from fleet_app.services.driver_service import (
    ensure_demo_data,
    list_drivers,
    update_compliance,
)


@api_view(['GET', 'PATCH'])
def drivers(request):
    """司机列表（含今日累计/下次可接单/未来占用）；PATCH 更新合规配置。"""
    if request.method == 'PATCH':
        return _patch_bulk(request)
    ensure_demo_data()
    return Response(list_drivers())


def _patch_bulk(request):
    serializer = DriverComplianceSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    # 未指定 id 时更新全部司机，便于演示统一配置
    driver_ids = request.data.get('driverIds')
    if driver_ids is None:
        driver_ids = [item['id'] for item in list_drivers()]
    results = []
    for driver_id in driver_ids:
        updated = update_compliance(int(driver_id), serializer.validated_data)
        if updated is not None:
            results.append(updated)
    return Response(results)


@api_view(['GET', 'PATCH'])
def driver_detail(request, driver_id):
    ensure_demo_data()
    from fleet_app.services.driver_service import get_driver, serialize_driver

    driver = get_driver(driver_id)
    if driver is None:
        return Response({'detail': '司机不存在'}, status=status.HTTP_404_NOT_FOUND)
    if request.method == 'PATCH':
        serializer = DriverComplianceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            updated = update_compliance(driver.id, serializer.validated_data)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(updated)
    return Response(serialize_driver(driver))


@api_view(['POST'])
def driver_assignment_check(request, driver_id):
    """调度页选人时实时预检：返回能否指派及冲突原因（涉及单号、还缺时间）。"""
    ensure_demo_data()
    from fleet_app.services.driver_service import get_driver

    driver = get_driver(driver_id)
    if driver is None:
        return Response({'detail': '司机不存在'}, status=status.HTTP_404_NOT_FOUND)
    result = compliance_service.assignment_check(
        driver,
        request.data.get('planDepartAt'),
        request.data.get('planArriveAt'),
        exclude_id=request.data.get('excludeOrderId'),
    )
    return Response(result)
