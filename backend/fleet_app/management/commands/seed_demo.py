"""幂等写入演示数据：让合规预检在空库下也能直接演示。

    python manage.py seed_demo

重跑会先清掉演示车辆/司机/调度单，再按“今天”重建，因此长途+早班等
冲突场景始终相对当前时间成立。
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from fleet_app import models

DEMO_PLATES = ('沪A-7821', '苏E-5520')
DEMO_PHONES = ('13800000001', '13800000002')


class Command(BaseCommand):
    help = '空库时写入演示用的司机、车辆与调度单数据'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true',
                            help='即使库中已有数据也重建演示数据')

    def handle(self, *args, **options):
        if not options['force'] and (
                models.Driver.objects.exists() or models.Vehicle.objects.exists()):
            self.stdout.write('库中已有数据，跳过演示数据写入')
            return

        models.DispatchOrder.objects.filter(driver__phone__in=DEMO_PHONES).delete()
        models.Driver.objects.filter(phone__in=DEMO_PHONES).delete()
        models.Vehicle.objects.filter(plate_no__in=DEMO_PLATES).delete()

        now = timezone.localtime().replace(minute=0, second=0, microsecond=0)
        today = now.date()

        zhao = models.Driver.objects.create(
            name='赵强', phone=DEMO_PHONES[0], license_type='B2',
            license_expire_date=today + timedelta(days=600),
            hire_date=today - timedelta(days=900),
            status='Available', driving_hours=3200, violation_count=1,
            daily_drive_limit_minutes=480, min_rest_minutes=60,
            night_rest_minutes=480,
        )
        sun = models.Driver.objects.create(
            name='孙晨', phone=DEMO_PHONES[1], license_type='A2',
            license_expire_date=today + timedelta(days=900),
            hire_date=today - timedelta(days=1200),
            status='Available', driving_hours=4810, violation_count=0,
            daily_drive_limit_minutes=600, min_rest_minutes=120,
            night_rest_minutes=480,
        )
        cold = models.Vehicle.objects.create(
            plate_no='沪A-7821', vehicle_type='冷链车', brand_model='东风天锦 KR',
            purchase_date=today - timedelta(days=900),
            insurance_expire_date=today + timedelta(days=120),
            inspection_expire_date=today + timedelta(days=200),
            status='Available', mileage=88210, tank_capacity=380, fuel_consumption=24.6,
        )
        truck = models.Vehicle.objects.create(
            plate_no='苏E-5520', vehicle_type='重卡', brand_model='解放 J6P',
            purchase_date=today - timedelta(days=1500),
            insurance_expire_date=today + timedelta(days=40),
            inspection_expire_date=today + timedelta(days=90),
            status='OnTrip', mileage=210430, tank_capacity=520, fuel_consumption=31.2,
        )

        at = lambda h, d=0: now.replace(hour=h) + timedelta(days=d)

        # 赵强：昨天 18:00 出发、今天 02:00 完成的长途（实际记录）
        models.DispatchOrder.objects.create(
            order_no=f'DSP-{today.strftime("%Y%m%d")}-9001', vehicle=cold, driver=zhao,
            origin='上海青浦仓', destination='武汉转运中心',
            plan_depart_at=at(18, -1), plan_arrive_at=at(2, 0),
            actual_depart_at=at(18, -1), actual_arrive_at=at(2, 0),
            cargo='冷链食品', weight=8200, freight=7200,
            status='Completed', creator_id=1, note='夜间长途，刚收车',
        )
        # 孙晨：明天 09:00-15:00 已计划
        models.DispatchOrder.objects.create(
            order_no=f'DSP-{today.strftime("%Y%m%d")}-9002', vehicle=truck, driver=sun,
            origin='苏州园区', destination='宁波北仑',
            plan_depart_at=at(9, 1), plan_arrive_at=at(15, 1),
            cargo='建筑材料', weight=16000, freight=9800,
            status='Assigned', creator_id=1, note='',
        )
        # 赵强：明天 09:00-12:00 已计划（用于演示当日累计/相邻间隔）
        models.DispatchOrder.objects.create(
            order_no=f'DSP-{today.strftime("%Y%m%d")}-9003', vehicle=cold, driver=zhao,
            origin='上海青浦仓', destination='杭州萧山仓',
            plan_depart_at=at(9, 1), plan_arrive_at=at(12, 1),
            cargo='生鲜', weight=6000, freight=3600,
            status='Assigned', creator_id=1, note='',
        )

        self.stdout.write(self.style.SUCCESS('演示数据已写入：赵强（昨夜长途）、孙晨（明日已排班）'))
