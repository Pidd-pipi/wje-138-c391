import { request } from '../utils/request';
import { apiPaths } from '../constants/apiPaths';
import type { DispatchCreatePayload, DispatchOrder } from '../types';

export const dispatchApi = {
  list: () => request<DispatchOrder[]>(apiPaths.dispatch),
  create: (payload: DispatchCreatePayload) =>
    request<DispatchOrder>(apiPaths.dispatch, { method: 'POST', body: JSON.stringify(payload) }),
  assign: (id: number, driverId: number) =>
    request<DispatchOrder>(apiPaths.dispatchAssign(id), {
      method: 'POST',
      body: JSON.stringify({ driverId })
    }),
  start: (id: number) =>
    request<DispatchOrder>(apiPaths.dispatchStart(id), { method: 'POST', body: JSON.stringify({}) })
};
