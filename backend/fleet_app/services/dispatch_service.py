"""调度单服务：建单、指派、发车均经司机班次合规预检。"""
from datetime import datetime

from django.db.models import Max
from django.utils import timezone

from fleet_app import models
from fleet_app.services import compliance_service
from fleet_app.services.compliance_service import eligibility
from fleet_app.services.exceptions import BadRequest, BusinessConflict

VALID_STATUSES = ('Pending', 'Assigned', 'InProgress', 'Completed', 'Cancelled')


def _as_aware(value):
    if value is None:
        return None
    if timezone.is_naive(value):
        return timezone.make_aware(value)
    return value


def _dt(value):
    return _as_aware(compliance_service.parse_dt(value))


def _fmt_dt(value):
    return timezone.localtime(value).strftime('%Y-%m-%d %H:%M') if value else None


def _serialize(order):
    return {
        'id': order.id,
        'orderNo': order.order_no,
        'vehicleId': order.vehicle_id,
        'driverId': order.driver_id,
        'origin': order.origin,
        'destination': order.destination,
        'planDepartAt': _fmt_dt(order.plan_depart_at),
        'planArriveAt': _fmt_dt(order.plan_arrive_at),
        'actualDepartAt': _fmt_dt(order.actual_depart_at),
        'actualArriveAt': _fmt_dt(order.actual_arrive_at),
        'cargo': order.cargo,
        'weight': order.weight,
        'freight': order.freight,
        'status': order.status,
        'creatorId': order.creator_id,
        'note': order.note,
    }


def list_orders(status=None):
    queryset = models.DispatchOrder.objects.select_related('driver', 'vehicle').all()
    if status and status != 'all':
        queryset = queryset.filter(status=status)
    return [_serialize(order) for order in queryset.order_by('-plan_depart_at', '-id')]


def _generate_order_no(now):
    prefix = f'DSP-{now.strftime("%Y%m%d")}-'
    last = models.DispatchOrder.objects.filter(
        order_no__startswith=prefix).aggregate(m=Max('order_no'))['m']
    seq = int(last.rsplit('-', 1)[1]) + 1 if last else 1
    return f'{prefix}{seq:04d}'


def _driver_tasks(driver_id, exclude_order_id=None):
    orders = models.DispatchOrder.objects.filter(driver_id=driver_id).exclude(
        status='Cancelled').order_by('plan_depart_at')
    tasks = [_serialize(o) for o in orders]
    if exclude_order_id is not None:
        tasks = [t for t in tasks if t['id'] != exclude_order_id]
    return tasks


def check_driver(driver_id, start, end):
    """选人/建单前的合规预检（不落库）。"""
    driver = models.Driver.objects.filter(id=driver_id).first()
    if not driver:
        raise BadRequest(f'司机不存在：{driver_id}')
    try:
        start_dt, end_dt = _dt(start), _dt(end)
    except (ValueError, TypeError):
        raise BadRequest('时间格式应为 YYYY-MM-DD HH:MM')
    tasks = _driver_tasks(driver_id)
    return eligibility(driver, tasks, start_dt, end_dt)


def create_order(payload):
    driver_id = payload.get('driverId')
    start_raw = payload.get('planDepartAt')
    end_raw = payload.get('planArriveAt')
    try:
        start_dt, end_dt = _dt(start_raw), _dt(end_raw)
    except (ValueError, TypeError):
        raise BadRequest('预计出发/到达时间格式应为 YYYY-MM-DD HH:MM')
    if not start_dt or not end_dt or end_dt <= start_dt:
        raise BadRequest('预计到达时间必须晚于预计出发时间')

    driver = models.Driver.objects.filter(id=driver_id).first() if driver_id else None
    if driver_id and not driver:
        raise BadRequest(f'司机不存在：{driver_id}')

    result = None
    if driver:
        tasks = _driver_tasks(driver_id)
        result = eligibility(driver, tasks, start_dt, end_dt)
        if not result['eligible']:
            # 冲突：调度单不落库，不进入执行
            raise BusinessConflict(
                '司机班次合规预检不通过，调度单未创建',
                details=result)

    order = models.DispatchOrder.objects.create(
        order_no=_generate_order_no(start_dt),
        vehicle_id=payload.get('vehicleId'),
        driver=driver,
        origin=payload.get('origin', ''),
        destination=payload.get('destination', ''),
        plan_depart_at=start_dt,
        plan_arrive_at=end_dt,
        cargo=payload.get('cargo', ''),
        weight=payload.get('weight') or 0,
        freight=payload.get('freight') or 0,
        status='Assigned' if driver else 'Pending',
        creator_id=payload.get('creatorId') or 1,
        note=payload.get('note', ''),
    )
    return _serialize(order)


def start_order(order_id):
    """发车：再次按已有计划与完成记录核对，冲突则不进入执行。"""
    from django.utils import timezone
    order = models.DispatchOrder.objects.select_related('driver').filter(id=order_id).first()
    if not order:
        raise BadRequest(f'调度单不存在：{order_id}')
    if order.status not in ('Pending', 'Assigned'):
        raise BadRequest(f'当前状态 {order.status} 不可发车')
    if not order.driver_id:
        raise BadRequest('请先指派司机再发车')

    start_dt = order.plan_depart_at
    end_dt = order.plan_arrive_at
    tasks = _driver_tasks(order.driver_id, exclude_order_id=order.id)
    result = eligibility(order.driver, tasks, start_dt, end_dt)
    if not result['eligible']:
        raise BusinessConflict(
            f'单号 {order.order_no} 班次合规预检不通过，禁止发车',
            details={'orderNo': order.order_no, **result})

    order.status = 'InProgress'
    order.actual_depart_at = timezone.localtime()
    if not order.actual_arrive_at and end_dt and end_dt < order.actual_depart_at:
        order.actual_arrive_at = None
    order.save(update_fields=['status', 'actual_depart_at'])
    return _serialize(order)
