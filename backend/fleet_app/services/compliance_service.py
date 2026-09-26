"""司机班次合规预检引擎。

规则（均可在司机档案中配置，0 表示不启用对应限制）：
1. 每日驾驶上限：按当地日历日统计，已完成/进行中的任务按实际时间，
   已排未执行的计划按计划时间；
2. 任务间最短休息：新任务与相邻任务（前序结束→新开始、新结束→后序开始）
   的空档必须不少于 min_rest_minutes，时间重叠直接冲突；
3. 夜间连续休息：每日 22:00 至次日 06:00 为夜间休息窗口，被任务空档跨过的
   夜间窗口必须在窗内留足 night_rest_minutes；完整跑满整窗（通宵）直接违规。

所有函数为纯计算，时间以 USE_TZ 的 aware datetime 传入、按 TIME_ZONE
（Asia/Shanghai）折算到当地日历日。
"""
from datetime import datetime, timedelta, time
from django.utils import timezone

# 参与当日累计/排班核对的调度单状态
SCHEDULED_STATUSES = ('Assigned', 'InProgress')
FINISHED_STATUSES = ('Completed',)
ACTIVE_STATUSES = ('Pending', 'Assigned', 'InProgress')

NIGHT_START = time(22, 0)   # 夜间休息窗口开始
NIGHT_END = time(6, 0)      # 夜间休息窗口结束（次日）

CANCELLED_STATUS = 'Cancelled'


def local_dt(value):
    if value is None:
        return None
    if isinstance(value, str):
        value = parse_dt(value)
    if not timezone.is_aware(value):
        value = timezone.make_aware(value)
    return timezone.localtime(value)


def parse_dt(value):
    """兼容 'YYYY-MM-DDTHH:MM' 与 'YYYY-MM-DD HH:MM'（分钟/秒均可）。"""
    if value is None or isinstance(value, datetime):
        return value
    if isinstance(value, str):
        text = value.strip().replace('T', ' ', 1) if 'T' in value else value.strip()
        try:
            return datetime.fromisoformat(value.strip().replace(' ', 'T', 1))
        except ValueError:
            pass
        for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        raise ValueError(f'无法解析时间: {value!r}')
    raise ValueError(f'无法解析时间: {value!r}')


def task_span(task, now=None):
    """提取任务实际占用（完成记录）或计划占用区间。"""
    now = now or timezone.localtime()

    def pick(snake, camel):
        value = task.get(snake)
        if value is None:
            value = task.get(camel)
        return value

    status = task.get('status')
    actual_s = pick('actual_depart_at', 'actualDepartAt')
    actual_e = pick('actual_arrive_at', 'actualArriveAt')
    plan_s = pick('plan_depart_at', 'planDepartAt')
    plan_e = pick('plan_arrive_at', 'planArriveAt')
    if status in FINISHED_STATUSES:
        start, end = actual_s or plan_s, actual_e or plan_e
    elif status == 'InProgress':
        start, end = actual_s or plan_s, actual_e or plan_e or now
    else:
        start, end = plan_s, plan_e
    return local_dt(parse_dt(start)), local_dt(parse_dt(end))


def _order_no(task):
    return task.get('order_no') or task.get('orderNo') or f"#{task.get('id')}"


def _iter_days(day, end_day):
    while day <= end_day:
        yield day
        day += timedelta(days=1)


def _day_bounds(day, tzref):
    """当地日历日 [00:00, 次日00:00) 的 aware 边界。"""
    start = timezone.make_aware(datetime.combine(day, time.min))
    return start, start + timedelta(days=1)


def _local_dt_at(day, hour_minute):
    return timezone.make_aware(datetime.combine(day, hour_minute))


def _overlap_minutes(start, end, win_start, win_end):
    lo, hi = max(start, win_start), min(end, win_end)
    return max(0.0, (hi - lo).total_seconds() / 60.0)


