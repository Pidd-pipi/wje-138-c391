import os
from datetime import datetime, timedelta

from django.test import TestCase
from django.utils import timezone

from fleet_app.services import compliance_service as cs

os.environ.setdefault('DB_ENGINE', 'django.db.backends.sqlite3')


def dt(h, d=0, minute=0):
    base = timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)
    return base + timedelta(days=d, hours=h, minutes=minute)


def iso(value):
    return value.isoformat()


DRIVER = {
    'status': 'Available',
    'daily_drive_limit_minutes': 480,
    'min_rest_minutes': 60,
    'night_rest_minutes': 480,
}


def task(order_no, s, e, status='Assigned', actual_s=None, actual_e=None):
    return {
        'id': abs(hash(order_no)) % 100000,
        'orderNo': order_no,
        'status': status,
        'origin': 'A', 'destination': 'B',
        'planDepartAt': iso(s), 'planArriveAt': iso(e),
        'actualDepartAt': iso(actual_s) if actual_s else None,
        'actualArriveAt': iso(actual_e) if actual_e else None,
    }


class ComplianceEngineTests(TestCase):
    def rules(self, tasks, s, e, driver=None):
        return cs.evaluate(driver or DRIVER, tasks, s, e)

    def test_clean_schedule_passes(self):
        tasks = [task('DSP-1', dt(9), dt(12))]
        self.assertEqual(self.rules(tasks, dt(14), dt(17)), [])

    def test_overlap_reported_with_order_no(self):
        tasks = [task('DSP-1', dt(9), dt(12))]
        violations = self.rules(tasks, dt(11), dt(13))
        self.assertEqual(violations[0]['rule'], 'overlap')
        self.assertIn('DSP-1', violations[0]['message'])

    def test_daily_limit_accumulates_completed_and_planned(self):
        # 已完成 6h + 新单 3h = 9h > 8h
        tasks = [task('DSP-OLD', dt(8), dt(14), status='Completed',
                      actual_s=dt(8), actual_e=dt(14))]
        violations = self.rules(tasks, dt(15), dt(18))
        daily = [v for v in violations if v['rule'] == 'daily_limit']
        self.assertEqual(len(daily), 1)
        self.assertEqual(daily[0]['usedMinutes'], 360)
        self.assertEqual(daily[0]['shortageMinutes'], 60)
        self.assertIn('DSP-OLD', daily[0]['message'])

    def test_daily_limit_splits_by_calendar_day(self):
        # 跨天 8h（每天 4h），新单当天只占 4h => 不超限
        tasks = [task('DSP-OLD', dt(20), dt(0, 1), status='Completed',
                      actual_s=dt(20), actual_e=dt(0, 1))]
        violations = self.rules(tasks, dt(9, 1), dt(13, 1))
        self.assertFalse([v for v in violations if v['rule'] == 'daily_limit'])

    def test_min_rest_gap_after_predecessor_with_shortage(self):
        # 前序 10:00 结束，新单 10:30 开始 -> 缺 30 分钟
        tasks = [task('DSP-2', dt(8), dt(10))]
        violations = self.rules(tasks, dt(10, minute=30), dt(12))
        min_rest = [v for v in violations if v['rule'] == 'min_rest' and v['kind'] == 'predecessor']
        self.assertEqual(min_rest[0]['shortageMinutes'], 30)
        self.assertIn('DSP-2', min_rest[0]['message'])
        self.assertIn('还缺 30分钟', min_rest[0]['message'])

    def test_min_rest_gap_before_successor(self):
        tasks = [task('DSP-3', dt(14), dt(18))]
        violations = self.rules(tasks, dt(12), dt(13, minute=30))
        succ = [v for v in violations if v['rule'] == 'min_rest' and v['kind'] == 'successor']
        self.assertEqual(succ[0]['shortageMinutes'], 30)

    def test_exactly_enough_rest_passes(self):
        tasks = [task('DSP-4', dt(8), dt(10))]
        self.assertEqual(self.rules(tasks, dt(11), dt(12)), [])

    # --------- 夜间连续休息 ---------

    def test_long_haul_then_early_shift_is_night_violation(self):
        # 昨夜 18:00 -> 今晨 02:00 完成长途，新单 07:00 出发：
        # 夜间窗 22:00~06:00 内只能休 02:00~06:00 = 4h，缺 4h
        tasks = [task('DSP-N1', dt(18, -1), dt(2), status='Completed',
                      actual_s=dt(18, -1), actual_e=dt(2))]
        violations = self.rules(tasks, dt(7), dt(11))
        night = [v for v in violations if v['rule'] == 'night_rest']
        self.assertTrue(night)
        self.assertEqual(night[0]['shortageMinutes'], 240)
        self.assertIn('DSP-N1', night[0]['message'])
        # 还缺多少时间 + 单号都要在提示里
        self.assertIn('还缺 4小时', night[0]['message'])

    def test_enough_night_rest_passes(self):
        # 昨夜长途 02:00 结束，次日 06:00 后再出发：完整跨过下一个夜间窗（8h）
        tasks = [task('DSP-N2', dt(18, -1), dt(2), status='Completed',
                      actual_s=dt(18, -1), actual_e=dt(2))]
        self.assertEqual(self.rules(tasks, dt(6, 1), dt(10, 1)), [])

    def test_long_haul_same_morning_never_enough_in_window(self):
        # 02:00 收车，哪怕 10:00 出发，昨夜窗内也只休 4h，仍违规
        tasks = [task('DSP-N2B', dt(18, -1), dt(2), status='Completed',
                      actual_s=dt(18, -1), actual_e=dt(2))]
        violations = self.rules(tasks, dt(10), dt(14))
        self.assertTrue([v for v in violations if v['rule'] == 'night_rest'])

    def test_afternoon_finish_then_early_shift_short_in_window(self):
        # 下午 15:00 收车，次日 04:00 出发：窗内（22:00~04:00）仅 6h < 8h
        tasks = [task('DSP-N3', dt(8), dt(15))]
        violations = self.rules(tasks, dt(4, 1), dt(8, 1))
        night = [v for v in violations if v['rule'] == 'night_rest']
        self.assertTrue(night)
        self.assertEqual(night[0]['shortageMinutes'], 120)

    def test_afternoon_finish_then_six_oclock_passes(self):
        # 次日 06:00 出发：窗内完整休息 8h
        tasks = [task('DSP-N3', dt(8), dt(15))]
        self.assertEqual(self.rules(tasks, dt(6, 1), dt(10, 1)), [])

    def test_full_overnight_driving_violation(self):
        # 新单自身 20:00 -> 次日 08:00，完整覆盖 22:00~06:00
        violations = self.rules([], dt(20), dt(8, 1))
        full = [v for v in violations if v['rule'] == 'night_rest' and v['kind'] == 'full_window']
        self.assertTrue(full)

    def test_driver_leave_not_assignable(self):
        driver = dict(DRIVER, status='Leave')
        violations = self.rules([], dt(9), dt(12), driver=driver)
        self.assertEqual(violations[0]['rule'], 'driver_status')

    def test_zero_limit_disables_rule(self):
        driver = dict(DRIVER, daily_drive_limit_minutes=0,
                      min_rest_minutes=0, night_rest_minutes=0)
        tasks = [task('DSP-Z', dt(18, -1), dt(2), status='Completed',
                      actual_s=dt(18, -1), actual_e=dt(2))]
        self.assertEqual(self.rules(tasks, dt(2, minute=30), dt(23), driver=driver), [])

    def test_earliest_after_long_haul_pushes_to_six(self):
        # 02:00 收车：min_rest 60 给 03:00，但夜间窗只休到 03:00(1h) -> 推到 06:00
        nxt = cs.earliest_after(dt(2), 60, 480)
        self.assertEqual(nxt.hour, 6)
        self.assertEqual(nxt.date(), dt(2).date())

    def test_earliest_after_afternoon_finish(self):
        nxt = cs.earliest_after(dt(15), 60, 480)
        self.assertEqual(nxt, dt(16))

    def test_schedule_overview_fields(self):
        tasks = [task('DSP-S', dt(18, -1), dt(2), status='Completed',
                      actual_s=dt(18, -1), actual_e=dt(2)),
                 task('DSP-F', dt(9, 1), dt(12, 1))]
        overview = cs.schedule_overview(DRIVER, tasks)
        self.assertEqual(overview['dailyLimitMinutes'], 480)
        self.assertIn('nextAvailableAt', overview)
        self.assertTrue(any(o['orderNo'] == 'DSP-F' for o in overview['upcoming']))
        # 昨夜长途实际在今日 00:00-02:00，今日累计 120 分钟
        self.assertEqual(overview['todayUsedMinutes'], 120)
