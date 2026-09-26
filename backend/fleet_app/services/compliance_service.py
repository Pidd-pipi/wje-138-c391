"""司机班次合规预检引擎。

在建单（指派司机）和发车（开始运输）两个节点，按已有计划与完成记录核对：
1. 当日累计驾驶时长是否超过司机档案设置的每日驾驶上限；
2. 与相邻任务之间的间隔是否满足任务间最短休息；
3. 跨夜的相邻任务间隔是否满足夜间连续休息。

冲突结果统一携带涉及单号与还缺时间（分钟），调度单因此不进入执行。
"""
from datetime import datetime, time, timedelta

from django.utils import timezone

CANCELLED_STATUS = 'Cancelled'
INPROGRESS_STATUS = 'InProgress'

NIGHT_START = time(22, 0)   # 夜间休息窗口 22:00 起
NIGHT_END = time(6, 0)      # 到次日 06:00 止


class ComplianceViolation(Exception):
    """合规预检冲突，message 为面向调度员的中文说明。"""

    def __init__(self, violations):
        self.violations = violations
        detail = '；'.join(item['message'] for item in violations)
        super().__init__(detail or '司机班次合规预检未通过')


def parse_dt(value):
    """容错解析 ISO/「YYYY-MM-DD HH:MM」时间字符串，返回带时区的 datetime。"""
    if not value:
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip().replace('T', ' ')
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
            try:
                dt = datetime.strptime(text, fmt)
                break
            except ValueError:
                continue
        else:
            return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def local_now():
    return timezone.localtime(timezone.now())


def _fmt_minutes(value):
    """把分钟差（int 分钟或 timedelta）格式化成「X小时Y分钟」。"""
    if isinstance(value, timedelta):
        value = value.total_seconds() // 60
    minutes = max(0, int(round(value)))
    hours, mins = divmod(minutes, 60)
    if hours and mins:
        return f'{hours}小时{mins}分钟'
    if hours:
        return f'{hours}小时'
    return f'{mins}分钟'


def _order_no(order):
    return order.order_no if hasattr(order, 'order_no') else order.get('orderNo')


def order_window(order):
    """计算任务计划/有效占用区间 (start, end)，无有效时间返回 None。"""
    if hasattr(order, 'status'):
        status = order.status
        start = order.actual_depart_at or order.plan_depart_at
        end = order.actual_arrive_at or order.plan_arrive_at
    else:
        status = order.get('status')
        start = order.get('actualDepartAt') or order.get('planDepartAt')
        end = order.get('actualArriveAt') or order.get('planArriveAt')
    start, end = parse_dt(start), parse_dt(end)
    if start is None:
        return None
    # 只有出发没有到达的在途任务，按当前时刻计累计算
    if end is None:
        end = local_now() if status == INPROGRESS_STATUS else start
    if end < start:
        end = start
    return start, end


def actual_window(order):
    """实际驾驶区间：仅取实际出发/到达；在途未到达算到当前时刻。未发车返回 None。"""
    if hasattr(order, 'status'):
        status = order.status
        start = order.actual_depart_at
        end = order.actual_arrive_at
    else:
        status = order.get('status')
        start = order.get('actualDepartAt')
        end = order.get('actualArriveAt')
    start, end = parse_dt(start), parse_dt(end)
    if start is None:
        return None
    if end is None:
        end = local_now() if status == INPROGRESS_STATUS else start
    if end < start:
        end = start
    return start, end


def _driver_orders(driver_id, exclude_id=None):
    from fleet_app import models

    qs = models.DispatchOrder.objects.filter(driver_id=driver_id).exclude(status=CANCELLED_STATUS)
    if exclude_id is not None:
        qs = qs.exclude(id=exclude_id)
    return list(qs)


def _windows(orders):
    """返回按开始时间排序的 [(order, start, end)]，跳过缺时间的记录。"""
    rows = []
    for order in orders:
        window = order_window(order)
        if window:
            rows.append((order, window[0], window[1]))
    return sorted(rows, key=lambda row: row[1])


def _actual_windows(orders):
    """实际驾驶区间序列（已实际出发的任务），按开始时间排序。"""
    rows = []
    for order in orders:
        window = actual_window(order)
        if window:
            rows.append((order, window[0], window[1]))
    return sorted(rows, key=lambda row: row[1])


