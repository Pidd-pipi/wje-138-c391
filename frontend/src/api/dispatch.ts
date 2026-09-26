import { request } from '../utils/request';
import { apiPaths } from '../constants/apiPaths';
import type { DispatchOrder } from '../types';
export const dispatchApi = {
  list: () => request<DispatchOrder[]>(apiPaths.dispatch),
  create: (payload: Partial<DispatchOrder>) => request<DispatchOrder>(apiPaths.dispatch, { method: 'POST', body: JSON.stringify(payload) })
};
