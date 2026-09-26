from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from fleet_app import models
from fleet_app.services import dispatch_service, driver_service
from fleet_app.services.exceptions import BusinessConflict


def at(hour, day=0, minute=0):
    base = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
    return base + timedelta(days=day) + timedelta(hours=hour, minutes=minute)


def fmt(value):
    return value.strftime('%Y-%m-%d %H:%M')


class DispatchComplianceFlowTests(TestCase):
    def setUp(self):
        self.driver = models.Driver.objects.create(
            name='赵强', phone='13800000001', license_type='B2',
            status='Available', daily_drive_limit_minutes=480,
            min_rest_minutes=60, night_rest_minutes=480)
        self.vehicle = models.Vehicle.objects.create(
            plate_no='沪A-0001', vehicle_type='冷链车', brand_model='X',
            status='Available')
        # 昨夜 18:00 -> 今晨 02:00 已完成长途
        models.DispatchOrder.objects.create(
            order_no='DSP-OLD-1', vehicle=self.vehicle, driver=self.driver,
            origin='A', destination='B',
            plan_depart_at=at(18, -1), plan_arrive_at=at(2),
            actual_depart_at=at(18, -1), actual_arrive_at=at(2),
            status='Completed')

    def test_precheck_rejects_early_shift_after_long_haul(self):
        result = dispatch_service.check_driver(
            self.driver.id, fmt(at(7)), fmt(at(11)))
        self.assertFalse(result['eligible'])
        self.assertTrue(any('DSP-OLD-1' in r for r in result['reasons']))
        self.assertTrue(any('还缺' in r for r in result['reasons']))

    def test_create_order_conflict_does_not_persist(self):
        before = models.DispatchOrder.objects.count()
        with self.assertRaises(BusinessConflict):
            dispatch_service.create_order({
                'driverId': self.driver.id, 'vehicleId': self.vehicle.id,
                'origin': 'C', 'destination': 'D',
                'planDepartAt': fmt(at(7)), 'planArriveAt': fmt(at(11)),
            })
        self.assertEqual(models.DispatchOrder.objects.count(), before)

    def test_create_then_start_conflict_blocks_execution(self):
        # 次日 06:30 合法（跨过完整夜间窗），可建单
        order = dispatch_service.create_order({
            'driverId': self.driver.id, 'vehicleId': self.vehicle.id,
            'origin': 'C', 'destination': 'D',
            'planDepartAt': fmt(at(6, 1) + timedelta(minutes=30)),
            'planArriveAt': fmt(at(10, 1)),
        })
        self.assertEqual(order['status'], 'Assigned')

    def test_start_order_conflict(self):
        # 手工建一张违规的 Assigned 单（绕过建单预检），发车必须被拦
        order = models.DispatchOrder.objects.create(
            order_no='DSP-BAD-1', vehicle=self.vehicle, driver=self.driver,
            origin='C', destination='D',
            plan_depart_at=at(5), plan_arrive_at=at(9), status='Assigned')
        with self.assertRaises(BusinessConflict) as ctx:
            dispatch_service.start_order(order.id)
        self.assertIn('DSP-BAD-1', ctx.exception.message)
        order.refresh_from_db()
        self.assertEqual(order.status, 'Assigned')
        self.assertIsNone(order.actual_depart_at)

    def test_driver_overview_carries_used_and_next_available(self):
        data = driver_service.get_driver(self.driver.id)
        self.assertEqual(data['schedule']['todayUsedMinutes'], 120)
        self.assertTrue(data['schedule']['nextAvailableAt'])
        self.assertEqual(data['dailyDriveLimitMinutes'], 480)

    def test_update_compliance_limits(self):
        driver_service.update_compliance(self.driver.id, {
            'dailyDriveLimitMinutes': 600, 'minRestMinutes': 90,
            'nightRestMinutes': 600})
        self.driver.refresh_from_db()
        self.assertEqual(self.driver.daily_drive_limit_minutes, 600)
        self.assertEqual(self.driver.min_rest_minutes, 90)
        self.assertEqual(self.driver.night_rest_minutes, 600)
