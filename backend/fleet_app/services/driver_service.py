"""司机档案服务：列表/详情携带今日累计、下次可接单时间与未来占用。"""
from fleet_app import models
from fleet_app.services import compliance_service


def _serialize(driver, overview=None):
    data = {
        'id': driver.id,
        'name': driver.name,
        'phone': driver.phone,
        'licenseType': driver.license_type,
        'licenseExpireDate': driver.license_expire_date.strftime('%Y-%m-%d') if driver.license_expire_date else None,
        'hireDate': driver.hire_date.strftime('%Y-%m-%d') if driver.hire_date else None,
        'status': driver.status,
        'drivingHours': driver.driving_hours,
        'violationCount': driver.violation_count,
        'dailyDriveLimitMinutes': driver.daily_drive_limit_minutes,
        'minRestMinutes': driver.min_rest_minutes,
        'nightRestMinutes': driver.night_rest_minutes,
    }
    if overview is not None:
        data['schedule'] = overview
    return data


def _tasks(driver_id):
    return list(models.DispatchOrder.objects.filter(driver_id=driver_id).exclude(
        status='Cancelled').order_by('plan_depart_at').values(
        'id', 'order_no', 'origin', 'destination', 'status',
        'plan_depart_at', 'plan_arrive_at',
        'actual_depart_at', 'actual_arrive_at'))


def list_drivers(with_schedule=False):
    result = []
    for driver in models.Driver.objects.all().order_by('id'):
        overview = compliance_service.schedule_overview(driver, _tasks(driver.id)) if with_schedule else None
        result.append(_serialize(driver, overview))
    return result


def get_driver(driver_id):
    driver = models.Driver.objects.filter(id=driver_id).first()
    if not driver:
        return None
    return _serialize(driver, compliance_service.schedule_overview(driver, _tasks(driver_id)))


def update_compliance(driver_id, payload):
    from fleet_app.services.exceptions import BadRequest
    driver = models.Driver.objects.filter(id=driver_id).first()
    if not driver:
        raise BadRequest(f'司机不存在：{driver_id}')
    fields = {
        'dailyDriveLimitMinutes': 'daily_drive_limit_minutes',
        'minRestMinutes': 'min_rest_minutes',
        'nightRestMinutes': 'night_rest_minutes',
    }
    for camel, snake in fields.items():
        if camel in payload and payload[camel] is not None:
            try:
                value = int(payload[camel])
            except (TypeError, ValueError):
                raise BadRequest(f'{camel} 必须是分钟整数（0 表示不限制）')
            if value < 0:
                raise BadRequest(f'{camel} 不能为负数')
            setattr(driver, snake, value)
    driver.save(update_fields=list(fields.values()))
    return _serialize(driver)
