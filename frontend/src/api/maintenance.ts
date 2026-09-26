import { request } from '../utils/request';
import { apiPaths } from '../constants/apiPaths';
export const maintenanceApi = {
  list: <T>() => request<T[]>(apiPaths.maintenance)
};
