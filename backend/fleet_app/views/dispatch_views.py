from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from fleet_app.serializers.dispatch_serializer import DispatchOrderCreateSerializer
from fleet_app.services.compliance_service import ComplianceViolation
from fleet_app.services.dispatch_service import (
    assign_driver,
    create_order,
    list_orders,
    start_order,
)


def _violation_response(exc):
    """合规冲突统一 409：返回结构化冲突（单号、缺口分钟、中文说明），调度单不进入执行。"""
    return Response(
        {'detail': str(exc), 'code': 'driver_compliance_conflict', 'violations': exc.violations},
        status=status.HTTP_409_CONFLICT,
    )


@api_view(['GET', 'POST'])
def dispatch_orders(request):
    if request.method == 'POST':
        serializer = DispatchOrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            order = create_order(serializer.validated_data)
        except ComplianceViolation as exc:
            return _violation_response(exc)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(order, status=status.HTTP_201_CREATED)
    return Response(list_orders())


@api_view(['POST'])
def dispatch_assign(request, order_id):
    """给已有调度单指派/更换司机。"""
    serializer = DispatchOrderCreateSerializer(data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    try:
        order = assign_driver(order_id, serializer.validated_data.get('driver_id'))
    except ComplianceViolation as exc:
        return _violation_response(exc)
    except ValueError as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(order)


@api_view(['POST'])
def dispatch_start(request, order_id):
    """发车：合规预检不过返回 409，单据保持 Assigned 不进入 InProgress。"""
    try:
        order = start_order(order_id)
    except ComplianceViolation as exc:
        return _violation_response(exc)
    except ValueError as exc:
        return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
    return Response(order)
