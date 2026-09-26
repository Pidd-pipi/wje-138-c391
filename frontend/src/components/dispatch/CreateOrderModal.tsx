import { useEffect, useMemo, useState } from 'react';
import {
  DatePicker,
  Form,
  Input,
  InputNumber,
  Modal,
  Select,
  Space,
  Spin,
  Tag,
  Typography
} from 'antd';
import dayjs, { type Dayjs } from 'dayjs';
import type { Driver, Vehicle } from '../../types';
import { driverApi } from '../../api/driver';
import { dispatchApi } from '../../api/dispatch';
import type { AssignmentCheck } from '../../types';
import { ApiError } from '../../utils/request';
import { formatMinutes } from '../../utils/formatMinutes';
import { ComplianceViolationList } from '../common/ComplianceViolations';

const { RangePicker } = DatePicker;

interface FormValues {
  range: [Dayjs, Dayjs];
  origin: string;
  destination: string;
  cargo?: string;
  weight?: number;
  freight?: number;
  note?: string;
  vehicleId?: number;
  driverId?: number;
}

/** 创建调度单弹窗：选司机时实时预检，展示能否指派及原因；冲突时不提交。 */
export function CreateOrderModal({
  open,
  drivers,
  vehicles,
  onClose,
  onCreated
}: {
  open: boolean;
  drivers: Driver[];
  vehicles: Vehicle[];
  onClose: () => void;
  onCreated: () => void;
}) {
  const [form] = Form.useForm<FormValues>();
  const [submitting, setSubmitting] = useState(false);
  const [checking, setChecking] = useState(false);
  const [check, setCheck] = useState<AssignmentCheck | null>(null);
  const [submitError, setSubmitError] = useState<{ violations: any[]; message: string } | null>(null);

  const range = Form.useWatch('range', form);
  const driverId = Form.useWatch('driverId', form);

  useEffect(() => {
    if (!open) {
      form.resetFields();
      setCheck(null);
      setSubmitError(null);
    }
  }, [open, form]);

  // 选人/改时间后实时预检（仅当司机与计划时间齐备）
  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      if (!driverId || !range || !range[0] || !range[1]) {
        setCheck(null);
        return;
      }
      setChecking(true);
      try {
        const result = await driverApi.assignmentCheck(driverId, {
          planDepartAt: range[0].format('YYYY-MM-DD HH:mm'),
          planArriveAt: range[1].format('YYYY-MM-DD HH:mm')
        });
        if (!cancelled) setCheck(result);
      } finally {
        if (!cancelled) setChecking(false);
      }
    };
    run();
    return () => {
      cancelled = true;
    };
  }, [driverId, range]);

  const selectedDriver = useMemo(
    () => drivers.find((d) => d.id === driverId) ?? null,
    [drivers, driverId]
  );

  const submit = async () => {
    const values = await form.validateFields();
    setSubmitError(null);
    setSubmitting(true);
    try {
      await dispatchApi.create({
        vehicleId: values.vehicleId ?? null,
        driverId: values.driverId ?? null,
        origin: values.origin,
        destination: values.destination,
        planDepartAt: values.range[0].format('YYYY-MM-DD HH:mm'),
        planArriveAt: values.range[1].format('YYYY-MM-DD HH:mm'),
        cargo: values.cargo ?? '',
        weight: values.weight ?? 0,
        freight: values.freight ?? 0,
        note: values.note ?? ''
      });
      onCreated();
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setSubmitError({ violations: err.data?.violations ?? [], message: err.message });
      } else if (err instanceof ApiError) {
        setSubmitError({ violations: [], message: err.message });
      } else {
        setSubmitError({ violations: [], message: (err as Error).message });
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      title="创建调度单"
      open={open}
      onCancel={onClose}
      onOk={submit}
      confirmLoading={submitting}
      okText="创建并指派"
      cancelText="取消"
      width={620}
      destroyOnClose
      okButtonProps={{ danger: !!check && !check.assignable }}
    >
      <Form form={form} layout="vertical" preserve={false}>
        <Form.Item label="计划出发 / 到达时间" name="range" rules={[{ required: true, message: '请选择时间' }]}>
          <RangePicker showTime={{ format: 'HH:mm' }} format="YYYY-MM-DD HH:mm" style={{ width: '100%' }} />
        </Form.Item>
        <Space style={{ display: 'flex' }} align="start">
          <Form.Item label="出发地" name="origin" style={{ flex: 1 }} rules={[{ required: true, message: '必填' }]}>
            <Input placeholder="出发地" />
          </Form.Item>
          <Form.Item label="目的地" name="destination" style={{ flex: 1 }} rules={[{ required: true, message: '必填' }]}>
            <Input placeholder="目的地" />
          </Form.Item>
        </Space>
        <Form.Item label="指派车辆" name="vehicleId">
          <Select
            allowClear
            placeholder="可稍后指派"
            options={vehicles.map((v) => ({
              value: v.id,
              label: `${v.plateNo} · ${v.type} ${v.brandModel}`
            }))}
          />
        </Form.Item>
        <Form.Item label="指派司机（实时合规预检）" name="driverId">
          <Select
            allowClear
            placeholder="可稍后指派"
            showSearch
            optionFilterProp="label"
            options={drivers.map((d) => {
              const c = d.compliance;
              return {
                value: d.id,
                label: `${d.name}（${d.phone}）`,
                tag: c?.nextAvailable ? '可接单' : `休息至 ${c?.nextAvailableAt ?? ''}`
              };
            })}
            optionRender={(option) => {
              const d = drivers.find((x) => x.id === option.value);
              const c = d?.compliance;
              return (
                <Space size={6} wrap>
                  <span>{option.label}</span>
                  <Tag color={c?.nextAvailable ? 'green' : 'orange'} style={{ marginInlineStart: 0 }}>
                    {c?.nextAvailable ? '可接单' : `休息至 ${c?.nextAvailableAt ?? ''}`}
                  </Tag>
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                    今日 {formatMinutes(c?.todayPlannedMinutes ?? 0)}/
                    {formatMinutes(c?.todayLimitMinutes ?? 0)}
                  </Typography.Text>
                </Space>
              );
            }}
          />
        </Form.Item>
        <Space style={{ display: 'flex' }} align="start">
          <Form.Item label="货物" name="cargo" style={{ flex: 1 }}>
            <Input placeholder="货物描述" />
          </Form.Item>
          <Form.Item label="重量(kg)" name="weight">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item label="运费" name="freight">
            <InputNumber min={0} style={{ width: '100%' }} />
          </Form.Item>
        </Space>
        <Form.Item label="备注" name="note">
          <Input.TextArea rows={2} />
        </Form.Item>
      </Form>

      {checking && (
        <Space>
          <Spin size="small" />
          <Typography.Text type="secondary">正在核对班次合规…</Typography.Text>
        </Space>
      )}

      {!checking && selectedDriver && check && (
        <ComplianceViolationList
          violations={check.violations}
          title={
            check.assignable
              ? `合规预检通过：可指派 ${selectedDriver.name}`
              : `无法指派 ${selectedDriver.name}，调度单不会进入执行`
          }
        />
      )}

      {submitError && (
        <div style={{ marginTop: 12 }}>
          <ComplianceViolationList violations={submitError.violations} title={submitError.message} />
        </div>
      )}
    </Modal>
  );
}
