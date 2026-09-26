"""司机档案与班次合规摘要服务。"""
from datetime import date

from django.utils import timezone

from fleet_app import models
from fleet_app.services import compliance_service

COMPLIANCE_FIELDS = (
    'daily_driving_limit_minutes',
    'min_rest_minutes',
    'nightly_rest_minutes',
)


def serialize_driver(driver, now=None):
    data = {
        'id': driver.id,
        'name': driver.name,
        'phone': driver.phone,
        'licenseType': driver.license_type,
        'licenseExpireDate': driver.license_expire_date.strftime('%Y-%m-%d') if driver.license_expire_date else '',
        'hireDate': driver.hire_date.strftime('%Y-%m-%d') if driver.hire_date else '',
        'status': driver.status,
        'drivingHours': driver.driving_hours,
        'violationCount': driver.violation_count,
        'dailyDrivingLimitMinutes': driver.daily_driving_limit_minutes,
        'minRestMinutes': driver.min_rest_minutes,
        'nightlyRestMinutes': driver.nightly_rest_minutes,
    }
    data['compliance'] = compliance_service.schedule_summary(driver, now=now)
    return data


def list_drivers():
    return [serialize_driver(driver) for driver in models.Driver.objects.all().order_by('id')]


def get_driver(driver_id):
    return models.Driver.objects.filter(id=driver_id).first()


def update_compliance(driver_id, payload):
    driver = get_driver(driver_id)
    if driver is None:
        return None
    for field in COMPLIANCE_FIELDS:
        if field in payload and payload[field] is not None:
            value = int(payload[field])
            if value < 0:
                raise ValueError(f'{field} 不能为负数')
            setattr(driver, field, value)
    driver.save()
    return serialize_driver(driver)


def ensure_demo_data():
    """空库时写入演示档案与调度单（供无迁移环境下直接体验，时间以「现在」为基准生成）。"""
    from fleet_app.services.vehicle_service import ensure_demo_vehicles

    ensure_demo_vehicles()
    if models.Driver.objects.exists():
        return
    models.Driver.objects.bulk_create([
        models.Driver(name='赵强', phone='13800000001', license_type='A2',
                      license_expire_date=date(2028, 5, 1), hire_date=date(2022, 1, 10),
                      status='Available', driving_hours=3200, violation_count=1,
                      daily_driving_limit_minutes=480, min_rest_minutes=60,
                      nightly_rest_minutes=600),
        models.Driver(name='孙晨', phone='13800000002', license_type='A2',
                      license_expire_date=date(2029, 4, 18), hire_date=date(2021, 11, 16),
                      status='OnTrip', driving_hours=4810, violation_count=0,
                      daily_driving_limit_minutes=480, min_rest_minutes=120,
                      nightly_rest_minutes=600),
        models.Driver(name='李玮', phone='13800000003', license_type='B2',
                      license_expire_date=date(2027, 9, 30), hire_date=date(2023, 3, 22),
                      status='Available', driving_hours=1900, violation_count=0,
                      daily_driving_limit_minutes=540, min_rest_minutes=60,
                      nightly_rest_minutes=600),
    ])
    _ensure_demo_orders(timezone.localtime(timezone.now()))


def _ensure_demo_orders(now):
    from datetime import datetime, time, timedelta

    from django.utils.timezone import make_aware

    if models.DispatchOrder.objects.exists():
        return

    zhao, sun, li = list(models.Driver.objects.all().order_by('id'))
    v1, v2, v3 = list(models.Vehicle.objects.all().order_by('id'))

    def next_occurrence(hour, minute, after):
        """after 之后（严格晚于）下一个到达指定钟点的时刻。"""
        day = after.date()
        candidate = make_aware(datetime.combine(day, time(hour=hour, minute=minute)))
        while candidate <= after:
            day += timedelta(days=1)
            candidate = make_aware(datetime.combine(day, time(hour=hour, minute=minute)))
        return candidate

    # —— 赵强（min_rest=60）：3 小时前刚跑完一趟、此刻收车，30 分钟后又排一班。
    #    与上一班仅隔 30 分钟（落在夜间则按夜间连续休息），任意钟点都稳定复现
    #    「刚跑完长途接着排早班」。
    just_end = now
    just_start = now - timedelta(hours=3)
    soon_start = now + timedelta(minutes=30)
    soon_end = soon_start + timedelta(hours=2)

    # —— 孙晨：当前在途（2 小时前出发、2 小时后到达），min_rest=120。
    inprogress_depart = now - timedelta(hours=2)
    inprogress_arrive = now + timedelta(hours=2)

    # —— 李玮（nightly_rest=600）：未来一对「夜间长途 + 次日早班」。
    #    夜班 22:00→次日03:00，早班 07:00→09:00，间隔 4 小时且覆盖夜间窗口，
    #    稳定触发夜间连续休息冲突；两单锚定在未来，不受当前钟点影响。
    night_arrive = next_occurrence(3, 0, now + timedelta(hours=6))
    night_depart = night_arrive - timedelta(hours=5)      # 前一日 22:00
    early_depart = night_arrive + timedelta(hours=4)      # 07:00
    early_arrive = early_depart + timedelta(hours=2)      # 09:00

    models.DispatchOrder.objects.bulk_create([
        models.DispatchOrder(order_no='DSP-DEMO-0001', driver=zhao, vehicle=v2,
                             origin='上海青浦仓', destination='杭州萧山',
                             plan_depart_at=just_start, plan_arrive_at=just_end,
                             actual_depart_at=just_start, actual_arrive_at=just_end,
                             cargo='电子设备', weight=9000, freight=6800,
                             status='Completed', creator_id=1, note='刚跑完的长途'),
        models.DispatchOrder(order_no='DSP-DEMO-0002', driver=zhao, vehicle=v1,
                             origin='上海青浦仓', destination='苏州工业园',
                             plan_depart_at=soon_start, plan_arrive_at=soon_end,
                             cargo='冷链食品', weight=4200, freight=1600,
                             status='Assigned', creator_id=1, note='紧接着排的早班'),
        # 孙晨：当前在途，任务间最短休息设 120 分钟
        models.DispatchOrder(order_no='DSP-DEMO-0003', driver=sun, vehicle=v2,
                             origin='苏州园区', destination='宁波北仑',
                             plan_depart_at=inprogress_depart, plan_arrive_at=inprogress_arrive,
                             actual_depart_at=inprogress_depart,
                             cargo='建筑材料', weight=16000, freight=9800,
                             status='InProgress', creator_id=1, note='在途'),
        # 李玮：未来夜间长途
        models.DispatchOrder(order_no='DSP-DEMO-0004', driver=li, vehicle=v3,
                             origin='南京龙潭', destination='合肥撮镇',
                             plan_depart_at=night_depart, plan_arrive_at=night_arrive,
                             cargo='机械设备', weight=12000, freight=8600,
                             status='Assigned', creator_id=1, note='夜间长途'),
        # 李玮：次日早班，与夜班间隔不足夜间连续休息
        models.DispatchOrder(order_no='DSP-DEMO-0005', driver=li, vehicle=v1,
                             origin='合肥撮镇', destination='南京龙潭',
                             plan_depart_at=early_depart, plan_arrive_at=early_arrive,
                             cargo='回程零担', weight=6000, freight=5200,
                             status='Pending', creator_id=1, note='早班（休息不足）'),
    ])
