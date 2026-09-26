import { request } from '../utils/request';
import { apiPaths } from '../constants/apiPaths';
import type { FuelRecord } from '../types';
export const fuelApi = { list: () => request<FuelRecord[]>(apiPaths.fuel) };
