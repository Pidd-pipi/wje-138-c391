import { request } from '../utils/request';
import { apiPaths } from '../constants/apiPaths';
import type { DispatchOrder } from '../types';

export type CreateDispatchPayload = {
  vehicleId?: number;
  driverId?: number;
  origin: string;
  destination: string;
  planDepartAt: string;
  planArriveAt: string;
  cargo?: string;
  weight?: number;
  freight?: number;
  note?: string;
};

export const dispatchApi = {
  list: () => request<DispatchOrder[]>(apiPaths.dispatch),
  create: (payload: CreateDispatchPayload) =>
    request<DispatchOrder>(apiPaths.dispatch, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  start: (id: number) =>
    request<DispatchOrder>(apiPaths.dispatchStart(id), { method: 'POST' }),
};
