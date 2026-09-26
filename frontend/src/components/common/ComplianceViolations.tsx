import { Alert, Space, Tag, Tooltip, Typography } from 'antd';
import { ExclamationCircleFilled, CheckCircleFilled } from '@ant-design/icons';
import type { ComplianceViolation } from '../../types';

const TYPE_LABEL: Record<string, string> = {
  daily_limit: '当日驾驶上限',
  min_rest: '任务间休息不足',
  nightly_rest: '夜间连续休息不足',
  overlap: '任务时间重叠'
};

const TYPE_COLOR: Record<string, string> = {
  daily_limit: 'volcano',
  min_rest: 'orange',
  nightly_rest: 'red',
  overlap: 'magenta'
};

/** 单条冲突：标签 + 单号 + 中文原因（含还缺时间）。 */
export function ComplianceViolationTag({ violation }: { violation: ComplianceViolation }) {
  return (
    <Tooltip title={violation.message}>
      <Tag icon={<ExclamationCircleFilled />} color={TYPE_COLOR[violation.type] ?? 'default'}>
        {TYPE_LABEL[violation.type] ?? violation.type}
        {violation.orderNo ? `·${violation.orderNo}` : ''}
      </Tag>
    </Tooltip>
  );
}

/** 冲突列表（建单/发车被拦截时的完整说明）。 */
export function ComplianceViolationList({
  violations,
  title = '司机班次合规预检未通过，调度单不进入执行'
}: {
  violations: ComplianceViolation[];
  title?: string;
}) {
  if (!violations.length) {
    return (
      <Alert
        type="success"
        showIcon
        icon={<CheckCircleFilled />}
        message="合规预检通过，可以指派"
      />
    );
  }
  return (
    <Alert
      type="error"
      showIcon
      message={title}
      description={
        <Space direction="vertical" size={6} style={{ width: '100%' }}>
          {violations.map((v, idx) => (
            <div key={`${v.type}-${idx}`}>
              <Space size={4} wrap>
                <ComplianceViolationTag violation={v} />
                {v.missingMinutes > 0 && <Tag color="red">还缺 {v.missingMinutes} 分钟</Tag>}
              </Space>
              <Typography.Text type="secondary" style={{ display: 'block', fontSize: 12 }}>
                {v.message}
              </Typography.Text>
            </div>
          ))}
        </Space>
      }
    />
  );
}
