import { Card } from 'antd';
import type { Vehicle } from '../../types';
import { StatusBadge } from './StatusBadge';
export function VehicleCard({ vehicle }: { vehicle: Vehicle }) {
  return <Card size="small" title={vehicle.plateNo} extra={<StatusBadge status={vehicle.status} />}><p>{vehicle.brandModel}</p><p>{vehicle.mileage.toLocaleString()} km</p></Card>;
}
