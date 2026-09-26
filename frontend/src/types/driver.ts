import { DriverStatus } from './enums';

export type Driver = {
  id: number;
  name: string;
  phone: string;
  licenseType: 'C1' | 'B2' | 'A2' | 'A1';
  licenseExpireDate: string;
  hireDate: string;
  status: DriverStatus;
  drivingHours: number;
  violationCount: number;
  /** 每日驾驶上限（分钟，0 表示不限制） */
  dailyDriveLimitMinutes: number;
  /** 相邻任务最短休息（分钟） */
  minRestMinutes: number;
  /** 夜间最短连续休息（分钟，22:00-次日06:00） */
  nightRestMinutes: number;
  schedule?: DriverScheduleOverview;
};

export type UpcomingOccupancy = {
  orderNo: string;
  origin: string;
  destination: string;
  start: string;
  end: string;
  status: string;
};

export type DriverScheduleOverview = {
  todayUsedMinutes: number;
  dailyLimitMinutes: number | null;
  todayRemainingMinutes: number | null;
  nextAvailableAt: string;
  upcoming: UpcomingOccupancy[];
};

export type ComplianceRule =
  | 'daily_limit'
  | 'min_rest'
  | 'night_rest'
  | 'overlap'
  | 'driver_status'
  | 'invalid_time';

export type ComplianceViolation = {
  rule: ComplianceRule;
  kind?: string;
  message: string;
  relatedOrderNo?: string | null;
  relatedOrderNos?: string[];
  shortageMinutes?: number;
  requiredMinutes?: number;
  actualMinutes?: number;
  blockedUntil?: string | null;
  day?: string;
};

export type AssignmentEligibility = {
  eligible: boolean;
  reasons: string[];
  violations: ComplianceViolation[];
  blockedUntil: string | null;
};
