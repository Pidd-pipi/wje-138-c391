import { useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { Card, Statistic } from 'antd';
import { fuelApi } from '../api/fuel';
import type { FuelRecord } from '../types';
import { PageShell } from './PageShell';
export function FuelAnalytics() {
  const [records, setRecords] = useState<FuelRecord[]>([]);
  useEffect(() => { fuelApi.list().then(setRecords).catch(() => setRecords([])); }, []);
  return <PageShell title="油耗分析"><div className="grid grid-2"><Card><Statistic title="月度总油耗" value={records.reduce((sum, item) => sum + item.liters, 0)} suffix="L" /></Card><Card><ReactECharts style={{ height: 320 }} option={{ xAxis: { type: 'category', data: records.map(r => r.date) }, yAxis: { type: 'value' }, series: [{ type: 'line', data: records.map(r => r.totalAmount), smooth: true }] }} /></Card></div></PageShell>;
}
