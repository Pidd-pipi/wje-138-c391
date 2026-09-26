import { useEffect, useState } from 'react';
import { Card } from 'antd';
import { vehicleApi } from '../api/vehicle';
import type { Vehicle } from '../types';
import { VehicleCard } from '../components/common/VehicleCard';
import { PageShell } from './PageShell';
export function VehicleManage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  useEffect(() => { vehicleApi.list<Vehicle>().then(setVehicles).catch(() => setVehicles([])); }, []);
  return <PageShell title="车辆管理"><div className="grid grid-3">{vehicles.map((vehicle) => <VehicleCard vehicle={vehicle} key={vehicle.id} />)}</div><Card title="油耗趋势" style={{ marginTop: 16 }}>各车油耗趋势图预留，与油耗分析页使用同一数据。</Card></PageShell>;
}
