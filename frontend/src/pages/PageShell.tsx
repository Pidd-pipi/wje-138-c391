import { NavLink } from 'react-router-dom';
const nav = [['/dispatch','调度中心'],['/vehicles','车辆管理'],['/drivers','司机管理'],['/maintenance','维保管理'],['/fuel-analytics','油耗分析']];
export function PageShell({ title, children }: { title: string; children: React.ReactNode }) {
  return <div className="layout"><aside className="sidebar"><div className="brand">车队调度<br/>维护平台</div><nav className="nav">{nav.map(([to,label]) => <NavLink key={to} to={to}>{label}</NavLink>)}</nav></aside><main className="main"><div className="head"><h1>{title}</h1></div>{children}</main></div>;
}
