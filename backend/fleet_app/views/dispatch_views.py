from rest_framework.decorators import api_view
from rest_framework.response import Response
from fleet_app.services import dispatch_service


@api_view(['GET', 'POST'])
def dispatch_orders(request):
    if request.method == 'POST':
        # 建单即做班次合规预检；冲突时 service 抛 BusinessConflict，不进入执行
        return Response(dispatch_service.create_order(request.data), status=201)
    return Response(dispatch_service.list_orders(request.query_params.get('status')))


@api_view(['POST'])
def dispatch_order_start(request, order_id):
    # 发车前二次预检：冲突则保持原状态，调度单不进入执行
    return Response(dispatch_service.start_order(int(order_id)))


@api_view(['POST'])
def dispatch_assign_precheck(request):
    # 选人时实时预检，返回能否指派及原因
    result = dispatch_service.check_driver(
        request.data.get('driverId'),
        request.data.get('planDepartAt'),
        request.data.get('planArriveAt'),
    )
    return Response(result)