def _night_windows_between(start, end, limit=4):
    """返回与 [start, end] 有交集的夜间窗口，按开始时间排序。"""
    windows = []
    first_evening = _local_dt_at(start.date(), NIGHT_START)
    candidate = first_evening - timedelta(days=1)
    while candidate < end and len(windows) < limit + 2:
        win_start = candidate
        win_end = _local_dt_at((candidate + timedelta(days=1)).date(), NIGHT_END)
        if win_end > start and win_start < end:
            windows.append((win_start, win_end))
        candidate += timedelta(days=1)
    return windows


def _format_minutes(minutes):
    minutes = int(round(minutes))
    if minutes <= 0:
        return '0分钟'
    hours, minute = divmod(minutes, 60)
    if hours and minute:
        return f'{hours}小时{minute}分钟'
    if hours:
        return f'{hours}小时'
    return f'{minute}分钟'


def _fmt_dt(value):
    return local_dt(value).strftime('%m-%d %H:%M')


# ---------------------------------------------------------------- 每日累计

def daily_used_minutes(tasks, day, now=None):
    """某一当地日历日已占用的驾驶分钟数（完成记录 + 进行中 + 已计划）。"""
    day_start, day_end = _day_bounds(day, None)
    total = 0.0
    for task in tasks:
        start, end = task_span(task, now)
        if not start or not end or end <= start:
            continue
        total += _overlap_minutes(start, end, day_start, day_end)
    return total


def _check_daily_limit(tasks, new_start, new_end, limit):
    violations = []
    if limit <= 0:
        return violations
    for day in _iter_days(new_start.date(), new_end.date()):
        used = daily_used_minutes(tasks, day)
        day_start, day_end = _day_bounds(day, new_start)
        adding = _overlap_minutes(new_start, new_end, day_start, day_end)
        if used + adding > limit + 1e-6:
            day_orders = [
                _order_no(t) for t in tasks
                if task_span(t)[0] and _overlap_minutes(*task_span(t), day_start, day_end) > 0
            ]
            violations.append({
                'rule': 'daily_limit',
                'message': (
                    f"{day.strftime('%Y-%m-%d')} 当日累计驾驶将达 {_format_minutes(used + adding)}，"
                    f'超过档案上限 {_format_minutes(limit)}，已超 {_format_minutes(used + adding - limit)}'
                    + (f'；涉及单号 {", ".join(day_orders)}' if day_orders else '')
                ),
                'day': day.strftime('%Y-%m-%d'),
                'usedMinutes': int(round(used)),
                'limitMinutes': limit,
                'projectedMinutes': int(round(used + adding)),
                'shortageMinutes': int(round(used + adding - limit)),
                'relatedOrderNos': day_orders,
                'blockedUntil': None,
            })
    return violations


# ---------------------------------------------------- 相邻任务间隔/夜间休息

def _adjacent_tasks(tasks, new_start, new_end):
    """返回 (前驱任务, 后继任务)：结束/开始时间最贴近新任务的两张单。"""
    predecessor = successor = None
    for task in tasks:
        start, end = task_span(task)
        if not start or not end or end <= start:
            continue
        if end <= new_start:
            if predecessor is None or end > task_span(predecessor)[1]:
                predecessor = task
        elif start >= new_end:
            if successor is None or start < task_span(successor)[0]:
                successor = task
        else:
            # 与新任务重叠的单交由 _check_overlap 处理
            continue
    return predecessor, successor


def _check_overlap(tasks, new_start, new_end):
    violations = []
    for task in tasks:
        start, end = task_span(task)
        if not start or not end or end <= start:
            continue
        if start < new_end and end > new_start:
            overlap = min(end, new_end) - max(start, new_start)
            minutes = max(0.0, overlap.total_seconds() / 60.0)
            violations.append({
                'rule': 'overlap',
                'message': f'与单号 {_order_no(task)}（{_fmt_dt(start)}~{_fmt_dt(end)}）任务时间重叠'
                           + (f'，重叠 {_format_minutes(minutes)}，该时段无法同时执行' if minutes else '，该时段无法同时执行'),
                'relatedOrderNo': _order_no(task),
                'conflictStart': _fmt_dt(start),
                'conflictEnd': _fmt_dt(end),
                'shortageMinutes': int(round(minutes)),
                'blockedUntil': end.isoformat(),
            })
    return violations


