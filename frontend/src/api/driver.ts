import { request } from '../utils/request';
import { apiPaths } from '../constants/apiPaths';
export const driverApi = {
  list: <T>() => request<T[]>(apiPaths.drivers)
};
