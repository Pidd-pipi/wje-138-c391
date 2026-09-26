"""调度单服务：建单与发车均经过司机班次合规预检，冲突时单据不进入执行。"""
from datetime import datetime, timedelta

from django.utils import timezone

from fleet_app import models
from fleet_app.services import compliance_service
from fleet_app.services.compliance_service import ComplianceViolation


def _pick(payload, *keys):
    for key in keys:
        if key in payload and payload[key] not in (None, ''):
            return payload[key]
    return None


def _parse_dt(value):
    return compliance_service.parse_dt(value)


def _format_dt(dt):
    if not dt:
        return None
    return timezone.localtime(dt).strftime('%Y-%m-%d %H:%M')


def _generate_order_no():
    today = timezone.localtime(timezone.now()).strftime('%Y%m%d')
    prefix = f'DSP-{today}-'
    count = models.DispatchOrder.objects.filter(order_no__startswith=prefix).count()
    return f'{prefix}{count + 1:04d}'


def serialize_order(order):
    data = {
        'id': order.id,
        'orderNo': order.order_no,
        'vehicleId': order.vehicle_id,
        'driverId': order.driver_id,
        'origin': order.origin,
        'destination': order.destination,
        'planDepartAt': _format_dt(order.plan_depart_at),
        'planArriveAt': _format_dt(order.plan_arrive_at),
        'actualDepartAt': _format_dt(order.actual_depart_at),
        'actualArriveAt': _format_dt(order.actual_arrive_at),
        'cargo': order.cargo,
        'weight': order.weight,
        'freight': order.freight,
        'status': order.status,
        'creatorId': order.creator_id,
        'note': order.note or '',
    }
    data['compliance'] = _order_compliance(order)
    return data


def _order_compliance(order):
    """该单按自身计划时间再次预检（排除自身），用于列表标识能否发车及原因。"""
    if order.status in ('Completed', 'Cancelled') or not order.driver_id:
        return {'assignable': True, 'violations': []}
    driver = models.Driver.objects.filter(id=order.driver_id).first()
    if driver is None:
        return {'assignable': True, 'violations': []}
    result = compliance_service.assignment_check(
        driver, order.plan_depart_at, order.plan_arrive_at, exclude_id=order.id)
    return {'assignable': result['assignable'], 'violations': result['violations']}


def list_orders():
    from fleet_app.services.driver_service import ensure_demo_data

    ensure_demo_data()
    return [serialize_order(o) for o in
            models.DispatchOrder.objects.select_related('driver', 'vehicle').all().order_by('-plan_depart_at', '-id')]


def create_order(payload):
    """建单（可同时指派车辆与司机）；司机合规预检不过则抛 ComplianceViolation，不落库。"""
    from fleet_app.services.driver_service import ensure_demo_data

    ensure_demo_data()

    origin = _pick(payload, 'origin') or '未填写出发地'
    destination = _pick(payload, 'destination') or '未填写目的地'
    plan_start = _parse_dt(_pick(payload, 'planDepartAt', 'plan_depart_at')) or timezone.now()
    plan_end = _parse_dt(_pick(payload, 'planArriveAt', 'plan_arrive_at'))
    if plan_end is None:
        plan_end = plan_start + timedelta(hours=4)
    if plan_end <= plan_start:
        raise ValueError('预计到达时间必须晚于预计出发时间')

    driver_id = _pick(payload, 'driverId', 'driver_id')
    vehicle_id = _pick(payload, 'vehicleId', 'vehicle_id')
    driver = models.Driver.objects.filter(id=driver_id).first() if driver_id else None
    if driver_id and driver is None:
        raise ValueError('所选司机不存在')
    vehicle = models.Vehicle.objects.filter(id=vehicle_id).first() if vehicle_id else None
    if vehicle_id and vehicle is None:
        raise ValueError('所选车辆不存在')

    # 合规预检：冲突时不允许建单/指派，调度单不进入执行
    if driver is not None:
        compliance_service.assert_assignable(driver, plan_start, plan_end)

    order = models.DispatchOrder.objects.create(
        order_no=_generate_order_no(),
        driver=driver,
        vehicle=vehicle,
        origin=origin,
        destination=destination,
        plan_depart_at=plan_start,
        plan_arrive_at=plan_end,
        cargo=_pick(payload, 'cargo') or '',
        weight=float(_pick(payload, 'weight') or 0),
        freight=float(_pick(payload, 'freight') or 0),
        status='Assigned' if driver is not None else 'Pending',
        creator_id=int(_pick(payload, 'creatorId', 'creator_id') or 1),
        note=_pick(payload, 'note') or '',
    )
    return serialize_order(order)


def assign_driver(order_id, driver_id):
    """给已有调度单指派司机，同样执行合规预检。"""
    order = models.DispatchOrder.objects.filter(id=order_id).first()
    if order is None:
        raise ValueError('调度单不存在')
    driver = models.Driver.objects.filter(id=driver_id).first() if driver_id else None
    if driver_id and driver is None:
        raise ValueError('所选司机不存在')
    if driver is not None:
        compliance_service.assert_assignable(
            driver,
            order.plan_depart_at or timezone.now(),
            order.plan_arrive_at or timezone.now() + timedelta(hours=4),
            exclude_id=order.id,
        )
    order.driver = driver
    if driver is not None and order.status == 'Pending':
        order.status = 'Assigned'
    order.save()
    return serialize_order(order)


def start_order(order_id):
    """发车：以「现在」为实际出发时刻复检合规，不通过则保持 Assigned、不进入 InProgress。"""
    order = models.DispatchOrder.objects.filter(id=order_id).first()
    if order is None:
        raise ValueError('调度单不存在')
    if order.status not in ('Assigned', 'Pending'):
        raise ValueError(f'当前状态 {order.status} 不允许发车')
    if not order.driver_id:
        raise ValueError('尚未指派司机，不能发车')

    depart_at = timezone.now()
    arrive_at = order.plan_arrive_at
    # 晚点发车时保留计划行车时长，避免「计划到达早于实际出发」导致无法复检
    if order.plan_depart_at and arrive_at and arrive_at <= depart_at:
        duration = arrive_at - order.plan_depart_at
        if duration.total_seconds() > 0:
            arrive_at = depart_at + duration
    if arrive_at is None or arrive_at <= depart_at:
        raise ValueError('缺少有效的预计到达时间，无法完成发车预检')
    driver = models.Driver.objects.filter(id=order.driver_id).first()
    # 关键卡口：夜间连续休息 / 任务间休息 / 当日累计，任一不过都不发车
    compliance_service.assert_assignable(driver, depart_at, arrive_at, exclude_id=order.id)

    order.actual_depart_at = depart_at
    order.status = 'InProgress'
    order.save()
    return serialize_order(order)
