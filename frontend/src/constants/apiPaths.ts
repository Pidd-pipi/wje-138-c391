export const apiPaths = {
  vehicles: '/api/vehicles/',
  drivers: '/api/drivers/',
  driverDetail: (id: number) => `/api/drivers/${id}/`,
  dispatch: '/api/dispatch-orders/',
  dispatchStart: (id: number) => `/api/dispatch-orders/${id}/start/`,
  dispatchPrecheck: '/api/dispatch-orders/precheck/',
  maintenance: '/api/maintenance-records/',
  fuel: '/api/fuel-records/'
} as const;