def _gap_violation(kind, task, required, actual, **points):
    shortage = max(0.0, required - actual)
    order_no = _order_no(task)
    if kind == 'predecessor':
        prev_end = points['prev_end']
        message = (
            f'与单号 {order_no}（{_fmt_dt(prev_end)} 结束）之间仅休息 '
            f'{_format_minutes(actual)}，少于档案规定的最短休息 {_format_minutes(required)}，'
            f'还缺 {_format_minutes(shortage)}'
        )
        blocked_until = (prev_end + timedelta(minutes=required)).isoformat()
    else:
        next_start = points['next_start']
        message = (
            f'与单号 {order_no}（{_fmt_dt(next_start)} 开始）之间仅休息 '
            f'{_format_minutes(actual)}，少于档案规定的最短休息 {_format_minutes(required)}，'
            f'还缺 {_format_minutes(shortage)}'
        )
        blocked_until = None
    return {
        'rule': 'min_rest',
        'kind': kind,
        'message': message,
        'relatedOrderNo': order_no,
        'requiredMinutes': int(required),
        'actualMinutes': int(round(actual)),
        'shortageMinutes': int(round(shortage)),
        'blockedUntil': blocked_until,
    }


def _check_rest_gaps(predecessor, successor, new_start, new_end, min_rest):
    violations = []
    if min_rest <= 0:
        return violations
    if predecessor:
        _, prev_end = task_span(predecessor)
        gap = (new_start - prev_end).total_seconds() / 60.0
        if gap + 1e-6 < min_rest:
            violations.append(_gap_violation('predecessor', predecessor,
                                             min_rest, gap, prev_end=prev_end))
    if successor:
        next_start, _ = task_span(successor)
        gap = (next_start - new_end).total_seconds() / 60.0
        if gap + 1e-6 < min_rest:
            violations.append(_gap_violation('successor', successor,
                                             min_rest, gap, next_start=next_start))
    return violations


def _night_violation(kind, task, win_start, win_end, rest_in_window,
                     required, gap_start, gap_end, blocked_until=None):
    shortage = max(0.0, required - rest_in_window)
    if kind == 'predecessor':
        msg = (f'与单号 {_order_no(task)}（{_fmt_dt(gap_start)} 结束）之间跨过夜间休息窗口'
               f'（{_fmt_dt(win_start)}~{_fmt_dt(win_end)}），窗内仅能休息 '
               f'{_format_minutes(rest_in_window)}，不足夜间连续休息 {_format_minutes(required)}，'
               f'还缺 {_format_minutes(shortage)}')
    elif kind == 'successor':
        msg = (f'与单号 {_order_no(task)}（{_fmt_dt(gap_end)} 开始）之间跨过夜间休息窗口'
               f'（{_fmt_dt(win_start)}~{_fmt_dt(win_end)}），窗内仅能休息 '
               f'{_format_minutes(rest_in_window)}，不足夜间连续休息 {_format_minutes(required)}，'
               f'还缺 {_format_minutes(shortage)}')
    else:
        msg = (f'任务跑满夜间休息窗口（{_fmt_dt(win_start)}~{_fmt_dt(win_end)}），'
               f'未保证夜间连续休息 {_format_minutes(required)}，'
               f'还缺 {_format_minutes(required - rest_in_window)}')
    return {
        'rule': 'night_rest',
        'kind': kind,
        'message': msg,
        'relatedOrderNo': _order_no(task) if task else None,
        'windowStart': _fmt_dt(win_start),
        'windowEnd': _fmt_dt(win_end),
        'requiredMinutes': int(required),
        'restMinutes': int(round(rest_in_window)),
        'shortageMinutes': int(round(shortage)),
        'blockedUntil': blocked_until.isoformat() if blocked_until else None,
    }


