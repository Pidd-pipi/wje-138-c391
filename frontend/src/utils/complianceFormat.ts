/** 分钟数格式化为「x小时y分钟」。 */
export function formatMinutes(minutes: number | null | undefined): string {
  if (minutes === null || minutes === undefined) return '不限';
  const value = Math.round(minutes);
  if (value <= 0) return '0分钟';
  const hours = Math.floor(value / 60);
  const rest = value % 60;
  if (hours && rest) return `${hours}小时${rest}分钟`;
  if (hours) return `${hours}小时`;
  return `${rest}分钟`;
}

function parseDate(value: string): Date {
  // 后端返回 'YYYY-MM-DD HH:MM' 或 ISO，统一可解析
  return new Date(value.includes('T') ? value : value.replace(' ', 'T'));
}

const pad = (n: number) => String(n).padStart(2, '0');

/** 'MM-DD HH:mm' */
export function formatDateTime(value?: string | null): string {
  if (!value) return '—';
  const d = parseDate(value);
  if (Number.isNaN(d.getTime())) return value;
  return `${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** 完整 'YYYY-MM-DD HH:mm'，用于表单提交 */
export function formatDateTimeFull(value?: string | null): string {
  if (!value) return '—';
  const d = parseDate(value);
  if (Number.isNaN(d.getTime())) return value;
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/** 相对当前时间的友好提示：可接单 / 还需等待 */
export function describeAvailability(nextAvailableAt: string, now = new Date()): { text: string; available: boolean } {
  const target = parseDate(nextAvailableAt);
  if (Number.isNaN(target.getTime())) return { text: '—', available: true };
  const diffMin = Math.round((target.getTime() - now.getTime()) / 60000);
  if (diffMin <= 0) return { text: '现在可接单', available: true };
  return { text: `${formatDateTimeFull(nextAvailableAt)} 后可接单（还需等待 ${formatMinutes(diffMin)}）`, available: false };
}
