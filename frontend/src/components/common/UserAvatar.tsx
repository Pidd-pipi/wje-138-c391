import { Avatar } from 'antd';
export function UserAvatar({ name }: { name: string }) {
  return <Avatar style={{ background: '#0f766e' }}>{name.slice(0, 1)}</Avatar>;
}