def _check_night_rest(tasks, predecessor, successor,
                      new_start, new_end, night_rest):
    violations = []
    if night_rest <= 0:
        return violations

    # 1) 新任务自身完整覆盖某个夜间窗口（通宵）→ 无任何窗内休息
    for win_start, win_end in _night_windows_between(new_start, new_end):
        if new_start <= win_start and new_end >= win_end:
            violations.append(_night_violation('full_window', None,
                                               win_start, win_end, 0,
                                               night_rest, new_start, new_end))

    # 2) 与前序任务的空档跨过夜间窗口：空档中需出现过一个完整夜间休息窗
    if predecessor:
        _, prev_end = task_span(predecessor)
        windows = _night_windows_between(prev_end, new_start)
        best = None
        for win_start, win_end in windows:
            rest = max(0.0, (min(new_start, win_end) - max(prev_end, win_start)).total_seconds() / 60.0)
            if rest + 1e-6 >= night_rest:
                best = None
                break
            best = (win_start, win_end, rest)
        if best is not None:
            win_start, win_end, rest = best
            blocked_until = earliest_after(
                prev_end, min_rest=0, night_rest=night_rest, max_iterations=6)
            violations.append(_night_violation(
                'predecessor', predecessor, win_start, win_end, rest,
                night_rest, prev_end, new_start, blocked_until))

    # 3) 与后继任务的空档跨过夜间窗口：空档中需出现过一个完整夜间休息窗
    if successor:
        next_start, _ = task_span(successor)
        windows = _night_windows_between(new_end, next_start)
        best = None
        for win_start, win_end in windows:
            rest = max(0.0, (min(next_start, win_end) - max(new_end, win_start)).total_seconds() / 60.0)
            if rest + 1e-6 >= night_rest:
                best = None
                break
            best = (win_start, win_end, rest)
        if best is not None:
            win_start, win_end, rest = best
            violations.append(_night_violation(
                'successor', successor, win_start, win_end, rest,
                night_rest, new_end, next_start))
    return violations


# ------------------------------------------------------- 下次可接单时间

def earliest_after(last_end, min_rest, night_rest, max_iterations=8):
    """从 last_end 起，满足「总空档 ≥ min_rest 且每个跨过的夜间窗口内
    休息 ≥ night_rest」的最早可开始时刻。"""
    candidate = last_end + timedelta(minutes=min_rest or 0)
    checked_until = last_end
    for _ in range(max_iterations):
        windows = [w for w in _night_windows_between(last_end, candidate)
                   if w[1] > checked_until]
        if not windows:
            return candidate
        win_start, win_end = windows[0]
        rest_in_window = max(
            0.0, (min(candidate, win_end) - win_start).total_seconds() / 60.0)
        if night_rest and candidate < win_end and rest_in_window + 1e-6 < night_rest:
            candidate = win_end
        checked_until = win_end
    return candidate


# ------------------------------------------------------------- 对外入口

def evaluate(driver, tasks, start, end, now=None, exclude_order_id=None,
             ignore_status=False):
    """对一张拟安排的任务做合规预检，返回违规明细列表（空列表=可指派）。"""
    now = now or timezone.localtime()
    start = local_dt(parse_dt(start))
    end = local_dt(parse_dt(end))
    if timezone.is_naive(start):
        start = timezone.make_aware(start)
    if timezone.is_naive(end):
        end = timezone.make_aware(end)

    violations = []
    if not ignore_status:
        status = driver.get('status') if isinstance(driver, dict) else driver.status
        if status in ('Leave', 'Suspended'):
            violations.append({
                'rule': 'driver_status',
                'message': f'司机当前状态为 {status}，不可指派任务',
                'blockedUntil': None,
                'relatedOrderNos': [],
            })
    if not start or not end or end <= start:
        violations.append({
            'rule': 'invalid_time',
            'message': '任务时间无效：预计到达时间必须晚于出发时间',
            'blockedUntil': None,
            'relatedOrderNos': [],
        })
        return violations

    relevant = []
    for task in tasks:
        if exclude_order_id is not None and task.get('id') == exclude_order_id:
            continue
        if task.get('status') == CANCELLED_STATUS:
            continue
        if task_span(task, now)[0] is not None:
            relevant.append(task)

    cfg = driver if isinstance(driver, dict) else {
        'daily_drive_limit_minutes': driver.daily_drive_limit_minutes,
        'min_rest_minutes': driver.min_rest_minutes,
        'night_rest_minutes': driver.night_rest_minutes,
        'status': driver.status,
    }

    overlap = _check_overlap(relevant, start, end)
    violations.extend(overlap)
    # 时间已重叠时不再重复计算间隔/夜间休息
    if not overlap:
        predecessor, successor = _adjacent_tasks(relevant, start, end)
        violations.extend(_check_daily_limit(
            relevant, start, end, cfg.get('daily_drive_limit_minutes') or 0))
        violations.extend(_check_rest_gaps(
            predecessor, successor, start, end,
            cfg.get('min_rest_minutes') or 0))
        violations.extend(_check_night_rest(
            relevant, predecessor, successor, start, end,
            cfg.get('night_rest_minutes') or 0))
    return violations


