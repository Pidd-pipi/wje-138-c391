import { request } from '../utils/request';
import { apiPaths } from '../constants/apiPaths';
import type { AssignmentEligibility, Driver } from '../types';

export type ComplianceSettingsPayload = {
  dailyDriveLimitMinutes?: number;
  minRestMinutes?: number;
  nightRestMinutes?: number;
};

export const driverApi = {
  list: (withSchedule = false) =>
    request<Driver[]>(`${apiPaths.drivers}?withSchedule=${withSchedule ? 1 : 0}`),
  get: (id: number) => request<Driver>(apiPaths.driverDetail(id)),
  updateCompliance: (id: number, payload: ComplianceSettingsPayload) =>
    request<Driver>(apiPaths.driverDetail(id), {
      method: 'PATCH',
      body: JSON.stringify(payload),
    }),
};

/** 选人时的合规预检：返回能否指派及原因 */
export function precheckAssignment(params: {
  driverId: number;
  planDepartAt: string;
  planArriveAt: string;
}): Promise<AssignmentEligibility> {
  return request<AssignmentEligibility>(apiPaths.dispatchPrecheck, {
    method: 'POST',
    body: JSON.stringify(params),
  });
}
