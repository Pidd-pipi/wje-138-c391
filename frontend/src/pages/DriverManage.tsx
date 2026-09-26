import { useEffect, useState } from 'react';
import { Button, Card, Col, Form, InputNumber, Modal, Progress, Row, Tag, message } from 'antd';
import { driverApi, type ComplianceSettingsPayload } from '../api/driver';
import type { Driver } from '../types';
import { UserAvatar } from '../components/common/UserAvatar';
import { StatusBadge } from '../components/common/StatusBadge';
import { PageShell } from './PageShell';
import { describeAvailability, formatDateTime, formatMinutes } from '../utils/complianceFormat';

export function DriverManage() {
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [editing, setEditing] = useState<Driver | null>(null);

  const reload = () =>
    driverApi.list(true).then(setDrivers).catch(() => setDrivers([]));
  useEffect(() => { reload(); }, []);

  return (
    <PageShell title="司机管理">
      <Row gutter={[16, 16]}>
        {drivers.map((driver) => {
          const schedule = driver.schedule;
          const availability = schedule
            ? describeAvailability(schedule.nextAvailableAt)
            : null;
          const percent = schedule?.dailyLimitMinutes
            ? Math.min(100, Math.round((schedule.todayUsedMinutes / schedule.dailyLimitMinutes) * 100))
            : 0;
          const overLimit = (schedule?.todayRemainingMinutes ?? 0) < 0;
          return (
            <Col xs={24} md={12} key={driver.id}>
              <Card
                title={
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <UserAvatar name={driver.name} />
                    <div>
                      <div style={{ fontWeight: 600 }}>
                        {driver.name}
                        <StatusBadge status={driver.status} />
                      </div>
                      <div style={{ color: '#999', fontSize: 12 }}>{driver.phone} · {driver.licenseType}</div>
                    </div>
                  </div>
                }
                extra={<Button size="small" onClick={() => setEditing(driver)}>合规配置</Button>}
              >
                {schedule && (
                  <>
                    <div style={{ marginBottom: 8 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span>今日累计驾驶</span>
                        <span style={{ color: overLimit ? '#cf1322' : undefined, fontWeight: 600 }}>
                          {formatMinutes(schedule.todayUsedMinutes)}
                          {schedule.dailyLimitMinutes ? ` / 上限 ${formatMinutes(schedule.dailyLimitMinutes)}` : '（不限）'}
                        </span>
                      </div>
                      {schedule.dailyLimitMinutes ? (
                        <Progress percent={percent} size="small" status={overLimit ? 'exception' : 'active'} />
                      ) : null}
                      {schedule.todayRemainingMinutes !== null && (
                        <div style={{ color: overLimit ? '#cf1322' : '#888', fontSize: 12 }}>
                          {overLimit
                            ? `今日已超 ${formatMinutes(Math.abs(schedule.todayRemainingMinutes))}，不可再派`
                            : `今日剩余可驾驶 ${formatMinutes(schedule.todayRemainingMinutes)}`}
                        </div>
                      )}
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      <span>下次可接单：</span>
                      <Tag color={availability?.available ? 'green' : 'red'}>
                        {availability?.text}
                      </Tag>
                    </div>
                    <div>
                      <div style={{ color: '#666', marginBottom: 4 }}>未来占用（{schedule.upcoming.length} 单）</div>
                      {schedule.upcoming.length === 0 ? (
                        <span style={{ color: '#aaa' }}>暂无已排任务</span>
                      ) : (
                        schedule.upcoming.map((item) => (
                          <div key={item.orderNo} style={{ fontSize: 13, marginBottom: 2 }}>
                            <Tag color="blue">{item.status === 'InProgress' ? '运输中' : '已排班'}</Tag>
                            <span style={{ fontFamily: 'monospace' }}>{item.orderNo}</span>{' '}
                            {formatDateTime(item.start)} ~ {formatDateTime(item.end)}{' '}
                            {item.origin} → {item.destination}
                          </div>
                        ))
                      )}
                    </div>
                    <div style={{ marginTop: 8, color: '#999', fontSize: 12 }}>
                      档案规则：每日上限 {formatMinutes(driver.dailyDriveLimitMinutes)} ·
                      任务间隔 {formatMinutes(driver.minRestMinutes)} ·
                      夜间连续休息 {formatMinutes(driver.nightRestMinutes)}（22:00-次日06:00）
                    </div>
                  </>
                )}
              </Card>
            </Col>
          );
        })}
      </Row>

      <ComplianceSettingsModal
        driver={editing}
        onClose={() => setEditing(null)}
        onSaved={(updated) => {
          setDrivers((prev) => prev.map((d) => (d.id === updated.id ? { ...d, ...updated } : d)));
          setEditing(null);
          message.success('合规配置已更新');
        }}
      />
    </PageShell>
  );
}

function ComplianceSettingsModal({
  driver, onClose, onSaved,
}: {
  driver: Driver | null;
  onClose: () => void;
  onSaved: (driver: Driver) => void;
}) {
  const [form] = Form.useForm<ComplianceSettingsPayload>();
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (driver) {
      form.setFieldsValue({
        dailyDriveLimitMinutes: driver.dailyDriveLimitMinutes,
        minRestMinutes: driver.minRestMinutes,
        nightRestMinutes: driver.nightRestMinutes,
      });
    }
  }, [driver, form]);

  const handleOk = async () => {
    if (!driver) return;
    const values = await form.validateFields();
    setSaving(true);
    try {
      const updated = await driverApi.updateCompliance(driver.id, values);
      onSaved(updated);
    } catch (error) {
      message.error(error instanceof Error ? error.message : '保存失败');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal
      title={`班次合规配置 · ${driver?.name ?? ''}`}
      open={!!driver}
      onCancel={onClose}
      onOk={handleOk}
      confirmLoading={saving}
      okText="保存"
    >
      <p style={{ color: '#999' }}>三项均为分钟数，填 0 表示不启用该限制。建单与发车时会自动核对。</p>
      <Form form={form} layout="vertical">
        <Form.Item
          label="每日驾驶上限（分钟）"
          name="dailyDriveLimitMinutes"
          tooltip="按当地日历日统计已完成、进行中与已计划任务的驾驶时长合计"
          rules={[{ required: true, message: '请输入每日驾驶上限' }]}
        >
          <InputNumber min={0} step={30} style={{ width: '100%' }} addonAfter="分钟" />
        </Form.Item>
        <Form.Item
          label="相邻任务最短休息（分钟）"
          name="minRestMinutes"
          tooltip="新任务与前序/后继任务之间必须留出的空档"
          rules={[{ required: true, message: '请输入最短休息' }]}
        >
          <InputNumber min={0} step={15} style={{ width: '100%' }} addonAfter="分钟" />
        </Form.Item>
        <Form.Item
          label="夜间最短连续休息（分钟，22:00-次日06:00）"
          name="nightRestMinutes"
          tooltip="跨夜任务空档中必须包含一个完整的夜间连续休息（默认 480 分钟）"
          rules={[{ required: true, message: '请输入夜间连续休息' }]}
        >
          <InputNumber min={0} step={30} style={{ width: '100%' }} addonAfter="分钟" />
        </Form.Item>
      </Form>
    </Modal>
  );
}
