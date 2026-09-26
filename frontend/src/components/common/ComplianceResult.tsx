import { Alert, Tag } from 'antd';
import { CheckCircleFilled, CloseCircleFilled } from '@ant-design/icons';
import type { AssignmentEligibility } from '../../types';

/** 选人/建单/发车预检结果：可指派绿条；冲突红条逐条列出原因（含单号、还缺时间） */
export function ComplianceResult({ result, compact }: { result: AssignmentEligibility | null; compact?: boolean }) {
  if (!result) return null;
  if (result.eligible) {
    return (
      <Alert
        type="success"
        showIcon
        icon={<CheckCircleFilled />}
        message="班次合规预检通过，可以指派"
        style={{ marginTop: 12 }}
      />
    );
  }
  return (
    <Alert
      type="error"
      showIcon
      icon={<CloseCircleFilled />}
      style={{ marginTop: 12 }}
      message={
        <span>
          不可指派（{result.reasons.length} 项冲突），调度单不会进入执行
          {result.blockedUntil && <Tag color="red" style={{ marginLeft: 8 }}>放行时间 {result.blockedUntil.slice(5, 16).replace('T', ' ')}</Tag>}
        </span>
      }
      description={
        <ul style={{ margin: 0, paddingLeft: 18 }}>
          {result.violations.map((v, idx) => (
            <li key={idx} style={{ marginBottom: compact ? 0 : 4 }}>
              <Tag color={tagColor(v.rule)} style={{ marginRight: 6 }}>{ruleLabel(v.rule)}</Tag>
              {v.message}
            </li>
          ))}
        </ul>
      }
    />
  );
}

function ruleLabel(rule: string): string {
  switch (rule) {
    case 'daily_limit': return '当日累计';
    case 'min_rest': return '间隔休息';
    case 'night_rest': return '夜间休息';
    case 'overlap': return '时间重叠';
    case 'driver_status': return '司机状态';
    default: return '时间';
  }
}

function tagColor(rule: string): string {
  if (rule === 'night_rest') return 'purple';
  if (rule === 'daily_limit') return 'orange';
  if (rule === 'overlap') return 'red';
  return 'default';
}
