import { useEffect, useMemo, useState } from 'react';
import { Button, Card, Form, Input, InputNumber, Modal, Select, Table, message } from 'antd';
import { dispatchApi, type CreateDispatchPayload } from '../api/dispatch';
import { vehicleApi } from '../api/vehicle';
import type { DispatchOrder, Vehicle } from '../types';
import { DispatchStatus } from '../types/enums';
import { StatusBadge } from '../components/common/StatusBadge';
import { Timeline } from '../components/common/Timeline';
import { ComplianceResult } from '../components/common/ComplianceResult';
import { DriverSelectWithPrecheck } from '../components/common/DriverSelectWithPrecheck';
import { PageShell } from './PageShell';
import { useDispatch, complianceFromError } from '../hooks/useDispatch';
import { formatDateTime } from '../utils/complianceFormat';
import type { AssignmentEligibility } from '../types';

const STATUS_TABS = [
  { value: 'all', label: '全部状态' },
  { value: DispatchStatus.Pending, label: '待指派' },
  { value: DispatchStatus.Assigned, label: '已指派' },
  { value: DispatchStatus.InProgress, label: '运输中' },
  { value: DispatchStatus.Completed, label: '已完成' },
  { value: DispatchStatus.Cancelled, label: '已取消' },
];

type FormValues = {
  vehicleId?: number;
  driverId?: number;
  origin: string;
  destination: string;
  range: [string, string];
  cargo?: string;
  weight?: number;
  freight?: number;
  note?: string;
};

