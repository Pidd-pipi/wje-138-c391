import { Badge, Card } from 'antd';
export function CalendarCell({ date, title }: { date: string; title: string }) {
  return <Card size="small"><Badge status="processing" text={date} /><div>{title}</div></Card>;
}
