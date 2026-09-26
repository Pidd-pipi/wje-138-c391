export const apiPaths = {
  vehicles: '/api/vehicles/',
  drivers: '/api/drivers/',
  driverDetail: (id: number) => `/api/drivers/${id}/`,
  driverAssignmentCheck: (id: number) => `/api/drivers/${id}/assignment-check/`,
  dispatch: '/api/dispatch-orders/',
  dispatchAssign: (id: number) => `/api/dispatch-orders/${id}/assign/`,
  dispatchStart: (id: number) => `/api/dispatch-orders/${id}/start/`,
  maintenance: '/api/maintenance-records/',
  fuel: '/api/fuel-records/'
} as const;