export function DispatchCenter() {
  const [orders, setOrders] = useState<DispatchOrder[]>([]);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [modalOpen, setModalOpen] = useState(false);
  const [eligibility, setEligibility] = useState<AssignmentEligibility | null>(null);
  const [form] = Form.useForm<FormValues>();
  const { createOrder, startOrder, submitting } = useDispatch();

  const reload = () => dispatchApi.list().then(setOrders).catch(() => setOrders([]));
  useEffect(() => {
    reload();
    vehicleApi.list<Vehicle>().then(setVehicles).catch(() => setVehicles([]));
  }, []);

  const range = Form.useWatch('range', form);
  const driverId = Form.useWatch('driverId', form);
  const planDepartAt = range?.[0];
  const planArriveAt = range?.[1];

  const filteredOrders = useMemo(
    () => (statusFilter === 'all' ? orders : orders.filter((o) => o.status === statusFilter)),
    [orders, statusFilter],
  );

  const openModal = () => {
    form.resetFields();
    setEligibility(null);
    setModalOpen(true);
  };

  const handleCreate = async () => {
    const values = await form.validateFields();
    const payload: CreateDispatchPayload = {
      vehicleId: values.vehicleId,
      driverId: values.driverId,
      origin: values.origin,
      destination: values.destination,
      planDepartAt: values.range[0],
      planArriveAt: values.range[1],
      cargo: values.cargo,
      weight: values.weight,
      freight: values.freight,
      note: values.note,
    };
    try {
      await createOrder(payload);
      message.success('调度单已创建');
      setModalOpen(false);
      reload();
    } catch (error) {
      const compliance = complianceFromError(error);
      if (compliance) {
        setEligibility(compliance);
        message.error('班次合规预检不通过，调度单未创建');
      } else {
        message.error(error instanceof Error ? error.message : '创建失败');
      }
    }
  };

  const handleStart = async (order: DispatchOrder) => {
    try {
      await startOrder(order);
      message.success(`单号 ${order.orderNo} 已发车`);
      reload();
    } catch (error) {
      const compliance = complianceFromError(error);
      if (compliance) {
        Modal.error({
          title: `单号 ${order.orderNo} 禁止发车`,
          width: 560,
          content: (
            <ul style={{ paddingLeft: 18, marginBottom: 0 }}>
              {compliance.violations.map((v, i) => <li key={i}>{v.message}</li>)}
            </ul>
          ),
        });
      } else {
        message.error(error instanceof Error ? error.message : '发车失败');
      }
    }
  };

  return (
    <PageShell title="调度中心">
      <div className="grid grid-2">
        <Card
          title="调度单"
          extra={
            <>
              <Select
                value={statusFilter}
                onChange={setStatusFilter}
                style={{ width: 130, marginRight: 12 }}
                options={STATUS_TABS.map((t) => ({ value: t.value, label: t.label }))}
              />
              <Button type="primary" onClick={openModal}>创建调度单</Button>
            </>
          }
        >
          <Table
            rowKey="id"
            dataSource={filteredOrders}
            pagination={false}
            columns={[
              { title: '单号', dataIndex: 'orderNo' },
              { title: '路线', render: (_, r) => `${r.origin} → ${r.destination}` },
              {
                title: '计划时间',
                render: (_, r) => `${formatDateTime(r.planDepartAt)} ~ ${formatDateTime(r.planArriveAt)}`,
              },
              { title: '状态', render: (_, r) => <StatusBadge status={r.status} /> },
              {
                title: '操作',
                render: (_, r) =>
                  r.status === DispatchStatus.Assigned || r.status === DispatchStatus.Pending ? (
                    <Button size="small" type="primary" ghost onClick={() => handleStart(r)}>发车</Button>
                  ) : null,
              },
            ]}
          />
        </Card>
        <Card title="运输时间线">
          <Timeline items={['创建调度单（班次合规预检）', '指派车辆与司机', '发车前二次预检', '开始运输', '完成运输']} />
        </Card>
      </div>

      <Modal
        title="创建调度单"
        open={modalOpen}
        onCancel={() => setModalOpen(false)}
        onOk={handleCreate}
        confirmLoading={submitting}
        okText="创建（自动预检）"
        width={620}
        okButtonProps={{ danger: eligibility?.eligible === false }}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 12 }}>
          <Form.Item label="司机" name="driverId">
            <DriverSelectWrapper
              planDepartAt={planDepartAt}
              planArriveAt={planArriveAt}
              onEligibilityChange={setEligibility}
            />
          </Form.Item>
          <Form.Item
            label="车辆"
            name="vehicleId"
            rules={[{ required: true, message: '请选择车辆' }]}
          >
            <Select
              placeholder="选择车辆"
              showSearch
              optionFilterProp="label"
              options={vehicles.map((v) => ({ value: v.id, label: `${v.plateNo} ${v.brandModel}` }))}
            />
          </Form.Item>
          <div style={{ display: 'flex', gap: 12 }}>
            <Form.Item
              label="出发地"
              name="origin"
              style={{ flex: 1 }}
              rules={[{ required: true, message: '请输入出发地' }]}
            >
              <Input placeholder="如：上海青浦仓" />
            </Form.Item>
            <Form.Item
              label="目的地"
              name="destination"
              style={{ flex: 1 }}
              rules={[{ required: true, message: '请输入目的地' }]}
            >
              <Input placeholder="如：杭州萧山仓" />
            </Form.Item>
          </div>
          <Form.Item
            label="预计出发 / 到达时间"
            name="range"
            rules={[{ required: true, message: '请选择计划出发与到达时间' }]}
          >
            <RangeTimePicker />
          </Form.Item>
          <div style={{ display: 'flex', gap: 12 }}>
            <Form.Item label="货物" name="cargo" style={{ flex: 1 }}><Input /></Form.Item>
            <Form.Item label="重量(kg)" name="weight" style={{ flex: 1 }}><InputNumber style={{ width: '100%' }} min={0} /></Form.Item>
            <Form.Item label="运费(元)" name="freight" style={{ flex: 1 }}><InputNumber style={{ width: '100%' }} min={0} /></Form.Item>
          </div>
          <Form.Item label="备注" name="note"><Input.TextArea rows={2} /></Form.Item>
          {driverId && planDepartAt && planArriveAt && <ComplianceResult result={eligibility} compact />}
        </Form>
      </Modal>
    </PageShell>
  );
}

/** Form.Item 注入 value/onChange，桥接到带预检的司机选择器 */
function DriverSelectWrapper({
  value, onChange, planDepartAt, planArriveAt, onEligibilityChange,
}: {
  value?: number;
  onChange?: (v: number | undefined) => void;
  planDepartAt?: string;
  planArriveAt?: string;
  onEligibilityChange?: (result: AssignmentEligibility | null) => void;
}) {
  return (
    <DriverSelectWithPrecheck
      value={value}
      onChange={onChange}
      planDepartAt={planDepartAt}
      planArriveAt={planArriveAt}
      onEligibilityChange={(_, res) => onEligibilityChange?.(res)}
    />
  );
}

/** 两个分钟精度的时间选择（后端接受 'YYYY-MM-DD HH:mm'） */
function RangeTimePicker({ value, onChange }: { value?: [string, string]; onChange?: (v: [string, string]) => void }) {
  const toInput = (v?: string) => (v ? v.replace(' ', 'T') : undefined);
  const toValue = (v: string) => v.replace('T', ' ');
  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
      <Input
        type="datetime-local"
        value={toInput(value?.[0])}
        onChange={(e) => onChange?.([toValue(e.target.value), value?.[1] ?? ''])}
      />
      <span>~</span>
      <Input
        type="datetime-local"
        value={toInput(value?.[1])}
        onChange={(e) => onChange?.([value?.[0] ?? '', toValue(e.target.value)])}
      />
    </div>
  );
}