def _gap_covers_night(gap_start, gap_end):
    """休息段是否碰到夜间窗口（22:00-次日06:00，含边界：06:00 收车也算夜间刚结束）。"""
    if gap_end <= gap_start:
        return False
    # 间隔可能从凌晨开始（碰到的是前一晚的窗口），故从前一晚起连查三个窗口
    night_date = gap_start.date() - timedelta(days=1)
    for _ in range(3):
        win_start = timezone.make_aware(datetime.combine(night_date, NIGHT_START))
        win_end = timezone.make_aware(datetime.combine(night_date + timedelta(days=1), NIGHT_END))
        # 触碰夜间边界即按夜间休息对待（<= / >= 为含边界）
        if gap_start <= win_end and win_start <= gap_end:
            return True
        night_date += timedelta(days=1)
    return False


def _day_planned_minutes(driver_id, day, exclude_id=None):
    """当日累计：已有计划（Pending/Assigned/InProgress）与完成记录落在当日的分钟数。"""
    orders = _driver_orders(driver_id, exclude_id=exclude_id)
    day_start = timezone.make_aware(datetime.combine(day, time.min))
    day_end = day_start + timedelta(days=1)
    total = timedelta()
    for order in orders:
        window = order_window(order)
        if not window:
            continue
        start, end = window
        overlap = min(end, day_end) - max(start, day_start)
        if overlap.total_seconds() > 0:
            total += overlap
    return int(total.total_seconds() // 60)


def _today_used_minutes(driver_id, day, now, exclude_id=None):
    """今日已发生的实际驾驶分钟：完成记录按实际时长，在途任务算到当前时刻。"""
    orders = _driver_orders(driver_id, exclude_id=exclude_id)
    day_start = timezone.make_aware(datetime.combine(day, time.min))
    day_end = day_start + timedelta(days=1)
    total = timedelta()
    for order, start, end in _actual_windows(orders):
        start, end = max(start, day_start), min(end, day_end, now)
        if end > start:
            total += end - start
    return int(total.total_seconds() // 60)


def evaluate_driver(driver, candidate_start, candidate_end, exclude_id=None, now=None):
    """核对候选任务，返回冲突列表；空列表表示可指派。

    candidate_start/candidate_end：候选任务的开始、结束时刻（aware datetime）。
    exclude_id：候选任务自身的调度单 ID（建单/发车复检时排除自己）。
    """
    now = now or local_now()
    violations = []
    rows = _windows(_driver_orders(driver.id, exclude_id=exclude_id))

    required_gap = timedelta(minutes=driver.min_rest_minutes)
    required_night = timedelta(minutes=driver.nightly_rest_minutes)

    # 0. 与已有任务时间重叠：直接冲突，不允许同一司机同一时间跑两单
    overlapping = [row for row in rows if row[1] < candidate_end and candidate_start < row[2]]

    def _check_overlap(row):
        order = row[0]
        violations.append({
            'type': 'overlap',
            'orderNo': _order_no(order),
            'requiredMinutes': 0,
            'actualMinutes': 0,
            'missingMinutes': 0,
            'message': f'与任务 {_order_no(order)} 的执行时间重叠（{row[1]:%H:%M}-{row[2]:%H:%M}），需先调整时间',
        })

    for row in overlapping:
        _check_overlap(row)

    # 1. 相邻任务间隔：在已有任务序列中找到插入位置，核对前后两段
    free_rows = [row for row in rows if row not in overlapping]
    prior = max((row for row in free_rows if row[2] <= candidate_start), default=None, key=lambda r: r[2])
    following = min((row for row in free_rows if row[1] >= candidate_end), default=None, key=lambda r: r[1])

    def _check_gap(neighbor, gap_start, gap_end, side):
        if neighbor is None:
            return
        order = neighbor[0]
        gap = gap_end - gap_start
        nightly = _gap_covers_night(gap_start, gap_end)
        required = required_night if nightly else required_gap
        if gap < required:
            missing = required - gap
            kind = 'nightly_rest' if nightly else 'min_rest'
            label = '夜间连续休息' if nightly else '任务间最短休息'
            violations.append({
                'type': kind,
                'orderNo': _order_no(order),
                'requiredMinutes': int(required.total_seconds() // 60),
                'actualMinutes': int(gap.total_seconds() // 60),
                'missingMinutes': int(missing.total_seconds() // 60),
                'message': (
                    f'与{side}任务 {_order_no(order)} 间隔 {_fmt_minutes(gap)}，'
                    f'未满足{label} {_fmt_minutes(required)}，还缺 {_fmt_minutes(missing)}'
                ),
            })

    if prior is not None:
        _check_gap(prior, prior[2], candidate_start, '上一班')
    if following is not None:
        _check_gap(following, candidate_end, following[1], '下一班')

    # 2. 当日累计驾驶时长（已有计划 + 完成记录一起核对，候选单计入当日安排）
    limit = driver.daily_driving_limit_minutes
    if limit > 0:
        candidate_day = timezone.localtime(candidate_start).date()
        day_start = timezone.make_aware(datetime.combine(candidate_day, time.min))
        day_end = day_start + timedelta(days=1)
        candidate_overlap = min(candidate_end, day_end) - max(candidate_start, day_start)
        candidate_minutes = int(max(timedelta(), candidate_overlap).total_seconds() // 60)
        planned = _day_planned_minutes(driver.id, candidate_day, exclude_id=exclude_id)
        projected = planned + candidate_minutes
        if projected > limit:
            missing = timedelta(minutes=projected - limit)
            violations.append({
                'type': 'daily_limit',
                'orderNo': None,
                'requiredMinutes': limit,
                'actualMinutes': planned,
                'missingMinutes': int(missing.total_seconds() // 60),
                'message': (
                    f'当日已计划/完成驾驶 {_fmt_minutes(planned)}，加上本单 {_fmt_minutes(candidate_minutes)} '
                    f'将达 {_fmt_minutes(projected)}，超过每日驾驶上限 {_fmt_minutes(limit)}，'
                    f'还需压减 {_fmt_minutes(missing)}'
                ),
            })

    return violations


def assert_assignable(driver, candidate_start, candidate_end, exclude_id=None):
    """建单/发车节点调用：有冲突直接抛 ComplianceViolation，调度单不进入执行。"""
    violations = evaluate_driver(driver, candidate_start, candidate_end, exclude_id=exclude_id)
    if violations:
        raise ComplianceViolation(violations)


def next_available_time(driver, now=None):
    """最早可接单时刻：与每段任务之间必须留足任务间最短休息；
    若休息段覆盖夜间，则须满足夜间连续休息。已结束任务的休息若已休满则不再前推。"""
    now = now or local_now()
    min_rest = timedelta(minutes=driver.min_rest_minutes)
    night_rest = timedelta(minutes=driver.nightly_rest_minutes)
    candidate = now
    for _order, start, end in _windows(_driver_orders(driver.id)):
        required = night_rest if _gap_covers_night(end, end + min_rest) else min_rest
        # 历史任务的休息截止点可能已过（与 now 取大）；未来/在途任务须等结束后休满
        candidate = max(candidate, end + required)
    return candidate


def schedule_summary(driver, now=None):
    """司机页/选人面板所需的合规摘要：今日累计、下次可接单、未来占用。"""
    now = now or local_now()
    used_today = _today_used_minutes(driver.id, now.date(), now)
    planned_today = _day_planned_minutes(driver.id, now.date())
    next_at = next_available_time(driver, now=now)

    upcoming = []
    for order, start, end in _windows(_driver_orders(driver.id)):
        status = getattr(order, 'status', None) or order.get('status')
        # 未完成的单（含晚点未发的 Assigned）都属于未来/当前占用
        if status in ('Completed', 'Cancelled'):
            continue
        upcoming.append({
            'orderNo': _order_no(order),
            'origin': getattr(order, 'origin', None) or (order.get('origin') if isinstance(order, dict) else ''),
            'destination': getattr(order, 'destination', None) or (order.get('destination') if isinstance(order, dict) else ''),
            'status': status,
            'startAt': timezone.localtime(start).strftime('%Y-%m-%d %H:%M'),
            'endAt': timezone.localtime(end).strftime('%Y-%m-%d %H:%M'),
        })
    upcoming.sort(key=lambda item: item['startAt'])

    return {
        'todayMinutes': used_today,
        'todayPlannedMinutes': planned_today,
        'todayLimitMinutes': driver.daily_driving_limit_minutes,
        'nextAvailableAt': timezone.localtime(next_at).strftime('%Y-%m-%d %H:%M'),
        'nextAvailable': next_at <= now,
        'upcoming': upcoming,
    }


def assignment_check(driver, plan_start, plan_end, exclude_id=None):
    """选人时的预检结果（不抛异常），供调度页展示能否指派及原因。"""
    start = parse_dt(plan_start) or local_now()
    end = parse_dt(plan_end) or (start + timedelta(hours=1))
    violations = evaluate_driver(driver, start, end, exclude_id=exclude_id)
    return {
        'assignable': not violations,
        'violations': violations,
        'summary': schedule_summary(driver),
    }