def eligibility(driver, tasks, start, end, now=None, exclude_order_id=None):
    """选人时使用的完整指派结论。"""
    now = now or timezone.localtime()
    violations = evaluate(driver, tasks, start, end, now=now,
                          exclude_order_id=exclude_order_id)
    blocked_until_candidates = [
        timezone.datetime.fromisoformat(v['blockedUntil'])
        for v in violations if v.get('blockedUntil')
    ]
    return {
        'eligible': len(violations) == 0,
        'reasons': [v['message'] for v in violations],
        'violations': violations,
        'blockedUntil': max(blocked_until_candidates).isoformat()
        if blocked_until_candidates else None,
    }


def _next_available_time(cfg, tasks, now):
    """最早可开始一个新任务的时刻：从 now 起做零时长探针预检，
    命中冲突就按「放行时间 / 冲突任务结束 + 休息 / 夜间窗结束」推进。"""
    min_rest = cfg.get('min_rest_minutes') or 0
    night_rest = cfg.get('night_rest_minutes') or 0
    candidate = now

    for _ in range(16):
        violations = evaluate(cfg, tasks, candidate, candidate + timedelta(minutes=1),
                              now=now, ignore_status=True)
        if not violations:
            return candidate

        advanced = candidate
        for v in violations:
            if v.get('blockedUntil'):
                advanced = max(advanced, local_dt(parse_dt(v['blockedUntil'])))
            order_no = v.get('relatedOrderNo')
            if order_no:
                task = next((t for t in tasks if _order_no(t) == order_no), None)
                if task:
                    _, end = task_span(task, now)
                    if end and end > candidate:
                        advanced = max(advanced, earliest_after(end, min_rest, night_rest))
        if advanced <= candidate:
            # 兜底：按最短休息推进，避免死循环
            advanced = candidate + timedelta(minutes=max(min_rest, 1))
        candidate = advanced
    return candidate


def schedule_overview(driver, tasks, now=None):
    """司机页：今日累计 / 下次可接单时间 / 未来占用。"""
    now = now or timezone.localtime()
    day = now.date()
    used_today = daily_used_minutes(tasks, day, now=now)

    active = [t for t in tasks if t.get('status') in ACTIVE_STATUSES
              and t.get('status') != CANCELLED_STATUS]

    cfg = driver if isinstance(driver, dict) else {
        'daily_drive_limit_minutes': driver.daily_drive_limit_minutes,
        'min_rest_minutes': driver.min_rest_minutes,
        'night_rest_minutes': driver.night_rest_minutes,
        'status': driver.status,
    }
    next_available = _next_available_time(cfg, tasks, now)

    upcoming = []
    for task in sorted(active, key=lambda t: task_span(t, now)[0] or now):
        s, e = task_span(task, now)
        if s and e >= now:
            upcoming.append({
                'orderNo': _order_no(task),
                'origin': task.get('origin'),
                'destination': task.get('destination'),
                'start': s.isoformat(),
                'end': e.isoformat(),
                'status': task.get('status'),
            })

    limit = driver.get('daily_drive_limit_minutes') if isinstance(driver, dict) else driver.daily_drive_limit_minutes
    return {
        'todayUsedMinutes': int(round(used_today)),
        'dailyLimitMinutes': limit or None,
        'todayRemainingMinutes': (int(round(limit - used_today)) if limit else None),
        'nextAvailableAt': next_available.isoformat(),
        'upcoming': upcoming[:10],
    }
