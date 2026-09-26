import { DriverStatus } from './enums';

/** 班次合规冲突类型：当日上限 / 任务间最短休息 / 夜间连续休息 / 时间重叠 */
export type ComplianceViolationType =
  | 'daily_limit'
  | 'min_rest'
  | 'nightly_rest'
  | 'overlap';

export interface ComplianceViolation {
  type: ComplianceViolationType;
  /** 冲突涉及的调度单号（当日上限类冲突可为空） */
  orderNo: string | null;
  requiredMinutes: number;
  actualMinutes: number;
  /** 还缺多少时间（分钟） */
  missingMinutes: number;
  message: string;
}

/** 司机未来占用（未完成的调度单） */
export interface UpcomingOrder {
  orderNo: string;
  origin: string;
  destination: string;
  status: string;
  startAt: string;
  endAt: string;
}

/** 司机页/选人面板所需的班次合规摘要 */
export interface DriverComplianceSummary {
  /** 今日实际累计驾驶（分钟） */
  todayMinutes: number;
  /** 今日已计划+完成驾驶（分钟） */
  todayPlannedMinutes: number;
  /** 每日驾驶上限（分钟） */
  todayLimitMinutes: number;
  /** 下次可接单时间（YYYY-MM-DD HH:mm） */
  nextAvailableAt: string;
  /** 当前是否可立即接单 */
  nextAvailable: boolean;
  upcoming: UpcomingOrder[];
}

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
  /** 每日驾驶上限（分钟） */
  dailyDrivingLimitMinutes: number;
  /** 任务间最短休息（分钟） */
  minRestMinutes: number;
  /** 夜间连续休息（分钟） */
  nightlyRestMinutes: number;
  compliance?: DriverComplianceSummary;
};

/** 选人时的实时预检结果 */
export interface AssignmentCheck {
  assignable: boolean;
  violations: ComplianceViolation[];
  summary: DriverComplianceSummary;
}
