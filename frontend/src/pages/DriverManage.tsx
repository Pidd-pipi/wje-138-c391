import { useEffect, useMemo, useState } from 'react';
import { Card, Col, Empty, List, Row, Select, Space, Statistic, Tag } from 'antd';
import { driverApi } from '../api/driver';
import type { Driver } from '../types';
import { DriverStatus } from '../types/enums';
import { UserAvatar } from '../components/common/UserAvatar';
import { StatusBadge } from '../components/common/StatusBadge';
import { DriverComplianceCard } from '../components/driver/DriverComplianceCard';
import { PageShell } from './PageShell';
import { formatMinutes } from '../utils/formatMinutes';

export function DriverManage() {
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [selectedId, setSelectedId] = useState<number | null>(null);

  const load = () => {
    driverApi
      .list()
      .then((list) => {
        setDrivers(list);
        setSelectedId((prev) => prev ?? list[0]?.id ?? null);
      })
      .catch(() => setDrivers([]));
  };
  useEffect(load, []);

  const filtered = useMemo(
    () => (statusFilter === 'all' ? drivers : drivers.filter((d) => d.status === statusFilter)),
    [drivers, statusFilter]
  );
  const selected = drivers.find((d) => d.id === selectedId) ?? null;

  return (
    <PageShell title="司机管理">
      <Row gutter={16}>
        <Col xs={24} md={11} lg={9}>
          <Card
            title="司机列表"
            extra={
              <Select
                size="small"
                value={statusFilter}
                onChange={setStatusFilter}
                style={{ width: 120 }}
                options={[
                  { value: 'all', label: '全部状态' },
                  { value: DriverStatus.Available, label: '空闲' },
                  { value: DriverStatus.OnTrip, label: '在途' },
                  { value: DriverStatus.Leave, label: '休假' },
                  { value: DriverStatus.Suspended, label: '停职' }
                ]}
              />
            }
          >
            <List
              dataSource={filtered}
              renderItem={(driver) => {
                const c = driver.compliance;
                const active = driver.id === selectedId;
                return (
                  <List.Item
                    onClick={() => setSelectedId(driver.id)}
                    style={{
                      cursor: 'pointer',
                      padding: '12px 10px',
                      borderRadius: 8,
                      background: active ? '#f0faf8' : undefined,
                      border: active ? '1px solid #0f766e' : undefined
                    }}
                  >
                    <List.Item.Meta
                      avatar={<UserAvatar name={driver.name} />}
                      title={
                        <Space wrap>
                          {driver.name}
                          <StatusBadge status={driver.status} />
                        </Space>
                      }
                      description={
                        <Space direction="vertical" size={2}>
                          <span>{driver.phone}</span>
                          <Space size={4} wrap>
                            <Tag color={c?.nextAvailable ? 'green' : 'orange'}>
                              {c?.nextAvailable ? '可接单' : `可接单 ${c?.nextAvailableAt ?? '-'}`}
                            </Tag>
                            <Tag>
                              今日 {formatMinutes(c?.todayMinutes ?? 0)}/
                              {formatMinutes(c?.todayLimitMinutes ?? 0)}
                            </Tag>
                          </Space>
                        </Space>
                      }
                    />
                  </List.Item>
                );
              }}
            />
          </Card>
        </Col>
        <Col xs={24} md={13} lg={15}>
          <Card title={selected ? `${selected.name} · 班次合规` : '班次合规'}>
            {selected ? (
              <Space direction="vertical" size={16} style={{ width: '100%' }}>
                <Row gutter={12}>
                  <Col span={8}>
                    <Statistic
                      title="今日实际驾驶"
                      value={formatMinutes(selected.compliance?.todayMinutes ?? 0)}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="含今日计划"
                      value={formatMinutes(selected.compliance?.todayPlannedMinutes ?? 0)}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="未来占用"
                      value={selected.compliance?.upcoming.length ?? 0}
                      suffix="单"
                    />
                  </Col>
                </Row>
                <DriverComplianceCard driver={selected} onUpdated={load} />
              </Space>
            ) : (
              <Empty description="选择左侧司机查看班次合规" />
            )}
          </Card>
        </Col>
      </Row>
    </PageShell>
  );
}
