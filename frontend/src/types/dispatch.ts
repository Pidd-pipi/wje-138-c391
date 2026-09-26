import { DispatchStatus } from './enums';
import type { ComplianceViolation } from './driver';

export type DispatchOrder = {
  id: number;
  orderNo: string;
  vehicleId: number | null;
  driverId: number | null;
  origin: string;
  destination: string;
  planDepartAt: string | null;
  planArriveAt: string | null;
  actualDepartAt?: string | null;
  actualArriveAt?: string | null;
  cargo: string;
  weight: number;
  freight: number;
  status: DispatchStatus;
  creatorId: number;
  note?: string;
  /** 按单据计划时间复检的合规结果（列表用于标识能否发车及原因） */
  compliance?: {
    assignable: boolean;
    violations: ComplianceViolation[];
  };
};

/** 建单入参 */
export type DispatchCreatePayload = {
  vehicleId?: number | null;
  driverId?: number | null;
  origin: string;
  destination: string;
  planDepartAt: string;
  planArriveAt: string;
  cargo?: string;
  weight?: number;
  freight?: number;
  note?: string;
};
