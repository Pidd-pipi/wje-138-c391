import { useState } from 'react';
import {
  Button,
  Descriptions,
  Divider,
  Form,
  InputNumber,
  List,
  message,
  Popconfirm,
  Progress,
  Space,
  Tag,
  Typography
} from 'antd';
import { ClockCircleOutlined, FieldTimeOutlined } from '@ant-design/icons';
import type { Driver } from '../../types';
import { driverApi } from '../../api/driver';
import { formatMinutes } from '../../utils/formatMinutes';
import { StatusBadge } from '../common/StatusBadge';

/** 司机班次合规面板：今日累计、下次可接单时间、未来占用，以及档案合规配置编辑。 */
export function DriverComplianceCard({ driver, onUpdated }: { driver: Driver; onUpdated: () => void }) {
  const [saving, setSaving] = useState(false);
  const [form] = Form.useForm();
  const c = driver.compliance;

  const percent = c && c.todayLimitMinutes > 0
    ? Math.min(100, Math.round((c.todayPlannedMinutes / c.todayLimitMinutes) * 100))
    : 0;
  const overLimit = (c?.todayPlannedMinutes ?? 0) > (c?.todayLimitMinutes ?? 0);

  const save = async () => {
    const values = await form.validateFields();
    setSaving(true);
    try {
      await driverApi.updateCompliance(driver.id, {
        dailyDrivingLimitMinutes: values.daily,
        minRestMinutes: values.minRest,
        nightlyRestMinutes: values.nightlyRest
      });
      message.success('合规配置已保存');
      onUpdated();
    } catch {
      message.error('保存失败，请重试');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <Descriptions
        size="small"
        column={1}
        colon={false}
        labelStyle={{ width: 120 }}
        items={[
          {
            key: 'today',
            label: <Space><ClockCircleOutlined />今日累计</Space>,
            children: c ? (
              <Space direction="vertical" size={2} style={{ width: '100%' }}>
                <Space wrap>
                  <Typography.Text strong>
                    实际 {formatMinutes(c.todayMinutes)}
                  </Typography.Text>
                  <Typography.Text type="secondary">
                    / 含计划 {formatMinutes(c.todayPlannedMinutes)}
                  </Typography.Text>
                  <Typography.Text type="secondary">
                    上限 {formatMinutes(c.todayLimitMinutes)}
                  </Typography.Text>
                  {overLimit && <Tag color="red">已超上限</Tag>}
                </Space>
                <Progress
                  percent={percent}
                  size="small"
                  status={overLimit ? 'exception' : percent >= 90 ? 'active' : 'normal'}
                />
              </Space>
            ) : '—'
          },
          {
            key: 'next',
            label: <Space><FieldTimeOutlined />下次可接单</Space>,
            children: c ? (
              <Space wrap>
                <Typography.Text strong>{c.nextAvailableAt}</Typography.Text>
                <Tag color={c.nextAvailable ? 'green' : 'orange'}>
                  {c.nextAvailable ? '现在可接单' : '休息中'}
                </Tag>
              </Space>
            ) : '—'
          }
        ]}
      />

      <Divider style={{ margin: '10px 0' }} orientation="left" plain>
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>未来占用</Typography.Text>
      </Divider>
      <List
        size="small"
        dataSource={c?.upcoming ?? []}
        renderItem={(item) => (
          <List.Item>
            <List.Item.Meta
              title={
                <Space wrap>
                  <Typography.Text code>{item.orderNo}</Typography.Text>
                  <StatusBadge status={item.status} />
                </Space>
              }
              description={`${item.origin} → ${item.destination}　${item.startAt} ~ ${item.endAt}`}
            />
          </List.Item>
        )}
      />

      <Divider style={{ margin: '10px 0' }} orientation="left" plain>
        <Typography.Text type="secondary" style={{ fontSize: 12 }}>班次合规配置（分钟）</Typography.Text>
      </Divider>
      <Form
        form={form}
        layout="inline"
        initialValues={{
          daily: driver.dailyDrivingLimitMinutes,
          minRest: driver.minRestMinutes,
          nightlyRest: driver.nightlyRestMinutes
        }}
      >
        <Form.Item
          name="daily"
          label="每日驾驶上限"
          rules={[{ required: true, message: '必填' }]}
        >
          <InputNumber min={0} step={30} addonAfter="分" style={{ width: 130 }} />
        </Form.Item>
        <Form.Item name="minRest" label="任务间最短休息" rules={[{ required: true, message: '必填' }]}>
          <InputNumber min={0} step={15} addonAfter="分" style={{ width: 130 }} />
        </Form.Item>
        <Form.Item name="nightlyRest" label="夜间连续休息" rules={[{ required: true, message: '必填' }]}>
          <InputNumber min={0} step={30} addonAfter="分" style={{ width: 130 }} />
        </Form.Item>
        <Form.Item>
          <Popconfirm title="保存该司机的合规配置？" onConfirm={save}>
            <Button type="primary" loading={saving}>保存配置</Button>
          </Popconfirm>
        </Form.Item>
      </Form>
    </div>
  );
}
