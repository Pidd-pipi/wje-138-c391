import { request } from '../utils/request';
import { apiPaths } from '../constants/apiPaths';
export const vehicleApi = {
  list: <T>() => request<T[]>(apiPaths.vehicles)
};
