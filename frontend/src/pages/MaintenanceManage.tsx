import { useEffect, useState } from 'react';
import { Card } from 'antd';
import { maintenanceApi } from '../api/maintenance';
import type { MaintenanceRecord } from '../types';
import { CalendarCell } from '../components/common/CalendarCell';
import { StatusBadge } from '../components/common/StatusBadge';
import { PageShell } from './PageShell';
export function MaintenanceManage() {
  const [records, setRecords] = useState<MaintenanceRecord[]>([]);
  useEffect(() => { maintenanceApi.list<MaintenanceRecord>().then(setRecords).catch(() => setRecords([])); }, []);
  return <PageShell title="维保管理"><div className="grid grid-3">{records.map((record) => <CalendarCell key={record.id} date={record.date} title={record.vendor} />)}</div><Card style={{ marginTop: 16 }}>{records.map((record) => <p key={record.id}>{record.items.join('、')} <StatusBadge status={record.status} /></p>)}</Card></PageShell>;
}
