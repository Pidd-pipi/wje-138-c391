import { request } from '../utils/request';
import { apiPaths } from '../constants/apiPaths';
import type { AssignmentCheck, Driver } from '../types';

export type DriverCompliancePatch = {
  dailyDrivingLimitMinutes?: number;
  minRestMinutes?: number;
  nightlyRestMinutes?: number;
};

export const driverApi = {
  list: () => request<Driver[]>(apiPaths.drivers),
  updateCompliance: (id: number, payload: DriverCompliancePatch) =>
    request<Driver>(apiPaths.driverDetail(id), {
      method: 'PATCH',
      body: JSON.stringify(payload)
    }),
  assignmentCheck: (
    id: number,
    payload: { planDepartAt: string; planArriveAt: string; excludeOrderId?: number }
  ) =>
    request<AssignmentCheck>(apiPaths.driverAssignmentCheck(id), {
      method: 'POST',
      body: JSON.stringify(payload)
    })
};
