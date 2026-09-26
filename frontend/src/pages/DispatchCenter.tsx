import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Button,
  Card,
  Col,
  message,
  notification,
  Popconfirm,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Tooltip,
  Typography
} from 'antd';
import { PlusOutlined, PlayCircleOutlined } from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { dispatchApi } from '../api/dispatch';
import { driverApi } from '../api/driver';
import { vehicleApi } from '../api/vehicle';
import type { DispatchOrder, Driver, Vehicle } from '../types';
import { DispatchStatus } from '../types/enums';
import { StatusBadge } from '../components/common/StatusBadge';
import { Timeline } from '../components/common/Timeline';
import { ComplianceViolationTag } from '../components/common/ComplianceViolations';
import { CreateOrderModal } from '../components/dispatch/CreateOrderModal';
import { useDispatch } from '../hooks/useDispatch';
import { PageShell } from './PageShell';

const STATUS_TABS = [
  { value: 'all', label: '全部状态' },
  { value: DispatchStatus.Pending, label: '待指派' },
  { value: DispatchStatus.Assigned, label: '待发车' },
  { value: DispatchStatus.InProgress, label: '运输中' },
  { value: DispatchStatus.Completed, label: '已完成' },
  { value: DispatchStatus.Cancelled, label: '已取消' }
];

export function DispatchCenter() {
  const [orders, setOrders] = useState<DispatchOrder[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [tab, setTab] = useState('all');
  const [createOpen, setCreateOpen] = useState(false);
  const [startingId, setStartingId] = useState<number | null>(null);
  const { canStart, start } = useDispatch();

  const load = useCallback(() => {
    dispatchApi.list().then(setOrders).catch(() => setOrders([]));
  }, []);
  useEffect(() => {
    load();
    driverApi.list().then(setDrivers).catch(() => setDrivers([]));
    vehicleApi.list<Vehicle>().then(setVehicles).catch(() => setVehicles([]));
  }, [load]);

  const driverName = useCallback(
    (id: number | null) => drivers.find((d) => d.id === id)?.name ?? (id ? `#${id}` : '未指派'),
    [drivers]
  );
  const plate = useCallback(
    (id: number | null) => vehicles.find((v) => v.id === id)?.plateNo ?? (id ? `#${id}` : '未指派'),
    [vehicles]
  );

  const onStart = async (order: DispatchOrder) => {
    setStartingId(order.id);
    const result = await start(order.id);
    setStartingId(null);
    if (result.ok) {
      notification.success({ message: `${order.orderNo} 已发车` });
      load();
    } else {
      notification.error({
        message: `${order.orderNo} 未通过班次合规预检，未发车`,
        duration: 8,
        description: result.violations.length ? (
          <Space direction="vertical" size={4}>
            {result.violations.map((v, i) => (
              <Typography.Text key={i} style={{ color: '#cf1322' }}>
                · {v.message}
              </Typography.Text>
            ))}
          </Space>
        ) : (
          result.message
        )
      });
    }
  };

  const columns: ColumnsType<DispatchOrder> = useMemo(
    () => [
      {
        title: '单号',
        dataIndex: 'orderNo',
        render: (no: string) => <Typography.Text code>{no}</Typography.Text>
      },
      { title: '路线', render: (_, r) => `${r.origin} → ${r.destination}` },
      { title: '车辆', render: (_, r) => plate(r.vehicleId) },
      { title: '司机', render: (_, r) => driverName(r.driverId) },
      {
        title: '计划时间',
        render: (_, r) => (
          <Space direction="vertical" size={0}>
            <span>{r.planDepartAt ?? '-'}</span>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              至 {r.planArriveAt ?? '-'}
            </Typography.Text>
          </Space>
        )
      },
      {
        title: '班次合规预检',
        width: 260,
        render: (_, r) => {
          if (!r.compliance || r.status === DispatchStatus.Completed || r.status === DispatchStatus.Cancelled) {
            return <Tag color="default">—</Tag>;
          }
          if (r.compliance.assignable) {
            return <Tag color="green">预检通过</Tag>;
          }
          return (
            <Space size={4} wrap>
              {r.compliance.violations.map((v, i) => (
                <ComplianceViolationTag key={`${v.type}-${i}`} violation={v} />
              ))}
            </Space>
          );
        }
      },
      {
        title: '状态',
        render: (_, r) => <StatusBadge status={r.status} />
      },
      {
        title: '操作',
        fixed: 'right',
        width: 110,
        render: (_, r) =>
          canStart(r) ? (
            <Popconfirm
              title={`发车 ${r.orderNo}？`}
              description="将再次进行司机班次合规预检，冲突时不会发车。"
              onConfirm={() => onStart(r)}
            >
              <Button
                type="link"
                size="small"
                icon={<PlayCircleOutlined />}
                loading={startingId === r.id}
                danger={!!(r.compliance && !r.compliance.assignable)}
              >
                发车
              </Button>
            </Popconfirm>
          ) : (
            <Tooltip title="当前状态不可发车">
              <Button type="link" size="small" disabled>
                发车
              </Button>
            </Tooltip>
          )
      }
    ],
    [plate, driverName, canStart, startingId]
  );

  const data = tab === 'all' ? orders : orders.filter((o) => o.status === tab);

  return (
    <PageShell title="调度中心">
      <Row gutter={16}>
        <Col xs={24} xl={17}>
          <Card
            title="调度单"
            extra={
              <Space>
                <Select
                  value={tab}
                  onChange={setTab}
                  style={{ width: 130 }}
                  options={STATUS_TABS}
                />
                <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
                  创建调度单
                </Button>
              </Space>
            }
          >
            <Table
              rowKey="id"
              dataSource={data}
              columns={columns}
              size="small"
              scroll={{ x: 1100 }}
              pagination={{ pageSize: 8, showSizeChanger: false }}
            />
          </Card>
        </Col>
        <Col xs={24} xl={7}>
          <Card title="运输时间线">
            <Timeline
              items={[
                '创建调度单',
                '指派车辆与司机（建单合规预检）',
                '发车（再次合规预检）',
                '运输中',
                '完成运输'
              ]}
            />
            <Typography.Paragraph type="secondary" style={{ marginTop: 12, fontSize: 12 }}>
              建单/发车时核对：当日累计驾驶上限、任务间最短休息、夜间连续休息。
              冲突时提示涉及单号与还缺时间，调度单不进入执行。
            </Typography.Paragraph>
          </Card>
        </Col>
      </Row>

      <CreateOrderModal
        open={createOpen}
        drivers={drivers}
        vehicles={vehicles}
        onClose={() => setCreateOpen(false)}
        onCreated={() => {
          setCreateOpen(false);
          message.success('调度单已创建');
          load();
        }}
      />
    </PageShell>
  );
}
