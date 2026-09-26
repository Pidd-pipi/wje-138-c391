import { Navigate, createBrowserRouter } from 'react-router-dom';
import { DispatchCenter } from '../pages/DispatchCenter';
import { VehicleManage } from '../pages/VehicleManage';
import { DriverManage } from '../pages/DriverManage';
import { MaintenanceManage } from '../pages/MaintenanceManage';
import { FuelAnalytics } from '../pages/FuelAnalytics';

export const router = createBrowserRouter([
  { path: '/', element: <Navigate to="/dispatch" replace /> },
  { path: '/dispatch', element: <DispatchCenter /> },
  { path: '/vehicles', element: <VehicleManage /> },
  { path: '/drivers', element: <DriverManage /> },
  { path: '/maintenance', element: <MaintenanceManage /> },
  { path: '/fuel-analytics', element: <FuelAnalytics /> }
]);
