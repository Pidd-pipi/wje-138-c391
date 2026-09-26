import { Tag } from 'antd';
export function StatusBadge({ status }: { status: string }) {
  const color = status.includes('Available') || status.includes('Completed') ? 'green' : status.includes('Maintenance') || status.includes('InProgress') ? 'orange' : 'blue';
  return <Tag color={color}>{status}</Tag>;
}
