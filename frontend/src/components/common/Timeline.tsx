import { Timeline as AntTimeline } from 'antd';
export function Timeline({ items }: { items: string[] }) {
  return <AntTimeline items={items.map((children) => ({ children }))} />;
}
