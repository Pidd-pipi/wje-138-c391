import { useEffect, useState } from 'react';
import { Card, List } from 'antd';
import { driverApi } from '../api/driver';
import type { Driver } from '../types';
import { UserAvatar } from '../components/common/UserAvatar';
import { StatusBadge } from '../components/common/StatusBadge';
import { PageShell } from './PageShell';
export function DriverManage() {
  const [drivers, setDrivers] = useState<Driver[]>([]);
  useEffect(() => { driverApi.list<Driver>().then(setDrivers).catch(() => setDrivers([])); }, []);
  return <PageShell title="司机管理"><Card><List dataSource={drivers} renderItem={(driver) => <List.Item actions={[<StatusBadge status={driver.status} key="s" />]}><List.Item.Meta avatar={<UserAvatar name={driver.name} />} title={driver.name} description={driver.phone} /></List.Item>} /></Card></PageShell>;
}
