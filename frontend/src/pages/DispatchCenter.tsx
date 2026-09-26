import { useEffect, useState } from 'react';
import { Button, Card, Select, Table } from 'antd';
import { dispatchApi } from '../api/dispatch';
import type { DispatchOrder } from '../types';
import { StatusBadge } from '../components/common/StatusBadge';
import { Timeline } from '../components/common/Timeline';
import { PageShell } from './PageShell';

export function DispatchCenter() {
  const [orders, setOrders] = useState<DispatchOrder[]>([]);
  useEffect(() => { dispatchApi.list().then(setOrders).catch(() => setOrders([])); }, []);
  return <PageShell title="调度中心">
    <div className="grid grid-2">
      <Card title="调度单"><Select defaultValue="all" options={[{ value: 'all', label: '全部状态' }]} /><Button type="primary" style={{ marginLeft: 12 }}>创建调度单</Button><Table rowKey="id" dataSource={orders} columns={[{ title: '单号', dataIndex: 'orderNo' }, { title: '路线', render: (_, r) => `${r.origin} → ${r.destination}` }, { title: '状态', render: (_, r) => <StatusBadge status={r.status} /> }]} pagination={false} /></Card>
      <Card title="运输时间线"><Timeline items={['创建调度单', '指派车辆与司机', '开始运输', '完成运输']} /></Card>
    </div>
  </PageShell>;
}
