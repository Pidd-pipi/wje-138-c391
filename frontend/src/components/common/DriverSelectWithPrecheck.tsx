import { useEffect, useState } from 'react';
import { Select, Spin, Tag, Tooltip } from 'antd';
import { driverApi, precheckAssignment } from '../../api/driver';
import type { AssignmentEligibility, Driver } from '../../types';

type Props = {
  value?: number;
  onChange?: (driverId: number | undefined) => void;
  /** 任务计划时间（'YYYY-MM-DD HH:mm'）；齐备时自动跑预检 */
  planDepartAt?: string;
  planArriveAt?: string;
  onEligibilityChange?: (driverId: number | undefined, result: AssignmentEligibility | null) => void;
};

/** 调度页选人控件：每个司机按当前计划时间显示能否指派及原因 */
export function DriverSelectWithPrecheck({ value, onChange, planDepartAt, planArriveAt, onEligibilityChange }: Props) {
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(false);
  const [result, setResult] = useState<AssignmentEligibility | null>(null);

  useEffect(() => {
    setLoading(true);
    driverApi.list(false)
      .then(setDrivers)
      .catch(() => setDrivers([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!value || !planDepartAt || !planArriveAt) {
      setResult(null);
      onEligibilityChange?.(value ?? undefined, null);
      return;
    }
    let cancelled = false;
    setChecking(true);
    precheckAssignment({ driverId: value, planDepartAt, planArriveAt })
      .then((res) => {
        if (cancelled) return;
        setResult(res);
        onEligibilityChange?.(value, res);
      })
      .catch(() => {
        if (!cancelled) {
          setResult(null);
          onEligibilityChange?.(value, null);
        }
      })
      .finally(() => !cancelled && setChecking(false));
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, planDepartAt, planArriveAt]);

  const selected = drivers.find((d) => d.id === value);

  return (
    <div>
      <Select
        style={{ width: '100%' }}
        placeholder={loading ? '司机加载中…' : '选择司机'}
        value={value}
        onChange={(v) => onChange?.(v)}
        showSearch
        optionFilterProp="label"
        options={drivers.map((d) => ({
          value: d.id,
          label: `${d.name}（${d.phone}）`,
        }))}
      />
      {selected && (
        <div style={{ marginTop: 6 }}>
          {checking ? (
            <span>
              <Spin size="small" /> <span style={{ color: '#888' }}>正在核对班次合规…</span>
            </span>
          ) : result ? (
            result.eligible ? (
              <Tag color="green">✓ 可指派</Tag>
            ) : (
              <Tooltip title={result.reasons.map((r, i) => <div key={i}>{r}</div>)}>
                <Tag color="red" style={{ cursor: 'help' }}>
                  ✕ 不可指派（{result.reasons.length} 项冲突，悬停查看原因）
                </Tag>
              </Tooltip>
            )
          ) : (
            <Tag>请选择计划出发/到达时间后核对</Tag>
          )}
        </div>
      )}
    </div>
  );
}
