import json
from datetime import timedelta

from django.test import Client, TestCase
from django.utils import timezone

from fleet_app import models


def at(hour, day=0):
    base = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
    return (base + timedelta(days=day)).replace(hour=hour)


class DispatchApiTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.driver = models.Driver.objects.create(
            name='赵强', phone='13800000001', license_type='B2',
            status='Available', daily_drive_limit_minutes=480,
            min_rest_minutes=60, night_rest_minutes=480)
        self.vehicle = models.Vehicle.objects.create(
            plate_no='沪A-0001', vehicle_type='冷链车', brand_model='X',
            status='Available')
        models.DispatchOrder.objects.create(
            order_no='DSP-OLD-1', vehicle=self.vehicle, driver=self.driver,
            origin='A', destination='B',
            plan_depart_at=at(18, -1), plan_arrive_at=at(2),
            actual_depart_at=at(18, -1), actual_arrive_at=at(2),
            status='Completed')

    def post_json(self, path, payload):
        return self.client.post(path, data=json.dumps(payload),
                                content_type='application/json')

    def test_precheck_endpoint(self):
        resp = self.post_json('/api/dispatch-orders/precheck/', {
            'driverId': self.driver.id,
            'planDepartAt': at(7).strftime('%Y-%m-%d %H:%M'),
            'planArriveAt': at(11).strftime('%Y-%m-%d %H:%M'),
        })
        self.assertEqual(resp.status_code, 200)
        body = resp.json()
        self.assertFalse(body['eligible'])
        self.assertTrue(body['reasons'])

    def test_create_conflict_returns_409(self):
        resp = self.post_json('/api/dispatch-orders/', {
            'driverId': self.driver.id, 'vehicleId': self.vehicle.id,
            'origin': 'C', 'destination': 'D',
            'planDepartAt': at(7).strftime('%Y-%m-%d %H:%M'),
            'planArriveAt': at(11).strftime('%Y-%m-%d %H:%M'),
        })
        self.assertEqual(resp.status_code, 409)
        body = resp.json()
        self.assertEqual(body['code'], 'compliance_conflict')
        self.assertFalse(body['details']['eligible'])

    def test_start_conflict_returns_409_and_keeps_status(self):
        order = models.DispatchOrder.objects.create(
            order_no='DSP-BAD-1', vehicle=self.vehicle, driver=self.driver,
            origin='C', destination='D',
            plan_depart_at=at(5), plan_arrive_at=at(9), status='Assigned')
        resp = self.client.post(f'/api/dispatch-orders/{order.id}/start/')
        self.assertEqual(resp.status_code, 409)
        order.refresh_from_db()
        self.assertEqual(order.status, 'Assigned')

    def test_driver_list_with_schedule_and_patch(self):
        resp = self.client.get('/api/drivers/?withSchedule=1')
        data = resp.json()[0]
        self.assertIn('schedule', data)
        self.assertEqual(data['schedule']['todayUsedMinutes'], 120)

        resp = self.client.patch(
            f'/api/drivers/{self.driver.id}/',
            data=json.dumps({'minRestMinutes': 120}),
            content_type='application/json')
        self.assertEqual(resp.status_code, 200)
        self.driver.refresh_from_db()
        self.assertEqual(self.driver.min_rest_minutes, 120)
